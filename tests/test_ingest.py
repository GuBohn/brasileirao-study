import pandas as pd
import pytest

from brasileirao import ingest


def _raw_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "data": ["11/04/2021", "28/02/2021", "01/05/2004"],
            "hora": ["16:00", "18:15", "16:00"],
            "mandante": ["Flamengo", "Gremio", "Santos"],
            "visitante": ["Vasco", "Internacional", "Vitoria"],
            "mandante_placar": ["1", "2", "3"],
            "visitante_placar": ["1", "0", "1"],
            "arena": ["Maracana", "Arena do Gremio", "Vila Belmiro"],
            "mandante_estado": ["RJ", "RS", "SP"],
            "visitante_estado": ["RJ", "RS", "BA"],
        }
    )


def test_clean_canonical_columns_and_sort():
    df = ingest.clean(_raw_fixture())
    assert list(df.columns) == [
        "date", "season", "home_team", "away_team", "home_goals",
        "away_goals", "outcome", "stadium", "home_state", "away_state",
    ]
    assert df["date"].is_monotonic_increasing
    assert df["outcome"].tolist() == ["H", "H", "D"]  # sorted: 2004, feb-2021, apr-2021


def test_season_rule_early_year_belongs_to_previous_season():
    df = ingest.clean(_raw_fixture())
    by_team = df.set_index("home_team")["season"]
    assert by_team["Gremio"] == 2020   # Feb 2021 match -> 2020 season
    assert by_team["Flamengo"] == 2021
    assert by_team["Santos"] == 2004


def test_clean_raises_on_missing_columns():
    bad = _raw_fixture().drop(columns=["mandante"])
    with pytest.raises(ValueError, match="mandante"):
        ingest.clean(bad)


def test_clean_deduplicates_exact_copies():
    doubled = pd.concat([_raw_fixture(), _raw_fixture()])
    assert len(ingest.clean(doubled)) == 3
