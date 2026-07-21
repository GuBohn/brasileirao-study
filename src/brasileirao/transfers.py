"""Acquire Brazilian mid-season departures by scraping Transfermarkt's per-club
transfer pages.

Why not the open dcaribou dump: its transfers table is limited to a recent-biased
player universe, so it undercounts historical departures badly (~64 total; a single
big club has that many alone). Transfermarkt's club-season transfer page lists
*every* departure with fee and destination, and its summer/winter window filter
(`w_s=s`) isolates the mid-Brasileirao-season (Jul-Aug) moves directly — so we need
no exact transfer date, the window itself is the treatment.

Scraping is rate-limited, cached per club-season to data/raw, and fails loud on an
unmapped club or a page whose expected structure is missing (a ban or layout drift).
Match results and Elo still come from matches.parquet, never from here.
"""
import re
import time
import urllib.request

import pandas as pd
from bs4 import BeautifulSoup

from . import ingest
from .paths import RAW

# Transfermarkt club_id -> our canonical Serie A club name. IDs (not names) are the
# join key. Covers every club that played Serie A in 2012-2024.
SERIE_A_CLUB_IDS = {
    17776: "Chapecoense", 2029: "Ceara", 978: "Vasco", 330: "Atletico-MG",
    679: "Athletico-PR", 614: "Flamengo", 776: "Coritiba", 609: "Cruzeiro",
    10010: "Bahia", 10492: "Juventude", 2125: "Vitoria", 2462: "Fluminense",
    10870: "Fortaleza", 210: "Gremio", 8793: "Bragantino", 537: "Botafogo-RJ",
    221: "Santos", 1023: "Palmeiras", 199: "Corinthians", 6600: "Internacional",
    8718: "Sport", 585: "Sao Paulo",
    2863: "America-MG", 3197: "Goias", 1134: "Ponte Preta", 2035: "Avai",
    28022: "Cuiaba", 15172: "Atletico-GO", 18545: "CSA", 4064: "Figueirense",
    3330: "Joinville", 7178: "Criciuma", 2646: "Nautico", 309: "Parana",
    10247: "Portuguesa", 1785: "Santa Cruz",
}
CANON_TO_ID = {v: k for k, v in SERIE_A_CLUB_IDS.items()}

FIRST_SEASON, LAST_SEASON = 2012, 2024
EXCLUDE_SEASONS = {2020}                     # COVID-shifted calendar (summer pre-kickoff)
# Summer window (w_s/s) of season YYYY = Jul-Aug YYYY = mid Brasileirao season YYYY.
URL = ("https://www.transfermarkt.com/x/transfers/verein/{cid}"
       "/saison_id/{year}/pos//detailpos/0/w_s/s")
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}
REQUEST_DELAY_S = 3.5                         # courtesy delay between live fetches
CACHE = RAW / "tm"

DEPARTURE_COLS = ["club", "season", "player", "to_club", "to_dest",
                  "to_foreign", "fee_eur", "transfer_type"]

# Transfermarkt writes the Brazilian tiers as "Série A/B/C/D" (accented) and its
# lower/regional destinations as "Brazil"; Italy's "Serie A" has no accent, so the
# marker set below cleanly separates domestic moves from moves abroad. A release
# (no club) is not a move abroad.
_BR_MARKERS = ("Série", "Brazil")
_NON_CLUB = ("Without Club", "Career break", "Retired", "Unknown")


def _is_foreign(to_dest: str) -> bool:
    if any(k in to_dest for k in _NON_CLUB):
        return False
    return not any(k in to_dest for k in _BR_MARKERS)

_FEE_RE = re.compile(r"€\s*([\d.,]+)\s*(bn|m|k)?", re.I)
_UNIT = {"bn": 1e9, "m": 1e6, "k": 1e3, "": 1.0}


