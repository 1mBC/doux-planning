from unittest.mock import patch

import pytest

from doux_planning.context import (
    employee_board,
    empty_restaurant,
    enter_live_sandbox,
    generate_team,
    upsert_employee,
)
from doux_planning.invites import UnknownEmployee
from doux_planning.planning import PlanningStore
from doux_planning.staff import Employee, Role, Unavailability
from doux_planning.types import SearchEffort, Team, WarningSeverity, WellbeingPreference
from tests.test_team_generate import _complete_salle


def _salle_with_wish():
    state = _complete_salle(empty_restaurant("resto-new"))
    emma = next(person for person in state.employees if person.id == "emma")
    upsert_employee(
        state,
        emma.with_wellbeing(WellbeingPreference.TWO_CONSECUTIVE_REST_DAYS).with_unavailability(
            Unavailability(weekday="sunday")
        ),
    )
    upsert_employee(
        state,
        Employee(
            id="karim",
            name="Karim",
            role=Role("CHEF", 4, Team.CUISINE),
            team=Team.CUISINE,
            contractual_hours_per_week=39,
        ),
    )
    generate_team(state, Team.SALLE, search=SearchEffort.MINIMAL)
    return state


def test_unknown_employee_raises():
    state = _salle_with_wish()
    with pytest.raises(UnknownEmployee):
        employee_board(state, "ghost")


def test_cuisine_without_cycle_has_empty_assignments():
    state = _salle_with_wish()
    with patch("doux_planning.context.generate_cycle") as solve:
        board = employee_board(state, "karim")
    solve.assert_not_called()
    assert board.employee_id == "karim"
    assert board.team is Team.CUISINE
    assert board.assignments == ()
    assert board.contract.assigned == 0
    assert board.wishes == ()


def test_salle_board_is_full_published_grid_and_wishes():
    state = _salle_with_wish()
    published = state.published_cycles[Team.SALLE]
    assert published is not None
    with patch("doux_planning.context.generate_cycle") as solve:
        board = employee_board(state, "emma")
    solve.assert_not_called()
    assert board.assignments == published.result.assignments
    assert board.assignments
    assert board.team is Team.SALLE
    assert board.contract.weekly == 39
    assert board.unavailabilities == (Unavailability(weekday="sunday"),)
    assert len(board.wishes) == 1
    wish = board.wishes[0]
    assert wish.key is WellbeingPreference.TWO_CONSECUTIVE_REST_DAYS
    warned = any(
        item.severity == WarningSeverity.SOUHAIT
        and item.employee_id == "emma"
        and item.code == "consecutive_rest_days"
        for item in published.result.warnings
    )
    assert wish.held is not warned


def test_unpublished_live_cran_is_invisible():
    state = _salle_with_wish()
    published = state.published_cycles[Team.SALLE].result.assignments
    store = PlanningStore()
    store.add_restaurant(state)
    sandbox = enter_live_sandbox(state, Team.SALLE)
    shift = sandbox.draft.assignments[0]
    proposal = store.preview_retune(
        state.identity.id,
        shift,
        shift.start_minutes + 15,
        shift.end_minutes,
        team=Team.SALLE,
    )[0]
    store.apply_proposal(state.identity.id, proposal, team=Team.SALLE)
    assert sandbox.draft.assignments != published
    board = employee_board(state, "emma")
    assert board.assignments == published
    assert board.assignments != sandbox.draft.assignments
