from unittest.mock import patch

import pytest

from doux_planning.context import (
    TeamNotReady,
    empty_restaurant,
    enter_live_sandbox,
    generate_team,
    seed_empty_team_cycle,
)
from doux_planning.hydrate import hydrate_delivered_cycle
from doux_planning.planning import FillSlot, PlanningStore
from doux_planning.types import SearchEffort, ServiceName, Team
from tests.test_team_generate import _complete_salle


def _seeded_salle():
    state = _complete_salle(empty_restaurant("resto-new"))
    published = seed_empty_team_cycle(state, Team.SALLE)
    store = PlanningStore()
    store.add_restaurant(state)
    return state, store, published


def test_seed_empty_salle_has_no_assignments_and_empty_posts():
    state = _complete_salle(empty_restaurant("resto-new"))
    with patch("doux_planning.context.generate_cycle") as solve:
        with patch("doux_planning.context.generate_for") as frozen:
            published = seed_empty_team_cycle(state, Team.SALLE)
    solve.assert_not_called()
    frozen.assert_not_called()
    assert published is state.published_cycles[Team.SALLE]
    assert published.draft.assignments == ()
    assert published.result.assignments == ()
    assert published.draft.search_effort is SearchEffort.OPTIMIZED
    assert any(warning.code == "empty_post" for warning in published.result.warnings)
    assert state.published_cycles[Team.CUISINE] is None
    assert state.sandbox is None


def test_seed_empty_cuisine_not_ready_does_not_solve():
    state = _complete_salle(empty_restaurant("resto-new"))
    with patch("doux_planning.context.generate_cycle") as solve:
        with patch("doux_planning.context.generate_for") as frozen:
            with pytest.raises(TeamNotReady) as raised:
                seed_empty_team_cycle(state, Team.CUISINE)
    assert raised.value.team is Team.CUISINE
    solve.assert_not_called()
    frozen.assert_not_called()
    assert state.published_cycles[Team.SALLE] is None
    assert state.published_cycles[Team.CUISINE] is None


def test_seed_enter_fill_apply_undo_restores_empty():
    state, store, published = _seeded_salle()
    original = published.result.assignments
    first = enter_live_sandbox(state, Team.SALLE)
    assert enter_live_sandbox(state, Team.SALLE) is first
    assert first.draft.assignments == original == ()
    assert first.history == []
    assert state.sandbox is None
    slot = FillSlot(
        employee_id="emma",
        day_index=0,
        weekday="monday",
        service_id=ServiceName.MIDDAY.value,
        team=Team.SALLE,
    )
    with patch("doux_planning.context.generate_cycle") as solve:
        proposals = store.preview_fill(state.identity.id, slot, None, None, team=Team.SALLE)
        assert proposals
        store.apply_proposal(state.identity.id, proposals[0], team=Team.SALLE)
        assert first.draft.assignments != original
        assert first.history
        store.undo_sandbox(state.identity.id, team=Team.SALLE)
        assert first.draft.assignments == original
        assert first.history == []
    solve.assert_not_called()
    assert state.published_cycles[Team.SALLE].result.assignments == original
    assert state.published_cycles[Team.CUISINE] is None


def test_generate_team_after_seed_replaces_salle_slot():
    state = _complete_salle(empty_restaurant("resto-new"))
    seeded = seed_empty_team_cycle(state, Team.SALLE)
    assert seeded.result.assignments == ()
    generate_team(state, Team.SALLE, search=SearchEffort.MINIMAL)
    salle = state.published_cycles[Team.SALLE]
    assert salle is not None
    assert salle is not seeded
    assert salle.result.assignments
    assert state.published_cycles[Team.CUISINE] is None


def test_hydrate_saint_cloud_keeps_toy_sandbox():
    state = hydrate_delivered_cycle(PlanningStore(), "saint-cloud")
    assert state.sandbox is not None
    assert state.sandbox.target == "cycle"
    assert state.cycle is not None
    assert state.published_cycles[Team.SALLE] is None
    assert state.published_cycles[Team.CUISINE] is None
    assert state.live_sandboxes[Team.SALLE] is None
    assert state.live_sandboxes[Team.CUISINE] is None
