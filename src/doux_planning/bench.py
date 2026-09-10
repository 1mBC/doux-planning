from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from doux_planning.context import (
    CycleScore,
    cycle_recap_from_draft,
    empty_restaurant,
    expand_typical_week,
    set_restaurant_name,
    set_role_ladder,
    set_services,
    set_typical_week,
    upsert_employee,
    upsert_service_type,
)
from doux_planning.engine import PlanningDraft, Shift, evaluate, generate_cycle
from doux_planning.warnings import ScoreFact
from doux_planning.hydrate import _employee, _shift, data_dir
from doux_planning.planning import RestaurantState
from doux_planning.staff import Role, RoleLadder, default_legal_rules
from doux_planning.structures import ArrivalWave, DepartureWave, RestaurantHours, ServiceType, TypicalWeek, TypicalWeekCell
from doux_planning.types import SearchEffort, Team, WEEKDAYS

BENCH_CATEGORY_ORDER = ("tight", "clock", "wishes", "ladder", "crafted")
NOTE_KEYS = ("couverture", "legal", "contrat", "wellbeing", "roles")


class UnknownBenchDataset(KeyError):
    def __init__(self, category: str, dataset_id: str) -> None:
        self.category = category
        self.dataset_id = dataset_id
        super().__init__(f"{category}/{dataset_id}")


@dataclass(frozen=True)
class BenchListing:
    category: str
    id: str
    name: str
    challenge_fr: str


@dataclass
class BenchDataset:
    category: str
    id: str
    name: str
    challenge_fr: str
    state: RestaurantState
    expected: tuple[Shift, ...]


@dataclass(frozen=True)
class BenchOutcome:
    category: str
    id: str
    search_effort: SearchEffort
    duration_seconds: float
    assignments: tuple[Shift, ...]
    warnings: tuple
    facts: tuple[ScoreFact, ...]
    expected_facts: tuple[ScoreFact, ...]
    score: CycleScore
    expected_score: CycleScore
    deltas: dict[str, float | None]
    engine_ref: str


def bench_dir() -> Path:
    return data_dir() / "bench"


def engine_ref() -> str:
    return (bench_dir() / "VERSION").read_text(encoding="utf-8").strip()


def list_bench_datasets() -> list[BenchListing]:
    root = bench_dir()
    found: dict[tuple[str, str], BenchListing] = {}
    if not root.is_dir():
        return []
    for category_dir in root.iterdir():
        if not category_dir.is_dir():
            continue
        category = category_dir.name
        for dataset_dir in category_dir.iterdir():
            if not dataset_dir.is_dir():
                continue
            listing = _listing_if_complete(dataset_dir, category)
            if listing is None:
                continue
            found[(listing.category, listing.id)] = listing
    return [
        found[key]
        for key in sorted(
            found,
            key=lambda item: (
                BENCH_CATEGORY_ORDER.index(item[0]) if item[0] in BENCH_CATEGORY_ORDER else len(BENCH_CATEGORY_ORDER),
                item[1],
            ),
        )
    ]


def load_bench_dataset(category: str, dataset_id: str) -> BenchDataset:
    folder = bench_dir() / category / dataset_id
    context_path = folder / "context.json"
    expected_path = folder / "expected.json"
    if not context_path.is_file() or not expected_path.is_file():
        raise UnknownBenchDataset(category, dataset_id)
    raw = json.loads(context_path.read_text(encoding="utf-8"))
    expected_raw = json.loads(expected_path.read_text(encoding="utf-8"))
    state = _load_context(category, dataset_id, raw)
    expected = tuple(_shift(item) for item in expected_raw["assignments"])
    return BenchDataset(
        category=category,
        id=dataset_id,
        name=raw["name"],
        challenge_fr=raw["challenge_fr"],
        state=state,
        expected=expected,
    )


