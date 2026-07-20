"""Six cross-league unpredictability / competitive-balance metrics."""
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss

from . import model
from .analysis import HOME_POINTS, AWAY_POINTS
from .features import TARGET
from .leagues import implied_probabilities
from .ratings import INITIAL, add_elo

# ---- Match level -----------------------------------------------------------


def outcome_entropy(outcomes: pd.Series) -> float:
    """Shannon entropy (bits) of the H/D/A distribution. Higher = less
    predictable at the base-rate level. NOTE: raw, so a strong home advantage
    lowers it - read alongside upset share and model log loss (see spec guardrail)."""
    p = outcomes.value_counts(normalize=True)
    return float(-(p * np.log2(p)).sum())


def add_model_features(matches: pd.DataFrame) -> pd.DataFrame:
    """League-agnostic subset of Chapter A's feature build: causal Elo + y.
    Requires canonical schema sorted by date within the league."""
    if not matches["date"].is_monotonic_increasing:
        matches = matches.sort_values("date").reset_index(drop=True)
    df = add_elo(matches)
    df["elo_diff"] = df["elo_home_pre"] - df["elo_away_pre"]
    df["y"] = df["outcome"].map(TARGET)
    return df


def upset_points_share(df: pd.DataFrame) -> float:
    """Share of all points won by the pre-match Elo underdog. Restricted to
    rows where both teams already have a rating (both off INITIAL) - the Elo
    burn-in cut. `df` must carry elo_home_pre/elo_away_pre (add_model_features)."""
    m = df[(df["elo_home_pre"] != INITIAL) & (df["elo_away_pre"] != INITIAL)]
    m = m[m["elo_home_pre"] != m["elo_away_pre"]]
    home_pts = m["outcome"].map(HOME_POINTS)
    away_pts = m["outcome"].map(AWAY_POINTS)
    home_is_underdog = m["elo_home_pre"] < m["elo_away_pre"]
    underdog_pts = home_pts.where(home_is_underdog, away_pts)
    total = (home_pts + away_pts).sum()
    return float(underdog_pts.sum() / total)


def forecastability(matches: pd.DataFrame, first_test_season: int) -> dict:
    """Per-league forecastability: Elo-only model log loss vs the class-prior
    floor (both via Chapter A's time-aware CV) and vs the bookmaker's implied
    odds on rows where odds exist. Lower = more predictable."""
    df = add_model_features(matches)
    model_ll = model.evaluate(df, model.BASELINE_FEATURES, first_test_season)["log_loss"].mean()
    floor_ll = model.class_prior_baseline(df, first_test_season)["log_loss"].mean()

    have_odds = df[["odds_h", "odds_d", "odds_a"]].notna().all(axis=1) & (df["season"] >= first_test_season)
    if have_odds.sum() >= 1:
        sub = df[have_odds]
        implied = implied_probabilities(sub[["odds_h", "odds_d", "odds_a"]].to_numpy())
        market_ll = log_loss(sub["y"], implied, labels=[0, 1, 2])
    else:
        market_ll = np.nan
    return {"model_ll": float(model_ll), "floor_ll": float(floor_ll),
            "market_ll": float(market_ll), "n_odds": int(have_odds.sum())}
