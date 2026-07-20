import pandas as pd
import pytest

from brasileirao import features


def _matches():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2019-05-01", "2019-05-08", "2020-09-01", "2021-11-01"]
            ),
            "home_team": ["Flamengo", "Vasco", "Flamengo", "Gremio"],
            "away_team": ["Gremio", "Flamengo", "Vasco", "Paysandu"],
            "home_state": ["RJ", "RJ", "RJ", "RS"],
            "away_state": ["RS", "RJ", "RJ", "PA"],
            "outcome": ["H", "D", "A", "H"],
        }
    )


def test_crowd_status_windows():
    s = features.crowd_status(_matches()["date"])
    assert s.tolist() == ["full", "full", "closed", "partial"]


def test_build_features_keeps_three_way_crowd_status():
    f = features.build_features(_matches())
    assert f["crowd"].tolist() == ["full", "full", "closed", "partial"]
    assert f["crowd_closed"].tolist() == [0, 0, 1, 0]


def test_rest_days_first_match_capped_and_causal():
    rest = features.rest_days(_matches())
    assert rest.loc[0, "home_rest"] == 14  # Flamengo's first match
    assert rest.loc[1, "away_rest"] == 7   # Flamengo played 7 days before
    assert rest.loc[2, "home_rest"] == 14  # capped: gap >> 14 days


def test_rest_days_stable_when_team_appears_twice_same_date():
    # Real-data quirk (e.g. 2008-07-06): a team can appear in two separate
    # matches dated the same day, so (date, team) is not a unique key. A
    # join on that key would many-to-many blow up and misalign every later
    # row. Row count must stay 1:1 with the input, and later matches must
    # not be corrupted by the earlier same-date collision.
    matches = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2020-01-01", "2020-01-08", "2020-01-08", "2020-01-15"]
            ),
            "home_team": ["Flamengo", "Flamengo", "Vasco", "Gremio"],
            "away_team": ["Vasco", "Botafogo", "Flamengo", "Flamengo"],
        }
    )
    rest = features.rest_days(matches)
    assert len(rest) == len(matches)
    assert rest.loc[3, "away_rest"] == 7  # Flamengo last played 2020-01-08


def test_same_state_flag():
    f = features.build_features(_matches())
    assert f["same_state"].tolist() == [0, 1, 1, 0]


def test_target_encoding():
    f = features.build_features(_matches())
    assert f["y"].tolist() == [0, 1, 2, 0]


def test_build_raises_on_unsorted():
    with pytest.raises(ValueError, match="sorted"):
        features.build_features(_matches().iloc[::-1].reset_index(drop=True))


def test_feature_columns_exact():
    f = features.build_features(_matches())
    assert list(f[features.FEATURES].columns) == features.FEATURES
