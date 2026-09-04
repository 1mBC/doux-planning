from unittest.mock import patch
import os

import pytest

from doux_planning.engine import EngineResult, PlanningDraft, Shift, evaluate, generate_cycle, rank_candidates, swap_shifts
from doux_planning.hydrate import data_dir, hydrate_delivered_cycle, load_delivered_cycle
from doux_planning.invites import RestaurantIdentity
from doux_planning.planning import (
    EmptyHistoryError,
    FillSlot,
    IdentityRetuneError,
    OccupiedSlotError,
    PlanningStore,
    PublishedCycle,
    RestaurantState,
    occupied_sort_key,
    preview_impact,
    warning_delta,
)
from doux_planning.staff import Employee, Role
from doux_planning.structures import ArrivalWave, DepartureWave, RestaurantHours, ServiceStructure
from doux_planning.types import ServiceName, Team, WarningSeverity
from doux_planning.warnings import Warning
from tests.fixtures import kitchen_midday_structure, kitchen_staff


def _salle(name: str, level: int, hours: float = 39.0, min_shift: float = 4.0) -> Employee:
    role = "RESPONSABLE" if level >= 3 else "CHEF DE RANG"
    return Employee(
        id=name.lower(),
        name=name,
        role=Role(role, level, Team.SALLE),
        team=Team.SALLE,
        contractual_hours_per_week=hours,
        min_shift_hours=min_shift,
    )


def _structure(service: str) -> ServiceStructure:
    if service == ServiceName.MIDDAY.value:
        arrivals = (ArrivalWave(10 * 60, (1,)), ArrivalWave(11 * 60, (3,)))
        departures = (DepartureWave(16 * 60, ()),)
    else:
        arrivals = (ArrivalWave(18 * 60, (3,)), ArrivalWave(19 * 60, (1,)))
        departures = (DepartureWave(24 * 60, ()),)
    return ServiceStructure(
        id=f"salle-{service}",
        team=Team.SALLE,
        service_id=service,
        weekdays=frozenset({"monday", "tuesday", "wednesday", "thursday", "friday", "saturday"}),
        arrivals=arrivals,
        departures=departures,
    )


def _shift(
    employee_id: str,
    day: int,
    start: int,
    end: int,
    level: int,
    service: str = ServiceName.MIDDAY.value,
) -> Shift:
    days = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    return Shift(
        employee_id=employee_id,
        day_index=day,
        weekday=days[day % 7],
        service_id=service,
        team=Team.SALLE,
        start_minutes=start,
        end_minutes=end,
        post_level=level,
    )


def _store(assignments: tuple[Shift, ...], extra: tuple[Employee, ...] = ()) -> PlanningStore:
    staff = (_salle("THEO", 3), _salle("EMMA", 3), _salle("DIANE", 4), *extra)
    hours = RestaurantHours.multi_service(ServiceName.MIDDAY.value, ServiceName.EVENING.value)
    structures = (_structure(ServiceName.MIDDAY.value), _structure(ServiceName.EVENING.value))
    draft = PlanningDraft(employees=staff, structures=structures, hours=hours, assignments=assignments)
    state = RestaurantState(
        identity=RestaurantIdentity(id="resto-1"),
        employees=list(staff),
        structures=list(structures),
        hours=hours,
        cycle=PublishedCycle(id="cycle-1", draft=draft, result=evaluate(draft)),
    )
    store = PlanningStore()
    store.add_restaurant(state)
    store.enter_sandbox("resto-1", "cycle")
    return store


def test_load_saint_cloud_round_trips_diane_monday_midday():
    delivered = load_delivered_cycle("saint-cloud")
    diane = next(
        shift
        for shift in delivered.assignments
        if shift.employee_id == "diane" and shift.day_index == 0 and shift.service_id == "midday"
    )
    assert diane.start_minutes == 11 * 60
    assert diane.end_minutes == 15 * 60
    assert diane.post_level == 1


