"""Download and clean Serie A match results into a canonical table."""
import urllib.request
from pathlib import Path

import pandas as pd

from .paths import PROCESSED, RAW

MATCHES_URL = (
    "https://raw.githubusercontent.com/adaoduque/"
    "Brasileirao_Dataset/master/campeonato-brasileiro-full.csv"
)
RAW_FILE = RAW / "campeonato-brasileiro-full.csv"
PROCESSED_FILE = PROCESSED / "matches.parquet"

# raw (lowercased) column -> canonical name. If the upstream schema drifts,
# clean() raises listing what it actually found - fix the mapping here only.
COLUMN_MAP = {
    "data": "date",
    "mandante": "home_team",
    "visitante": "away_team",
    "mandante_placar": "home_goals",
    "visitante_placar": "away_goals",
    "arena": "stadium",
    "mandante_estado": "home_state",
    "visitante_estado": "away_state",
}
CANONICAL = [
    "date", "season", "home_team", "away_team", "home_goals",
    "away_goals", "outcome", "stadium", "home_state", "away_state",
]


def download_raw(force: bool = False) -> Path:
    if force or not RAW_FILE.exists():
        urllib.request.urlretrieve(MATCHES_URL, RAW_FILE)
    return RAW_FILE


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    missing = set(COLUMN_MAP) - set(df.columns)
    if missing:
        raise ValueError(
            f"Raw data is missing expected columns {sorted(missing)}; "
            f"found {sorted(df.columns)}. Update COLUMN_MAP in ingest.py."
        )
    df = df[list(COLUMN_MAP)].rename(columns=COLUMN_MAP)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True)
    for col in ("home_goals", "away_goals"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", "home_goals", "away_goals"])
    df[["home_goals", "away_goals"]] = df[["home_goals", "away_goals"]].astype(int)
    for col in ("home_team", "away_team", "stadium", "home_state", "away_state"):
        df[col] = df[col].astype(str).str.strip()

    df["season"] = df["date"].dt.year.where(df["date"].dt.month > 3,
                                            df["date"].dt.year - 1)
    df["outcome"] = "D"
    df.loc[df["home_goals"] > df["away_goals"], "outcome"] = "H"
    df.loc[df["home_goals"] < df["away_goals"], "outcome"] = "A"

    df = df.drop_duplicates(subset=["date", "home_team", "away_team"])
    df = df.sort_values("date").reset_index(drop=True)
    return df[CANONICAL]


def build(force: bool = False) -> pd.DataFrame:
    raw = pd.read_csv(download_raw(force=force))
    df = clean(raw)
    df = df[df["season"] >= 2003].reset_index(drop=True)
    df.to_parquet(PROCESSED_FILE, index=False)
    return df


def load() -> pd.DataFrame:
    if not PROCESSED_FILE.exists():
        return build()
    return pd.read_parquet(PROCESSED_FILE)
