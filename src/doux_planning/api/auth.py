from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from doux_planning.api.db import (
    AccountEmail,
    AuthSession,
    Company,
    EmployeeAccountRow,
    RestaurateurAccount,
    StaffFiche,
    database_url,
    session_scope,
)
from doux_planning.invites import (
    InvalidInviteCode,
    InviteAlreadyRedeemed,
    InviteTargetMismatch,
    RestaurantIdentity,
    UnknownEmployee,
    UnknownInviteToken,
    redeem_invite,
    rotate_employee_invite_token,
)
from doux_planning.staff import Employee, Role
from doux_planning.types import Team

PASSWORD_HASHER = PasswordHasher()
SESSION_TTL = timedelta(days=30)
MIN_PASSWORD_LENGTH = 8
DETAIL_INVALID_FIELDS = "Champs invalides."
DETAIL_INVALID_INVITE = "Code entreprise ou jeton invalide."
DETAIL_BAD_CREDENTIALS = "Email ou mot de passe incorrect."
DETAIL_SESSION = "Session invalide."
DETAIL_FORBIDDEN = "Action réservée au restaurateur."
DETAIL_EMAIL_TAKEN = "Cet email est déjà utilisé."
DETAIL_FICHE_LINKED = "Cette fiche a déjà un compte."
DETAIL_COMPANY_MISSING = "Entreprise introuvable."
DETAIL_FICHE_MISSING = "Fiche introuvable."
DETAIL_DB = "Base indisponible."


def require_database() -> None:
    if not database_url():
        raise HTTPException(status_code=503, detail=DETAIL_DB)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_id() -> str:
    return secrets.token_urlsafe(12)


def _normalize_email(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    email = value.strip()
    return email.lower() if email else None


def _as_optional_str(body: dict[str, Any], key: str) -> str | None:
    if key not in body:
        return None
    value = body[key]
    if value is None:
        return None
    if not isinstance(value, str):
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    return value


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail=DETAIL_SESSION)
    token = authorization[len("Bearer ") :].strip()
    if not token:
        raise HTTPException(status_code=401, detail=DETAIL_SESSION)
    return token


def _load_session(db: Session, token: str) -> AuthSession:
    row = db.get(AuthSession, _hash_token(token))
    if row is None:
        raise HTTPException(status_code=401, detail=DETAIL_SESSION)
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= _now():
        db.delete(row)
        raise HTTPException(status_code=401, detail=DETAIL_SESSION)
    return row


def _me_payload(*, kind: str, email: str, restaurant_id: str, employee_id: str | None) -> dict[str, Any]:
    return {
        "kind": kind,
        "email": email,
        "restaurant_id": restaurant_id,
        "employee_id": employee_id,
    }


def _issue_session(db: Session, *, kind: str, account_id: str, restaurant_id: str) -> str:
    token = secrets.token_urlsafe(32)
    db.add(
        AuthSession(
            token_hash=_hash_token(token),
            kind=kind,
            account_id=account_id,
            restaurant_id=restaurant_id,
            expires_at=_now() + SESSION_TTL,
        )
    )
    return token


def _fiche_to_employee(row: StaffFiche) -> Employee:
    from doux_planning.staff import Unavailability
    from doux_planning.types import DEFAULT_MIN_SHIFT_HOURS, WellbeingPreference

    team = Team(row.team)
    role = Role(name=row.role, level=getattr(row, "role_level", 1) or 1, team=team)
    unavailabilities = tuple(
        Unavailability(
            weekday=item.get("weekday"),
            every_morning=bool(item.get("every_morning")),
            every_evening=bool(item.get("every_evening")),
            service_id=item.get("service_id"),
        )
        for item in (row.unavailabilities or [])
        if isinstance(item, dict)
    )
    wellbeing = frozenset(
        WellbeingPreference(value) for value in (row.wellbeing or []) if isinstance(value, str)
    )
    return Employee(
        id=row.id,
        name=row.name,
        role=role,
        team=team,
        contractual_hours_per_week=getattr(row, "contractual_hours_per_week", None) or 35,
        unavailabilities=unavailabilities,
        wellbeing=wellbeing,
        min_shift_hours=getattr(row, "min_shift_hours", None) or DEFAULT_MIN_SHIFT_HOURS,
        invite_token=row.invite_token,
    )