def test_hydrate_copies_assignments_into_cycle_sandbox_without_generate():
    delivered = load_delivered_cycle("saint-cloud")
    store = PlanningStore()
    with patch("doux_planning.planning.generate_cycle", wraps=generate_cycle) as generate:
        state = hydrate_delivered_cycle(store, "saint-cloud")
    generate.assert_not_called()
    assert state.sandbox is not None
    assert state.sandbox.target == "cycle"
    assert state.sandbox.draft.assignments == delivered.assignments
    assert state.cycle is not None
    assert state.cycle.draft.assignments == delivered.assignments


def test_hydrate_does_not_rewrite_saint_cloud_file():
    path = data_dir() / "examples" / "saint-cloud.json"
    before = path.read_bytes()
    hydrate_delivered_cycle(PlanningStore(), "saint-cloud")
    assert path.read_bytes() == before


def test_warning_delta_keeps_contract_hours_identity_and_adds_interdit():
    current = (
        Warning(
            WarningSeverity.SOUHAIT,
            "contract_hours",
            "DIANE has 30.0h vs 39.0h contract",
            employee_id="diane",
            day_index=0,
        ),
    )
    trial = (
        Warning(
            WarningSeverity.SOUHAIT,
            "contract_hours",
            "DIANE has 31.0h vs 39.0h contract",
            employee_id="diane",
            day_index=0,
        ),
        Warning(
            WarningSeverity.INTERDIT,
            "rest_between_days",
            "DIANE rest too short",
            employee_id="diane",
            day_index=1,
        ),
    )
    delta = warning_delta(current, trial)
    assert len(delta.unchanged) == 1
    assert delta.unchanged[0].message == "DIANE has 31.0h vs 39.0h contract"
    assert [item.code for item in delta.added] == ["rest_between_days"]
    assert delta.removed == ()
    assert all(item.code != "rest_between_days" for item in delta.unchanged)


def test_preview_does_not_mutate_draft_or_history():
    theo = _shift("theo", 0, 11 * 60, 16 * 60, 3)
    emma = _shift("emma", 2, 18 * 60, 24 * 60, 3, ServiceName.EVENING.value)
    store = _store((theo, emma))
    sandbox = store.get("resto-1").sandbox
    before = sandbox.draft.assignments
    before_result = sandbox.last_result
    before_history = list(sandbox.history)
    store.preview_retune("resto-1", theo, 11 * 60 + 15, 16 * 60)
    store.preview_replace("resto-1", theo)
    store.preview_swap("resto-1", theo)
    assert sandbox.draft.assignments == before
    assert sandbox.last_result == before_result
    assert sandbox.history == before_history


def test_apply_then_undo_restores_and_empty_stack_fails():
    theo = _shift("theo", 0, 11 * 60, 16 * 60, 3)
    store = _store((theo,))
    sandbox = store.get("resto-1").sandbox
    original = sandbox.draft.assignments
    original_result = sandbox.last_result
    proposals = store.preview_retune("resto-1", theo, 11 * 60 + 15, 16 * 60)
    store.apply_proposal("resto-1", proposals[0])
    assert sandbox.draft.assignments != original
    assert len(sandbox.history) == 1
    store.undo_sandbox("resto-1")
    assert sandbox.draft.assignments == original
    assert sandbox.last_result == original_result
    assert sandbox.history == []
    with pytest.raises(EmptyHistoryError):
        store.undo_sandbox("resto-1")
    assert sandbox.draft.assignments == original


def test_two_applies_then_one_undo_restores_mid_state():
    theo = _shift("theo", 0, 11 * 60, 16 * 60, 3)
    emma = _shift("emma", 2, 18 * 60, 24 * 60, 3, ServiceName.EVENING.value)
    store = _store((theo, emma))
    sandbox = store.get("resto-1").sandbox
    retune = store.preview_retune("resto-1", theo, 11 * 60 + 15, 16 * 60)
    store.apply_proposal("resto-1", retune[0])
    after_retune = sandbox.draft.assignments
    after_result = sandbox.last_result
    swapped = next(shift for shift in after_retune if shift.employee_id == "theo" and shift.day_index == 0)
    partners = store.preview_swap("resto-1", swapped)
    store.apply_proposal("resto-1", partners[0])
    store.undo_sandbox("resto-1")
    assert sandbox.draft.assignments == after_retune
    assert sandbox.last_result == after_result


