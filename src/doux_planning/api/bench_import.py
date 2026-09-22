from __future__ import annotations

import math
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select

from doux_planning.api.auth import (
    DETAIL_INVALID_FIELDS,
    DETAIL_RESTAURANT_MISSING,
    require_admin,
    require_database,
)
from doux_planning.api.context import (
    _load_company,
    _serialize_employee,
    _serialize_type,
    _state_from_rows,
)
from doux_planning.api.db import (
    BenchImportedDataset,
    BenchRun,
    Company,
    GenerateLog,
    RestaurateurAccount,
    session_scope,
)
from doux_planning.api.generate import (
    SCORE_AXES,
    _cycle_score_json,
    _stored_published,
    get_effective_engine_ref,
    normalize_published,
)
from doux_planning.bench import UnknownBenchDataset, bench_dataset_from_json
from doux_planning.context import SCORE_WEIGHTS, cycle_recap_from_draft, expand_typical_week, team_ready
from doux_planning.engine import PlanningDraft, evaluate
from doux_planning.staff import default_legal_rules
from doux_planning.types import Team

IMPORTED_CATEGORY = "imported"
IMPORTED_ORIGIN = "imported"
DETAIL_NO_SALLE = "Ce jeu n’a pas de salle."
EFFORTS = ("minimal", "optimized", "maximal")
TEAMS = (Team.SALLE, Team.CUISINE)


def _invalid() -> HTTPException:
    return HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)


def list_imported_rows() -> list[BenchImportedDataset]:
    require_database()
    with session_scope() as db:
        rows = list(
            db.scalars(
                select(BenchImportedDataset).order_by(
                    BenchImportedDataset.created_at.desc(),
                    BenchImportedDataset.id.desc(),
                )
            )
        )
        for row in rows:
            db.expunge(row)
        return rows


def get_imported_row(dataset_id: str) -> BenchImportedDataset | None:
    require_database()
    with session_scope() as db:
        row = db.get(BenchImportedDataset, dataset_id)
        if row is None:
            return None
        db.expunge(row)
        return row


def imported_override(dataset_id: str) -> float | None:
    row = get_imported_row(dataset_id)
    if row is None:
        return None
    return row.manual_score_override


def imported_context(dataset_id: str) -> dict[str, Any] | None:
    row = get_imported_row(dataset_id)
    if row is None or not isinstance(row.context, dict):
        return None
    return dict(row.context)


def context_has_salle(context: dict[str, Any] | None) -> bool:
    if not isinstance(context, dict):
        return False
    for key in ("employees", "types", "roles"):
        for item in context.get(key) or []:
            if isinstance(item, dict) and item.get("team") == Team.SALLE.value:
                return True
    for item in context.get("typical_week") or []:
        if isinstance(item, dict) and item.get("team") == Team.SALLE.value:
            return True
    return False


def load_imported_dataset(category: str, dataset_id: str):
    row = get_imported_row(dataset_id)
    if row is None or row.category != category:
        raise UnknownBenchDataset(category, dataset_id)
    expected = row.expected if isinstance(row.expected, dict) else {}
    assignments = expected.get("assignments") or []
    if not isinstance(assignments, list):
        assignments = []
    context = row.context if isinstance(row.context, dict) else {}
    return bench_dataset_from_json(
        category=row.category,
        id=row.id,
        name=row.name,
        challenge_fr=row.challenge_fr,
        context=context,
        assignments=assignments,
    )


def _bool_flag(body: dict[str, Any], key: str) -> bool:
    if key not in body:
        return True
    value = body[key]
    if not isinstance(value, bool):
        raise _invalid()
    return value


def _parse_comment(body: dict[str, Any]) -> str | None:
    if "comment" not in body or body["comment"] is None:
        return None
    comment = body["comment"]
    if not isinstance(comment, str):
        raise _invalid()
    trimmed = comment.strip()
    return trimmed or None