def _identity_from_company(company: Company) -> RestaurantIdentity:
    linked = company.linked_employee_ids or []
    return RestaurantIdentity(
        id=company.id,
        invite_code=company.invite_code,
        linked_employee_ids=frozenset(linked),
        name=company.name or "",
        legal_context_id=getattr(company, "legal_context_id", None) or "france",
    )


def require_company_restaurant_id(authorization: str | None) -> str:
    require_database()
    token = _bearer_token(authorization)
    with session_scope() as db:
        session = _load_session(db, token)
        if session.kind != "company":
            raise HTTPException(status_code=403, detail=DETAIL_FORBIDDEN)
        return session.restaurant_id


def _claim_email(db: Session, email: str) -> None:
    if db.get(AccountEmail, email) is not None:
        raise HTTPException(status_code=409, detail=DETAIL_EMAIL_TAKEN)
    db.add(AccountEmail(email=email))


def _map_invite_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (InvalidInviteCode, UnknownInviteToken, InviteTargetMismatch)):
        return HTTPException(status_code=400, detail=DETAIL_INVALID_INVITE)
    if isinstance(exc, InviteAlreadyRedeemed):
        return HTTPException(status_code=409, detail=DETAIL_FICHE_LINKED)
    if isinstance(exc, UnknownEmployee):
        return HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    raise exc


def register(body: dict[str, Any]) -> dict[str, Any]:
    require_database()
    kind = body.get("kind")
    email = _normalize_email(body.get("email"))
    password = body.get("password")
    if kind not in {"company", "employee"} or not email or not isinstance(password, str):
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    company_code = _as_optional_str(body, "company_code")
    employee_token = _as_optional_str(body, "employee_token")
    employee_id = _as_optional_str(body, "employee_id")
    if kind == "company":
        if any(key in body for key in ("company_code", "employee_token", "employee_id")):
            raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
        return _register_company(email, password)
    if not company_code:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    if not employee_token and not employee_id:
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    return _register_employee(email, password, company_code, employee_token, employee_id)


def _register_company(email: str, password: str) -> dict[str, Any]:
    identity = RestaurantIdentity(id=_new_id())
    account_id = _new_id()
    try:
        with session_scope() as db:
            _claim_email(db, email)
            db.add(
                Company(
                    id=identity.id,
                    invite_code=identity.invite_code,
                    name="",
                    linked_employee_ids=[],
                    legal_context_id="france",
                    services=[],
                    ladders={"salle": None, "cuisine": None},
                    types=[],
                    typical_week={"salle": None, "cuisine": None},
                    published_cycles={"salle": None, "cuisine": None},
                    live_sandboxes={"salle": None, "cuisine": None},
                )
            )
            db.add(
                RestaurateurAccount(
                    id=account_id,
                    email=email,
                    password_hash=PASSWORD_HASHER.hash(password),
                    restaurant_id=identity.id,
                )
            )
            token = _issue_session(db, kind="company", account_id=account_id, restaurant_id=identity.id)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail=DETAIL_EMAIL_TAKEN) from exc
    return {
        "token": token,
        "me": _me_payload(kind="company", email=email, restaurant_id=identity.id, employee_id=None),
    }


def _register_employee(
    email: str,
    password: str,
    company_code: str,
    employee_token: str | None,
    employee_id: str | None,
) -> dict[str, Any]:
    account_id = _new_id()
    try:
        with session_scope() as db:
            company = db.scalars(select(Company).where(Company.invite_code == company_code)).first()
            if company is None:
                raise InvalidInviteCode("Invalid invite code")
            fiches = list(db.scalars(select(StaffFiche).where(StaffFiche.company_id == company.id)))
            employees = tuple(_fiche_to_employee(row) for row in fiches)
            account, updated = redeem_invite(
                _identity_from_company(company),
                employees,
                company_code,
                account_id,
                employee_id=employee_id,
                employee_token=employee_token,
            )
            _claim_email(db, email)
            company.linked_employee_ids = sorted(updated.linked_employee_ids)
            flag_modified(company, "linked_employee_ids")
            db.add(
                EmployeeAccountRow(
                    id=account.id,
                    email=email,
                    password_hash=PASSWORD_HASHER.hash(password),
                    restaurant_id=account.restaurant_id,
                    employee_id=account.employee_id,
                )
            )
            token = _issue_session(
                db, kind="employee", account_id=account.id, restaurant_id=account.restaurant_id
            )
            me = _me_payload(
                kind="employee",
                email=email,
                restaurant_id=account.restaurant_id,
                employee_id=account.employee_id,
            )
    except HTTPException:
        raise
    except (InvalidInviteCode, UnknownInviteToken, InviteAlreadyRedeemed, InviteTargetMismatch, UnknownEmployee, ValueError) as exc:
        raise _map_invite_error(exc) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail=DETAIL_EMAIL_TAKEN) from exc
    return {"token": token, "me": me}


