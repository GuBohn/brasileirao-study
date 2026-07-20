import pandas as pd
import pytest

from brasileirao import transfers
from brasileirao.paths import RAW


def _transfers_df(rows):
    cols = ["from_club_id", "transfer_date", "market_value_in_eur",
            "to_club_name", "player_name"]
    return pd.DataFrame(rows, columns=cols)


def _matches_df(pairs):
    # pairs: list of (team, season); create a single self-match row per pair
    r = [{"home_team": t, "away_team": "X", "season": s} for t, s in pairs]
    return pd.DataFrame(r)


CLUBS_OK = pd.DataFrame({"club_id": list(transfers.SERIE_A_CLUB_IDS),
                         "domestic_competition_id": "BRA1"})


def test_keeps_only_window_season_and_member_clubseasons():
    tr = _transfers_df([
        (614, "2015-07-15", 5e6, "FC Porto", "A"),   # Flamengo 2015 Jul -> keep
        (614, "2015-01-20", 5e6, "FC Porto", "B"),   # January -> drop
        (614, "2020-07-15", 5e6, "FC Porto", "C"),   # 2020 excluded -> drop
        (614, "2011-07-15", 5e6, "FC Porto", "D"),   # pre-2012 -> drop
        (999, "2015-07-15", 5e6, "FC Porto", "E"),   # unmapped club -> drop
    ])
    matches = _matches_df([("Flamengo", 2015)])
    dep = transfers.build_departures(tr, CLUBS_OK, matches)
    assert list(dep["player"]) == ["A"]
    assert dep.loc[0, "club"] == "Flamengo" and dep.loc[0, "season"] == 2015


def test_clubseason_not_in_serie_a_is_dropped():
    tr = _transfers_df([(614, "2015-07-15", 5e6, "FC Porto", "A")])
    dep = transfers.build_departures(tr, CLUBS_OK, _matches_df([("Flamengo", 2016)]))
    assert dep.empty


def test_placeholder_date_flagged_not_dropped():
    tr = _transfers_df([
        (614, "2015-07-01", 5e6, "FC Porto", "ph"),    # placeholder
        (614, "2015-07-15", 5e6, "FC Porto", "real"),  # real
    ])
    dep = transfers.build_departures(tr, CLUBS_OK, _matches_df([("Flamengo", 2015)]))
    flags = dict(zip(dep["player"], dep["is_placeholder_date"]))
    assert flags == {"ph": True, "real": False}


def test_unmapped_bra1_club_raises():
    clubs = pd.concat([CLUBS_OK,
                       pd.DataFrame({"club_id": [123456],
                                     "domestic_competition_id": ["BRA1"]})])
    with pytest.raises(ValueError, match="not in SERIE_A_CLUB_IDS"):
        transfers.build_departures(_transfers_df([]), clubs, _matches_df([]))


def test_no_duplicate_departures():
    tr = _transfers_df([
        (614, "2015-07-15", 5e6, "FC Porto", "A"),
        (614, "2015-07-15", 5e6, "FC Porto", "A"),  # exact dup
    ])
    dep = transfers.build_departures(tr, CLUBS_OK, _matches_df([("Flamengo", 2015)]))
    assert len(dep) == 1


@pytest.mark.skipif(not (RAW / "tm_transfers.csv.gz").exists(),
                    reason="run transfers.build() first to cache the dump")
def test_real_dump_has_reasonable_treated_set():
    dep = transfers.build()
    treated = dep.groupby(["club", "season"]).ngroups
    assert 40 <= treated <= 80, f"treated club-seasons drifted to {treated}"
    assert dep["market_value_eur"].notna().mean() > 0.8
