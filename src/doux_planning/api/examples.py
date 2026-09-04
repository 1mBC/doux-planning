from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from doux_planning.api.db import ExampleSnapshot, LegalContext, Restaurant, database_url, session_scope


class ExampleNotFound(KeyError):
    pass


class LegalContextNotFound(KeyError):
    pass


def data_dir() -> Path:
    env = os.environ.get("DOUX_PLANNING_DATA")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[3] / "data"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _plain(value: Any) -> Any:
    return json.loads(json.dumps(value))


def load_legal(legal_id: str) -> dict[str, Any]:
    path = data_dir() / "legal" / f"{legal_id}.json"
    if not path.is_file():
        raise LegalContextNotFound(legal_id)
    return _read_json(path)


def load_example_file(example_id: str) -> dict[str, Any]:
    path = data_dir() / "examples" / f"{example_id}.json"
    if not path.is_file():
        raise ExampleNotFound(example_id)
    return _read_json(path)


def example_payload_from_files(example_id: str) -> dict[str, Any]:
    raw = load_example_file(example_id)
    legal_id = raw["legal_context"]
    restaurant = dict(raw["restaurant"])
    restaurant.pop("legal_rules", None)
    return {
        "example": raw["id"],
        "legal": load_legal(legal_id),
        "restaurant": restaurant,
        "planning": raw["planning"],
    }


def example_payload_from_db(example_id: str) -> dict[str, Any]:
    with session_scope() as session:
        snapshot = session.get(ExampleSnapshot, example_id)
        if snapshot is None:
            raise ExampleNotFound(example_id)
        restaurant_row = session.get(Restaurant, snapshot.restaurant_id)
        if restaurant_row is None:
            raise ExampleNotFound(example_id)
        legal = session.get(LegalContext, restaurant_row.legal_context)
        if legal is None:
            raise LegalContextNotFound(restaurant_row.legal_context)
        restaurant = _plain(snapshot.restaurant)
        if isinstance(restaurant, dict):
            restaurant.pop("legal_rules", None)
        return {
            "example": snapshot.example_id,
            "legal": _plain(legal.document),
            "restaurant": restaurant,
            "planning": _plain(snapshot.planning),
        }


def example_payload(example_id: str) -> dict[str, Any]:
    if database_url():
        return example_payload_from_db(example_id)
    return example_payload_from_files(example_id)
