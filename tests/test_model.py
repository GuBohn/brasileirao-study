import numpy as np
import pandas as pd

from brasileirao import model


def _synthetic(n_seasons=6, per_season=80, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(2010, 2010 + n_seasons):
        for i in range(per_season):
            elo_diff = rng.normal(0, 120)
            p_home = 1 / (1 + np.exp(-elo_diff / 100)) * 0.75
            y = rng.choice([0, 1, 2], p=[p_home, 0.25, 0.75 - p_home])
            rows.append({"season": s, "date": pd.Timestamp(f"{s}-05-01")
                         + pd.Timedelta(days=i), "elo_home_pre": 1500 + elo_diff / 2,
                         "elo_away_pre": 1500 - elo_diff / 2,
                         "elo_diff": elo_diff, "y": y})
    return pd.DataFrame(rows)


def test_folds_respect_time():
    df = _synthetic()
    for train_idx, test_idx in model.season_folds(df, first_test_season=2012):
        assert df.loc[train_idx, "date"].max() < df.loc[test_idx, "date"].min()
        assert df.loc[test_idx, "season"].nunique() == 1


def test_evaluate_returns_finite_and_deterministic():
    df = _synthetic()
    feats = ["elo_home_pre", "elo_away_pre", "elo_diff"]
    a = model.evaluate(df, feats, first_test_season=2012)
    b = model.evaluate(df, feats, first_test_season=2012)
    assert np.isfinite(a["log_loss"]).all()
    pd.testing.assert_frame_equal(a, b)
    assert a["log_loss"].mean() < 1.2