def _parse_manual_score(body: dict[str, Any]) -> float | None:
    if "manual_score" not in body or body["manual_score"] is None:
        return None
    value = body["manual_score"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _invalid()
    number = float(value)
    if not math.isfinite(number) or number < 0 or number > 10:
        raise _invalid()
    return round(number, 1)


def _dataset_name(company_name: str, email: str) -> str:
    trimmed = (company_name or "").strip()
    if trimmed:
        return trimmed
    mail = (email or "").strip()
    if mail:
        return mail
    return "Sans nom"


def _challenge_fr(comment: str | None, email: str) -> str:
    if comment:
        return comment
    return f"Importé de {email}"


def _new_imported_id() -> str:
    return f"imp-{secrets.token_urlsafe(8)}"


def _load_restaurant(restaurant_id: str) -> tuple[Company, list, str]:
    with session_scope() as db:
        company = db.get(Company, restaurant_id)
        if company is None:
            raise HTTPException(status_code=404, detail=DETAIL_RESTAURANT_MISSING)
        account = db.scalars(
            select(RestaurateurAccount).where(RestaurateurAccount.restaurant_id == restaurant_id)
        ).first()
        email = account.email if account is not None else ""
    company, fiches = _load_company(restaurant_id)
    return company, fiches, email


def _generate_count(restaurant_id: str) -> int:
    with session_scope() as db:
        count = db.scalar(
            select(func.count()).select_from(GenerateLog).where(GenerateLog.restaurant_id == restaurant_id)
        )
    return int(count or 0)


def _team_preview(state, pack: dict[str, Any] | None, team: Team) -> dict[str, Any]:
    versions = (pack or {}).get("versions") or {}
    return {
        "ready": team_ready(state, team),
        "manuel_published": versions.get("manuel") is not None,
        "computes_published": {
            effort: versions.get(effort) is not None for effort in EFFORTS
        },
    }


def import_preview(authorization: str | None, restaurant_id: str) -> dict[str, Any]:
    require_admin(authorization)
    require_database()
    company, fiches, email = _load_restaurant(restaurant_id)
    state = _state_from_rows(company, fiches)
    stored = _stored_published(company.published_cycles)
    published, _dirty = normalize_published(stored, state)
    return {
        "restaurant_id": restaurant_id,
        "restaurant_name": company.name or "",
        "email": email,
        "salle": _team_preview(state, published.get("salle"), Team.SALLE),
        "cuisine": _team_preview(state, published.get("cuisine"), Team.CUISINE),
        "generate_count": _generate_count(restaurant_id),
    }


def _snapshot_context(
    *,
    dataset_id: str,
    name: str,
    challenge_fr: str,
    state,
    teams: set[Team],
) -> dict[str, Any]:
    hours = state.hours
    services = list(hours.services) if hours is not None else list(state.company_services)
    closed = sorted(hours.closed_weekdays) if hours is not None else []
    roles: list[dict[str, Any]] = []
    for team in TEAMS:
        if team not in teams:
            continue
        ladder = state.ladders.get(team)
        if ladder is None:
            continue
        for role in ladder.roles:
            roles.append({"name": role.name, "level": role.level, "team": team.value})
    types = [_serialize_type(item) for item in state.service_types if item.team in teams]
    employees: list[dict[str, Any]] = []
    for person in state.employees:
        if person.team not in teams:
            continue
        payload = _serialize_employee(person, services)
        payload.pop("invite_token", None)
        employees.append(payload)
    typical: list[dict[str, Any]] = []
    if state.typical_week is not None:
        for cell in state.typical_week.cells:
            if cell.team not in teams:
                continue
            typical.append(
                {
                    "weekday": cell.weekday,
                    "service_id": cell.service_id,
                    "type_id": cell.type_id,
                    "closed": cell.closed,
                    "team": cell.team.value,
                }
            )
    context: dict[str, Any] = {
        "id": dataset_id,
        "category": IMPORTED_CATEGORY,
        "name": name,
        "team": Team.SALLE.value if Team.SALLE in teams else Team.CUISINE.value,
        "challenge_fr": challenge_fr,
        "hours": {"mode": "services", "services": services, "closed_weekdays": closed},
        "roles": roles,
        "types": types,
        "employees": employees,
    }
    if typical:
        context["typical_week"] = typical
    return context


def _manuel_assignments(published: dict[str, Any], teams: set[Team]) -> list[dict[str, Any]]:
    assignments: list[dict[str, Any]] = []
    for team in TEAMS:
        if team not in teams:
            continue
        pack = published.get(team.value) or {}
        slot = (pack.get("versions") or {}).get("manuel")
        if not isinstance(slot, dict):
            continue
        for item in slot.get("assignments") or []:
            if not isinstance(item, dict):
                continue
            if item.get("team") != team.value:
                continue
            assignments.append(dict(item))
    return assignments


def _salle_score_json(dataset, assignments) -> dict[str, Any]:
    state = dataset.state
    employees = tuple(person for person in state.employees if person.team == Team.SALLE)
    structures = tuple(item for item in expand_typical_week(state) if item.team == Team.SALLE)
    if isinstance(assignments, tuple):
        shifts = assignments
    else:
        from doux_planning.api.sandbox import parse_shift

        shifts = tuple(parse_shift(item) if isinstance(item, dict) else item for item in assignments or ())
    draft = PlanningDraft(
        employees=employees,
        structures=structures,
        hours=state.hours,
        legal_rules=default_legal_rules(),
        assignments=tuple(shifts),
    )
    result = evaluate(draft)
    recap = cycle_recap_from_draft(draft, result)
    return _cycle_score_json(recap.score)


def _oracle_score_json(dataset, override: float | None) -> dict[str, Any]:
    if not dataset.expected and override is not None:
        return {
            "notes": {key: None for key in SCORE_AXES},
            "global": override,
            "weights": dict(SCORE_WEIGHTS),
        }
    score = _salle_score_json(dataset, dataset.expected)
    if override is not None:
        score = dict(score)
        score["global"] = override
    return score


def _json_deltas(score: dict[str, Any], expected: dict[str, Any]) -> dict[str, float | None]:
    notes = score.get("notes") if isinstance(score.get("notes"), dict) else {}
    expected_notes = expected.get("notes") if isinstance(expected.get("notes"), dict) else {}
    deltas: dict[str, float | None] = {}
    for key in SCORE_AXES:
        generated = notes.get(key)
        oracle = expected_notes.get(key)
        deltas[key] = None if generated is None or oracle is None else float(generated) - float(oracle)
    model_global = score.get("global")
    expected_global = expected.get("global")
    deltas["global"] = (
        None if model_global is None or expected_global is None else float(model_global) - float(expected_global)
    )
    return deltas


def _slot_score_json(slot: dict[str, Any], dataset, assignments) -> dict[str, Any]:
    score = slot.get("score")
    if isinstance(score, dict) and "global" in score:
        return dict(score)
    return _salle_score_json(dataset, assignments)


def _copy_salle_runs(
    *,
    dataset_id: str,
    dataset,
    published: dict[str, Any],
    override: float | None,
    created_at: datetime,
) -> list[BenchRun]:
    pack = published.get("salle") or {}
    versions = pack.get("versions") or {}
    expected_score = _oracle_score_json(dataset, override)
    live_ref = get_effective_engine_ref()
    rows: list[BenchRun] = []
    for effort in EFFORTS:
        slot = versions.get(effort)
        if not isinstance(slot, dict):
            continue
        assignments = list(slot.get("assignments") or [])
        score = _slot_score_json(slot, dataset, assignments)
        duration = slot.get("duration_seconds")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool):
            duration = 0.0
        engine = slot.get("engine_ref")
        if not isinstance(engine, str) or not engine:
            engine = live_ref
        warnings = slot.get("facts") if isinstance(slot.get("facts"), list) else []
        rows.append(
            BenchRun(
                id=secrets.token_urlsafe(12),
                created_at=created_at,
                app_version=engine,
                category=IMPORTED_CATEGORY,
                dataset_id=dataset_id,
                search_effort=effort,
                duration_seconds=max(0.0, float(duration)),
                score=score,
                expected_score=expected_score,
                deltas=_json_deltas(score, expected_score),
                assignments=assignments,
                warnings=warnings,
                trace=None,
            )
        )
    return rows


