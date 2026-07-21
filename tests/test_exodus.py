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
