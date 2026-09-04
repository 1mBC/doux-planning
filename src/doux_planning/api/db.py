from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, create_engine
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


class StaffFiche(Base):
    __tablename__ = "staff_fiches"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    team: Mapped[str] = mapped_column(String, nullable=False)
    invite_token: Mapped[str] = mapped_column(String, unique=True, nullable=False)


class AccountEmail(Base):
    __tablename__ = "account_emails"

    email: Mapped[str] = mapped_column(String, primary_key=True)


class RestaurateurAccount(Base):
    __tablename__ = "restaurateur_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(ForeignKey("account_emails.email"), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    restaurant_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), unique=True, nullable=False)


class EmployeeAccountRow(Base):
    __tablename__ = "employee_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(ForeignKey("account_emails.email"), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    restaurant_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(ForeignKey("staff_fiches.id"), unique=True, nullable=False)


class AuthSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (UniqueConstraint("token_hash"),)

    token_hash: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    account_id: Mapped[str] = mapped_column(String, nullable=False)
    restaurant_id: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def database_url() -> str | None:
    return os.environ.get("DATABASE_URL") or None


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
