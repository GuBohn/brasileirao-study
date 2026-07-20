import pandas as pd

from brasileirao import analysis


def test_home_points_share_extremes():
    all_h = pd.DataFrame({"outcome": ["H"] * 10})
    all_d = pd.DataFrame({"outcome": ["D"] * 10})
    assert analysis.home_points_share(all_h) == 1.0
    assert analysis.home_points_share(all_d) == 0.5


def test_away_points_share_complements():
    df = pd.DataFrame({"outcome": ["H", "A", "D", "H"]})
    total = analysis.home_points_share(df) + analysis.away_points_share(df)
    assert abs(total - 1.0) < 1e-9


def test_bootstrap_ci_brackets_and_deterministic():
    df = pd.DataFrame({"outcome": ["H"] * 60 + ["D"] * 25 + ["A"] * 15})
    lo1, hi1 = analysis.bootstrap_ci(df, analysis.home_points_share, seed=0)
    lo2, hi2 = analysis.bootstrap_ci(df, analysis.home_points_share, seed=0)
    point = analysis.home_points_share(df)
    assert lo1 <= point <= hi1
    assert (lo1, hi1) == (lo2, hi2)
    assert hi1 - lo1 < 0.25
