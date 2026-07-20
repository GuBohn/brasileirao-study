"""Model-ready feature table. Every feature is pre-match derivable."""
import pandas as pd

from . import geo
from .ratings import add_elo

CLOSED_START, CLOSED_END = "2020-08-08", "2021-09-30"
PARTIAL_START, PARTIAL_END = "2021-10-01", "2021-12-31"
REST_CAP_DAYS = 14
TARGET = {"H": 0, "D": 1, "A": 2}
FEATURES = [
    "elo_home_pre", "elo_away_pre", "elo_diff", "travel_km",
    "temp_gap", "rest_diff", "crowd_closed", "same_state",
]


def crowd_status(dates: pd.Series) -> pd.Series:
    s = pd.Series("full", index=dates.index)
    s[dates.between(CLOSED_START, CLOSED_END)] = "closed"
    s[dates.between(PARTIAL_START, PARTIAL_END)] = "partial"
    return s


def rest_days(matches: pd.DataFrame) -> pd.DataFrame:
    """Days since each side's previous match (any venue), capped, causal.

    Walks matches in order tracking each team's last-seen date, mirroring
    ratings.add_elo. A (date, team) join key is NOT reliably unique in the
    real dataset - a handful of dates have the same team listed in two
    separate matches (a data quirk, e.g. 2008-07-06) - so a join on that key
    is a many-to-many merge that silently inflates row count and misaligns
    every later row. A single forward pass sidesteps that entirely: one row
    in, one row out, by construction.
    """
    last_seen: dict[str, pd.Timestamp] = {}
    home_rest, away_rest = [], []
    for row in matches.itertuples():
        for team, bucket in ((row.home_team, home_rest), (row.away_team, away_rest)):
            prev = last_seen.get(team)
            if prev is None:
                bucket.append(float(REST_CAP_DAYS))
            else:
                bucket.append(float(min((row.date - prev).days, REST_CAP_DAYS)))
        last_seen[row.home_team] = row.date
        last_seen[row.away_team] = row.date
    return pd.DataFrame(
        {"home_rest": home_rest, "away_rest": away_rest}, index=matches.index
    )


def temp_gap(matches: pd.DataFrame) -> pd.Series:
    stadiums = geo.load_stadiums()
    home = geo._resolve(matches["home_team"], stadiums)["avg_temp_c"]
    away = geo._resolve(matches["away_team"], stadiums)["avg_temp_c"]
    return pd.Series((home - away).to_numpy(), index=matches.index,
                     name="temp_gap")


def build_features(matches: pd.DataFrame) -> pd.DataFrame:
    if not matches["date"].is_monotonic_increasing:
        raise ValueError("matches must be sorted by date")
    df = add_elo(matches)
    df["elo_diff"] = df["elo_home_pre"] - df["elo_away_pre"]
    df["travel_km"] = geo.travel_km(df)
    df["temp_gap"] = temp_gap(df)
    rest = rest_days(df)
    df["rest_diff"] = rest["home_rest"] - rest["away_rest"]
    crowd = crowd_status(df["date"])
    df["crowd_closed"] = (crowd == "closed").astype(int)
    df["same_state"] = (df["home_state"] == df["away_state"]).astype(int)
    df["y"] = df["outcome"].map(TARGET)
    return df