def test_retune_one_step_plus_fifteen_and_rejects_identity_or_short():
    theo = _shift("theo", 0, 11 * 60, 16 * 60, 3)
    store = _store((theo,))
    sandbox = store.get("resto-1").sandbox
    before = sandbox.draft.assignments
    proposals = store.preview_retune("resto-1", theo, 11 * 60 + 15, 16 * 60)
    assert len(proposals) == 1
    trial = next(shift for shift in proposals[0].result.assignments if shift.employee_id == "theo")
    assert trial.start_minutes == 11 * 60 + 15
    assert trial.end_minutes == 16 * 60
    assert trial.weekday == "monday"
    assert trial.service_id == ServiceName.MIDDAY.value
    assert sandbox.draft.assignments == before
    assert proposals[0].current_score
    assert proposals[0].trial_score
    with pytest.raises(IdentityRetuneError):
        store.preview_retune("resto-1", theo, 11 * 60, 16 * 60)
    with pytest.raises(ValueError):
        store.preview_retune("resto-1", theo, 12 * 60, 12 * 60 + 225)


def test_replace_omits_holder_and_empty_slot_still_skips_occupant():
    diane = _shift("diane", 0, 11 * 60, 15 * 60, 1)
    store = _store((diane,))
    proposals = store.preview_replace("resto-1", diane)
    assert proposals
    assert all(item.employee_id != "diane" for item in proposals)
    occupied = Shift(
        employee_id="chef-a",
        day_index=0,
        weekday="monday",
        service_id=ServiceName.MIDDAY.value,
        team=Team.CUISINE,
        start_minutes=11 * 60 + 30,
        end_minutes=15 * 60,
        post_level=1,
    )
    draft = PlanningDraft(
        employees=kitchen_staff(),
        structures=(kitchen_midday_structure(),),
        hours=RestaurantHours.multi_service(ServiceName.MIDDAY.value),
        assignments=(occupied,),
    )
    ranked = rank_candidates(
        draft, 0, "monday", ServiceName.MIDDAY.value, Team.CUISINE, 11 * 60 + 30, 15 * 60, 1
    )
    assert all(item.employee.id != "chef-a" for item in ranked)


def test_occupied_rank_prefers_one_interdit_over_interdit_plus_souhait():
    draft = PlanningDraft(
        employees=kitchen_staff(),
        structures=(kitchen_midday_structure(),),
        hours=RestaurantHours.multi_service(ServiceName.MIDDAY.value),
        assignments=(),
    )
    current = EngineResult(assignments=(), warnings=())
    only_interdit = EngineResult(
        assignments=(),
        warnings=(Warning(WarningSeverity.INTERDIT, "unavailability", "blocked", "alex", 0),),
    )
    interdit_and_wish = EngineResult(
        assignments=(),
        warnings=(
            Warning(WarningSeverity.INTERDIT, "unavailability", "blocked", "blair", 0),
            Warning(WarningSeverity.SOUHAIT, "max_coupures", "too many", "blair", 0),
        ),
    )
    assert occupied_sort_key(draft, current, only_interdit) < occupied_sort_key(
        draft, current, interdit_and_wish
    )


def test_retune_impact_lists_theo_contract_not_unchanged_emma():
    theo = _shift("theo", 0, 11 * 60, 16 * 60, 3)
    emma = _shift("emma", 2, 18 * 60, 24 * 60, 3, ServiceName.EVENING.value)
    store = _store((theo, emma))
    proposal = store.preview_retune("resto-1", theo, 10 * 60, 16 * 60)[0]
    people = {row.employee_id for row in proposal.impact.contract}
    assert "theo" in people
    assert "emma" not in people
    assert all(row.kind == "closer" for row in proposal.impact.contract if row.employee_id == "theo")
    assert len(proposal.current_score) == 6
    assert len(proposal.trial_score) == 6
    assert proposal.impact.role_fit == ()


