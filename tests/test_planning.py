import os
from datetime import date, timedelta
from pathlib import Path

import pytest

from doux_planning.engine import PlanningDraft, Shift, evaluate
from doux_planning.invites import RestaurantIdentity, redeem_invite
from doux_planning.planning import CalendarWeek, PlanningStore, PublishedCycle, RestaurantState, instantiate_week
from doux_planning.structures import RestaurantHours, StructuralEditRequiresCycleSandbox, brasserie_template
from doux_planning.types import ServiceName, Team
from tests.fixtures import kitchen_midday_structure, kitchen_staff, employee


def _shift(employee_id="chef-a", day=0, weekday="monday") -> Shift:
    return Shift(
        employee_id=employee_id,
        day_index=day,
        weekday=weekday,
        service_id=ServiceName.MIDDAY.value,
        team=Team.CUISINE,
        start_minutes=10 * 60,
        end_minutes=16 * 60,
        post_level=4,
    )


def _state(today: date | None = None) -> RestaurantState:
    identity = RestaurantIdentity(id="resto-1", invite_code="join-me")
    hours = RestaurantHours.multi_service(ServiceName.MIDDAY.value)
    staff = list(kitchen_staff())
    structures = [kitchen_midday_structure()]
    draft = PlanningDraft(employees=tuple(staff), structures=tuple(structures), hours=hours, assignments=(_shift(),))
    return RestaurantState(
        identity=identity,
        employees=staff,
        structures=structures,
        hours=hours,
        cycle=PublishedCycle(id="cycle-1", draft=draft, result=evaluate(draft)),
        today=today or date(2026, 9, 7),
    )


def test_clean_future_week_follows_cycle_and_past_is_kept():
    store = PlanningStore()
    state = _state(today=date(2026, 9, 10))
    past = instantiate_week(state.cycle.result.assignments, date(2026, 8, 31), "past", "cycle-1")
    past.assignments = (_shift(day=0, weekday="monday"),)
    future = CalendarWeek(week_id="future", week_start=date(2026, 9, 14), cycle_id="cycle-1")
    state.weeks = {"past": past, "future": future}
    store.add_restaurant(state)
    sandbox = store.enter_sandbox("resto-1", "cycle")
    new_shift = _shift(employee_id="chef-b")
    store.apply_edit("resto-1", (new_shift,))
    store.publish_sandbox("resto-1", acknowledged=frozenset())
    assert store.get("resto-1").weeks["past"].assignments[0].employee_id == "chef-a"
    assert store.get("resto-1").weeks["future"].assignments[0].employee_id == "chef-b"


def test_week_publish_stores_intents():
    store = PlanningStore()
    state = _state()
    week = instantiate_week(state.cycle.result.assignments, date(2026, 9, 14), "w12", "cycle-1")
    state.weeks = {"w12": week}
    store.add_restaurant(state)
    store.enter_sandbox("resto-1", "week", "w12")
    store.record_unavailability("resto-1", "chef-a", "monday")
    store.publish_sandbox("resto-1", acknowledged=frozenset())
    stored = store.get("resto-1").weeks["w12"]
    assert stored.intents
    assert stored.intents[0].employee_id == "chef-a"
    assert all(shift.employee_id != "chef-a" or shift.weekday != "monday" for shift in stored.assignments)


def test_sandbox_target_locked_and_persisted():
    store = PlanningStore()
    state = _state()
    state.weeks = {"w12": instantiate_week(state.cycle.result.assignments, date(2026, 9, 14), "w12", "cycle-1")}
    store.add_restaurant(state)
    first = store.enter_sandbox("resto-1", "week", "w12")
    again = store.enter_sandbox("resto-1", "cycle")
    assert again.target == "week"
    assert again.week_id == "w12"
    store.apply_edit("resto-1", (_shift(employee_id="sam", weekday="tuesday"),))
    store.publish_sandbox("resto-1", acknowledged=frozenset())
    assert store.get("resto-1").cycle.result.assignments[0].employee_id == "chef-a"
    assert store.get("resto-1").weeks["w12"].assignments[0].employee_id == "sam"


