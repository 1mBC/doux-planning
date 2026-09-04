from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from doux_planning.engine import PlanningDraft, Shift, evaluate
from doux_planning.invites import RestaurantIdentity
from doux_planning.planning import PlanningStore, PublishedCycle, RestaurantState
from doux_planning.staff import Employee, Role, Unavailability
from doux_planning.structures import ArrivalWave, DepartureWave, RestaurantHours, ServiceStructure
from doux_planning.types import Team, WellbeingPreference


class ExampleNotFound(KeyError):
    pass


@dataclass(frozen=True)
class DeliveredCycle:
    restaurant_id: str
    employees: tuple[Employee, ...]
    structures: tuple[ServiceStructure, ...]
    hours: RestaurantHours
    assignments: tuple[Shift, ...]


def data_dir() -> Path:
    env = os.environ.get("DOUX_PLANNING_DATA")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "data"


def load_delivered_cycle(example_id: str = "saint-cloud") -> DeliveredCycle:
    path = data_dir() / "examples" / f"{example_id}.json"
    if not path.is_file():
        raise ExampleNotFound(example_id)
    raw = json.loads(path.read_text(encoding="utf-8"))
    restaurant = raw["restaurant"]
    planning = raw["planning"]
    return DeliveredCycle(
        restaurant_id=restaurant["id"],
        employees=tuple(_employee(item) for item in restaurant["employees"]),
        structures=tuple(_structure(item) for item in restaurant["structures"]),
        hours=_hours(restaurant["hours"]),
        assignments=tuple(_shift(item) for item in planning["assignments"]),
    )


def hydrate_delivered_cycle(store: PlanningStore, example_id: str = "saint-cloud") -> RestaurantState:
    delivered = load_delivered_cycle(example_id)
    draft = PlanningDraft(
        employees=delivered.employees,
        structures=delivered.structures,
        hours=delivered.hours,
        assignments=delivered.assignments,
    )
    result = evaluate(draft)
    state = RestaurantState(
        identity=RestaurantIdentity(id=delivered.restaurant_id),
        employees=list(delivered.employees),
        structures=list(delivered.structures),
        hours=delivered.hours,
        cycle=PublishedCycle(id="cycle-1", draft=draft, result=result),
    )
    store.add_restaurant(state)
    store.discard_sandbox(delivered.restaurant_id)
    store.enter_sandbox(delivered.restaurant_id, "cycle")
    return store.get(delivered.restaurant_id)


def _hours(raw: dict[str, Any]) -> RestaurantHours:
    return RestaurantHours(
        mode=raw["mode"],
        services=tuple(raw["services"]),
        closed_weekdays=frozenset(raw.get("closed_weekdays") or ()),
        closed_services=frozenset(raw.get("closed_services") or ()),
    )


def _structure(raw: dict[str, Any]) -> ServiceStructure:
    return ServiceStructure(
        id=raw["id"],
        team=Team(raw["team"]),
        service_id=raw["service_id"],
        weekdays=frozenset(raw["weekdays"]),
        arrivals=tuple(ArrivalWave(wave["time_minutes"], tuple(wave["post_levels"])) for wave in raw["arrivals"]),
        departures=tuple(
            DepartureWave(wave["time_minutes"], tuple(wave["remaining_post_levels"])) for wave in raw["departures"]
        ),
    )


def _employee(raw: dict[str, Any]) -> Employee:
    role = raw["role"]
    team = Team(raw["team"])
    return Employee(
        id=raw["id"],
        name=raw["name"],
        role=Role(role["name"], role["level"], Team(role["team"])),
        team=team,
        contractual_hours_per_week=raw["contractual_hours_per_week"],
        unavailabilities=tuple(_unavailability(item) for item in raw.get("unavailabilities") or ()),
        wellbeing=frozenset(WellbeingPreference(item) for item in raw.get("wellbeing") or ()),
        forced_off_days=frozenset(raw.get("forced_off_days") or ()),
        max_evenings_per_week=raw.get("max_evenings_per_week"),
        max_mornings_per_week=raw.get("max_mornings_per_week"),
        min_shift_hours=raw.get("min_shift_hours", 4.0),
    )


def _unavailability(raw: dict[str, Any]) -> Unavailability:
    return Unavailability(
        weekday=raw.get("weekday"),
        every_morning=bool(raw.get("every_morning")),
        every_evening=bool(raw.get("every_evening")),
        service_id=raw.get("service_id"),
    )


def _shift(raw: dict[str, Any]) -> Shift:
    return Shift(
        employee_id=raw["employee_id"],
        day_index=raw["day_index"],
        weekday=raw["weekday"],
        service_id=raw["service_id"],
        team=Team(raw["team"]),
        start_minutes=raw["start_minutes"],
        end_minutes=raw["end_minutes"],
        post_level=raw["post_level"],
    )