def test_replace_role_fit_better_worse_same_and_swap_net_zero():
    lea = _salle("LEA", 2)
    diane = _shift("diane", 0, 11 * 60, 15 * 60, 1)
    store = _store((diane,), extra=(lea,))
    sandbox = store.get("resto-1").sandbox
    before = sandbox.draft.assignments
    better = next(item for item in store.preview_replace("resto-1", diane) if item.employee_id == "lea")
    assert len(better.impact.role_fit) == 1
    row = better.impact.role_fit[0]
    assert (row.current_gap, row.trial_gap, row.kind) == (3, 1, "better")
    assert sandbox.draft.assignments == before
    lea_shift = _shift("lea", 0, 11 * 60, 15 * 60, 1)
    worse_store = _store((lea_shift,), extra=(lea,))
    worse = next(
        item for item in worse_store.preview_replace("resto-1", lea_shift) if item.employee_id == "diane"
    )
    assert (worse.impact.role_fit[0].current_gap, worse.impact.role_fit[0].trial_gap, worse.impact.role_fit[0].kind) == (
        1,
        3,
        "worse",
    )
    theo = _shift("theo", 0, 11 * 60, 16 * 60, 1)
    same = next(item for item in _store((theo,)).preview_replace("resto-1", theo) if item.employee_id == "emma")
    assert same.impact.role_fit == ()
    ghost = _shift("inconnu", 0, 11 * 60, 15 * 60, 1)
    draft = store.get("resto-1").sandbox.draft
    current = EngineResult(assignments=(diane,), warnings=())
    trial = EngineResult(assignments=(ghost,), warnings=())
    missing = preview_impact(draft, current, trial, {"diane"}, (diane,), (ghost,))
    assert missing.role_fit == ()


def test_swap_role_fit_clicked_post_only():
    lea = _salle("LEA", 2)
    diane = _shift("diane", 0, 11 * 60, 15 * 60, 1)
    lea_elsewhere = _shift("lea", 2, 18 * 60, 24 * 60, 2, ServiceName.EVENING.value)
    changed = next(
        item
        for item in _store((diane, lea_elsewhere), extra=(lea,)).preview_swap("resto-1", diane)
        if item.partner == lea_elsewhere
    )
    assert len(changed.impact.role_fit) == 1
    assert (changed.impact.role_fit[0].current_gap, changed.impact.role_fit[0].trial_gap, changed.impact.role_fit[0].kind) == (
        3,
        1,
        "better",
    )
    theo_midi = _shift("theo", 0, 11 * 60, 16 * 60, 3)
    emma = _shift("emma", 2, 18 * 60, 24 * 60, 3, ServiceName.EVENING.value)
    swapped = _store((theo_midi, emma)).preview_swap("resto-1", theo_midi)
    assert swapped
    assert all(item.impact.role_fit == () for item in swapped)


def test_swap_preview_omits_own_shifts_and_apply_matches_engine():
    theo_midi = _shift("theo", 0, 11 * 60, 16 * 60, 3)
    theo_soir = _shift("theo", 4, 18 * 60, 24 * 60, 3, ServiceName.EVENING.value)
    emma = _shift("emma", 2, 18 * 60, 24 * 60, 3, ServiceName.EVENING.value)
    diane = _shift("diane", 0, 18 * 60, 24 * 60, 1, ServiceName.EVENING.value)
    store = _store((theo_midi, theo_soir, emma, diane))
    proposals = store.preview_swap("resto-1", theo_midi)
    partners = {item.partner for item in proposals}
    assert emma in partners
    assert diane in partners
    assert theo_soir not in partners
    chosen = next(item for item in proposals if item.partner == emma)
    engine = swap_shifts(store.get("resto-1").sandbox.draft, theo_midi, emma)
    store.apply_proposal("resto-1", chosen)
    assert store.get("resto-1").sandbox.draft.assignments == engine.assignments


def test_apply_retune_and_replace_crantes_history():
    theo = _shift("theo", 0, 11 * 60, 16 * 60, 3)
    store = _store((theo,))
    sandbox = store.get("resto-1").sandbox
    retune = store.preview_retune("resto-1", theo, 11 * 60 + 15, 16 * 60)
    store.apply_proposal("resto-1", retune[0])
    assert sandbox.draft.assignments == retune[0].result.assignments
    assert len(sandbox.history) == 1
    held = next(shift for shift in sandbox.draft.assignments if shift.day_index == 0)
    replace_list = store.preview_replace("resto-1", held)
    store.apply_proposal("resto-1", replace_list[0])
    assert sandbox.draft.assignments == replace_list[0].result.assignments
    assert len(sandbox.history) == 2
    assert replace_list[0].employee_id != "theo"


