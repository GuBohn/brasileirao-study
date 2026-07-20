"""League tables and cumulative standings from a canonical match table."""
import pandas as pd

HOME_PTS = {"H": 3, "D": 1, "A": 0}
AWAY_PTS = {"H": 0, "D": 1, "A": 3}


def final_table(matches: pd.DataFrame) -> pd.DataFrame:
    """One row per team, ranked by points, then goal difference, then goals for."""
    rows = []
    for _, m in matches.iterrows():
        rows.append((m["home_team"], HOME_PTS[m["outcome"]],
                     m["home_goals"], m["away_goals"]))
        rows.append((m["away_team"], AWAY_PTS[m["outcome"]],
                     m["away_goals"], m["home_goals"]))
    long = pd.DataFrame(rows, columns=["team", "points", "gf", "ga"])
    table = long.groupby("team").agg(
        played=("points", "size"), points=("points", "sum"),
        goals_for=("gf", "sum"), goals_against=("ga", "sum"),
    )
    table["goal_diff"] = table["goals_for"] - table["goals_against"]
    return table.sort_values(["points", "goal_diff", "goals_for"],
                             ascending=False)


def champion(matches: pd.DataFrame) -> str:
    return final_table(matches).index[0]


def relegation_set(matches: pd.DataFrame, k: int) -> list[str]:
    return list(final_table(matches).index[-k:])


def cumulative_points(matches: pd.DataFrame, n_teams: int,
                      total_rounds: int) -> list[dict]:
    """After each match (date order): each team's points-so-far and games
    remaining (total_rounds minus games played). Basis for 'mathematically
    secured' checks that don't depend on fragile matchday grouping."""
    teams = sorted(set(matches["home_team"]) | set(matches["away_team"]))
    points = {t: 0 for t in teams}
    played = {t: 0 for t in teams}
    trace = []
    for _, m in matches.sort_values("date").iterrows():
        points[m["home_team"]] += HOME_PTS[m["outcome"]]
        points[m["away_team"]] += AWAY_PTS[m["outcome"]]
        played[m["home_team"]] += 1
        played[m["away_team"]] += 1
        trace.append({
            "points": dict(points),
            "remaining": {t: total_rounds - played[t] for t in teams},
        })
    return trace
