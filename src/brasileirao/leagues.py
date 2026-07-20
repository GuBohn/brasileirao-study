"""Uniform football-data.co.uk loader for six leagues.

Results and closing odds live in the SAME row of each source file (European
main-league files and the Brazil extra-league file alike), so Chapter B never
needs the cross-source odds join Chapter A's Brasileirao benchmark used.
"""
import urllib.request

import numpy as np
import pandas as pd

from .paths import RAW

# Display name -> football-data code. Brasileirao uses the "extra leagues"
# single-file format; the five European leagues use per-season main files.
MAIN_LEAGUES = {
    "Premier League": "E0", "La Liga": "SP1", "Serie A": "I1",
    "Bundesliga": "D1", "Ligue 1": "F1",
}
EXTRA_LEAGUES = {"Brasileirao": "BRA"}

CANONICAL = ["league", "season", "date", "home_team", "away_team",
             "home_goals", "away_goals", "outcome", "odds_h", "odds_d", "odds_a"]

MAIN_MAP = {"HomeTeam": "home_team", "AwayTeam": "away_team",
            "FTHG": "home_goals", "FTAG": "away_goals"}
EXTRA_MAP = {"Home": "home_team", "Away": "away_team",
             "HG": "home_goals", "AG": "away_goals", "Season": "season"}
ODDS_PREFERENCES = [("PSCH", "PSCD", "PSCA"), ("B365H", "B365D", "B365A")]


def _season_code(start_year: int) -> str:
    """2012 -> '1213' (football-data's mmz4281 season directory format)."""
    return f"{start_year % 100:02d}{(start_year + 1) % 100:02d}"


def implied_probabilities(odds: np.ndarray) -> np.ndarray:
    """De-vig decimal odds [[H,D,A], ...] to probability rows summing to 1."""
    inv = 1.0 / np.asarray(odds, dtype=float)
    return inv / inv.sum(axis=1, keepdims=True)


def _extract_odds(df: pd.DataFrame) -> pd.DataFrame:
    for h, d, a in ODDS_PREFERENCES:
        if {h, d, a} <= set(df.columns):
            out = df[[h, d, a]].apply(pd.to_numeric, errors="coerce")
            out.columns = ["odds_h", "odds_d", "odds_a"]
            return out.reset_index(drop=True)
    return pd.DataFrame({"odds_h": np.nan, "odds_d": np.nan, "odds_a": np.nan},
                        index=range(len(df)))


def _finish(df: pd.DataFrame, league: str) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["date"], dayfirst=True)
    for col in ("home_goals", "away_goals"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", "home_goals", "away_goals"]).copy()
    df[["home_goals", "away_goals"]] = df[["home_goals", "away_goals"]].astype(int)
    for col in ("home_team", "away_team"):
        df[col] = df[col].astype(str).str.strip()
    df["outcome"] = "D"
    df.loc[df["home_goals"] > df["away_goals"], "outcome"] = "H"
    df.loc[df["home_goals"] < df["away_goals"], "outcome"] = "A"
    df["league"] = league
    df = df.drop_duplicates(subset=["league", "season", "date",
                                    "home_team", "away_team"])
    return df[CANONICAL].sort_values("date").reset_index(drop=True)


def _require(df: pd.DataFrame, cols: set[str], source_map: str) -> None:
    missing = cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Source is missing expected columns {sorted(missing)}; found "
            f"{sorted(df.columns)}. Update {source_map} in leagues.py."
        )


def _normalize_main(raw: pd.DataFrame, season: int, league: str) -> pd.DataFrame:
    _require(raw, {"Date", *MAIN_MAP}, "MAIN_MAP")
    df = raw.rename(columns=MAIN_MAP).copy()
    df["date"] = df["Date"]
    df["season"] = season
    odds = _extract_odds(raw)
    df = df.reset_index(drop=True)
    for c in ("odds_h", "odds_d", "odds_a"):
        df[c] = odds[c]
    return _finish(df, league)


def _normalize_extra(raw: pd.DataFrame, league: str) -> pd.DataFrame:
    _require(raw, {"Date", *EXTRA_MAP}, "EXTRA_MAP")
    df = raw.rename(columns=EXTRA_MAP).copy()
    df["date"] = df["Date"]
    df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int64")
    odds = _extract_odds(raw)
    df = df.reset_index(drop=True)
    for c in ("odds_h", "odds_d", "odds_a"):
        df[c] = odds[c]
    df = df.dropna(subset=["season"])
    df["season"] = df["season"].astype(int)
    return _finish(df, league)


def _is_corrupt(head: bytes) -> bool:
    """A football-data CSV starts with a UTF-8 BOM or a column name ('Div',
    'Country', ...), never NUL bytes. Guards against a partially-written /
    cached-garbage file that `_download` would otherwise never retry (observed:
    an interrupted fetch left a NUL-filled E0.csv that broke every later run)."""
    return len(head) == 0 or head[:1] == b"\x00"


def _download(url: str, path) -> None:
    if path.exists():
        return
    urllib.request.urlretrieve(url, path)
    with open(path, "rb") as fh:
        head = fh.read(16)
    if _is_corrupt(head):
        path.unlink()
        raise ValueError(
            f"Downloaded {url} looks corrupt (empty/NUL-filled); deleted "
            f"{path.name} so a re-run retries the fetch."
        )


def load_main_league(league: str, code: str, seasons) -> pd.DataFrame:
    frames = []
    for start in seasons:
        s = _season_code(start)
        path = RAW / f"{code}_{s}.csv"
        _download(f"https://www.football-data.co.uk/mmz4281/{s}/{code}.csv", path)
        raw = pd.read_csv(path, encoding="latin-1")
        frames.append(_normalize_main(raw, season=start, league=league))
    return pd.concat(frames, ignore_index=True)


def load_extra_league(league: str, code: str, seasons) -> pd.DataFrame:
    path = RAW / f"{code}.csv"
    _download(f"https://www.football-data.co.uk/new/{code}.csv", path)
    raw = pd.read_csv(path, encoding="latin-1")
    df = _normalize_extra(raw, league)
    return df[df["season"].isin(list(seasons))].reset_index(drop=True)


def load_all(seasons) -> pd.DataFrame:
    """Canonical six-league table over `seasons` (iterable of start years)."""
    parts = [load_main_league(name, code, seasons)
             for name, code in MAIN_LEAGUES.items()]
    parts += [load_extra_league(name, code, seasons)
              for name, code in EXTRA_LEAGUES.items()]
    return pd.concat(parts, ignore_index=True)