def _emma_monday_midday() -> FillSlot:
    return FillSlot(
        employee_id="emma",
        day_index=0,
        weekday="monday",
        service_id=ServiceName.MIDDAY.value,
        team=Team.SALLE,
    )


def test_preview_fill_empty_emma_first_span_occupied_and_undo():
    store = _store(())
    sandbox = store.get("resto-1").sandbox
    before = sandbox.draft.assignments
    before_result = sandbox.last_result
    slot = _emma_monday_midday()
    proposals = store.preview_fill("resto-1", slot, None, None)
    assert proposals
    assert proposals[0].employee_id == "emma"
    assert proposals[0].gesture == "fill"
    assert proposals[0].rank == 1
    assert proposals[0].start_minutes == 10 * 60
    assert proposals[0].end_minutes == 16 * 60
    assert all(item.impact.role_fit == () for item in proposals)
    assert {item.employee_id for item in proposals} == {"emma", "theo", "diane"}
    others = [item for item in proposals if item.employee_id != "emma"]
    current = sandbox.last_result
    assert current is not None
    keys = [occupied_sort_key(sandbox.draft, current, item.result) for item in others]
    assert keys == sorted(keys)
    assert sandbox.draft.assignments == before
    assert sandbox.last_result == before_result
    assert sandbox.history == []
    store.apply_proposal("resto-1", proposals[0])
    filled = next(
        item
        for item in sandbox.draft.assignments
        if item.employee_id == "emma" and item.day_index == 0 and item.service_id == ServiceName.MIDDAY.value
    )
    assert filled.start_minutes == 10 * 60
    assert filled.end_minutes == 16 * 60
    assert filled.post_level == 3
    assert len(sandbox.history) == 1
    store.undo_sandbox("resto-1")
    assert sandbox.draft.assignments == before
    with pytest.raises(OccupiedSlotError):
        _store((_shift("emma", 0, 11 * 60, 16 * 60, 3),)).preview_fill("resto-1", slot, None, None)
    timed = store.preview_fill("resto-1", slot, 11 * 60, 16 * 60)
    assert timed[0].start_minutes == 11 * 60
    assert timed[0].end_minutes == 16 * 60


DIANE_MONDAY_MIDDAY = {
    "employee_id": "diane",
    "day_index": 0,
    "weekday": "monday",
    "service_id": "midday",
    "team": "salle",
    "start_minutes": 11 * 60,
    "end_minutes": 15 * 60,
    "post_level": 1,
}


def _sandbox_client():
    from fastapi.testclient import TestClient

    from doux_planning.api.app import app
    from doux_planning.api.sandbox import reset_runtime

    reset_runtime()
    if os.environ.get("DATABASE_URL"):
        from doux_planning.api.seed import seed_from_files

        seed_from_files()
    return TestClient(app)


def test_sandbox_enter_get_and_reuse():
    from doux_planning.hydrate import data_dir

    path = data_dir() / "examples" / "saint-cloud.json"
    before = path.read_bytes()
    client = _sandbox_client()
    missing = client.get("/v1/sandbox")
    assert missing.status_code == 404
    assert "bac à sable" in missing.json()["detail"]
    entered = client.post("/v1/sandbox/enter")
    assert entered.status_code == 200
    body = entered.json()
    assert body["sandbox"] == {"target": "cycle", "history_length": 0}
    assert body["history"] == []
    assert set(body["score"]) == {
        "empty",
        "interdit",
        "hours_miss",
        "souhait",
        "below_role",
        "overqualification",
    }
    assert body["restaurant"]["id"] == "saint-cloud"
    assert body["restaurant"]["name"] == "Saint-Cloud"
    assert {person["id"] for person in body["restaurant"]["employees"]}
    assert body["planning"]["assignments"]
    assert "legal_rows" not in body["planning"]
    assert "stats" not in body["planning"]
    first = body["planning"]["assignments"][0]
    assert "duration_hours" in first
    again = client.post("/v1/sandbox/enter")
    assert again.status_code == 200
    assert again.json()["planning"]["assignments"] == body["planning"]["assignments"]
    assert again.json()["score"] == body["score"]
    fetched = client.get("/v1/sandbox")
    assert fetched.status_code == 200
    assert fetched.json()["sandbox"]["history_length"] == 0
    assert fetched.json()["score"] == body["score"]
    assert path.read_bytes() == before


