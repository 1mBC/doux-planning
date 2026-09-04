from __future__ import annotations

from typing import Any

from sqlalchemy.orm.attributes import flag_modified

from doux_planning.engine import EngineResult, Shift, _attempt_key
from doux_planning.hydrate import hydrate_delivered_cycle
from doux_planning.planning import (
    EmptyHistoryError,
    FillSlot,
    PlanningStore,
    PreviewImpact,
    PreviewProposal,
    SandboxSnapshot,
)
from doux_planning.types import Team, WarningSeverity
from doux_planning.warnings import Warning

RESTAURANT_ID = "saint-cloud"
GESTURES = {"retune", "replace", "swap", "fill"}
SCORE_FIELDS = ("empty", "interdit", "hours_miss", "souhait", "below_role", "overqualification")

_store: PlanningStore | None = None
_recaps: list[dict[str, Any]] = []
_restored = False


def reset_runtime(*, clear_db: bool = True) -> None:
    global _store, _recaps, _restored
    _store = None
    _recaps = []
    _restored = False
    if clear_db:
        _delete_persisted()


def get_store() -> PlanningStore:
    global _store, _recaps, _restored
    if _store is None:
        _store = PlanningStore()
        _recaps = []
        if not _restored:
            _restored = True
            _restore()
    return _store


def enter_sandbox_state() -> dict[str, Any]:
    store = get_store()
    try:
        store.get(RESTAURANT_ID)
    except KeyError:
        hydrate_delivered_cycle(store, RESTAURANT_ID)
        _recaps.clear()
    else:
        store.enter_sandbox(RESTAURANT_ID, "cycle")
    _persist()
    return sandbox_state()


def current_sandbox_state() -> dict[str, Any]:
    sandbox = _sandbox_or_none()
    if sandbox is None:
        raise LookupError("no sandbox")
    return sandbox_state()


def preview(body: dict[str, Any]) -> dict[str, Any]:
    gesture = body.get("gesture")
    if gesture not in GESTURES:
        raise ValueError("unknown gesture")
    proposals = _preview(get_store(), gesture, body)
    return {"proposals": [_proposal_json(item) for item in proposals]}


def commit(body: dict[str, Any]) -> dict[str, Any]:
    gesture = body.get("gesture")
    if gesture not in GESTURES:
        raise ValueError("unknown gesture")
    store = get_store()
    proposals = _preview(store, gesture, body)
    chosen = _match_proposal(gesture, body, proposals)
    if chosen is None:
        raise LookupError("no proposal")
    store.apply_proposal(RESTAURANT_ID, chosen)
    _recaps.append(_recap_json(gesture, body, chosen, len(_recaps) + 1))
    _persist()
    return sandbox_state()


def undo() -> dict[str, Any]:
    store = get_store()
    store.undo_sandbox(RESTAURANT_ID)
    if _recaps:
        _recaps.pop()
    _persist()
    return sandbox_state()


def discard_sandbox_state() -> dict[str, Any]:
    store = get_store()
    if _sandbox_or_none() is None:
        raise LookupError("no sandbox")
    store.discard_sandbox(RESTAURANT_ID)
    _recaps.clear()
    store.enter_sandbox(RESTAURANT_ID, "cycle")
    _delete_persisted()
    _persist()
    return sandbox_state()


def sandbox_state() -> dict[str, Any]:
    state = get_store().get(RESTAURANT_ID)
    sandbox = state.sandbox
    assert sandbox is not None
    result = sandbox.last_result
    assignments = sandbox.draft.assignments
    warnings = result.warnings if result is not None else ()
    return {
        "sandbox": {"target": "cycle", "history_length": len(sandbox.history)},
        "restaurant": {
            "id": state.identity.id,
            "name": "Saint-Cloud",
            "employees": [_employee_json(person) for person in state.employees],
        },
        "planning": {
            "assignments": [_shift_json(item) for item in assignments],
            "warnings": [_warning_json(item) for item in warnings],
        },
        "score": _score_json(sandbox.draft, result),
        "history": list(_recaps),
    }


def parse_shift(raw: dict[str, Any]) -> Shift:
    required = (
        "employee_id",
        "day_index",
        "weekday",
        "service_id",
        "team",
        "start_minutes",
        "end_minutes",
        "post_level",
    )
    missing = [key for key in required if key not in raw]
    if missing:
        raise ValueError("missing shift fields")
    return Shift(
        employee_id=raw["employee_id"],
        day_index=int(raw["day_index"]),
        weekday=raw["weekday"],
        service_id=raw["service_id"],
        team=Team(raw["team"]),
        start_minutes=int(raw["start_minutes"]),
        end_minutes=int(raw["end_minutes"]),
        post_level=int(raw["post_level"]),
    )


