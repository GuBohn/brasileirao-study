"""Event study: do mid-season departures dent a club's rest-of-season form?

Outcome is Elo-residual league points (actual minus what pre-match causal Elo
expects), so the differing second-half schedule is netted out. Match data and
Elo come from matches.parquet + ratings.py; departure events from transfers.py.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from . import ratings

_OUTCOME_TO_Y = {"H": 0, "D": 1, "A": 2}


def elo_expected_points(matches: pd.DataFrame) -> pd.DataFrame:
    """Fit outcome ~ elo_diff (multinomial logit) and attach expected home/away
    league points per match. This is a strength 'par score', not an out-of-sample
    forecast: any global fit bias cancels in each club-season's pre-minus-post
    difference, which is all the estimators use."""
    m = ratings.add_elo(matches.sort_values("date").reset_index(drop=True))
    m["elo_diff"] = m["elo_home_pre"] - m["elo_away_pre"]
    y = m["outcome"].map(_OUTCOME_TO_Y)
    clf = LogisticRegression(max_iter=1000)
    clf.fit(m[["elo_diff"]], y)
    p = clf.predict_proba(m[["elo_diff"]])            # columns ordered H, D, A
    ph, pd_, pa = p[:, 0], p[:, 1], p[:, 2]
    m["exp_home_pts"] = 3 * ph + 1 * pd_
    m["exp_away_pts"] = 3 * pa + 1 * pd_
    return m