def test_sandbox_preview_does_not_mutate_and_commit_undo():
    client = _sandbox_client()
    client.post("/v1/sandbox/enter")
    before = client.get("/v1/sandbox").json()
    retune_times = {
        "start_minutes": DIANE_MONDAY_MIDDAY["start_minutes"],
        "end_minutes": DIANE_MONDAY_MIDDAY["end_minutes"] + 15,
    }
    preview = client.post(
        "/v1/sandbox/preview",
        json={"gesture": "retune", "shift": DIANE_MONDAY_MIDDAY, **retune_times},
    )
    assert preview.status_code == 200
    proposals = preview.json()["proposals"]
    assert len(proposals) == 1
    item = proposals[0]
    assert "assignments" not in item
    assert "delta" not in item
    assert "warnings" not in item
    assert {
        "rank",
        "gesture",
        "start_minutes",
        "end_minutes",
        "employee_id",
        "partner",
        "impact",
        "current_score",
        "trial_score",
    } <= set(item)
    assert set(item["impact"]) == {
        "new_interdits",
        "broken_wishes",
        "contract",
        "coverage_added",
        "coverage_removed",
        "role_fit",
    }
    assert set(item["current_score"]) == set(before["score"])
    after_preview = client.get("/v1/sandbox").json()
    assert after_preview["planning"]["assignments"] == before["planning"]["assignments"]
    assert after_preview["history"] == []
    identity = client.post(
        "/v1/sandbox/preview",
        json={
            "gesture": "retune",
            "shift": DIANE_MONDAY_MIDDAY,
            "start_minutes": DIANE_MONDAY_MIDDAY["start_minutes"],
            "end_minutes": DIANE_MONDAY_MIDDAY["end_minutes"],
        },
    )
    assert identity.status_code == 400
    assert identity.json()["detail"]
    short = client.post(
        "/v1/sandbox/preview",
        json={
            "gesture": "retune",
            "shift": DIANE_MONDAY_MIDDAY,
            "start_minutes": DIANE_MONDAY_MIDDAY["start_minutes"],
            "end_minutes": DIANE_MONDAY_MIDDAY["start_minutes"] + 3 * 60,
        },
    )
    assert short.status_code == 400
    assert short.json()["detail"]
    missing_shift = client.post(
        "/v1/sandbox/preview",
        json={
            "gesture": "retune",
            "shift": {**DIANE_MONDAY_MIDDAY, "employee_id": "inconnu"},
            **retune_times,
        },
    )
    assert missing_shift.status_code in {400, 404}
    assert missing_shift.json()["detail"]
    replace_list = client.post(
        "/v1/sandbox/preview",
        json={"gesture": "replace", "shift": DIANE_MONDAY_MIDDAY},
    )
    assert replace_list.status_code == 200
    ranked = replace_list.json()["proposals"]
    assert ranked == sorted(ranked, key=lambda row: row["rank"])
    assert all("delta" not in row and "warnings" not in row for row in ranked)
    swaps = client.post(
        "/v1/sandbox/preview",
        json={"gesture": "swap", "shift": DIANE_MONDAY_MIDDAY},
    )
    assert swaps.status_code == 200
    partner = swaps.json()["proposals"][0]["partner"]
    assert partner is not None
    assert {"day_index", "weekday", "employee_id", "start_minutes", "end_minutes"} <= set(partner)
    missing_replace = client.post(
        "/v1/sandbox/commit",
        json={"gesture": "replace", "shift": DIANE_MONDAY_MIDDAY},
    )
    assert missing_replace.status_code == 400
    assert "manquants" in missing_replace.json()["detail"]
    chosen = proposals[0]
    committed = client.post(
        "/v1/sandbox/commit",
        json={
            "gesture": "retune",
            "shift": DIANE_MONDAY_MIDDAY,
            "start_minutes": chosen["start_minutes"],
            "end_minutes": chosen["end_minutes"],
        },
    )
    assert committed.status_code == 200
    state = committed.json()
    assert state["sandbox"]["history_length"] == 1
    recap = state["history"][0]
    assert recap["index"] == 1
    assert recap["gesture"] == "retune"
    assert recap["shift"]["employee_id"] == "diane"
    assert recap["slot"] is None
    assert recap["impact"] == chosen["impact"]
    assert recap["start_minutes"] == chosen["start_minutes"]
    assert recap["end_minutes"] == chosen["end_minutes"]
    fetched = client.get("/v1/sandbox").json()
    assert fetched["history"][0]["shift"] == recap["shift"]
    assert fetched["history"][0]["impact"] == recap["impact"]
    assert state["planning"]["assignments"] != before["planning"]["assignments"]
    assert set(state["score"]) == set(before["score"])
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
    undone = client.post("/v1/sandbox/undo")
    assert undone.status_code == 200
    assert undone.json()["history"] == []
    assert undone.json()["planning"]["assignments"] == before["planning"]["assignments"]
    empty = client.post("/v1/sandbox/undo")
    assert empty.status_code == 409
    assert "annuler" in empty.json()["detail"]