def run_bench(category: str, dataset_id: str, effort: SearchEffort) -> BenchOutcome:
    dataset = load_bench_dataset(category, dataset_id)
    state = dataset.state
    published_before = dict(state.published_cycles)
    structures = tuple(item for item in expand_typical_week(state) if item.team == Team.SALLE)
    employees = tuple(person for person in state.employees if person.team == Team.SALLE)
    draft = PlanningDraft(
        employees=employees,
        structures=structures,
        hours=state.hours,
        legal_rules=default_legal_rules(),
        search_effort=effort,
    )
    started = time.perf_counter()
    result = generate_cycle(draft, effort)
    duration = time.perf_counter() - started
    if state.published_cycles != published_before:
        raise RuntimeError("run_bench must not write published_cycles")
    recap = cycle_recap_from_draft(draft.with_assignments(result.assignments), result)
    expected_draft = draft.with_assignments(dataset.expected)
    expected_result = evaluate(expected_draft)
    expected_recap = cycle_recap_from_draft(expected_draft, expected_result)
    return BenchOutcome(
        category=category,
        id=dataset_id,
        search_effort=effort,
        duration_seconds=duration,
        assignments=result.assignments,
        warnings=result.warnings,
        facts=recap.facts,
        expected_facts=expected_recap.facts,
        score=recap.score,
        expected_score=expected_recap.score,
        deltas=_score_deltas(recap.score, expected_recap.score),
        engine_ref=engine_ref(),
    )


def _listing_if_complete(dataset_dir: Path, category: str) -> BenchListing | None:
    context_path = dataset_dir / "context.json"
    expected_path = dataset_dir / "expected.json"
    if not context_path.is_file() or not expected_path.is_file():
        return None
    raw = json.loads(context_path.read_text(encoding="utf-8"))
    return BenchListing(
        category=category,
        id=dataset_dir.name,
        name=raw["name"],
        challenge_fr=raw["challenge_fr"],
    )


def _load_context(category: str, dataset_id: str, raw: dict) -> RestaurantState:
    hours_raw = raw["hours"]
    services = list(hours_raw["services"])
    closed = frozenset(hours_raw.get("closed_weekdays") or ())
    state = empty_restaurant(f"bench-{category}-{dataset_id}")
    set_restaurant_name(state, raw["name"])
    set_services(state, services)
    state.hours = RestaurantHours.multi_service(*services, closed_weekdays=closed)
    roles_by_team: dict[Team, list[Role]] = {}
    for item in raw["roles"]:
        team = Team(item["team"])
        roles_by_team.setdefault(team, []).append(Role(item["name"], item["level"], team))
    for team, roles in roles_by_team.items():
        set_role_ladder(state, RoleLadder(team, tuple(roles), substitution_explained=True))
    for item in raw["types"]:
        upsert_service_type(state, _service_type(item))
    set_typical_week(state, _derived_typical_week(raw["roles"], hours_raw, raw["types"]))
    for item in raw["employees"]:
        upsert_employee(state, _employee(item))
    state.structures = expand_typical_week(state)
    return state


def _service_type(raw: dict) -> ServiceType:
    return ServiceType(
        id=raw["id"],
        name=raw["name"],
        team=Team(raw["team"]),
        service_id=raw["service_id"],
        arrivals=tuple(ArrivalWave(wave["time_minutes"], tuple(wave["post_levels"])) for wave in raw["arrivals"]),
        departures=tuple(
            DepartureWave(wave["time_minutes"], tuple(wave["remaining_post_levels"])) for wave in raw["departures"]
        ),
    )


def _derived_typical_week(roles: list[dict], hours_raw: dict, types: list[dict]) -> TypicalWeek:
    teams: list[Team] = []
    for item in roles:
        team = Team(item["team"])
        if team not in teams:
            teams.append(team)
    type_by: dict[tuple[Team, str], str] = {}
    for item in types:
        type_by[(Team(item["team"]), item["service_id"])] = item["id"]
    closed_days = set(hours_raw.get("closed_weekdays") or ())
    cells: list[TypicalWeekCell] = []
    for team in teams:
        for service_id in hours_raw["services"]:
            type_id = type_by[(team, service_id)]
            for weekday in WEEKDAYS:
                closed = weekday in closed_days
                cells.append(
                    TypicalWeekCell(
                        weekday=weekday,
                        service_id=service_id,
                        type_id=None if closed else type_id,
                        closed=closed,
                        team=team,
                    )
                )
    return TypicalWeek(cells=tuple(cells))


def _note_delta(generated: float | None, expected: float | None) -> float | None:
    if generated is None or expected is None:
        return None
    return generated - expected


def _score_deltas(score, expected_score) -> dict[str, float | None]:
    deltas = {
        key: _note_delta(getattr(score.notes, key), getattr(expected_score.notes, key)) for key in NOTE_KEYS
    }
    deltas["global"] = _note_delta(score.global_score, expected_score.global_score)
    return deltas
