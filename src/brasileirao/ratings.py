"""Causal Elo ratings: each row gets ratings from strictly prior matches."""
import pandas as pd

K = 20.0
INITIAL = 1500.0
SCORE = {"H": 1.0, "D": 0.5, "A": 0.0}


def expected_home(rating_home: float, rating_away: float) -> float:
    return 1.0 / (1.0 + 10 ** (-(rating_home - rating_away) / 400.0))


def add_elo(matches: pd.DataFrame) -> pd.DataFrame:
    if not matches["date"].is_monotonic_increasing:
        raise ValueError("matches must be sorted by date (causality)")
    current: dict[str, float] = {}
    pre_home, pre_away = [], []
    for row in matches.itertuples():
        rh = current.get(row.home_team, INITIAL)
        ra = current.get(row.away_team, INITIAL)
        pre_home.append(rh)
        pre_away.append(ra)
        score = SCORE[row.outcome]
        exp = expected_home(rh, ra)
        current[row.home_team] = rh + K * (score - exp)
        current[row.away_team] = ra - K * (score - exp)
    out = matches.copy()
    out["elo_home_pre"] = pre_home
    out["elo_away_pre"] = pre_away
    return out
