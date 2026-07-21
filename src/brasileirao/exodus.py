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


_HOME_PTS = {"H": 3, "D": 1, "A": 0}
_AWAY_PTS = {"H": 0, "D": 1, "A": 3}


def window_bounds(season: int):
    """Pre-window ends when the summer window opens (Jul 1); post-window begins
    when it closes (Sep 1). The Jul-Aug window itself is an excluded washout."""
    return pd.Timestamp(season, 7, 1), pd.Timestamp(season, 9, 1)


def club_match_view(matches_exp: pd.DataFrame, club: str, season: int) -> pd.DataFrame:
    """One row per match `club` played in `season`, with the club's actual points,
    Elo-expected points, residual, own pre-match Elo, and window phase."""
    s = matches_exp[(matches_exp["season"] == season)
                    & ((matches_exp["home_team"] == club)
                       | (matches_exp["away_team"] == club))].copy()
    s = s.sort_values("date").reset_index(drop=True)
    is_home = s["home_team"] == club
    s["pts"] = np.where(is_home, s["outcome"].map(_HOME_PTS),
                        s["outcome"].map(_AWAY_PTS))
    s["exp_pts"] = np.where(is_home, s["exp_home_pts"], s["exp_away_pts"])
    s["resid"] = s["pts"] - s["exp_pts"]
    s["club_elo"] = np.where(is_home, s["elo_home_pre"], s["elo_away_pre"])
    open_, close_ = window_bounds(season)
    s["phase"] = np.where(s["date"] < open_, "pre",
                          np.where(s["date"] >= close_, "post", "window"))
    return s


def club_season_stat(view: pd.DataFrame) -> dict:
    pre = view[view["phase"] == "pre"]
    post = view[view["phase"] == "post"]
    if len(pre) == 0 or len(post) == 0:
        return dict(d_resid=np.nan, d_ppg=np.nan, pre_slope=np.nan, pre_elo=np.nan)
    pre_slope = np.nan
    if len(pre) >= 2:
        pre_slope = float(np.polyfit(np.arange(len(pre)), pre["resid"].to_numpy(), 1)[0])
    return dict(
        d_resid=float(post["resid"].mean() - pre["resid"].mean()),
        d_ppg=float(post["pts"].mean() - pre["pts"].mean()),
        pre_slope=pre_slope,
        pre_elo=float(pre["club_elo"].mean()),
    )
