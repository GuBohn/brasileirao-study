"""Season-wise expanding-window evaluation of outcome models."""
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss

BASELINE_FEATURES = ["elo_home_pre", "elo_away_pre", "elo_diff"]
QUIRK_FEATURES = ["travel_km", "temp_gap", "rest_diff", "crowd_closed",
                  "same_state"]
FULL_FEATURES = BASELINE_FEATURES + QUIRK_FEATURES

PARAMS = dict(objective="multiclass", num_class=3, n_estimators=300,
              learning_rate=0.05, num_leaves=31, min_child_samples=50,
              random_state=0, verbose=-1)


def make_model() -> lgb.LGBMClassifier:
    return lgb.LGBMClassifier(**PARAMS)


def season_folds(df: pd.DataFrame, first_test_season: int):
    for season in sorted(df.loc[df.season >= first_test_season, "season"].unique()):
        train = df.index[df.season < season]
        test = df.index[df.season == season]
        if len(train) and len(test):
            yield train, test


def evaluate(df: pd.DataFrame, feature_cols: list[str],
             first_test_season: int = 2010) -> pd.DataFrame:
    rows = []
    for train_idx, test_idx in season_folds(df, first_test_season):
        clf = make_model()
        clf.fit(df.loc[train_idx, feature_cols], df.loc[train_idx, "y"])
        proba = clf.predict_proba(df.loc[test_idx, feature_cols])
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
        clf = make_model()
        clf.fit(df.loc[train_idx, feature_cols], df.loc[train_idx, "y"])
        proba = clf.predict_proba(df.loc[test_idx, feature_cols])
        part = pd.DataFrame(proba, columns=["p_home", "p_draw", "p_away"],
                            index=test_idx)
        part["y"] = df.loc[test_idx, "y"]
        parts.append(part)
    return pd.concat(parts)
