from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


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


def example_payload(example_id: str) -> dict[str, Any]:
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
