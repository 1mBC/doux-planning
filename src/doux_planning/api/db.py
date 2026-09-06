from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, ForeignKeyConstraint, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

_engine: Engine | None = None
_SessionFactory: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    pass


class LegalContext(Base):
    __tablename__ = "legal_contexts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    document: Mapped[dict] = mapped_column(JSONB, nullable=False)


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    legal_context: Mapped[str] = mapped_column(ForeignKey("legal_contexts.id"), nullable=False)
    document: Mapped[dict] = mapped_column(JSONB, nullable=False)


class ExampleSnapshot(Base):
    __tablename__ = "example_snapshots"

    example_id: Mapped[str] = mapped_column(String, primary_key=True)
    restaurant_id: Mapped[str] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    restaurant: Mapped[dict] = mapped_column(JSONB, nullable=False)
    planning: Mapped[dict] = mapped_column(JSONB, nullable=False)


class SandboxSession(Base):
    __tablename__ = "sandbox_sessions"

    restaurant_id: Mapped[str] = mapped_column(String, primary_key=True)
    document: Mapped[dict] = mapped_column(JSONB, nullable=False)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    invite_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    linked_employee_ids: Mapped[list] = mapped_column(JSONB, nullable=False)
    legal_context_id: Mapped[str] = mapped_column(String, nullable=False, default="france")
    services: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    ladders: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    types: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    typical_week: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    published_cycles: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=lambda: {"salle": None, "cuisine": None}
    )
    live_sandboxes: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=lambda: {"salle": None, "cuisine": None}
    )
    hours: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class StaffFiche(Base):
    __tablename__ = "staff_fiches"

    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), primary_key=True)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    team: Mapped[str] = mapped_column(String, nullable=False)
    invite_token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    contractual_hours_per_week: Mapped[float] = mapped_column(Float, nullable=False, default=35)
    min_shift_hours: Mapped[float] = mapped_column(Float, nullable=False, default=4)
    unavailabilities: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    wellbeing: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class AccountEmail(Base):
    __tablename__ = "account_emails"

    email: Mapped[str] = mapped_column(String, primary_key=True)


class RestaurateurAccount(Base):
    __tablename__ = "restaurateur_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(ForeignKey("account_emails.email"), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    restaurant_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), unique=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class GenerateLog(Base):
    __tablename__ = "generate_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    restaurant_name: Mapped[str] = mapped_column(String, nullable=False)
    team: Mapped[str] = mapped_column(String, nullable=False)
    warnings: Mapped[list] = mapped_column(JSONB, nullable=False)


class EmployeeAccountRow(Base):
    __tablename__ = "employee_accounts"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "employee_id", name="employee_accounts_restaurant_employee_key"),
        ForeignKeyConstraint(
            ["restaurant_id", "employee_id"],
            ["staff_fiches.company_id", "staff_fiches.id"],
            name="employee_accounts_restaurant_employee_fkey",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(ForeignKey("account_emails.email"), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    restaurant_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(String, nullable=False)


class AuthSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (UniqueConstraint("token_hash"),)

    token_hash: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    account_id: Mapped[str] = mapped_column(String, nullable=False)
    restaurant_id: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def database_url() -> str | None:
    raw = os.environ.get("DATABASE_URL") or None
    if not raw:
        return None
    return normalize_database_url(raw)


def get_engine() -> Engine:
    global _engine, _SessionFactory
    url = database_url()
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    if _engine is None:
        _engine = create_engine(url)
        _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def reset_engine() -> None:
    global _engine, _SessionFactory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionFactory = None


@contextmanager
def session_scope() -> Iterator[Session]:
    get_engine()
    assert _SessionFactory is not None
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
