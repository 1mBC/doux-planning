from dataclasses import replace

import pytest

from doux_planning.context import (
    empty_restaurant,
    enter_live_sandbox,
    remove_employee,
    upsert_employee,
)
from doux_planning.engine import EngineResult, PlanningDraft
from doux_planning.invites import UnknownEmployee
from doux_planning.planning import PublishedCycle
from doux_planning.staff import Employee, Role, default_legal_rules
from doux_planning.structures import RestaurantHours
from doux_planning.types import ServiceName, Team
from tests.test_team_generate import _salle_fiche


def _cuisine_fiche() -> Employee:
    return Employee(
        id="karim",
        name="Karim",
        role=Role("CHEF", 4, Team.CUISINE),
        team=Team.CUISINE,
        contractual_hours_per_week=39,
    )


def _stub_cycle(team: Team, person: Employee) -> PublishedCycle:
    draft = PlanningDraft(
        employees=(person,),
        structures=(),
        hours=RestaurantHours.multi_service(ServiceName.MIDDAY.value),
        assignments=(),
        legal_rules=default_legal_rules(),
    )
    return PublishedCycle(
        id=team.value,
        draft=draft,
        result=EngineResult(assignments=(), warnings=()),
    )


def _two_teams_published_salle_live():
    state = empty_restaurant("resto-new")
    emma = _salle_fiche()
    karim = _cuisine_fiche()
    upsert_employee(state, emma)
    upsert_employee(state, karim)
    state.identity = replace(state.identity, linked_employee_ids=frozenset({emma.id, karim.id}))
    cuisine_cycle = _stub_cycle(Team.CUISINE, karim)
    state.published_cycles[Team.SALLE] = _stub_cycle(Team.SALLE, emma)
    state.published_cycles[Team.CUISINE] = cuisine_cycle
    enter_live_sandbox(state, Team.SALLE)
    enter_live_sandbox(state, Team.CUISINE)
    return state, cuisine_cycle


def test_remove_salle_employee_unpublishes_salle_keeps_cuisine():
    state, cuisine_cycle = _two_teams_published_salle_live()
    cuisine_live = state.live_sandboxes[Team.CUISINE]
    hours = state.hours
    types = state.service_types
    week = state.typical_week
    ladders = dict(state.ladders)
    returned = remove_employee(state, "emma")
    assert returned is state
    assert all(person.id != "emma" for person in state.employees)
    assert any(person.id == "karim" for person in state.employees)
    assert "emma" not in state.identity.linked_employee_ids
    assert "karim" in state.identity.linked_employee_ids
    assert state.published_cycles[Team.SALLE] is None
    assert state.live_sandboxes[Team.SALLE] is None
    assert state.published_cycles[Team.CUISINE] is cuisine_cycle
    assert state.live_sandboxes[Team.CUISINE] is cuisine_live
    assert state.hours is hours
    assert state.service_types is types
    assert state.typical_week is week
    assert state.ladders == ladders


def test_remove_unknown_employee_raises():
    state, cuisine_cycle = _two_teams_published_salle_live()
    staff = list(state.employees)
    linked = state.identity.linked_employee_ids
    salle_published = state.published_cycles[Team.SALLE]
    salle_live = state.live_sandboxes[Team.SALLE]
    cuisine_live = state.live_sandboxes[Team.CUISINE]
    with pytest.raises(UnknownEmployee):
        remove_employee(state, "ghost")
    assert state.employees == staff
    assert state.identity.linked_employee_ids is linked
    assert state.published_cycles[Team.SALLE] is salle_published
    assert state.live_sandboxes[Team.SALLE] is salle_live
    assert state.published_cycles[Team.CUISINE] is cuisine_cycle
    assert state.live_sandboxes[Team.CUISINE] is cuisine_live
