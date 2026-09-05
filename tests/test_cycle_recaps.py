from dataclasses import replace

import pytest

from doux_planning.context import NoPublishedCycle, cycle_recap, empty_restaurant, generate_team, upsert_employee
from doux_planning.engine import evaluate
from doux_planning.staff import Wellbeing
from doux_planning.types import SearchEffort, Team
from tests.fixtures import employee
from tests.test_engine import _draft, _shift
from tests.test_team_generate import _complete_salle, _salle_fiche


def test_cycle_recap_requires_published():
    state = empty_restaurant("resto-new")
    with pytest.raises(NoPublishedCycle):
        cycle_recap(state, Team.SALLE)


def test_salle_recap_has_legal_row_per_fiche_and_no_cuisine_col():
    state = _complete_salle(empty_restaurant("resto-new"))
    generate_team(state, Team.SALLE, search=SearchEffort.MINIMAL)
    recap = cycle_recap(state, Team.SALLE)
    published = state.published_cycles[Team.SALLE]
    assert published is not None
    assert recap.stats.assignments == len(published.result.assignments)
    assert {row.employee_id for row in recap.legal_rows} == {person.id for person in state.employees if person.team == Team.SALLE}
    assert all(row.employee_id for row in recap.legal_rows)
    assert "max_daily_cuisine" not in {col.id for col in recap.legal_cols}
    assert "max_daily_salle" in {col.id for col in recap.legal_cols}
    assert {col.key for col in recap.wish_cols}.isdisjoint({"we1j", "weA", "weB", "soirs", "repos2"})
    assert "contrat" in {col.key for col in recap.wish_cols}


def test_weekend_rest_day_column_null_for_colleague_without_box():
    state = _complete_salle(empty_restaurant("resto-new"))
    posed = _salle_fiche().with_wellbeing(Wellbeing(weekend_rest_day=True))
    colleague = replace(_salle_fiche(), id="lea", name="Lea", contractual_hours_per_week=25)
    upsert_employee(state, posed)
    upsert_employee(state, colleague)
    generate_team(state, Team.SALLE, search=SearchEffort.MINIMAL)
    recap = cycle_recap(state, Team.SALLE)
    assert any(col.key == "weekend_rest_day" for col in recap.wish_cols)
    by_id = {row.employee_id: row for row in recap.wish_rows}
    assert by_id["emma"].cells["weekend_rest_day"] is not None
    assert by_id["lea"].cells["weekend_rest_day"] is None


def test_rest_between_warning_has_french_clocks():
    person = employee("ChefA", "chef", employee_id="chef-a")
    assignments = [
        _shift("chef-a", 0, 10 * 60, 23 * 60, 4, weekday="monday"),
        _shift("chef-a", 1, 8 * 60, 16 * 60, 4, weekday="tuesday"),
    ]
    result = evaluate(_draft(assignments, employees=(person,)))
    warning = next(item for item in result.warnings if item.code == "rest_between_days")
    assert warning.day_index == 0
    assert "lundi 23h" in warning.message
    assert "mardi 8h" in warning.message
    assert "→" in warning.message
    assert "moins de 11 h de repos" in warning.message
