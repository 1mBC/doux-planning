from doux_planning.context import (
    empty_restaurant,
    expand_typical_week,
    fortnight_coverage,
    set_role_ladder,
    set_services,
    set_typical_week,
    team_ready,
    upsert_employee,
    upsert_service_type,
)
from doux_planning.hydrate import hydrate_delivered_cycle
from doux_planning.planning import PlanningStore
from doux_planning.staff import Employee, Role, RoleLadder
from doux_planning.structures import ArrivalWave, DepartureWave, ServiceType, TypicalWeek, TypicalWeekCell
from doux_planning.types import ServiceName, Team, WEEKDAYS


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


def test_empty_restaurant_is_not_ready():
    state = empty_restaurant("resto-new")
    assert state.identity.name == ""
    assert state.identity.legal_context_id == "france"
    assert state.employees == []
    assert state.service_types == []
    assert state.company_services == ()
    assert state.typical_week is None
    assert state.hours is None
    assert state.cycle is None
    assert not team_ready(state, Team.SALLE)
    assert not team_ready(state, Team.CUISINE)


def test_salle_ready_without_cuisine_and_open_cell_needs_type():
    state = _complete_salle(empty_restaurant("resto-new"))
    assert team_ready(state, Team.SALLE)
    assert not team_ready(state, Team.CUISINE)
    set_typical_week(state, _open_week(None))
    assert not team_ready(state, Team.SALLE)


def test_expand_typical_week_week_a_equals_week_b():
    state = _complete_salle(empty_restaurant("resto-new"))
    structures = expand_typical_week(state)
    assert structures
    week_a, week_b = fortnight_coverage(structures)
    assert week_a == week_b
    assert week_a


def test_hydrate_saint_cloud_still_has_hours_and_assignments():
    state = hydrate_delivered_cycle(PlanningStore(), "saint-cloud")
    assert state.hours is not None
    assert state.hours.services
    assert state.cycle is not None
    assert state.cycle.draft.assignments
    assert not team_ready(state, Team.SALLE)
