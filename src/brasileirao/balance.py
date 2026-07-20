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


from . import standings  # noqa: E402  (grouped with season-level section)

# ---- Season level ----------------------------------------------------------


def _final_points(matches: pd.DataFrame) -> np.ndarray:
    return standings.final_table(matches)["points"].to_numpy()


def noll_scully(matches: pd.DataFrame, league: str, season: int,
                n_boot: int = 1000, seed: int = 0) -> float:
    """Actual SD of final points divided by an idealized 'balanced-league' SD
    estimated by simulation: replay the exact fixture list with every outcome
    redrawn from this season's own H/D/A base rates (identical-strength teams),
    take the mean SD of final points across `n_boot` simulated seasons. A ratio
    near 1 means the table is about as spread as pure chance; higher means real
    strength gaps. Simulation makes the null self-consistent with draws / 3-1-0
    and normalizes away the 34-vs-38-game team-count difference."""
    rng = np.random.default_rng(seed)
    actual_sd = float(np.std(_final_points(matches), ddof=0))
    rates = matches["outcome"].value_counts(normalize=True).reindex(
        ["H", "D", "A"], fill_value=0.0).to_numpy()

    # Vectorized simulation: draw H/D/A codes (0/1/2) for the exact fixture
    # list and accumulate points per team with bincount - identical statistic
    # to replaying final_table, without rebuilding a DataFrame each draw (the
    # notebook runs this thousands of times across leagues x seasons).
    teams = pd.Index(sorted(set(matches["home_team"]) | set(matches["away_team"])))
    home_idx = teams.get_indexer(matches["home_team"])
    away_idx = teams.get_indexer(matches["away_team"])
    n_teams, n_matches = len(teams), len(matches)
    home_pts = np.array([3, 1, 0])   # points for a [H, D, A] result
    away_pts = np.array([0, 1, 3])
    sds = np.empty(n_boot)
    for b in range(n_boot):
        codes = rng.choice(3, size=n_matches, p=rates)
        pts = (np.bincount(home_idx, weights=home_pts[codes], minlength=n_teams)
               + np.bincount(away_idx, weights=away_pts[codes], minlength=n_teams))
        sds[b] = pts.std(ddof=0)
    ideal_sd = float(sds.mean())
    return actual_sd / ideal_sd if ideal_sd > 0 else np.nan


def title_hhi(champions: list[str]) -> float:
    """Herfindahl index of championship shares over the window."""
    s = pd.Series(champions).value_counts(normalize=True)
    return float((s ** 2).sum())


def _secured_index(matches: pd.DataFrame, n_teams: int, condition) -> int:
    """Index (1-based match count) at which `condition(points, remaining)` first
    holds, walking matches in date order. total_rounds = 2*(n_teams-1)."""
    total_rounds = 2 * (n_teams - 1)
    trace = standings.cumulative_points(matches, n_teams, total_rounds)
    for i, state in enumerate(trace, start=1):
        if condition(state["points"], state["remaining"]):
            return i
    return len(trace)


def title_decidedness(matches: pd.DataFrame, n_teams: int) -> float:
    """Share of the season's matches still unplayed when the champion became
    mathematically secured (0 = decided on the last match, higher = earlier).
    Title secured when the leader's current points exceed every rival's maximum
    possible final points (P_j + 3 * remaining_j)."""
    def secured(points, remaining):
        order = sorted(points, key=points.get, reverse=True)
        leader = order[0]
        return all(points[leader] > points[j] + 3 * remaining[j]
                   for j in order[1:])
    idx = _secured_index(matches, n_teams, secured)
    total = len(matches)
    return (total - idx) / total


def relegation_decidedness(matches: pd.DataFrame, n_teams: int, k: int) -> float:
    """Share of matches unplayed when exactly `k` teams are mathematically
    relegated (each can no longer climb above the k-th-from-bottom safe line)."""
    def secured(points, remaining):
        max_final = {t: points[t] + 3 * remaining[t] for t in points}
        relegated = 0
        for t in points:
            # t is doomed if at least (n_teams - k) teams already exceed t's max.
            better = sum(points[o] > max_final[t] for o in points if o != t)
            if better >= n_teams - k:
                relegated += 1
        return relegated >= k
    idx = _secured_index(matches, n_teams, secured)
    total = len(matches)
    return (total - idx) / total
