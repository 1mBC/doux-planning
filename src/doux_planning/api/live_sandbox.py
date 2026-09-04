from __future__ import annotations

from dataclasses import replace
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm.attributes import flag_modified

from doux_planning.api.auth import DETAIL_INVALID_FIELDS, require_company_restaurant_id, require_database
from doux_planning.api.context import _load_company, _state_from_rows
from doux_planning.api.db import Company, session_scope
from doux_planning.api.generate import _cycle_json
from doux_planning.api.sandbox import (
    GESTURES,
    _employee_json,
    _match_proposal,
    _proposal_json,
    _recap_json,
    _score_json,
    _shift_json,
    _warning_from_json,
    _warning_json,
    parse_shift,
    parse_slot,
)
from doux_planning.context import (
    NoPublishedCycle,
    discard_live_sandbox,
    enter_live_sandbox,
    expand_typical_week,
    publish_live_sandbox,
)
from doux_planning.engine import EngineResult, PlanningDraft
from doux_planning.planning import (
    EmptyHistoryError,
    IdentityRetuneError,
    OccupiedSlotError,
    PlanningStore,
    PublishedCycle,
    RestaurantState,
    Sandbox,
    SandboxSnapshot,
)
from doux_planning.staff import default_legal_rules
from doux_planning.types import Team

DETAIL_NO_CYCLE = "Aucun cycle publié pour cette équipe."
DETAIL_NO_SANDBOX = "Aucun bac à sable n'est ouvert."
TEAMS = (Team.SALLE, Team.CUISINE)


def _parse_team(team: str) -> Team:
    if team not in {item.value for item in TEAMS}:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    return Team(team)


def _published_from_json(state: RestaurantState, team: Team, blob: Any) -> PublishedCycle | None:
    if not isinstance(blob, dict):
        return None
    assignments = tuple(parse_shift(item) for item in blob.get("assignments") or [])
    warnings = tuple(_warning_from_json(item) for item in blob.get("warnings") or [])
    structures = tuple(item for item in expand_typical_week(state) if item.team == team)
    employees = tuple(person for person in state.employees if person.team == team)
    draft = PlanningDraft(
        employees=employees,
        structures=structures,
        hours=state.hours,
        legal_rules=default_legal_rules(),
        assignments=assignments,
    )
    return PublishedCycle(
        id=team.value,
        draft=draft,
        result=EngineResult(assignments=assignments, warnings=warnings),
    )


def _sandbox_from_json(state: RestaurantState, team: Team, blob: Any) -> Sandbox | None:
    if not isinstance(blob, dict):
        return None
    published = state.published_cycles.get(team)
    if published is None:
        return None
    assignments = tuple(parse_shift(item) for item in blob.get("assignments") or [])
    warnings = tuple(_warning_from_json(item) for item in blob.get("warnings") or [])
    sandbox = Sandbox(
        restaurant_id=state.identity.id,
        target="cycle",
        week_id=None,
        draft=replace(published.draft).with_assignments(assignments),
        last_result=EngineResult(assignments=assignments, warnings=warnings),
    )
    sandbox.history = [
        SandboxSnapshot(
            assignments=tuple(parse_shift(item) for item in snap.get("assignments") or []),
            last_result=EngineResult(
                assignments=tuple(parse_shift(item) for item in snap.get("assignments") or []),
                warnings=tuple(_warning_from_json(item) for item in snap.get("warnings") or []),
            ),
        )
        for snap in blob.get("history") or []
        if isinstance(snap, dict)
    ]
    return sandbox


def _hydrate(state: RestaurantState, company: Company) -> dict[Team, list[dict[str, Any]]]:
    published_raw = company.published_cycles or {}
    live_raw = company.live_sandboxes or {}
    recaps: dict[Team, list[dict[str, Any]]] = {}
    for team in TEAMS:
        state.published_cycles[team] = _published_from_json(state, team, published_raw.get(team.value))
        blob = live_raw.get(team.value)
        state.live_sandboxes[team] = _sandbox_from_json(state, team, blob)
        recaps[team] = list(blob.get("recaps") or []) if isinstance(blob, dict) else []
    return recaps


def _sandbox_blob(sandbox: Sandbox | None, recaps: list[dict[str, Any]]) -> dict[str, Any] | None:
    if sandbox is None:
        return None
    result = sandbox.last_result
    return {
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
        "recaps": list(recaps),
    }


