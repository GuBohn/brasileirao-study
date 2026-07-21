import numpy as np
import pandas as pd

from brasileirao import exodus


def _synthetic_matches(n_per_pair=40, seed=0, home_edge=0.15):
    """A tiny 4-team league where strength is baked in, so Elo separates teams
    and expected points rise with elo_diff. `home_edge` shifts the outcome
    thresholds so home teams win more often at every strength gap (including
    equal strength) — mirroring real football, where at a 0 Elo gap the home
    side still wins more, which is what elo_expected_points must recover."""
    rng = np.random.default_rng(seed)
    teams = ["Strong", "Mid1", "Mid2", "Weak"]
    strength = {"Strong": 0.75, "Mid1": 0.5, "Mid2": 0.5, "Weak": 0.25}
    rows, day = [], pd.Timestamp("2012-04-01")
    for _ in range(n_per_pair):
        for h in teams:
            for a in teams:
                if h == a:
                    continue
                ph = strength[h] / (strength[h] + strength[a])
                lo, hi = ph - 0.1 + home_edge, ph + 0.1 + home_edge
                r = rng.random()
                outcome = "H" if r < lo else ("A" if r > hi else "D")
                rows.append({"date": day, "season": 2012, "home_team": h,
                             "away_team": a, "outcome": outcome})
                day += pd.Timedelta(days=1)
    return pd.DataFrame(rows)


def test_expected_points_monotonic_and_bounded():
    m = exodus.elo_expected_points(_synthetic_matches())
    assert m["exp_home_pts"].between(0, 3).all()
    assert m["exp_away_pts"].between(0, 3).all()
    ordered = m.sort_values("elo_diff")
    assert (np.diff(ordered["exp_home_pts"].to_numpy()) >= -1e-9).all()


def test_home_advantage_at_zero_gap():
    m = exodus.elo_expected_points(_synthetic_matches())
    near0 = m[m["elo_diff"].abs() < 20]
    assert near0["exp_home_pts"].mean() > near0["exp_away_pts"].mean()


def _view_row(date, home, away, outcome, exp_home, exp_away, elo_home=1500, elo_away=1500):
    return {"date": pd.Timestamp(date), "season": 2015, "home_team": home,
            "away_team": away, "outcome": outcome, "exp_home_pts": exp_home,
            "exp_away_pts": exp_away, "elo_home_pre": elo_home, "elo_away_pre": elo_away}


def test_phase_assignment_exhaustive_disjoint():
    rows = [
        _view_row("2015-05-10", "Flamengo", "X", "H", 1.8, 1.0),   # pre
        _view_row("2015-07-20", "Flamengo", "Y", "H", 1.8, 1.0),   # window (excluded)
        _view_row("2015-10-01", "Flamengo", "Z", "A", 1.8, 1.0),   # post
    ]
    view = exodus.club_match_view(pd.DataFrame(rows), "Flamengo", 2015)
    assert list(view["phase"]) == ["pre", "window", "post"]


def test_club_season_stat_hand_computed():
    rows = [
        _view_row("2015-05-10", "Flamengo", "X", "H", 1.8, 1.0),
        _view_row("2015-05-20", "Flamengo", "X", "H", 2.0, 1.0),
        _view_row("2015-10-01", "W", "Flamengo", "H", 1.5, 1.0),
    ]
    view = exodus.club_match_view(pd.DataFrame(rows), "Flamengo", 2015)
    stat = exodus.club_season_stat(view)
    assert abs(stat["d_resid"] - (-1.0 - 1.1)) < 1e-9      # -2.1
    assert abs(stat["d_ppg"] - (0.0 - 3.0)) < 1e-9         # -3.0


def test_stat_nan_without_both_phases():
    rows = [_view_row("2015-05-10", "Flamengo", "X", "H", 1.8, 1.0)]  # pre only
    view = exodus.club_match_view(pd.DataFrame(rows), "Flamengo", 2015)
    assert np.isnan(exodus.club_season_stat(view)["d_resid"])