def _posted_shift(assignment: dict) -> dict:
    return {
        key: assignment[key]
        for key in (
            "employee_id",
            "day_index",
            "weekday",
            "service_id",
            "team",
            "start_minutes",
            "end_minutes",
            "post_level",
        )
    }


def test_sandbox_preview_replace_role_fit_from_engine():
    client = _sandbox_client()
    entered = client.post("/v1/sandbox/enter")
    assert entered.status_code == 200
    assignments = entered.json()["planning"]["assignments"]
    diane = next(
        item
        for item in assignments
        if item["employee_id"] == "diane" and item["day_index"] == 0 and item["service_id"] == "midday"
    )
    theo = next(
        item
        for item in assignments
        if item["employee_id"] == "theo" and item["day_index"] == 0 and item["service_id"] == "midday"
    )
    diane_preview = client.post(
        "/v1/sandbox/preview",
        json={"gesture": "replace", "shift": _posted_shift(diane)},
    )
    assert diane_preview.status_code == 200
    diane_proposals = diane_preview.json()["proposals"]
    changed = [item for item in diane_proposals if item["impact"]["role_fit"]]
    assert changed
    row = changed[0]["impact"]["role_fit"][0]
    assert set(row) == {"current_gap", "trial_gap", "kind"}
    assert row["kind"] in {"better", "worse"}
    assert all(len(item["impact"]["role_fit"]) <= 1 for item in diane_proposals)
    theo_preview = client.post(
        "/v1/sandbox/preview",
        json={"gesture": "replace", "shift": _posted_shift(theo)},
    )
    assert theo_preview.status_code == 200
    equal = [item for item in theo_preview.json()["proposals"] if item["impact"]["role_fit"] == []]
    assert equal
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92


