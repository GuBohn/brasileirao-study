import pandas as pd

from brasileirao import standings

POINTS = {"H": (3, 0), "D": (1, 1), "A": (0, 3)}


def _round_robin(results):
    """results: list of (home, away, outcome). Dates auto-incremented."""
    base = pd.Timestamp("2015-05-01")
    rows = []
    for i, (h, a, o) in enumerate(results):
        hg, ag = {"H": (1, 0), "D": (0, 0), "A": (0, 1)}[o]
        rows.append({"league": "T", "season": 2015, "date": base + pd.Timedelta(days=i),
                     "home_team": h, "away_team": a, "home_goals": hg,
                     "away_goals": ag, "outcome": o})
    return pd.DataFrame(rows)


def test_final_table_points_identity():
    df = _round_robin([("A", "B", "H"), ("B", "C", "D"),
                       ("C", "A", "A"), ("A", "C", "H"),
                       ("B", "A", "D"), ("C", "B", "H")])
    table = standings.final_table(df)
    decisive = (df["outcome"] != "D").sum()
    draws = (df["outcome"] == "D").sum()
    assert table["points"].sum() == 3 * decisive + 2 * draws
    assert set(table.index) == {"A", "B", "C"}
    assert (table["played"] == 4).all()


def test_champion_and_relegation():
    df = _round_robin([("A", "B", "H"), ("A", "C", "H"), ("A", "D", "H"),
                       ("B", "C", "H"), ("B", "D", "H"), ("C", "D", "H")])
    # A wins all, then B, then C, D last.
    assert standings.champion(df) == "A"
    assert standings.relegation_set(df, k=1) == ["D"]


def test_cumulative_points_tracks_remaining():
    df = _round_robin([("A", "B", "H"), ("A", "C", "H")])
    trace = standings.cumulative_points(df, n_teams=3, total_rounds=4)
    last = trace[-1]  # after 2 matches
    assert last["points"]["A"] == 6
    assert last["remaining"]["A"] == 4 - 2  # A played 2 of its 4 games
    assert last["remaining"]["B"] == 4 - 1
