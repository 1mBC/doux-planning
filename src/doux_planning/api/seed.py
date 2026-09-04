from __future__ import annotations

from sqlalchemy.orm.attributes import flag_modified

from doux_planning.api.db import ExampleSnapshot, LegalContext, Restaurant, session_scope
from doux_planning.api.examples import load_example_file, load_legal


def seed_from_files() -> None:
    """Copy frozen data/ files into Postgres. Does not run the solver."""
    with session_scope() as session:
        _seed_legal(session, "france")
        _seed_example(session, "saint-cloud")


def _seed_legal(session, legal_id: str) -> None:
    document = load_legal(legal_id)
    row = session.get(LegalContext, legal_id)
    if row is None:
        session.add(LegalContext(id=legal_id, document=document))
        return
    row.document = document
    flag_modified(row, "document")


def _seed_example(session, example_id: str) -> None:
    raw = load_example_file(example_id)
    legal_id = raw["legal_context"]
    restaurant = dict(raw["restaurant"])
    restaurant.pop("legal_rules", None)
    restaurant_id = restaurant["id"]
    existing = session.get(Restaurant, restaurant_id)
    if existing is None:
        session.add(
            Restaurant(
                id=restaurant_id,
                name=restaurant["name"],
                legal_context=legal_id,
                document=restaurant,
            )
        )
    else:
        existing.document = restaurant
        flag_modified(existing, "document")
    snapshot = session.get(ExampleSnapshot, example_id)
    if snapshot is None:
        session.add(
            ExampleSnapshot(
                example_id=example_id,
                restaurant_id=restaurant_id,
                restaurant=restaurant,
                planning=raw["planning"],
            )
        )
        return
    snapshot.restaurant_id = restaurant_id
    snapshot.restaurant = restaurant
    snapshot.planning = raw["planning"]
    flag_modified(snapshot, "restaurant")
    flag_modified(snapshot, "planning")
