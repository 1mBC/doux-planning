import json

from doux_planning.context import empty_restaurant, seed_example_context, team_ready, week_label_scheme
from doux_planning.engine import EngineResult, PlanningDraft
from doux_planning.hydrate import data_dir
from doux_planning.planning import PublishedCycle
from doux_planning.structures import RestaurantHours
from doux_planning.types import ServiceName, Team


def _fake_published(state) -> PublishedCycle:
    hours = state.hours or RestaurantHours.multi_service(ServiceName.MIDDAY.value)
    draft = PlanningDraft(employees=(), structures=(), hours=hours, assignments=())
    return PublishedCycle(id="fake-cycle", draft=draft, result=EngineResult(assignments=(), warnings=()))


def test_seed_empty_restaurant_from_saint_cloud():
    state = seed_example_context(empty_restaurant("co-1"))
    assert state.identity.id == "co-1"
    assert state.identity.name == ""
    assert state.identity.legal_context_id == "france"
    assert any(person.team == Team.SALLE for person in state.employees)
    assert {person.id for person in state.employees} >= {"diane", "theo"}
    assert state.hours is not None
    assert tuple(state.hours.services) == (ServiceName.MIDDAY.value, ServiceName.EVENING.value)
    assert state.company_services == (ServiceName.MIDDAY.value, ServiceName.EVENING.value)
    assert state.service_types
    assert state.typical_week is not None
    assert state.typical_week.cells
    assert state.structures
    assert team_ready(state, Team.SALLE)
    assert not team_ready(state, Team.CUISINE)
    assert Team.CUISINE not in state.ladders
    assert state.published_cycles == {Team.SALLE: None, Team.CUISINE: None}
    assert state.live_sandboxes == {Team.SALLE: None, Team.CUISINE: None}
    assert state.cycle is None
    assert state.accounts == []
    assert all(person.invite_token and person.invite_token != person.id for person in state.employees)
    assert week_label_scheme(state) == "ab"


def test_seed_again_clears_published_and_keeps_example_fiches():
    state = seed_example_context(empty_restaurant("co-1"))
    first_tokens = {person.id: person.invite_token for person in state.employees}
    state.published_cycles[Team.SALLE] = _fake_published(state)
    state.cycle = state.published_cycles[Team.SALLE]
    seeded = seed_example_context(state)
    assert seeded.published_cycles == {Team.SALLE: None, Team.CUISINE: None}
    assert seeded.cycle is None
    assert {person.id for person in seeded.employees} >= {"diane", "theo", "emma"}
    assert all(person.invite_token != person.id for person in seeded.employees)
    assert {person.id: person.invite_token for person in seeded.employees} != first_tokens
    assert team_ready(seeded, Team.SALLE)
    assert not team_ready(seeded, Team.CUISINE)


def test_saint_cloud_snapshot_has_live_french_recap():
    planning = json.loads((data_dir() / "examples" / "saint-cloud.json").read_text(encoding="utf-8"))["planning"]
    assert len(planning["assignments"]) == 92
    assert planning["stats"]["assignments"] == 92
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
    assert {col["key"] for col in planning["wish_cols"]}.isdisjoint({"we1j", "weA", "weB", "soirs", "repos2", "coupures"})
    assert "legal_cols" not in planning
    assert any(item["code"] == "contract_hours" and "contrat" in item["message"] for item in planning["warnings"])
    assert any(
        item["code"] == "consecutive_rest_days" and "pas deux repos" in item["message"]
        for item in planning["warnings"]
    )