def _parse_fee(text: str) -> tuple[float | None, str]:
    """Parse a Transfermarkt fee cell into (fee_eur, transfer_type).

    type: 'loan' (loan or loan-with-fee), 'free' (free transfer, fee 0),
    'permanent' (a cash sale or an undisclosed permanent move). fee_eur is the
    euro amount when shown, 0.0 for a free transfer, and None when undisclosed
    ('?', '-', 'draft')."""
    t = text.strip().lower()
    if "loan" in t:
        typ = "loan"
    elif "free" in t:
        typ = "free"
    else:
        typ = "permanent"
    m = _FEE_RE.search(text)
    fee = None
    if m:
        fee = float(m.group(1).replace(",", "")) * _UNIT[(m.group(2) or "").lower()]
    elif typ == "free":
        fee = 0.0
    return fee, typ


def _fetch(cid: int, year: int) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{cid}_{year}_s.html"
    if not path.exists():
        req = urllib.request.Request(URL.format(cid=cid, year=year), headers=HEADERS)
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
        # A real transfers page always carries both section headers; their absence
        # means an anti-bot page or a layout change - never cache that.
        if "Departures" not in html or "Arrivals" not in html:
            raise ValueError(
                f"club {cid} season {year}: transfers page missing expected "
                "sections (blocked, rate-limited, or layout drift). Not cached."
            )
        path.write_text(html, encoding="utf-8")
        time.sleep(REQUEST_DELAY_S)
    return path.read_text(encoding="utf-8")


def parse_departures(html: str, club: str, season: int) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    header = next((h for h in soup.find_all(["h2", "h3"])
                   if h.get_text(strip=True) == "Departures"), None)
    if header is None:
        raise ValueError(f"{club} {season}: 'Departures' header not found")
    table = header.find_next("table", class_="items")
    rows = []
    if table is None:
        return rows                          # a club-season with zero departures
    for tr in table.select("tbody tr"):
        name = tr.select_one("td.hauptlink a")
        tds = tr.find_all("td", recursive=False)
        if name is None or len(tds) < 3:
            continue
        dest_cell = tds[-2]
        # The destination cell nests a logo link (empty text) plus the club-name
        # link (td.hauptlink) plus a league link; take the club name specifically.
        club_link = (dest_cell.select_one("td.hauptlink a")
                     or next((a for a in dest_cell.find_all("a")
                              if a.get_text(strip=True)), None))
        fee, typ = _parse_fee(tds[-1].get_text(" ", strip=True))
        to_dest = dest_cell.get_text(" ", strip=True)
        rows.append({
            "club": club, "season": season, "player": name.get_text(strip=True),
            "to_club": (club_link.get_text(strip=True) if club_link else to_dest),
            "to_dest": to_dest, "to_foreign": _is_foreign(to_dest),
            "fee_eur": fee, "transfer_type": typ,
        })
    return rows


def _serie_a_club_seasons(matches: pd.DataFrame) -> list[tuple[str, int]]:
    m = matches[matches["season"].between(FIRST_SEASON, LAST_SEASON)
                & ~matches["season"].isin(EXCLUDE_SEASONS)]
    pairs = (set(zip(m["home_team"], m["season"]))
             | set(zip(m["away_team"], m["season"])))
    unmapped = sorted({c for c, _ in pairs} - set(CANON_TO_ID))
    if unmapped:
        raise ValueError(
            f"Serie A clubs with no Transfermarkt id in SERIE_A_CLUB_IDS: {unmapped}"
        )
    return sorted(pairs)


def build(matches: pd.DataFrame | None = None, limit: int | None = None) -> pd.DataFrame:
    """Scrape (or read from cache) the summer-window departures for every Serie A
    club-season 2012-2024 (excl. 2020) and return the canonical departures table.
    `limit` caps how many club-seasons are fetched (for a smoke test)."""
    matches = ingest.load() if matches is None else matches
    pairs = _serie_a_club_seasons(matches)
    if limit is not None:
        pairs = pairs[:limit]
    rows = []
    for club, season in pairs:
        html = _fetch(CANON_TO_ID[club], season)
        rows.extend(parse_departures(html, club, season))
    out = (pd.DataFrame(rows, columns=DEPARTURE_COLS)
           .drop_duplicates(["club", "season", "player", "to_club"])
           .sort_values(["season", "club"])
           .reset_index(drop=True))
    return out