def parse_slot(raw: dict[str, Any]) -> FillSlot:
    required = ("employee_id", "day_index", "weekday", "service_id", "team")
    missing = [key for key in required if key not in raw]
    if missing:
        raise ValueError("missing gesture fields")
    return FillSlot(
        employee_id=raw["employee_id"],
        day_index=int(raw["day_index"]),
        weekday=raw["weekday"],
        service_id=raw["service_id"],
        team=Team(raw["team"]),
    )


def _fill_times(body: dict[str, Any]) -> tuple[int | None, int | None]:
    start = body.get("start_minutes", None)
    end = body.get("end_minutes", None)
    start_present = "start_minutes" in body
    end_present = "end_minutes" in body
    if not start_present and not end_present:
        return None, None
    if start is None and end is None:
        return None, None
    if start is None or end is None:
        raise ValueError("missing gesture fields")
    return int(start), int(end)


def _preview(store: PlanningStore, gesture: str, body: dict[str, Any]) -> list[PreviewProposal]:
    if gesture == "fill":
        slot_raw = body.get("slot")
        if not isinstance(slot_raw, dict):
            raise ValueError("missing gesture fields")
        start, end = _fill_times(body)
        return store.preview_fill(RESTAURANT_ID, parse_slot(slot_raw), start, end)
    shift = parse_shift(body.get("shift") or {})
    if gesture == "retune":
        if "start_minutes" not in body or "end_minutes" not in body:
            raise ValueError("missing gesture fields")
        return store.preview_retune(
            RESTAURANT_ID,
            shift,
            int(body["start_minutes"]),
            int(body["end_minutes"]),
        )
    if gesture == "replace":
        return store.preview_replace(RESTAURANT_ID, shift)
    if gesture == "swap":
        return store.preview_swap(RESTAURANT_ID, shift)
    raise ValueError("unknown gesture")


def _match_proposal(gesture: str, body: dict[str, Any], proposals: list[PreviewProposal]) -> PreviewProposal | None:
    if gesture == "retune":
        return proposals[0] if proposals else None
    if gesture in {"replace", "fill"}:
        if "employee_id" not in body:
            raise ValueError("missing gesture fields")
        employee_id = body["employee_id"]
        for item in proposals:
            if item.employee_id == employee_id:
                return item
        return None
    partner_raw = body.get("partner")
    if not isinstance(partner_raw, dict):
        raise ValueError("missing gesture fields")
    partner = parse_shift(partner_raw)
    for item in proposals:
        if item.partner == partner:
            return item
    return None


def _sandbox_or_none():
    store = get_store()
    try:
        return store.get(RESTAURANT_ID).sandbox
    except KeyError:
        return None


def _employee_json(person) -> dict[str, Any]:
    return {
        "id": person.id,
        "name": person.name,
        "role": {"name": person.role.name, "level": person.role.level, "team": person.role.team.value},
        "team": person.team.value,
    }


def _shift_json(shift: Shift) -> dict[str, Any]:
    return {
        "employee_id": shift.employee_id,
        "day_index": shift.day_index,
        "weekday": shift.weekday,
        "service_id": shift.service_id,
        "team": shift.team.value,
        "start_minutes": shift.start_minutes,
        "end_minutes": shift.end_minutes,
        "post_level": shift.post_level,
        "duration_hours": shift.duration_hours,
    }


def _warning_json(warning: Warning) -> dict[str, Any]:
    return {
        "severity": warning.severity.value,
        "code": warning.code,
        "message": warning.message,
        "employee_id": warning.employee_id,
        "day_index": warning.day_index,
    }


def _score_json(draft, result: EngineResult | None) -> dict[str, Any]:
    if result is None:
        raise RuntimeError("No sandbox")
    return dict(zip(SCORE_FIELDS, _attempt_key(draft, result), strict=True))


def _impact_json(impact: PreviewImpact) -> dict[str, Any]:
    return {
        "new_interdits": [_warning_json(item) for item in impact.new_interdits],
        "broken_wishes": [_warning_json(item) for item in impact.broken_wishes],
        "contract": [
            {
                "employee_id": row.employee_id,
                "week_start": row.week_start,
                "current_hours": row.current_hours,
                "trial_hours": row.trial_hours,
                "contracted": row.contracted,
                "kind": row.kind,
            }
            for row in impact.contract
        ],
        "coverage_added": [_warning_json(item) for item in impact.coverage_added],
        "coverage_removed": [_warning_json(item) for item in impact.coverage_removed],
        "role_fit": [
            {
                "current_gap": row.current_gap,
                "trial_gap": row.trial_gap,
                "kind": row.kind,
            }
            for row in impact.role_fit
        ],
    }