def import_restaurant(authorization: str | None, body: dict[str, Any]) -> dict[str, Any]:
    require_admin(authorization)
    require_database()
    if not isinstance(body, dict):
        raise _invalid()
    restaurant_id = body.get("restaurant_id")
    if not isinstance(restaurant_id, str) or not restaurant_id:
        raise _invalid()
    include_salle = _bool_flag(body, "include_salle")
    include_cuisine = _bool_flag(body, "include_cuisine")
    include_manuel = _bool_flag(body, "include_manuel")
    include_runs = _bool_flag(body, "include_runs")
    if not include_salle and not include_cuisine:
        raise _invalid()
    override = _parse_manual_score(body)
    comment = _parse_comment(body)

    company, fiches, email = _load_restaurant(restaurant_id)
    state = _state_from_rows(company, fiches)
    stored = _stored_published(company.published_cycles)
    published, _dirty = normalize_published(stored, state)

    teams: set[Team] = set()
    if include_salle:
        teams.add(Team.SALLE)
    if include_cuisine:
        teams.add(Team.CUISINE)

    dataset_id = _new_imported_id()
    name = _dataset_name(company.name or "", email)
    challenge_fr = _challenge_fr(comment, email)
    context = _snapshot_context(
        dataset_id=dataset_id,
        name=name,
        challenge_fr=challenge_fr,
        state=state,
        teams=teams,
    )
    assignments: list[dict[str, Any]] = []
    if include_manuel:
        assignments = _manuel_assignments(published, teams)
    expected = {"assignments": assignments}
    created_at = datetime.now(timezone.utc)
    dataset = bench_dataset_from_json(
        category=IMPORTED_CATEGORY,
        id=dataset_id,
        name=name,
        challenge_fr=challenge_fr,
        context=context,
        assignments=assignments,
    )
    copied_runs: list[BenchRun] = []
    if include_runs and include_salle:
        copied_runs = _copy_salle_runs(
            dataset_id=dataset_id,
            dataset=dataset,
            published=published,
            override=override,
            created_at=created_at,
        )

    row = BenchImportedDataset(
        id=dataset_id,
        category=IMPORTED_CATEGORY,
        name=name,
        challenge_fr=challenge_fr,
        comment=comment,
        origin=IMPORTED_ORIGIN,
        source_restaurant_id=restaurant_id,
        context=context,
        expected=expected,
        manual_score_override=override,
        created_at=created_at,
    )
    with session_scope() as db:
        db.add(row)
        for run in copied_runs:
            db.add(run)

    return {
        "category": IMPORTED_CATEGORY,
        "id": dataset_id,
        "name": name,
        "challenge_fr": challenge_fr,
        "origin": IMPORTED_ORIGIN,
        "comment": comment,
        "manual_score_override": override,
        "included": {
            "salle": include_salle,
            "cuisine": include_cuisine,
            "manuel": include_manuel,
            "runs": include_runs,
        },
    }
