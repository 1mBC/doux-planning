from unittest.mock import patch

import pytest

from doux_planning.context import (
    TeamNotReady,
    empty_restaurant,
    generate_team,
    set_role_ladder,
    set_services,
    set_typical_week,
    upsert_employee,
    upsert_service_type,
)
from doux_planning.hydrate import hydrate_delivered_cycle
from doux_planning.planning import PlanningStore
from doux_planning.staff import Employee, Role, RoleLadder
from doux_planning.structures import ArrivalWave, DepartureWave, ServiceType, TypicalWeek, TypicalWeekCell
from doux_planning.types import SearchEffort, ServiceName, Team, WEEKDAYS


def _salle_ladder() -> RoleLadder:
    return RoleLadder(
        Team.SALLE,
        (Role("RESPONSABLE", 3, Team.SALLE), Role("EQUIPIER", 1, Team.SALLE)),
        substitution_explained=True,
    )


def _salle_fiche() -> Employee:
    return Employee(
        id="emma",
        name="Emma",
        role=Role("RESPONSABLE", 3, Team.SALLE),
        team=Team.SALLE,
        contractual_hours_per_week=39,
    )


def _salle_midday_type() -> ServiceType:
    return ServiceType(
        id="salle-midi",
        name="Salle midi",
        team=Team.SALLE,
        service_id=ServiceName.MIDDAY.value,
        arrivals=(ArrivalWave(11 * 60, (1,)),),
        departures=(DepartureWave(16 * 60, ()),),
    )


def _open_week(type_id: str | None) -> TypicalWeek:
    return TypicalWeek(
        cells=tuple(
            TypicalWeekCell(
                weekday=day,
                service_id=ServiceName.MIDDAY.value,
                type_id=type_id,
                closed=False,
                team=Team.SALLE,
            )
            for day in WEEKDAYS
        )
    )


def _complete_salle(state):
    set_role_ladder(state, _salle_ladder())
    upsert_employee(state, _salle_fiche())
    set_services(state, (ServiceName.MIDDAY.value,))
    upsert_service_type(state, _salle_midday_type())
    set_typical_week(state, _open_week("salle-midi"))
    return state


def test_empty_restaurant_has_no_published_cycles():
    state = empty_restaurant("resto-new")
    assert state.published_cycles[Team.SALLE] is None
    assert state.published_cycles[Team.CUISINE] is None
    assert state.cycle is None


def test_generate_team_salle_minimal_leaves_cuisine_unpublished():
    state = _complete_salle(empty_restaurant("resto-new"))
    generate_team(state, Team.SALLE, search=SearchEffort.MINIMAL)
    salle = state.published_cycles[Team.SALLE]
    assert salle is not None
    assert salle.result.assignments
    assert all(shift.employee_id == "emma" for shift in salle.result.assignments)
    assert all(shift.team == Team.SALLE for shift in salle.result.assignments)
    assert state.published_cycles[Team.CUISINE] is None


def test_generate_team_cuisine_not_ready_does_not_solve():
    state = _complete_salle(empty_restaurant("resto-new"))
    with patch("doux_planning.context.generate_cycle") as solve:
        with pytest.raises(TeamNotReady) as raised:
            generate_team(state, Team.CUISINE, search=SearchEffort.MINIMAL)
    assert raised.value.team is Team.CUISINE
    solve.assert_not_called()
    assert state.published_cycles[Team.SALLE] is None
    assert state.published_cycles[Team.CUISINE] is None


def test_regenerate_salle_replaces_salle_only():
    state = _complete_salle(empty_restaurant("resto-new"))
    generate_team(state, Team.SALLE, search=SearchEffort.MINIMAL)
    first = state.published_cycles[Team.SALLE]
    generate_team(state, Team.SALLE, search=SearchEffort.MINIMAL)
    second = state.published_cycles[Team.SALLE]
    assert first is not None
    assert second is not None
    assert second is not first
    assert state.published_cycles[Team.CUISINE] is None


def test_hydrate_saint_cloud_cycle_unchanged():
    state = hydrate_delivered_cycle(PlanningStore(), "saint-cloud")
    assert state.cycle is not None
    assert state.cycle.id == "cycle-1"
    assert state.cycle.draft.assignments
    assert state.published_cycles[Team.SALLE] is None
    assert state.published_cycles[Team.CUISINE] is None
