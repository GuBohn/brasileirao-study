import pandas as pd
import pytest

from brasileirao import ratings


def _matches(outcomes):
    n = len(outcomes)
    return pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=n, freq="7D"),
            "home_team": ["A"] * n,
            "away_team": ["B"] * n,
            "outcome": outcomes,
        }
    )


def test_initial_ratings_are_1500():
    out = ratings.add_elo(_matches(["H"]))
    assert out.loc[0, "elo_home_pre"] == 1500
    assert out.loc[0, "elo_away_pre"] == 1500


def test_winner_gains_rating():
    out = ratings.add_elo(_matches(["H", "H"]))
    assert out.loc[1, "elo_home_pre"] > 1500
    assert out.loc[1, "elo_away_pre"] < 1500


def test_causality_result_does_not_affect_own_pre_rating():
    a = ratings.add_elo(_matches(["H", "H", "A"]))
    b = ratings.add_elo(_matches(["H", "H", "H"]))  # only match 3 differs
    cols = ["elo_home_pre", "elo_away_pre"]
    pd.testing.assert_frame_equal(a.loc[:2, cols], b.loc[:2, cols])


def test_requires_sorted_dates():
    m = _matches(["H", "A"]).iloc[::-1].reset_index(drop=True)
    with pytest.raises(ValueError, match="sorted"):
        ratings.add_elo(m)
