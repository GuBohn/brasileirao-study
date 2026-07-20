"""Acquire Brazilian outbound transfer events from the open dcaribou dump.

Source: dcaribou/transfermarkt-datasets, published weekly to a public
Cloudflare-R2 bucket as gzipped CSVs. The Brazilian Serie A (BRA1) is in scope.
Events are keyed on Transfermarkt `club_id`, never on club name: names collide
badly (youth "U20"/"B" sides, foreign "Sporting", Atletico-PR vs Atletico-MG),
and substring matching was verified to inflate the treated set. Match results
and Elo come from matches.parquet, not from here.
"""
import gzip
import urllib.request

import pandas as pd

from .paths import RAW

R2 = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data"
TRANSFERS_URL = f"{R2}/transfers.csv.gz"
CLUBS_URL = f"{R2}/clubs.csv.gz"

# Transfermarkt club_id -> our canonical Serie A club name. The first block is
# the 22 current BRA1 clubs in our universe; the second is now-relegated Serie A
# clubs whose ids clubs.csv does not label (it carries only current top-flight
# + European clubs). Ids verified against the dump. Extend when the BRA1 drift
# guard (see _check_bra1_mapped) lists a new promoted club.
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
}

WINDOW_MONTHS = (7, 8)               # European summer window = mid Brasileirao season
FIRST_SEASON, LAST_SEASON = 2012, 2024
EXCLUDE_SEASONS = {2020}             # COVID-shifted calendar: summer window pre-kickoff
# Transfermarkt month-boundary stand-ins for an unknown exact day.
PLACEHOLDER_MD = {"01-01", "02-01", "06-30", "07-01", "12-01", "12-31"}

DEPARTURE_COLS = ["club", "season", "transfer_date", "is_placeholder_date",
                  "player", "market_value_eur", "to_club"]


def _download_gz(url: str, path) -> None:
    if path.exists():
        return
    # The R2 bucket 403s the default Python-urllib User-Agent (Cloudflare
    # bot-blocking); a browser-like UA is required.
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(path, "wb") as out:
        out.write(resp.read())
    with gzip.open(path, "rb") as fh:
        head = fh.read(64)
    if len(head) == 0 or head[:1] == b"\x00":
        path.unlink()
        raise ValueError(
            f"Downloaded {url} looks corrupt (empty/NUL); deleted {path.name} "
            "so a re-run retries the fetch."
        )


def load_raw(name: str, url: str) -> pd.DataFrame:
    path = RAW / name
    _download_gz(url, path)
    return pd.read_csv(path, compression="gzip")


def _check_bra1_mapped(clubs: pd.DataFrame) -> None:
    """Every current BRA1 club id must be mapped, or fail loud (schema/roster
    drift). Mirrors geo.py's unmapped-name test discipline."""
    bra1 = set(clubs.loc[clubs["domestic_competition_id"] == "BRA1", "club_id"])
    unmapped = sorted(bra1 - set(SERIE_A_CLUB_IDS))
    if unmapped:
        raise ValueError(
            f"Current BRA1 club ids not in SERIE_A_CLUB_IDS: {unmapped}. "
            "Add them (id -> canonical name) after confirming each in the dump."
        )


def build_departures(transfers: pd.DataFrame, clubs: pd.DataFrame,
                     matches: pd.DataFrame) -> pd.DataFrame:
    _check_bra1_mapped(clubs)
    df = transfers.copy()
    df["club"] = df["from_club_id"].map(SERIE_A_CLUB_IDS)
    df = df[df["club"].notna()].copy()
    df["transfer_date"] = pd.to_datetime(df["transfer_date"], errors="coerce")
    df = df.dropna(subset=["transfer_date"])
    df["season"] = df["transfer_date"].dt.year
    df = df[df["transfer_date"].dt.month.isin(WINDOW_MONTHS)]
    df = df[df["season"].between(FIRST_SEASON, LAST_SEASON)
            & ~df["season"].isin(EXCLUDE_SEASONS)]
    df["is_placeholder_date"] = (
        df["transfer_date"].dt.strftime("%m-%d").isin(PLACEHOLDER_MD))

    played = (set(zip(matches["home_team"], matches["season"]))
              | set(zip(matches["away_team"], matches["season"])))
    df = df[[(c, s) in played for c, s in zip(df["club"], df["season"])]]

    out = df.rename(columns={"market_value_in_eur": "market_value_eur",
                             "to_club_name": "to_club", "player_name": "player"})
    out = (out[DEPARTURE_COLS]
           .drop_duplicates(["club", "season", "transfer_date", "player"])
           .sort_values(["season", "club", "transfer_date"])
           .reset_index(drop=True))
    return out


def build() -> pd.DataFrame:
    """Download the dump and return the canonical departures table."""
    from . import ingest
    transfers = load_raw("tm_transfers.csv.gz", TRANSFERS_URL)
    clubs = load_raw("tm_clubs.csv.gz", CLUBS_URL)
    return build_departures(transfers, clubs, ingest.load())
