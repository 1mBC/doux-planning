from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import ForeignKey, String, create_engine
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
