"""Shared statistics helpers for the notebooks."""
from typing import Callable

import numpy as np
import pandas as pd

HOME_POINTS = {"H": 3, "D": 1, "A": 0}
AWAY_POINTS = {"H": 0, "D": 1, "A": 3}


def home_points_share(df: pd.DataFrame) -> float:
    home = df["outcome"].map(HOME_POINTS).sum()
    away = df["outcome"].map(AWAY_POINTS).sum()
    return home / (home + away)


def away_points_share(df: pd.DataFrame) -> float:
    return 1.0 - home_points_share(df)


def bootstrap_ci(
    df: pd.DataFrame,
    stat_fn: Callable[[pd.DataFrame], float],
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(df)
    stats = np.array(
        [stat_fn(df.iloc[rng.integers(0, n, n)]) for _ in range(n_boot)]
    )
    return (float(np.quantile(stats, alpha / 2)),
            float(np.quantile(stats, 1 - alpha / 2)))
