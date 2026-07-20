import pandas as pd
import pytest

from brasileirao import geo
from brasileirao.ingest import PROCESSED_FILE


def test_haversine_belem_porto_alegre():
    d = geo.haversine_km(-1.45, -48.49, -30.03, -51.23)
    assert 3090 <= d <= 3290


def test_haversine_zero_distance():
    assert geo.haversine_km(-23.55, -46.63, -23.55, -46.63) == 0


def test_travel_km_same_city_is_zero():
    matches = pd.DataFrame(
        {"home_team": ["Flamengo"], "away_team": ["Vasco"]}
    )
    assert geo.travel_km(matches).iloc[0] == 0


def test_travel_km_north_south():
    matches = pd.DataFrame(
        {"home_team": ["Paysandu"], "away_team": ["Gremio"]}
    )
    assert geo.travel_km(matches).iloc[0] > 3000


@pytest.mark.skipif(not PROCESSED_FILE.exists(), reason="run ingest.build() first")
def test_every_team_in_match_data_has_coordinates():
    matches = pd.read_parquet(PROCESSED_FILE)
    teams = set(matches["home_team"]) | set(matches["away_team"])
    known = set(geo.load_stadiums().index) | set(geo.TEAM_ALIASES)
    unmapped = sorted(teams - known)
    assert not unmapped, f"Add these to stadiums.csv or TEAM_ALIASES: {unmapped}"