def test_structural_edit_requires_cycle_sandbox():
    store = PlanningStore()
    state = _state()
    state.weeks = {"w12": instantiate_week(state.cycle.result.assignments, date(2026, 9, 14), "w12", "cycle-1")}
    store.add_restaurant(state)
    store.enter_sandbox("resto-1", "week", "w12")
    try:
        store.edit_structure("resto-1", [kitchen_midday_structure()])
        raise AssertionError("expected StructuralEditRequiresCycleSandbox")
    except StructuralEditRequiresCycleSandbox:
        pass
    store.discard_sandbox("resto-1")
    store.enter_sandbox("resto-1", "cycle")
    tuesday = kitchen_midday_structure({"tuesday"})
    earlier = [
        kitchen_midday_structure({"monday", "wednesday", "thursday", "friday", "saturday", "sunday"}),
        tuesday,
    ]
    # Open Tuesday earlier: first arrival 9:00
    from doux_planning.structures import ArrivalWave, DepartureWave, ServiceStructure

    early_tuesday = ServiceStructure(
        id="cuisine-midday-tue",
        team=Team.CUISINE,
        service_id=ServiceName.MIDDAY.value,
        weekdays=frozenset({"tuesday"}),
        arrivals=(
            ArrivalWave(9 * 60, (4,)),
            ArrivalWave(11 * 60, (2, 2)),
            ArrivalWave(11 * 60 + 30, (1,)),
        ),
        departures=(
            DepartureWave(14 * 60 + 30, (4, 2)),
            DepartureWave(15 * 60, (4,)),
            DepartureWave(16 * 60, ()),
        ),
    )
    store.edit_structure(
        "resto-1",
        [
            kitchen_midday_structure({"monday", "wednesday", "thursday", "friday", "saturday", "sunday"}),
            early_tuesday,
        ],
    )
    future = CalendarWeek(week_id="future", week_start=date(2026, 9, 14), cycle_id="old")
    store.get("resto-1").weeks["future"] = future
    store.publish_sandbox("resto-1", acknowledged=frozenset())
    published = store.get("resto-1").cycle.draft.structure_for(Team.CUISINE, ServiceName.MIDDAY.value, "tuesday")
    assert published is not None
    assert published.arrivals[0].time_minutes == 9 * 60


def test_dirty_week_needs_reconciliation():
    store = PlanningStore()
    state = _state()
    dirty = instantiate_week(state.cycle.result.assignments, date(2026, 9, 14), "w12", "cycle-1")
    dirty.intents = []
    store.add_restaurant(state)
    state.weeks = {"w12": dirty}
    store.enter_sandbox("resto-1", "week", "w12")
    store.record_unavailability("resto-1", "chef-a", "tuesday")
    store.publish_sandbox("resto-1", acknowledged=frozenset())
    store.enter_sandbox("resto-1", "cycle")
    store.apply_edit("resto-1", (_shift(employee_id="chef-b"),))
    recos = store.publish_sandbox("resto-1", acknowledged=frozenset())
    assert recos
    assert recos[0].week_id == "w12"
    assert any(intent.weekday == "tuesday" for intent in store.get("resto-1").weeks["w12"].intents)
    store.accept_reconciliation("resto-1", "w12", recos[0].proposal)
    tuesday_shifts = [
        shift
        for shift in store.get("resto-1").weeks["w12"].assignments
        if shift.weekday == "tuesday" and shift.employee_id == "chef-a"
    ]
    assert tuesday_shifts == []


def test_employee_cannot_see_sandbox_draft():
    store = PlanningStore()
    state = _state()
    week = instantiate_week(state.cycle.result.assignments, date(2026, 9, 14), "w12", "cycle-1")
    state.weeks = {"w12": week}
    store.add_restaurant(state)
    account = redeem_invite(state.identity, "join-me", "acc-1", "chef-a")
    before = store.employee_view("resto-1", account)
    store.enter_sandbox("resto-1", "cycle")
    store.apply_edit("resto-1", (_shift(employee_id="sam"),))
    after = store.employee_view("resto-1", account)
    assert before == after
    assert all(shift.employee_id == "chef-a" for shift in after)