def _persist(
    restaurant_id: str,
    state: RestaurantState,
    recaps: dict[Team, list[dict[str, Any]]],
    *,
    published: bool = False,
) -> None:
    with session_scope() as db:
        company = db.get(Company, restaurant_id)
        if company is None:
            raise HTTPException(status_code=401, detail="Session invalide.")
        company.live_sandboxes = {
            "salle": _sandbox_blob(state.live_sandboxes.get(Team.SALLE), recaps[Team.SALLE]),
            "cuisine": _sandbox_blob(state.live_sandboxes.get(Team.CUISINE), recaps[Team.CUISINE]),
        }
        flag_modified(company, "live_sandboxes")
        if published:
            company.published_cycles = {
                "salle": _cycle_json(state.published_cycles.get(Team.SALLE)),
                "cuisine": _cycle_json(state.published_cycles.get(Team.CUISINE)),
            }
            flag_modified(company, "published_cycles")


def _load(authorization: str | None) -> tuple[str, RestaurantState, dict[Team, list[dict[str, Any]]]]:
    require_database()
    restaurant_id = require_company_restaurant_id(authorization)
    company, fiches = _load_company(restaurant_id)
    state = _state_from_rows(company, fiches)
    recaps = _hydrate(state, company)
    return restaurant_id, state, recaps


def _store_for(state: RestaurantState) -> PlanningStore:
    store = PlanningStore()
    store.add_restaurant(state)
    return store


def _require_sandbox(state: RestaurantState, team: Team) -> Sandbox:
    sandbox = state.live_sandboxes.get(team)
    if sandbox is None:
        raise HTTPException(status_code=404, detail=DETAIL_NO_SANDBOX)
    return sandbox


def _live_state(
    state: RestaurantState, team: Team, recaps: dict[Team, list[dict[str, Any]]]
) -> dict[str, Any]:
    sandbox = _require_sandbox(state, team)
    result = sandbox.last_result
    employees = [person for person in state.employees if person.team == team]
    return {
        "team": team.value,
        "sandbox": {"target": "cycle", "history_length": len(sandbox.history)},
        "restaurant": {
            "id": state.identity.id,
            "name": state.identity.name,
            "employees": [_employee_json(person) for person in employees],
        },
        "planning": {
            "assignments": [_shift_json(item) for item in sandbox.draft.assignments],
            "warnings": [_warning_json(item) for item in (result.warnings if result else ())],
        },
        "score": _score_json(sandbox.draft, result),
        "history": list(recaps[team]),
    }


def _preview_live(
    store: PlanningStore, restaurant_id: str, team: Team, body: dict[str, Any]
):
    gesture = body.get("gesture")
    if gesture not in GESTURES:
        raise ValueError("unknown gesture")
    if gesture == "fill":
        slot_raw = body.get("slot")
        if not isinstance(slot_raw, dict):
            raise ValueError("missing gesture fields")
        start = body.get("start_minutes", None)
        end = body.get("end_minutes", None)
        if "start_minutes" not in body and "end_minutes" not in body:
            start, end = None, None
        elif start is None and end is None:
            start, end = None, None
        elif start is None or end is None:
            raise ValueError("missing gesture fields")
        else:
            start, end = int(start), int(end)
        return store.preview_fill(restaurant_id, parse_slot(slot_raw), start, end, team=team)
    shift = parse_shift(body.get("shift") or {})
    if gesture == "retune":
        if "start_minutes" not in body or "end_minutes" not in body:
            raise ValueError("missing gesture fields")
        return store.preview_retune(
            restaurant_id,
            shift,
            int(body["start_minutes"]),
            int(body["end_minutes"]),
            team=team,
        )
    if gesture == "replace":
        return store.preview_replace(restaurant_id, shift, team=team)
    return store.preview_swap(restaurant_id, shift, team=team)


def _map_edit_error(exc: Exception) -> HTTPException:
    if isinstance(exc, IdentityRetuneError):
        return HTTPException(status_code=400, detail="Ces horaires sont déjà ceux du créneau.")
    if isinstance(exc, OccupiedSlotError):
        return HTTPException(status_code=409, detail="Cette case est déjà occupée.")
    if isinstance(exc, EmptyHistoryError):
        return HTTPException(status_code=409, detail="Aucune modification à annuler.")
    if isinstance(exc, LookupError):
        if str(exc) == "no proposal":
            return HTTPException(status_code=400, detail="Proposition introuvable.")
        return HTTPException(status_code=404, detail=DETAIL_NO_SANDBOX)
    if isinstance(exc, (RuntimeError, KeyError)):
        return HTTPException(status_code=404, detail=DETAIL_NO_SANDBOX)
    if isinstance(exc, ValueError):
        message = str(exc)
        if "not in the sandbox" in message or "missing shift" in message:
            return HTTPException(status_code=404, detail="Ce créneau n'est pas dans le brouillon.")
        if "unknown gesture" in message:
            return HTTPException(status_code=400, detail="Geste inconnu.")
        if "min_shift_hours" in message:
            return HTTPException(status_code=400, detail="La durée est inférieure au minimum du salarié.")
        if "15-minute grid" in message:
            return HTTPException(status_code=400, detail="Les horaires doivent être sur la grille de 15 minutes.")
        if "closed" in message.lower():
            return HTTPException(status_code=400, detail="Ce service est fermé.")
        return HTTPException(status_code=400, detail="Champs manquants pour ce geste.")
    raise exc


