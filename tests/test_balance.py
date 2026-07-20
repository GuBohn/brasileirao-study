import numpy as np
import pandas as pd

from brasileirao import balance


def _league(n_seasons=6, per_season=180, seed=1):
    """Synthetic single league with a real strength signal, canonical schema.

    Sized (6 seasons x 180 matches) so the fixed model PARAMS - tuned for
    ~380-match real seasons, with min_child_samples=80 - have enough data per
    CV fold to actually split on the Elo signal. Smaller fixtures starve the
    model below its regularization floor and it degenerates to a noisy class
    prior, which is a fixture artifact, not the mis-specification the guard
    (test_forecastability_...) is meant to catch. Mirrors test_model.py's scale."""
    rng = np.random.default_rng(seed)
    teams = [f"T{i}" for i in range(10)]
    strength = {t: rng.normal(0, 200) for t in teams}
    rows = []
    for s in range(2012, 2012 + n_seasons):
        base = pd.Timestamp(f"{s}-05-01")
        for i in range(per_season):
            h, a = rng.choice(teams, 2, replace=False)
            d = strength[h] + 100 - strength[a]  # +100 home edge
            p_home = 1 / (1 + np.exp(-d / 150))
            o = rng.choice(["H", "D", "A"], p=[p_home * 0.8, 0.2, (1 - p_home) * 0.8])
            hg, ag = {"H": (2, 0), "D": (1, 1), "A": (0, 2)}[o]
            rows.append({"league": "T", "season": s, "date": base + pd.Timedelta(days=i),
                         "home_team": h, "away_team": a, "home_goals": hg,
                         "away_goals": ag, "outcome": o,
                         "odds_h": np.nan, "odds_d": np.nan, "odds_a": np.nan})
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def test_entropy_bounds():
    assert np.isclose(balance.outcome_entropy(pd.Series(["H", "D", "A"] * 10)),
                      np.log2(3))
    assert np.isclose(balance.outcome_entropy(pd.Series(["H"] * 10)), 0.0)


def test_add_model_features_columns():
    df = balance.add_model_features(_league())
    for col in ("elo_home_pre", "elo_away_pre", "elo_diff", "y"):
        assert col in df.columns
    assert df["y"].isin([0, 1, 2]).all()


def test_upset_points_share_in_unit_interval():
    df = balance.add_model_features(_league())
    share = balance.upset_points_share(df)
    assert 0.0 <= share <= 1.0
    # Favourites should win most points, so underdog share is well below half.
    assert share < 0.5


def test_forecastability_model_beats_floor_on_signal():
    df = _league()
    res = balance.forecastability(df, first_test_season=2014)
    assert np.isfinite(res["model_ll"]) and np.isfinite(res["floor_ll"])
    assert res["model_ll"] < res["floor_ll"]
    assert np.isnan(res["market_ll"])  # no odds in the synthetic league


# --- season-level metrics ---
from brasileirao import standings


def _full_schedule(n_teams, seed, base_rates=(0.45, 0.27, 0.28)):
    """Double round-robin; outcomes drawn from fixed base rates => a
    perfectly balanced league (Noll-Scully should be ~1)."""
    rng = np.random.default_rng(seed)
    teams = [f"T{i}" for i in range(n_teams)]
    base = pd.Timestamp("2015-01-01")
    rows, day = [], 0
    for h in teams:
        for a in teams:
            if h == a:
                continue
            o = rng.choice(["H", "D", "A"], p=base_rates)
            hg, ag = {"H": (1, 0), "D": (0, 0), "A": (0, 1)}[o]
            rows.append({"league": "T", "season": 2015,
                         "date": base + pd.Timedelta(days=day), "home_team": h,
                         "away_team": a, "home_goals": hg, "away_goals": ag,
                         "outcome": o})
            day += 1
    return pd.DataFrame(rows)


def test_noll_scully_of_balanced_league_near_one():
    df = _full_schedule(n_teams=16, seed=3)
    ns = balance.noll_scully(df, league="T", season=2015, n_boot=400)
    assert 0.7 < ns < 1.4  # stochastic; a balanced league sits around 1


def test_title_hhi_extremes():
    assert np.isclose(balance.title_hhi(["A", "A", "A"]), 1.0)
    assert np.isclose(balance.title_hhi(["A", "B", "C", "D"]), 0.25)


def test_title_decidedness_last_day_is_zero_ish():
    # Construct a season decided only on the final match: two teams neck and
    # neck, leader clinches with the last game.
    df = _full_schedule(n_teams=4, seed=7)
    dec = balance.title_decidedness(df, n_teams=4)
    assert 0.0 <= dec <= 1.0