def login(body: dict[str, Any]) -> dict[str, Any]:
    require_database()
    email = _normalize_email(body.get("email"))
    password = body.get("password")
    if not email or not isinstance(password, str):
        raise HTTPException(status_code=400, detail=DETAIL_INVALID_FIELDS)
    with session_scope() as db:
        restaurateur = db.scalars(select(RestaurateurAccount).where(RestaurateurAccount.email == email)).first()
        employee = db.scalars(select(EmployeeAccountRow).where(EmployeeAccountRow.email == email)).first()
        account = restaurateur or employee
        if account is None:
            raise HTTPException(status_code=401, detail=DETAIL_BAD_CREDENTIALS)
        try:
            PASSWORD_HASHER.verify(account.password_hash, password)
        except VerifyMismatchError:
            raise HTTPException(status_code=401, detail=DETAIL_BAD_CREDENTIALS) from None
        kind = "company" if restaurateur is not None else "employee"
        employee_id = None if restaurateur is not None else employee.employee_id
        token = _issue_session(
            db, kind=kind, account_id=account.id, restaurant_id=account.restaurant_id
        )
        me = _me_payload(
            kind=kind,
            email=account.email,
            restaurant_id=account.restaurant_id,
            employee_id=employee_id,
        )
    return {"token": token, "me": me}


def logout(authorization: str | None) -> None:
    require_database()
    token = _bearer_token(authorization)
    with session_scope() as db:
        row = db.get(AuthSession, _hash_token(token))
        if row is None:
            raise HTTPException(status_code=401, detail=DETAIL_SESSION)
        db.delete(row)


def me(authorization: str | None) -> dict[str, Any]:
    require_database()
    token = _bearer_token(authorization)
    with session_scope() as db:
        session = _load_session(db, token)
        if session.kind == "company":
            account = db.get(RestaurateurAccount, session.account_id)
            if account is None:
                raise HTTPException(status_code=401, detail=DETAIL_SESSION)
            return _me_payload(
                kind="company",
                email=account.email,
                restaurant_id=session.restaurant_id,
                employee_id=None,
            )
        account = db.get(EmployeeAccountRow, session.account_id)
        if account is None:
            raise HTTPException(status_code=401, detail=DETAIL_SESSION)
        return _me_payload(
            kind="employee",
            email=account.email,
            restaurant_id=session.restaurant_id,
            employee_id=account.employee_id,
        )


def list_invites(company_code: str) -> dict[str, Any]:
    require_database()
    with session_scope() as db:
        company = db.scalars(select(Company).where(Company.invite_code == company_code)).first()
        if company is None:
            raise HTTPException(status_code=404, detail=DETAIL_COMPANY_MISSING)
        linked = set(company.linked_employee_ids or [])
        fiches = db.scalars(select(StaffFiche).where(StaffFiche.company_id == company.id)).all()
        employees = [
            {"id": row.id, "name": row.name, "role": row.role, "team": row.team}
            for row in fiches
            if row.id not in linked
        ]
        return {"restaurant_name": company.name, "employees": employees}


def rotate_invite_token(employee_id: str, authorization: str | None) -> dict[str, Any]:
    require_database()
    token = _bearer_token(authorization)
    with session_scope() as db:
        session = _load_session(db, token)
        if session.kind != "company":
            raise HTTPException(status_code=403, detail=DETAIL_FORBIDDEN)
        fiche = db.get(StaffFiche, employee_id)
        if fiche is None or fiche.company_id != session.restaurant_id:
            raise HTTPException(status_code=404, detail=DETAIL_FICHE_MISSING)
        rotated = rotate_employee_invite_token(_fiche_to_employee(fiche))
        fiche.invite_token = rotated.invite_token
        return {"employee_id": fiche.id, "employee_token": rotated.invite_token}