def _slot_json(slot: FillSlot) -> dict[str, Any]:
    return {
        "employee_id": slot.employee_id,
        "day_index": slot.day_index,
        "weekday": slot.weekday,
        "service_id": slot.service_id,
        "team": slot.team.value,
    }


def _recap_json(gesture: str, body: dict[str, Any], chosen: PreviewProposal, index: int) -> dict[str, Any]:
    occupied = gesture in {"retune", "replace", "swap"}
    shift = parse_shift(body.get("shift") or {}) if occupied else None
    slot_raw = body.get("slot")
    slot = parse_slot(slot_raw) if gesture == "fill" and isinstance(slot_raw, dict) else None
    return {
        "index": index,
        "gesture": gesture,
        "shift": None if shift is None else _shift_json(shift),
        "slot": None if slot is None else _slot_json(slot),
        "employee_id": chosen.employee_id,
        "start_minutes": chosen.start_minutes,
        "end_minutes": chosen.end_minutes,
        "partner": None if chosen.partner is None else _shift_json(chosen.partner),
        "impact": _impact_json(chosen.impact),
    }


def _proposal_json(item: PreviewProposal) -> dict[str, Any]:
    return {
        "rank": item.rank,
        "gesture": item.gesture,
        "start_minutes": item.start_minutes,
        "end_minutes": item.end_minutes,
        "employee_id": item.employee_id,
        "partner": None if item.partner is None else _shift_json(item.partner),
        "impact": _impact_json(item.impact),
        "current_score": dict(zip(SCORE_FIELDS, item.current_score, strict=True)),
        "trial_score": dict(zip(SCORE_FIELDS, item.trial_score, strict=True)),
    }


def _warning_from_json(raw: dict[str, Any]) -> Warning:
    return Warning(
        WarningSeverity(raw["severity"]),
        raw["code"],
        raw["message"],
        raw.get("employee_id"),
        raw.get("day_index"),
    )


def _persist() -> None:
    from doux_planning.api.db import SandboxSession, database_url, session_scope

    if not database_url():
        return
    sandbox = _sandbox_or_none()
    if sandbox is None:
        return
    result = sandbox.last_result
    document = {
        "recaps": list(_recaps),
        "assignments": [_shift_json(item) for item in sandbox.draft.assignments],
        "warnings": [_warning_json(item) for item in (result.warnings if result else ())],
        "history": [
            {
                "assignments": [_shift_json(item) for item in snap.assignments],
                "warnings": [
                    _warning_json(item)
                    for item in (snap.last_result.warnings if snap.last_result is not None else ())
                ],
            }
            for snap in sandbox.history
        ],
    }
    with session_scope() as session:
        row = session.get(SandboxSession, RESTAURANT_ID)
        if row is None:
            session.add(SandboxSession(restaurant_id=RESTAURANT_ID, document=document))
        else:
            row.document = document
            flag_modified(row, "document")


def _delete_persisted() -> None:
    from doux_planning.api.db import SandboxSession, database_url, session_scope

    if not database_url():
        return
    try:
        with session_scope() as session:
            row = session.get(SandboxSession, RESTAURANT_ID)
            if row is not None:
                session.delete(row)
    except Exception:
        return


def _restore() -> None:
    from doux_planning.api.db import SandboxSession, database_url, session_scope

    global _recaps
    if not database_url() or _store is None:
        return
    try:
        with session_scope() as session:
            row = session.get(SandboxSession, RESTAURANT_ID)
            document = None if row is None else dict(row.document)
    except Exception:
        return
    if not document:
        return
    hydrate_delivered_cycle(_store, RESTAURANT_ID)
    sandbox = _store.get(RESTAURANT_ID).sandbox
    assert sandbox is not None
    assignments = tuple(parse_shift(item) for item in document["assignments"])
    warnings = tuple(_warning_from_json(item) for item in document.get("warnings") or ())
    sandbox.draft = sandbox.draft.with_assignments(assignments)
    sandbox.last_result = EngineResult(assignments=assignments, warnings=warnings)
    sandbox.history = [
        SandboxSnapshot(
            assignments=tuple(parse_shift(item) for item in snap["assignments"]),
            last_result=EngineResult(
                assignments=tuple(parse_shift(item) for item in snap["assignments"]),
                warnings=tuple(_warning_from_json(item) for item in snap.get("warnings") or ()),
            ),
        )
        for snap in document.get("history") or []
    ]
    _recaps = list(document.get("recaps") or [])
