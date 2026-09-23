from dataclasses import replace

import pytest

from doux_planning.context import (
    NoPublishedCycle,
    cycle_recap,
    cycle_recap_from_draft,
    cycle_score,
    empty_restaurant,
    generate_team,
    upsert_employee,
)
from doux_planning.engine import PlanningDraft, evaluate
from doux_planning.hydrate import load_delivered_cycle
from doux_planning.planning import PublishedCycle
from doux_planning.staff import Unavailability, Wellbeing
from doux_planning.structures import ArrivalWave, DepartureWave, RestaurantHours, ServiceStructure
from doux_planning.types import SearchEffort, ServiceName, Team, WarningSeverity, WEEKDAYS
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


def test_rest_between_warning_payload_is_minutes_not_french():
    person = employee("ChefA", "chef", employee_id="chef-a")
    assignments = [
        _shift("chef-a", 0, 10 * 60, 23 * 60, 4, weekday="monday"),
        _shift("chef-a", 1, 8 * 60, 16 * 60, 4, weekday="tuesday"),
    ]
    result = evaluate(_draft(assignments, employees=(person,)))
    warning = next(item for item in result.warnings if item.code == "rest_between_days")
    assert warning.day_index == 0
    assert warning.payload == {
        "day_index_b": 1,
        "end_minutes": 23 * 60,
        "start_minutes_b": 8 * 60,
        "rest_minutes": 9 * 60,
        "required_minutes": 660,
    }
    assert not hasattr(warning, "message")
    assert "lundi" not in str(warning.payload)
    assert "mardi" not in str(warning.payload)


def test_empty_post_payload_names_english_hole():
    assignments = [_shift("chef-a", 0, 11 * 60, 16 * 60, 4)]
    result = evaluate(_draft(assignments))
    hole = next(
        item
        for item in result.of_severity(WarningSeverity.COUVERTURE)
        if item.code == "empty_post"
        and item.payload.get("post_level") == 4
        and item.payload.get("start_minutes") == 10 * 60
    )
    assert hole.day_index == 0
    assert hole.payload == {
        "weekday": "monday",
        "service_id": ServiceName.MIDDAY.value,
        "team": Team.CUISINE.value,
        "start_minutes": 10 * 60,
        "end_minutes": 11 * 60,
        "post_level": 4,
    }
    assert not hasattr(hole, "message")


def test_wish_max_evening_shows_week_counts():
    person = employee("Emma", "sous-chef", hours=39, employee_id="emma").with_wellbeing(
        Wellbeing(max_services={ServiceName.EVENING.value: 2})
    )
    assignments = [
        _shift("emma", 0, 19 * 60, 23 * 60, 3, service=ServiceName.EVENING.value),
        _shift("emma", 7, 19 * 60, 23 * 60, 3, service=ServiceName.EVENING.value),
        _shift("emma", 8, 19 * 60, 23 * 60, 3, service=ServiceName.EVENING.value),
        _shift("emma", 9, 19 * 60, 23 * 60, 3, service=ServiceName.EVENING.value),
    ]
    draft = PlanningDraft(
        employees=(person,),
        structures=(),
        hours=RestaurantHours.multi_service(ServiceName.EVENING.value),
        assignments=tuple(assignments),
    )
    result = evaluate(draft)
    state = empty_restaurant("resto-wish")
    upsert_employee(state, person)
    state.published_cycles[Team.CUISINE] = PublishedCycle(id="cuisine", draft=draft, result=result)
    recap = cycle_recap(state, Team.CUISINE)
    cell = recap.wish_rows[0].cells["max_evening"]
    assert cell is not None
    assert cell.ok is False
    assert cell.kind == "max_evenings"
    assert cell.payload == {
        "limit": 2,
        "count_week_0": 1,
        "count_week_7": 3,
        "service_id": ServiceName.EVENING.value,
    }
    assert not hasattr(cell, "text")


def _score_monday_draft(person, assignments) -> PlanningDraft:
    structure = ServiceStructure(
        id="one-post",
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=frozenset({"monday"}),
        arrivals=(ArrivalWave(11 * 60, (2,)),),
        departures=(DepartureWave(15 * 60, ()),),
    )
    return PlanningDraft(
        employees=(person,),
        structures=(structure,),
        hours=RestaurantHours.multi_service(ServiceName.MIDDAY.value, closed_weekdays=set(WEEKDAYS) - {"monday"}),
        assignments=tuple(assignments),
    )


def test_cycle_score_notes_out_of_ten():
    person = employee("Sam", "commis", hours=4, employee_id="sam")
    assignments = [
        _shift("sam", 0, 11 * 60, 15 * 60, 2),
        _shift("sam", 7, 11 * 60, 15 * 60, 2),
    ]
    draft = _score_monday_draft(person, assignments)
    result = evaluate(draft)
    score = cycle_score(draft, result)
    assert result.codes().isdisjoint({"empty_post"})
    assert score.notes.couverture == 10.0
    assert score.notes.legal == 10.0
    assert score.notes.contrat == 10.0
    assert score.notes.wellbeing is None
    assert score.notes.roles == 10.0
    assert score.global_score is not None
    assert score.weights == {"couverture": 3.0, "legal": 3.0, "contrat": 2.0, "wellbeing": 1.5, "roles": 0.5}

    blocked = person.with_unavailability(Unavailability(weekday="monday", service_id=ServiceName.MIDDAY.value))
    broken = cycle_score(_score_monday_draft(blocked, assignments), evaluate(_score_monday_draft(blocked, assignments)))
    assert broken.notes.contrat is not None
    assert broken.notes.contrat < 10.0

    state = empty_restaurant("resto-score")
    upsert_employee(state, person)
    state.published_cycles[Team.CUISINE] = PublishedCycle(id="cuisine", draft=draft, result=result)
    recap = cycle_recap(state, Team.CUISINE)
    assert recap.score.notes == score.notes
    assert not hasattr(recap.score, "resumes")
    assert recap.score.global_score == score.global_score
    assert recap.facts
    for row in (*recap.legal_rows, *recap.wish_rows):
        for cell in row.cells.values():
            if cell is None:
                continue
            assert not hasattr(cell, "text")
            assert cell.kind
            assert isinstance(cell.payload, dict)


