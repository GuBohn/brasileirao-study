"""Season-wise expanding-window evaluation of outcome models."""
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss

BASELINE_FEATURES = ["elo_home_pre", "elo_away_pre", "elo_diff"]
QUIRK_FEATURES = ["travel_km", "temp_gap", "rest_diff", "crowd_closed",
                  "same_state"]
FULL_FEATURES = BASELINE_FEATURES + QUIRK_FEATURES

# Low capacity on purpose: ~380 matches/season and 3-8 features cannot
# support learning_rate=0.05/num_leaves=31/n_estimators=300 fixed - that
# configuration memorises the training seasons (see fit_model below, which
# holds out the most recent training season and stops early instead of
# trusting a fixed n_estimators). n_estimators here is a ceiling that early
# stopping is expected to cut short, not a target to hit.
PARAMS = dict(objective="multiclass", num_class=3, n_estimators=1000,
              learning_rate=0.03, num_leaves=7, min_child_samples=80,
              random_state=0, verbose=-1)
EARLY_STOPPING_ROUNDS = 50


def make_model() -> lgb.LGBMClassifier:
    return lgb.LGBMClassifier(**PARAMS)


def season_folds(df: pd.DataFrame, first_test_season: int):
    for season in sorted(df.loc[df.season >= first_test_season, "season"].unique()):
        train = df.index[df.season < season]
        test = df.index[df.season == season]
        if len(train) and len(test):
            yield train, test


def _split_validation(df: pd.DataFrame, train_idx: pd.Index):
    """Carve the most recent training season off as an early-stopping
    validation set. Falls back to no split (and no early stopping) if only
    one training season is available - there's nothing to hold out from."""
    train_seasons = df.loc[train_idx, "season"]
    val_season = train_seasons.max()
    is_val = (train_seasons == val_season).to_numpy()
    fit_idx, val_idx = train_idx[~is_val], train_idx[is_val]
    if len(fit_idx) == 0:
        return train_idx, None
    return fit_idx, val_idx


def fit_model(df: pd.DataFrame, train_idx: pd.Index,
             feature_cols: list[str]) -> lgb.LGBMClassifier:
    """Fit with early stopping against a held-out validation season, so a
    fixed n_estimators never gets the chance to memorise the training data."""
    fit_idx, val_idx = _split_validation(df, train_idx)
    clf = make_model()
    if val_idx is None or len(val_idx) == 0:
        clf.fit(df.loc[fit_idx, feature_cols], df.loc[fit_idx, "y"])
        return clf
    clf.fit(
        df.loc[fit_idx, feature_cols], df.loc[fit_idx, "y"],
        eval_X=df.loc[val_idx, feature_cols], eval_y=df.loc[val_idx, "y"],
        eval_metric="multi_logloss",
        callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)],
    )
    return clf


def evaluate(df: pd.DataFrame, feature_cols: list[str],
             first_test_season: int = 2010) -> pd.DataFrame:
    rows = []
    for train_idx, test_idx in season_folds(df, first_test_season):
        clf = fit_model(df, train_idx, feature_cols)
        proba = clf.predict_proba(df.loc[test_idx, feature_cols])
        rows.append({
            "season": int(df.loc[test_idx, "season"].iloc[0]),
            "n": len(test_idx),
            "log_loss": log_loss(df.loc[test_idx, "y"], proba,
                                 labels=[0, 1, 2]),
        })
    return pd.DataFrame(rows)


def class_prior_baseline(df: pd.DataFrame, first_test_season: int = 2010) -> pd.DataFrame:
    """No-feature reference: predict each fold's training-season class
    frequencies for every test row. The honest floor any model has to
    clear before its features can be credited with anything."""
    rows = []
    for train_idx, test_idx in season_folds(df, first_test_season):
        freq = (df.loc[train_idx, "y"].value_counts(normalize=True)
                .reindex([0, 1, 2], fill_value=0.0).to_numpy())
        proba = np.tile(freq, (len(test_idx), 1))
        rows.append({
            "season": int(df.loc[test_idx, "season"].iloc[0]),
            "n": len(test_idx),
            "log_loss": log_loss(df.loc[test_idx, "y"], proba,
                                 labels=[0, 1, 2]),
        })
    return pd.DataFrame(rows)


def oof_predictions(df: pd.DataFrame, feature_cols: list[str],
                    first_test_season: int = 2010) -> pd.DataFrame:
    """Out-of-fold class probabilities for calibration plots."""
    parts = []
    for train_idx, test_idx in season_folds(df, first_test_season):
        clf = fit_model(df, train_idx, feature_cols)
        proba = clf.predict_proba(df.loc[test_idx, feature_cols])
        part = pd.DataFrame(proba, columns=["p_home", "p_draw", "p_away"],
                            index=test_idx)
        part["y"] = df.loc[test_idx, "y"]
        parts.append(part)
    return pd.concat(parts)
