from doux_planning.bench import list_bench_datasets, load_bench_dataset, run_bench
from doux_planning.context import empty_restaurant, team_ready, upsert_employee
from doux_planning.engine import PlanningDraft, evaluate
from doux_planning.staff import default_legal_rules
from doux_planning.types import SearchEffort, Team, WarningSeverity
from tests.fixtures import employee


def _expected_result(dataset):
    staff = tuple(person for person in dataset.state.employees if person.team == Team.SALLE)
    structures = tuple(item for item in dataset.state.structures if item.team == Team.SALLE)
    draft = PlanningDraft(
        employees=staff,
        structures=structures,
        hours=dataset.state.hours,
        assignments=dataset.expected,
        legal_rules=default_legal_rules(),
    )
    return evaluate(draft)


def test_list_bench_datasets_has_four_salle_games():
    listed = list_bench_datasets()
    assert {(item.category, item.id) for item in listed} == {
        ("tight", "halles"),
        ("clock", "nocturne"),
        ("wishes", "campus"),
        ("ladder", "brigade"),
    }
    assert all(item.name and item.challenge_fr for item in listed)


def test_load_halles_is_salle_ready_not_cuisine():
    dataset = load_bench_dataset("tight", "halles")
    assert team_ready(dataset.state, Team.SALLE)
    assert not team_ready(dataset.state, Team.CUISINE)
    assert all(person.invite_token != person.id for person in dataset.state.employees)


def test_expected_assignments_have_zero_interdit():
    for item in list_bench_datasets():
        dataset = load_bench_dataset(item.category, item.id)
        result = _expected_result(dataset)
        assert result.of_severity(WarningSeverity.INTERDIT) == ()


def test_run_bench_tight_halles_minimal_has_scores_and_deltas():
    outcome = run_bench("tight", "halles", SearchEffort.MINIMAL)
    assert outcome.category == "tight"
    assert outcome.id == "halles"
    assert outcome.search_effort == SearchEffort.MINIMAL
    assert outcome.score is not None
    assert outcome.expected_score is not None
    assert set(outcome.deltas) == {"couverture", "legal", "contrat", "wellbeing", "roles", "global"}


def test_run_bench_leaves_live_restaurant_unchanged():
    state = empty_restaurant("resto-live")
    upsert_employee(state, employee("Sam", "commis", hours=35, employee_id="sam"))
    before = (
        state.identity,
        tuple(state.employees),
        tuple(state.structures),
        state.hours,
        state.cycle,
        dict(state.published_cycles),
        dict(state.live_sandboxes),
        tuple(state.service_types),
        state.typical_week,
        dict(state.ladders),
        state.company_services,
    )
    run_bench("tight", "halles", SearchEffort.MINIMAL)
    after = (
        state.identity,
        tuple(state.employees),
        tuple(state.structures),
        state.hours,
        state.cycle,
        dict(state.published_cycles),
        dict(state.live_sandboxes),
        tuple(state.service_types),
        state.typical_week,
        dict(state.ladders),
        state.company_services,
    )
    assert after == before
    assert state.published_cycles == {Team.SALLE: None, Team.CUISINE: None}
