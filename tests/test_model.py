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


def test_class_prior_baseline_matches_training_frequencies():
    df = _synthetic()
    result = model.class_prior_baseline(df, first_test_season=2012)
    assert np.isfinite(result["log_loss"]).all()

    # First fold by hand: predicting the 2010-2011 class frequencies for
    # every 2012 row should reproduce exactly the log loss the function
    # reports for season 2012.
    train = df[df.season < 2012]
    test = df[df.season == 2012]
    freq = train["y"].value_counts(normalize=True).reindex([0, 1, 2], fill_value=0.0).to_numpy()
    from sklearn.metrics import log_loss
    expected = log_loss(test["y"], np.tile(freq, (len(test), 1)), labels=[0, 1, 2])
    got = result.loc[result.season == 2012, "log_loss"].iloc[0]
    assert np.isclose(got, expected)


def test_evaluate_beats_class_prior_on_separable_synthetic_signal():
    # The synthetic data has a real elo_diff -> outcome relationship, so a
    # correctly regularised model should be able to beat a model with no
    # features at all. This is the same floor check applied to the real
    # data in the notebook - a model that fails it is mis-specified.
    df = _synthetic()
    feats = ["elo_home_pre", "elo_away_pre", "elo_diff"]
    fitted = model.evaluate(df, feats, first_test_season=2012)
    prior = model.class_prior_baseline(df, first_test_season=2012)
    assert fitted["log_loss"].mean() < prior["log_loss"].mean()
