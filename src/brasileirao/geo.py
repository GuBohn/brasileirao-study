"""Club home-city coordinates and travel distances."""
import numpy as np
import pandas as pd

from .paths import REFERENCE

EARTH_RADIUS_KM = 6371.0
STADIUMS_FILE = REFERENCE / "stadiums.csv"

# Match-data spelling -> stadiums.csv spelling. Extend when
# test_every_team_in_match_data_has_coordinates lists unmapped names.
TEAM_ALIASES: dict[str, str] = {
    "Atletico-PR": "Athletico-PR",
    "Red Bull Bragantino": "Bragantino",
    "Botafogo-RJ": "Botafogo",
    "Barueri": "Gremio Barueri",
}


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return float(2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a)))


def load_stadiums() -> pd.DataFrame:
    return pd.read_csv(STADIUMS_FILE).set_index("team")


def _resolve(teams: pd.Series, stadiums: pd.DataFrame) -> pd.DataFrame:
    canonical = teams.replace(TEAM_ALIASES)
    missing = sorted(set(canonical) - set(stadiums.index))
    if missing:
        raise KeyError(f"No coordinates for {missing}; extend TEAM_ALIASES "
                       "or stadiums.csv")
    return stadiums.loc[canonical].reset_index(drop=True)


def travel_km(matches: pd.DataFrame) -> pd.Series:
    """Great-circle distance the away team travels (its city -> home city)."""
    stadiums = load_stadiums()
    home = _resolve(matches["home_team"], stadiums)
    away = _resolve(matches["away_team"], stadiums)
    lat1, lon1 = np.radians(away["lat"]), np.radians(away["lon"])
    lat2, lon2 = np.radians(home["lat"]), np.radians(home["lon"])
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    dist = 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))
    return pd.Series(np.asarray(dist), index=matches.index, name="travel_km")