def enter(authorization: str | None, team_raw: str) -> dict[str, Any]:
    restaurant_id, state, recaps = _load(authorization)
    team = _parse_team(team_raw)
    try:
        enter_live_sandbox(state, team)
    except NoPublishedCycle as exc:
        raise HTTPException(status_code=409, detail=DETAIL_NO_CYCLE) from exc
    _persist(restaurant_id, state, recaps)
    return _live_state(state, team, recaps)


def get_live(authorization: str | None, team_raw: str) -> dict[str, Any]:
    _restaurant_id, state, recaps = _load(authorization)
    team = _parse_team(team_raw)
    return _live_state(state, team, recaps)


def preview(authorization: str | None, team_raw: str, body: dict[str, Any]) -> dict[str, Any]:
    restaurant_id, state, _recaps = _load(authorization)
    team = _parse_team(team_raw)
    _require_sandbox(state, team)
    store = _store_for(state)
    try:
        proposals = _preview_live(store, restaurant_id, team, body)
    except Exception as exc:
        mapped = _map_edit_error(exc)
        if mapped is not exc:
            raise mapped from exc
        raise
    return {"proposals": [_proposal_json(item) for item in proposals]}


def commit(authorization: str | None, team_raw: str, body: dict[str, Any]) -> dict[str, Any]:
    restaurant_id, state, recaps = _load(authorization)
    team = _parse_team(team_raw)
    _require_sandbox(state, team)
    store = _store_for(state)
    try:
        gesture = body.get("gesture")
        if gesture not in GESTURES:
            raise ValueError("unknown gesture")
        proposals = _preview_live(store, restaurant_id, team, body)
        chosen = _match_proposal(gesture, body, proposals)
        if chosen is None:
            raise LookupError("no proposal")
        store.apply_proposal(restaurant_id, chosen, team=team)
        recaps[team].append(_recap_json(gesture, body, chosen, len(recaps[team]) + 1))
    except Exception as exc:
        mapped = _map_edit_error(exc)
        if mapped is not exc:
            raise mapped from exc
        raise
    _persist(restaurant_id, state, recaps)
    return _live_state(state, team, recaps)


def undo(authorization: str | None, team_raw: str) -> dict[str, Any]:
    restaurant_id, state, recaps = _load(authorization)
    team = _parse_team(team_raw)
    _require_sandbox(state, team)
    store = _store_for(state)
    try:
        store.undo_sandbox(restaurant_id, team=team)
    except Exception as exc:
        mapped = _map_edit_error(exc)
        if mapped is not exc:
            raise mapped from exc
        raise
    if recaps[team]:
        recaps[team].pop()
    _persist(restaurant_id, state, recaps)
    return _live_state(state, team, recaps)


def discard(authorization: str | None, team_raw: str) -> dict[str, Any]:
    restaurant_id, state, recaps = _load(authorization)
    team = _parse_team(team_raw)
    _require_sandbox(state, team)
    discard_live_sandbox(state, team)
    try:
        enter_live_sandbox(state, team)
    except NoPublishedCycle as exc:
        raise HTTPException(status_code=409, detail=DETAIL_NO_CYCLE) from exc
    recaps[team] = []
    _persist(restaurant_id, state, recaps)
    return _live_state(state, team, recaps)


def publish(authorization: str | None, team_raw: str) -> dict[str, Any]:
    restaurant_id, state, recaps = _load(authorization)
    team = _parse_team(team_raw)
    _require_sandbox(state, team)
    try:
        publish_live_sandbox(state, team)
    except NoPublishedCycle as exc:
        raise HTTPException(status_code=409, detail=DETAIL_NO_CYCLE) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=DETAIL_NO_SANDBOX) from exc
    recaps[team] = []
    _persist(restaurant_id, state, recaps, published=True)
    return {
        "published": {
            "salle": _cycle_json(state.published_cycles.get(Team.SALLE)),
            "cuisine": _cycle_json(state.published_cycles.get(Team.CUISINE)),
        }
    }
