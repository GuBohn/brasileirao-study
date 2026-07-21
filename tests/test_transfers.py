import pandas as pd
import pytest

from brasileirao import transfers


def test_parse_fee_variants():
    fee, typ = transfers._parse_fee("€10.60m")
    assert typ == "permanent" and fee == pytest.approx(10_600_000.0)
    fee, typ = transfers._parse_fee("€145k")
    assert typ == "permanent" and fee == pytest.approx(145_000.0)
    fee, typ = transfers._parse_fee("Loan fee:€8.00m")
    assert typ == "loan" and fee == pytest.approx(8_000_000.0)
    assert transfers._parse_fee("loan transfer") == (None, "loan")
    assert transfers._parse_fee("free transfer") == (0.0, "free")
    assert transfers._parse_fee("?") == (None, "permanent")


def test_is_foreign_uses_accent_and_markers():
    assert transfers._is_foreign("Inter Serie A")             # Italy (no accent)
    assert transfers._is_foreign("Aris Limassol Cyprus League")
    assert not transfers._is_foreign("São Paulo Série A")     # Brazil (accented)
    assert not transfers._is_foreign("Ferroviária Brazil")    # Brazil lower tier
    assert not transfers._is_foreign("Without Club")          # release, not abroad


DEPARTURES_HTML = """
<h2>Departures</h2>
<table class="items"><tbody>
  <tr>
    <td class="hauptlink"><a href="/x">Léo Duarte</a></td><td>23</td><td>BRA</td>
    <td><a href="/inter">Inter</a> Serie A</td><td>€10.60m</td>
  </tr>
  <tr>
    <td class="hauptlink"><a href="/y">Fulano</a></td><td>25</td><td>BRA</td>
    <td><a href="/goias">Goiás</a> Série A</td><td>loan transfer</td>
  </tr>
</tbody></table>
"""


def test_parse_departures_extracts_fields_and_foreign():
    rows = transfers.parse_departures(DEPARTURES_HTML, "Flamengo", 2019)
    assert len(rows) == 2
    leo, dom = rows
    assert leo["player"] == "Léo Duarte" and leo["to_club"] == "Inter"
    assert leo["to_foreign"] and leo["transfer_type"] == "permanent"
    assert leo["fee_eur"] == pytest.approx(10_600_000.0)
    assert not dom["to_foreign"] and dom["transfer_type"] == "loan"
    assert dom["fee_eur"] is None


def test_serie_a_completeness_raises_on_unmapped_club():
    m = pd.DataFrame({"home_team": ["Nonexistent FC"], "away_team": ["Flamengo"],
                      "season": [2015]})
    with pytest.raises(ValueError, match="no Transfermarkt id"):
        transfers._serie_a_club_seasons(m)
