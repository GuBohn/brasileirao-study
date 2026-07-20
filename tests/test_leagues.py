import numpy as np
import pandas as pd
import pytest

from brasileirao import leagues


def test_normalize_main_derives_outcome_and_schema():
    raw = pd.DataFrame({
        "Date": ["10/08/2012", "11/08/2012", "11/08/2012"],
        "HomeTeam": ["Arsenal", "Chelsea", "Everton"],
        "AwayTeam": ["Sunderland", "Reading", "Man United"],
        "FTHG": [0, 2, 0], "FTAG": [0, 1, 1], "FTR": ["D", "H", "A"],
        "PSCH": [1.5, 1.8, 4.0], "PSCD": [4.0, 3.6, 3.5], "PSCA": [7.0, 4.5, 1.9],
    })
    out = leagues._normalize_main(raw, season=2012, league="Premier League")
    assert list(out.columns) == leagues.CANONICAL
    assert out["outcome"].tolist() == ["D", "H", "A"]
    assert (out["season"] == 2012).all()
    assert out["league"].eq("Premier League").all()
    assert out["odds_h"].tolist() == [1.5, 1.8, 4.0]


def test_normalize_extra_reads_season_column_and_home_away():
    raw = pd.DataFrame({
        "Season": [2012, 2012], "Date": ["19/05/2012", "20/05/2012"],
        "Home": ["Flamengo RJ", "Santos"], "Away": ["Botafogo RJ", "Palmeiras"],
        "HG": [2, 1], "AG": [0, 1], "Res": ["H", "D"],
        "PSCH": [1.7, 2.1], "PSCD": [3.4, 3.2], "PSCA": [5.0, 3.6],
    })
    out = leagues._normalize_extra(raw, league="Brasileirao")
    assert list(out.columns) == leagues.CANONICAL
    assert out["outcome"].tolist() == ["H", "D"]
    assert out["home_team"].tolist() == ["Flamengo RJ", "Santos"]
    assert (out["season"] == 2012).all()


def test_missing_result_column_raises():
    raw = pd.DataFrame({"Date": ["10/08/2012"], "HomeTeam": ["A"], "AwayTeam": ["B"]})
    with pytest.raises(ValueError, match="missing"):
        leagues._normalize_main(raw, season=2012, league="X")


def test_odds_fallback_to_b365_then_nan():
    raw = pd.DataFrame({
        "Date": ["10/08/2012"], "HomeTeam": ["A"], "AwayTeam": ["B"],
        "FTHG": [1], "FTAG": [0], "FTR": ["H"],
        "B365H": [1.5], "B365D": [4.0], "B365A": [7.0],
    })
    out = leagues._normalize_main(raw, season=2012, league="X")
    assert out["odds_h"].iloc[0] == 1.5
    raw2 = raw.drop(columns=["B365H", "B365D", "B365A"])
    out2 = leagues._normalize_main(raw2, season=2012, league="X")
    assert out2[["odds_h", "odds_d", "odds_a"]].isna().all(axis=None)


def test_implied_probabilities_devigs_to_one():
    odds = np.array([[2.0, 4.0, 4.0], [1.5, 4.0, 7.0]])
    p = leagues.implied_probabilities(odds)
    assert np.allclose(p.sum(axis=1), 1.0)
    assert p[0, 0] > p[0, 1]  # shorter price -> higher probability


def test_season_code_format():
    assert leagues._season_code(2012) == "1213"
    assert leagues._season_code(1999) == "9900"