@pytest.fixture(scope="session", autouse=True)
def _postgres_example_schema():
    if not os.environ.get("DATABASE_URL"):
        return
    from alembic import command
    from alembic.config import Config

    from doux_planning.api.db import reset_engine
    from doux_planning.api.seed import seed_from_files

    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    reset_engine()
    seed_from_files()


def _assert_saint_cloud_contract(body: dict) -> None:
    assert body["example"] == "saint-cloud"
    assert set(body) >= {"example", "legal", "restaurant", "planning"}
    assert body["legal"]["id"] == "france"
    assert body["legal"]["kind"] == "legal_context"
    assert "label" in body["legal"]
    assert {rule["id"] for rule in body["legal"]["rules"]} == {
        "rest_between_days",
        "weekly_rest_days",
        "max_coupure",
        "max_daily_cuisine",
        "max_daily_salle",
        "max_weekly_hours",
    }
    for rule in body["legal"]["rules"]:
        assert "id" in rule and "label_fr" in rule and "severity" in rule
    assert "legal_rules" not in body["restaurant"]
    assert body["restaurant"]["id"] == "saint-cloud"
    assert body["restaurant"]["name"] == "Saint-Cloud"
    assert body["restaurant"]["team"] == "salle"
    assert "hours" in body["restaurant"]
    employees = body["restaurant"]["employees"]
    assert employees
    for person in employees:
        assert {"id", "name", "role", "team"} <= set(person)
        assert {"name", "level", "team"} <= set(person["role"])
    planning = body["planning"]
    for key in (
        "search_effort",
        "calendars",
        "seconds",
        "assignments",
        "warnings",
        "stats",
        "legal_rows",
        "wish_cols",
        "wish_rows",
    ):
        assert key in planning
    assert planning["search_effort"] == "optimized"
    assert planning["stats"] == {
        "assignments": 92,
        "empty": 0,
        "interdit": 0,
        "below_role": 43,
        "hours": {
            "assigned": 416.0,
            "contracted": 494.0,
            "percent": 84,
        },
        "wellbeing": {
            "held": 21,
            "total": 21,
        },
    }
    assert len(planning["assignments"]) == 92
    assert len(planning["warnings"]) == 14
    theo = next(
        item
        for item in planning["assignments"]
        if item["employee_id"] == "theo" and item["day_index"] == 0 and item["service_id"] == "midday"
    )
    assert theo["start_minutes"] == 660
    assert theo["end_minutes"] == 960
    assert theo["duration_hours"] == 5.0
    diane = next(row for row in planning["wish_rows"] if row["employee_id"] == "diane")
    assert diane["cells"]["contrat"] == {"ok": False, "text": "30h · 29h / 39h"}


def test_saint_cloud_example_separates_france_legal():
    from doux_planning.api.examples import example_payload

    payload = example_payload("saint-cloud")
    _assert_saint_cloud_contract(payload)


def test_saint_cloud_example_route():
    from fastapi.testclient import TestClient

    from doux_planning.api.app import app

    client = TestClient(app)
    missing = client.get("/v1/examples/inconnu")
    assert missing.status_code == 404
    response = client.get("/v1/examples/saint-cloud")
    assert response.status_code == 200
    _assert_saint_cloud_contract(response.json())


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_saint_cloud_seed_restaurant_points_at_france():
    from doux_planning.api.db import Restaurant, session_scope

    with session_scope() as session:
        row = session.get(Restaurant, "saint-cloud")
        assert row is not None
        assert row.legal_context == "france"
        assert "legal_rules" not in row.document


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_saint_cloud_postgres_payload_matches_files():
    from doux_planning.api.examples import example_payload_from_db, example_payload_from_files

    assert example_payload_from_db("saint-cloud") == example_payload_from_files("saint-cloud")


def test_brasserie_template_is_editable():
    template = brasserie_template(Team.CUISINE, ServiceName.MIDDAY.value, {"monday"})
    assert template.arrivals
    assert template.departures
    edited = template.with_weekdays({"monday", "tuesday"})
    assert edited.weekdays == frozenset({"monday", "tuesday"})
    assert template.weekdays == frozenset({"monday"})