def test_sandbox_preview_fill_emma_monday_midday_and_occupied():
    client = _sandbox_client()
    client.post("/v1/sandbox/enter")
    slot = {
        "employee_id": "emma",
        "day_index": 0,
        "weekday": "monday",
        "service_id": "midday",
        "team": "salle",
    }
    preview = client.post(
        "/v1/sandbox/preview",
        json={"gesture": "fill", "slot": slot, "start_minutes": None, "end_minutes": None},
    )
    assert preview.status_code == 200
    proposals = preview.json()["proposals"]
    assert proposals
    first = proposals[0]
    assert first["rank"] == 1
    assert first["gesture"] == "fill"
    assert first["employee_id"] == "emma"
    assert first["start_minutes"] == 600
    assert first["end_minutes"] == 960
    assert first["impact"]["role_fit"] == []
    committed = client.post(
        "/v1/sandbox/commit",
        json={
            "gesture": "fill",
            "slot": slot,
            "employee_id": "emma",
            "start_minutes": first["start_minutes"],
            "end_minutes": first["end_minutes"],
        },
    )
    assert committed.status_code == 200
    fill_recap = committed.json()["history"][0]
    assert fill_recap["index"] == 1
    assert fill_recap["gesture"] == "fill"
    assert fill_recap["shift"] is None
    assert fill_recap["slot"] == slot
    assert fill_recap["employee_id"] == "emma"
    assert fill_recap["impact"] == first["impact"]
    filled = next(
        item
        for item in committed.json()["planning"]["assignments"]
        if item["employee_id"] == "emma" and item["day_index"] == 0 and item["service_id"] == "midday"
    )
    assert filled["start_minutes"] == 600
    assert filled["end_minutes"] == 960
    occupied = client.post(
        "/v1/sandbox/preview",
        json={"gesture": "fill", "slot": slot, "start_minutes": None, "end_minutes": None},
    )
    assert occupied.status_code == 409
    assert occupied.json()["detail"]
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92


def test_sandbox_discard_resets_to_hydrated_cycle():
    client = _sandbox_client()
    missing = client.post("/v1/sandbox/discard")
    assert missing.status_code == 404
    assert "bac à sable" in missing.json()["detail"]
    entered = client.post("/v1/sandbox/enter").json()
    before = entered["planning"]["assignments"]
    preview = client.post(
        "/v1/sandbox/preview",
        json={
            "gesture": "retune",
            "shift": DIANE_MONDAY_MIDDAY,
            "start_minutes": DIANE_MONDAY_MIDDAY["start_minutes"],
            "end_minutes": DIANE_MONDAY_MIDDAY["end_minutes"] + 15,
        },
    )
    chosen = preview.json()["proposals"][0]
    client.post(
        "/v1/sandbox/commit",
        json={
            "gesture": "retune",
            "shift": DIANE_MONDAY_MIDDAY,
            "start_minutes": chosen["start_minutes"],
            "end_minutes": chosen["end_minutes"],
        },
    )
    discarded = client.post("/v1/sandbox/discard")
    assert discarded.status_code == 200
    body = discarded.json()
    assert body["history"] == []
    assert body["sandbox"]["history_length"] == 0
    assert body["planning"]["assignments"] == before
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_sandbox_survives_runtime_reset_with_postgres():
    from doux_planning.api.sandbox import reset_runtime

    client = _sandbox_client()
    client.post("/v1/sandbox/enter")
    preview = client.post(
        "/v1/sandbox/preview",
        json={
            "gesture": "retune",
            "shift": DIANE_MONDAY_MIDDAY,
            "start_minutes": DIANE_MONDAY_MIDDAY["start_minutes"],
            "end_minutes": DIANE_MONDAY_MIDDAY["end_minutes"] + 15,
        },
    )
    chosen = preview.json()["proposals"][0]
    client.post(
        "/v1/sandbox/commit",
        json={
            "gesture": "retune",
            "shift": DIANE_MONDAY_MIDDAY,
            "start_minutes": chosen["start_minutes"],
            "end_minutes": chosen["end_minutes"],
        },
    )
    craned = client.get("/v1/sandbox").json()
    assert craned["history"][0]["shift"]["employee_id"] == "diane"
    assert craned["history"][0]["impact"] == chosen["impact"]
    reset_runtime(clear_db=False)
    restored = client.get("/v1/sandbox")
    assert restored.status_code == 200
    assert restored.json()["history"] == craned["history"]
    assert restored.json()["planning"]["assignments"] == craned["planning"]["assignments"]
    discarded = client.post("/v1/sandbox/discard")
    assert discarded.status_code == 200
    assert discarded.json()["history"] == []
    reset_runtime(clear_db=False)
    after_discard = client.get("/v1/sandbox")
    assert after_discard.status_code == 200
    assert after_discard.json()["history"] == []
    assert after_discard.json()["planning"]["assignments"] == discarded.json()["planning"]["assignments"]
