from unittest.mock import patch

import pytest

from doux_planning.context import (
    NoPublishedCycle,
    discard_live_sandbox,
    empty_restaurant,
    enter_live_sandbox,
    generate_team,
    publish_live_sandbox,
)
from doux_planning.hydrate import hydrate_delivered_cycle
from doux_planning.planning import PlanningStore
from doux_planning.types import SearchEffort, Team
from tests.test_team_generate import _complete_salle


def _generated_salle():
    state = _complete_salle(empty_restaurant("resto-new"))
    generate_team(state, Team.SALLE, search=SearchEffort.MINIMAL)
    store = PlanningStore()
    store.add_restaurant(state)
    return state, store


def test_empty_restaurant_has_no_live_sandboxes():
    state = empty_restaurant("resto-new")
    assert state.live_sandboxes[Team.SALLE] is None
    assert state.live_sandboxes[Team.CUISINE] is None
    assert state.sandbox is None


def test_enter_cuisine_without_published_cycle():
    state, _store = _generated_salle()
    with pytest.raises(NoPublishedCycle) as raised:
        enter_live_sandbox(state, Team.CUISINE)
    assert raised.value.team is Team.CUISINE
    assert state.live_sandboxes[Team.CUISINE] is None
    assert state.sandbox is None


def test_salle_enter_retune_undo_discard_restores_published():
    state, store = _generated_salle()
    published = state.published_cycles[Team.SALLE]
    assert published is not None
    original = published.result.assignments
    first = enter_live_sandbox(state, Team.SALLE)
    assert enter_live_sandbox(state, Team.SALLE) is first
    assert first.draft.assignments == original
    assert first.history == []
    assert state.sandbox is None
    shift = first.draft.assignments[0]
    with patch("doux_planning.context.generate_cycle") as solve:
        proposals = store.preview_retune(
            state.identity.id,
            shift,
            shift.start_minutes + 15,
            shift.end_minutes,
            team=Team.SALLE,
        )
        store.apply_proposal(state.identity.id, proposals[0], team=Team.SALLE)
        assert first.draft.assignments != original
        assert first.history
        store.undo_sandbox(state.identity.id, team=Team.SALLE)
        assert first.draft.assignments == original
        assert first.history == []
        store.apply_proposal(state.identity.id, proposals[0], team=Team.SALLE)
        discard_live_sandbox(state, Team.SALLE)
        assert state.live_sandboxes[Team.SALLE] is None
        assert state.published_cycles[Team.SALLE].result.assignments == original
        restored = enter_live_sandbox(state, Team.SALLE)
        assert restored is not first
        assert restored.draft.assignments == original
        assert restored.history == []
    solve.assert_not_called()


def test_publish_live_sandbox_updates_salle_only():
    state, store = _generated_salle()
    published = state.published_cycles[Team.SALLE]
    original = published.result.assignments
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
    draft_assignments = sandbox.draft.assignments
    publish_live_sandbox(state, Team.SALLE)
    assert state.live_sandboxes[Team.SALLE] is None
    assert state.published_cycles[Team.SALLE].result.assignments == draft_assignments
    assert state.published_cycles[Team.SALLE].result.assignments != original
    assert state.published_cycles[Team.CUISINE] is None
    assert state.sandbox is None


def test_hydrate_saint_cloud_keeps_toy_sandbox():
    state = hydrate_delivered_cycle(PlanningStore(), "saint-cloud")
    assert state.sandbox is not None
    assert state.sandbox.target == "cycle"
    assert state.cycle is not None
    assert state.live_sandboxes[Team.SALLE] is None
    assert state.live_sandboxes[Team.CUISINE] is None