def test_cycle_score_asymmetric_occupation():
    assignments = [
        _shift("sam", 0, 11 * 60, 15 * 60, 2),
        _shift("sam", 7, 11 * 60, 15 * 60, 2),
    ]
    under = employee("Sam", "commis", hours=6, employee_id="sam")
    over = employee("Sam", "commis", hours=2, employee_id="sam")
    under_score = cycle_score(_score_monday_draft(under, assignments), evaluate(_score_monday_draft(under, assignments)))
    over_score = cycle_score(_score_monday_draft(over, assignments), evaluate(_score_monday_draft(over, assignments)))
    assert under_score.notes.contrat is not None
    assert over_score.notes.contrat is not None
    assert over_score.notes.contrat < under_score.notes.contrat

    exact = employee("Sam", "commis", hours=4, employee_id="sam")
    draft = _score_monday_draft(exact, assignments)
    score = cycle_score(draft, evaluate(draft))
    assert score.notes.contrat == 10.0
    assert score.notes.roles == 10.0
    assert not hasattr(score, "resumes")

    blocked = exact.with_unavailability(Unavailability(weekday="monday", service_id=ServiceName.MIDDAY.value))
    broken = cycle_score(_score_monday_draft(blocked, assignments), evaluate(_score_monday_draft(blocked, assignments)))
    assert broken.notes.roles == 10.0
    assert broken.notes.contrat is not None
    assert broken.notes.contrat < 10.0
    assert not hasattr(broken, "resumes")


def test_saint_cloud_example_has_cycle_score_without_rewrite():
    delivered = load_delivered_cycle("saint-cloud")
    draft = PlanningDraft(
        employees=delivered.employees,
        structures=delivered.structures,
        hours=delivered.hours,
        assignments=delivered.assignments,
    )
    result = evaluate(draft)
    score = cycle_score(draft, result)
    assert len(draft.assignments) == 92
    assert score.notes.couverture == 10.0
    assert score.global_score is not None
    assert not hasattr(score, "resumes")


def test_saint_cloud_recap_facts_are_evaluate_misses_then_hits():
    delivered = load_delivered_cycle("saint-cloud")
    draft = PlanningDraft(
        employees=delivered.employees,
        structures=delivered.structures,
        hours=delivered.hours,
        assignments=delivered.assignments,
    )
    result = evaluate(draft)
    state = empty_restaurant("saint-cloud")
    state.employees = list(delivered.employees)
    state.structures = list(delivered.structures)
    state.hours = delivered.hours
    state.published_cycles[Team.SALLE] = PublishedCycle(id=Team.SALLE.value, draft=draft, result=result)
    recap = cycle_recap(state, Team.SALLE)
    evaluate_misses = [fact for fact in recap.facts if fact.polarity == "miss" and fact.kind != "role_gap"]
    assert len(result.assignments) == 92
    assert len(evaluate_misses) == 13
    assert [fact.kind for fact in evaluate_misses] == [item.code for item in result.warnings]
    assert recap.stats.below_role == 46
    assert recap.stats.wellbeing.held == 10
    assert recap.stats.wellbeing.total == 12
    diane = next(row for row in recap.wish_rows if row.employee_id == "diane")
    contrat = diane.cells["contrat"]
    assert contrat is not None
    assert contrat.ok is False
    assert contrat.kind == "contract_hours"
    assert contrat.payload["contracted"] == 39
    assert set(contrat.payload) == {"hours_week_0", "hours_week_7", "contracted"}
    assert not hasattr(contrat, "text")
    assert not hasattr(recap.score, "resumes")
    assert all(not hasattr(item, "message") for item in result.warnings)
    assert any(fact.kind == "contract_hours" and fact.polarity == "miss" for fact in evaluate_misses)
    assert any(fact.kind == "consecutive_rest_days" and fact.polarity == "miss" for fact in evaluate_misses)


def test_cycle_recap_from_draft_matches_live_when_published_identical():
    delivered = load_delivered_cycle("saint-cloud")
    draft = PlanningDraft(
        employees=delivered.employees,
        structures=delivered.structures,
        hours=delivered.hours,
        assignments=delivered.assignments,
    )
    result = evaluate(draft)
    state = empty_restaurant("saint-cloud")
    state.employees = list(delivered.employees)
    state.structures = list(delivered.structures)
    state.hours = delivered.hours
    state.published_cycles[Team.SALLE] = PublishedCycle(id=Team.SALLE.value, draft=draft, result=result)
    recap = cycle_recap(state, Team.SALLE)
    from_draft = cycle_recap_from_draft(draft, result)
    assert from_draft.facts == recap.facts
    assert from_draft.stats == recap.stats
    assert from_draft.score == recap.score
