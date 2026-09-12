from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from doux_planning.api.app import app
from doux_planning.api.auth import DETAIL_ADMIN, promote_admin_email
from doux_planning.api.db import BenchRun, GenerateLog, reset_engine, session_scope
from doux_planning.bench import BenchOutcome, engine_ref, list_bench_datasets, load_bench_dataset, run_bench
from doux_planning.context import (
    SCORE_WEIGHTS,
    CycleScore,
    ScoreNotes,
    cycle_score,
    empty_restaurant,
    team_ready,
    upsert_employee,
)
from doux_planning.engine import PlanningDraft, _below_role_count, _hours_miss, evaluate
from doux_planning.staff import default_legal_rules
from doux_planning.types import SearchEffort, Team, WEEKDAYS, WarningSeverity
from tests.fixtures import employee


@pytest.fixture(scope="session", autouse=True)
def _postgres_bench_schema():
    if not os.environ.get("DATABASE_URL"):
        return
    from alembic import command
    from alembic.config import Config

    from doux_planning.api.seed import seed_from_files

    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    reset_engine()
    seed_from_files()


def _client() -> TestClient:
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _open_week(type_id: str | None) -> list[dict]:
    return [
        {
            "weekday": day,
            "service_id": "midday",
            "type_id": type_id,
            "closed": False,
        }
        for day in WEEKDAYS
    ]


def _salle_patch(fiche_id: str) -> dict:
    return {
        "name": "Chez Bench",
        "services": ["midday"],
        "ladders": {
            "salle": {
                "roles": [{"name": "RESPONSABLE", "level": 3}, {"name": "EQUIPIER", "level": 1}],
                "substitution_explained": True,
            },
            "cuisine": None,
        },
        "employees": [
            {
                "id": fiche_id,
                "name": "Emma",
                "team": "salle",
                "role": {"name": "RESPONSABLE", "level": 3, "team": "salle"},
                "contractual_hours_per_week": 39,
            }
        ],
        "types": [
            {
                "id": "salle-midi",
                "name": "Salle midi",
                "team": "salle",
                "service_id": "midday",
                "arrivals": [{"time_minutes": 11 * 60, "post_levels": [1]}],
                "departures": [{"time_minutes": 16 * 60, "remaining_post_levels": []}],
            }
        ],
        "typical_week": {"salle": _open_week("salle-midi"), "cuisine": None},
    }


def _stub_run_bench(category, dataset_id, effort):
    notes = ScoreNotes(10.0, 10.0, 10.0, None, 10.0)
    score = CycleScore(notes=notes, weights=dict(SCORE_WEIGHTS), global_score=10.0)
    return BenchOutcome(
        category=category,
        id=dataset_id,
        search_effort=effort,
        duration_seconds=0.0,
        assignments=(),
        warnings=(),
        facts=(),
        expected_facts=(),
        score=score,
        expected_score=score,
        deltas={"couverture": 0.0, "legal": 0.0, "contrat": 0.0, "wellbeing": None, "roles": 0.0, "global": 0.0},
        engine_ref=engine_ref(),
    )


def _count_rows(model) -> int:
    with session_scope() as db:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _insert_bench_run(
    *,
    app_version: str,
    category: str,
    dataset_id: str,
    search_effort: str,
    score_global: float,
    expected_global: float,
) -> str:
    run_id = secrets.token_urlsafe(12)
    with session_scope() as db:
        db.add(
            BenchRun(
                id=run_id,
                created_at=datetime.now(timezone.utc),
                app_version=app_version,
                category=category,
                dataset_id=dataset_id,
                search_effort=search_effort,
                duration_seconds=0.0,
                score={"notes": {}, "global": score_global, "weights": {}},
                expected_score={"notes": {}, "global": expected_global, "weights": {}},
                deltas={"global": score_global - expected_global},
                assignments=[],
                warnings=[],
            )
        )
    return run_id


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


OLD_BENCH_PAIRS = (
    ("tight", "halles"),
    ("clock", "nocturne"),
    ("wishes", "campus"),
    ("ladder", "brigade"),
    ("crafted", "atelier"),
    ("crafted", "rivoli"),
    ("crafted", "marais"),
)

FROZEN_BENCH_ORDER = [
    ("tight", "halles"),
    ("tight", "marche"),
    ("tight", "quai"),
    ("clock", "aube"),
    ("clock", "brasserie"),
    ("clock", "nocturne"),
    ("wishes", "butte"),
    ("wishes", "campus"),
    ("wishes", "canal"),
    ("ladder", "brigade"),
    ("ladder", "jumeaux"),
    ("ladder", "pyramide"),
    ("ladder", "sommet"),
    ("ladder", "trou"),
    ("crafted", "abbesses"),
    ("crafted", "atelier"),
    ("crafted", "auteuil"),
    ("crafted", "bastille"),
    ("crafted", "bourse"),
    ("crafted", "clichy"),
    ("crafted", "concorde"),
    ("crafted", "denfert"),
    ("crafted", "grenelle"),
    ("crafted", "luxembourg"),
    ("crafted", "madeleine"),
    ("crafted", "marais"),
    ("crafted", "monceau"),
    ("crafted", "montparnasse"),
    ("crafted", "nation"),
    ("crafted", "odeon"),
    ("crafted", "opera"),
    ("crafted", "palais"),
    ("crafted", "passy"),
    ("crafted", "pigalle"),
    ("crafted", "republique"),
    ("crafted", "rivoli"),
    ("crafted", "sentier"),
    ("crafted", "temple"),
    ("crafted", "tuileries"),
    ("crafted", "vaugirard"),
    ("hours", "mixte"),
    ("hours", "petits"),
    ("size", "grande"),
    ("size", "studio"),
    ("overqual", "cadres"),
    ("closed", "lundi"),
    ("closed", "samedi"),
    ("shapes", "journee"),
    ("shapes", "triple"),
    ("shapes", "week-we"),
]
FROZEN_BENCH_PAIRS = set(FROZEN_BENCH_ORDER)

EXISTING_THIRTY_PAIRS = (
    ("tight", "halles"),
    ("tight", "marche"),
    ("tight", "quai"),
    ("clock", "aube"),
    ("clock", "brasserie"),
    ("clock", "nocturne"),
    ("wishes", "butte"),
    ("wishes", "campus"),
    ("wishes", "canal"),
    ("ladder", "brigade"),
    ("ladder", "jumeaux"),
    ("ladder", "pyramide"),
    ("ladder", "sommet"),
    ("ladder", "trou"),
    ("crafted", "atelier"),
    ("crafted", "marais"),
    ("crafted", "opera"),
    ("crafted", "republique"),
    ("crafted", "rivoli"),
    ("crafted", "temple"),
    ("hours", "mixte"),
    ("hours", "petits"),
    ("size", "grande"),
    ("size", "studio"),
    ("overqual", "cadres"),
    ("closed", "lundi"),
    ("closed", "samedi"),
    ("shapes", "journee"),
    ("shapes", "triple"),
    ("shapes", "week-we"),
)

NEW_CRAFTED_IDS = (
    "abbesses",
    "auteuil",
    "bastille",
    "bourse",
    "clichy",
    "concorde",
    "denfert",
    "grenelle",
    "luxembourg",
    "madeleine",
    "monceau",
    "montparnasse",
    "nation",
    "odeon",
    "palais",
    "passy",
    "pigalle",
    "sentier",
    "tuileries",
    "vaugirard",
)

CRAFTED_IDS = (
    "abbesses",
    "atelier",
    "auteuil",
    "bastille",
    "bourse",
    "clichy",
    "concorde",
    "denfert",
    "grenelle",
    "luxembourg",
    "madeleine",
    "marais",
    "monceau",
    "montparnasse",
    "nation",
    "odeon",
    "opera",
    "palais",
    "passy",
    "pigalle",
    "republique",
    "rivoli",
    "sentier",
    "temple",
    "tuileries",
    "vaugirard",
)

EXISTING_THIRTY_SHA256 = {
    ("clock", "aube", "context.json"): "c4063db03d64607d451d1632974c3c2ce4a2fca04bcb73cf662cda89061eb2fb",
    ("clock", "aube", "expected.json"): "cf7f08e0778b0734a39776a1467f05af4f56e13eccde123cb6baa641237a0d64",
    ("clock", "brasserie", "context.json"): "1c2d6d603b27e9e7f3673517b45190ccc1f1ebf0eb102cc0af0631d213c81376",
    ("clock", "brasserie", "expected.json"): "7643897c1806f0df1ba672d725b6082b5447bfa72e304056cf2e03d07804e7d7",
    ("clock", "nocturne", "context.json"): "6f0bfff46a31d2b772be37f032d07d4992a490cd8fcd8183ab2653178edc395c",
    ("clock", "nocturne", "expected.json"): "8216bec8eae55a317bca28479d6d33764f2858b7d748449458ee04fc053712a6",
    ("closed", "lundi", "context.json"): "6e14035c047946b20966d32cfb79dcbac96f27329b14aec4f1bbf7c808e5dbc9",
    ("closed", "lundi", "expected.json"): "717d80d663acc2f569e4124187f7bffc0bcbf45de73c49a5f9dce947135d894d",
    ("closed", "samedi", "context.json"): "e1b431830333bbd0466780e9e4881f3cee62880c0bc52a5f18984396fd26bdc3",
    ("closed", "samedi", "expected.json"): "5be4a2811a4b3bb142a8869c21b3bacadaf3c6dc4028d2a50533998d2a4e07cb",
    ("crafted", "atelier", "context.json"): "b234a0d015bfa01e78b07b0403f2aa78838d540ce9fbe0ed82a849c018b650d2",
    ("crafted", "atelier", "expected.json"): "6b820cc5c5f30072cd9bbdabd6968e8bd00a857b3e237153a6407e503c4055c0",
    ("crafted", "marais", "context.json"): "7d1c7bc9d2e13ac4993fd6ecc4f8e1d3d208448e063fc0204a0d8da453135484",
    ("crafted", "marais", "expected.json"): "483a21d14b83cd2eec266b292ca9d752db15eb7ba1cf62129d31a453250d95b5",
    ("crafted", "opera", "context.json"): "15ebeab8f947e51d903c09433392ffa9f0fa314eaa1855df8e0ffdd8d78ca8d8",
    ("crafted", "opera", "expected.json"): "cb127255e2f7d0b93959142c284ae2e291ba3ee70faae225685730383281af5c",
    ("crafted", "republique", "context.json"): "4d4de75c0533f93e0bdaa4710b15e2ff3c7c11d065fc8bb4f83bb4117cf5f01f",
    ("crafted", "republique", "expected.json"): "29d838641bb4ae4ebd6cf444080f47dcbf94d0d0beefa00431c30c6dabdfd2a9",
    ("crafted", "rivoli", "context.json"): "58694356b7074e53e3a46b49611becabd7da54a31b900c4be1ad81690704928b",
    ("crafted", "rivoli", "expected.json"): "54417750205e6213a55efabf1e5c308d1c0787159e213a5737ca71536b8430e5",
    ("crafted", "temple", "context.json"): "9248c9ff9a85452444819c6de1ea0433040c65120b966d944b1232ed85c8b00c",
    ("crafted", "temple", "expected.json"): "17c43479bb984d320e7b619e401631aa05d8f78337e0fbad0f3e38538526be8e",
    ("hours", "mixte", "context.json"): "e4a7ed54c70983f41034d3b2286064ec23f2e522c225df543f6b42303a7a61d3",
    ("hours", "mixte", "expected.json"): "d5546a74fa2e8749e8e0475490282aa1e42313cfc7ce9c856b403aad85ef9062",
    ("hours", "petits", "context.json"): "c80aa2ddbcc599e8a40af73d9f6313707f2602ffe16d8d755613dad7e4e7f728",
    ("hours", "petits", "expected.json"): "a1eef8bb84ab1b02d77cde24ca709159bad1da1690429bb5e4eff289d6a10ada",
    ("ladder", "brigade", "context.json"): "ca5bfb9ed299c707e1f80f558347f07e33e16e204a97ce40a62afd167a8a6446",
    ("ladder", "brigade", "expected.json"): "5276bab330344053a1db45e5d2ef3584662474c9b24c86489d00f1e51633e635",
    ("ladder", "jumeaux", "context.json"): "266ba076c23c186725a67731a46eceaf657a7a238adcf6096e6ac35eb5d20382",
    ("ladder", "jumeaux", "expected.json"): "0e65e63553b8d3c1e4bd35a21ae68391b8456af131f1e4d51596c2ee6e103a5a",
    ("ladder", "pyramide", "context.json"): "c92c7fb5cda370d2773a443157e725a69451a0e3f148d8c449aa6541421eefc7",
    ("ladder", "pyramide", "expected.json"): "dfc766e868ae17868778ff8c3f063e3b0d1e7bd1e977d9f01e7ad989a8b6398b",
    ("ladder", "sommet", "context.json"): "081fc35a446520231d53a2d0b17e5d0c7eb882a6591a73a0ba41763d083468ca",
    ("ladder", "sommet", "expected.json"): "4dfa437114a50aa842abe64350fed278b38067f95aeed575462de97abaf4cd82",
    ("ladder", "trou", "context.json"): "1c8944be13e349b63347f8bf8f576aec6b0af5474bb286b8276042430a677e49",
    ("ladder", "trou", "expected.json"): "bc2aa1aa3f47ffe8949daedbc37ef984b285f52992db92afdbbebb63caa8cdcd",
    ("overqual", "cadres", "context.json"): "68fbefb01aeef6a96c3321410fce7a9b6decb6ffbb2f2e6f61c386f0e77eb5d0",
    ("overqual", "cadres", "expected.json"): "f4a8894052300f3f8cab151b403434904d434520f6b23a8a4772d4513848ff1d",
    ("shapes", "journee", "context.json"): "38e12eca8e5914473d5e41da60c9aa2b7d8e4eb7a7ea4621c928d9744419da0f",
    ("shapes", "journee", "expected.json"): "29e4a2775a20f4128ad21e7ba19d03d084817e871d957c2eae9eacb93593e585",
    ("shapes", "triple", "context.json"): "fda40054eb2c2ed985197ed58f875e151760ffb12b81a262706c62884c070668",
    ("shapes", "triple", "expected.json"): "1d0242ef27d173f97dbdabf7db897da6674e01070d7a933691d6200833f84e5a",
    ("shapes", "week-we", "context.json"): "f7d4b4777bd7c86b82807070c32d6d412698dd27961e45c7628aa2bf475c6ba5",
    ("shapes", "week-we", "expected.json"): "2adb16bfdde8f4c2a9029d5c938d5894e7dc538e4d52e2a6d5629ed5770b4939",
    ("size", "grande", "context.json"): "af884a3b1c76ab22f8c225267ec4bab0145d6a2316d5b309b528f76f3568e6e1",
    ("size", "grande", "expected.json"): "4092bc2dc0bc4bd510f6f1a2fc928ff4e495240def2788f4622c775881c5262c",
    ("size", "studio", "context.json"): "dd8065301d38811a7e57f7ba626ee4d4cacbddfd81ccb06fc37e8d2b6d983fdc",
    ("size", "studio", "expected.json"): "49ae6a6cc0d812890c254f72e09a76a9a69e7511cfcdabf9b751b2afa5077d74",
    ("tight", "halles", "context.json"): "da342624c9100e37da03f8fae01d7a233c20514ae34a10f455a0e0f8cc21de14",
    ("tight", "halles", "expected.json"): "352e35dcf167b9f9cb848a5a7c3d09e971c5078c168450851cdf407609728f76",
    ("tight", "marche", "context.json"): "f42d42fba4abdebd900be8e8e6f9c8c3c53801fa9fb16e6a0d5ca9625ef40842",
    ("tight", "marche", "expected.json"): "ce3d34f6336714693760fd38f55a8e6f0a5a4dd817efa0e1013e9fd7ec1e82e3",
    ("tight", "quai", "context.json"): "97c06e0077af555f2a72fe5a53392ce186826179ca444c0c121316da7d52e59e",
    ("tight", "quai", "expected.json"): "f2764e1ab0af005f4ee9d13a932390b4aa645c2cc157c6f5ea5ce7cada9638aa",
    ("wishes", "butte", "context.json"): "c58238981357553a9c3451942619bbb86f3b4c8f05e3de13b9e42d3f92b1a51d",
    ("wishes", "butte", "expected.json"): "ef304b622b1253197a173f649078330c24bd09edc41e08bbca0a96ff44905ba5",
    ("wishes", "campus", "context.json"): "926dd3439fe5923b77f23e6aee10899d5887ecc40a5ed564317757c3720f433e",
    ("wishes", "campus", "expected.json"): "0368a227937a993b474518669e5946e1d25b014f60b59adc2370745fc2582e59",
    ("wishes", "canal", "context.json"): "8f6f4757acedbcb7e5c005ec27933e89be1c5e572ac1ba1a0824a73fde2baa42",
    ("wishes", "canal", "expected.json"): "af4b9a0f91adecde833e9ce7680eedc3b585e07d351b413f880586332c9c8179",
}


def test_list_bench_datasets_has_fifty_salle_games():
    listed = list_bench_datasets()
    assert [(item.category, item.id) for item in listed] == FROZEN_BENCH_ORDER
    assert {(item.category, item.id) for item in listed} == FROZEN_BENCH_PAIRS
    assert len(listed) == 50
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


def test_existing_thirty_dataset_files_unchanged():
    root = Path(__file__).resolve().parents[1] / "data" / "bench"
    for (category, dataset_id, filename), digest in EXISTING_THIRTY_SHA256.items():
        path = root / category / dataset_id / filename
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    listed = {(item.category, item.id) for item in list_bench_datasets()}
    assert set(EXISTING_THIRTY_PAIRS) <= listed
    assert set(OLD_BENCH_PAIRS) <= listed
    for category, dataset_id in EXISTING_THIRTY_PAIRS:
        dataset = load_bench_dataset(category, dataset_id)
        assert dataset.id == dataset_id
        assert dataset.expected


def test_new_datasets_cover_morning_multi_type_and_l6():
    morning = []
    multi = []
    level_six = []
    for dataset_id in NEW_CRAFTED_IDS:
        dataset = load_bench_dataset("crafted", dataset_id)
        if "morning" in dataset.state.hours.services:
            morning.append(dataset_id)
        by_service: dict[str, set[str]] = {}
        for kind in dataset.state.service_types:
            by_service.setdefault(kind.service_id, set()).add(kind.id)
        if any(len(ids) >= 2 for ids in by_service.values()):
            multi.append(dataset_id)
        roles = [
            role
            for ladder in dataset.state.ladders.values()
            if ladder is not None
            for role in ladder.roles
        ]
        if any(role.level >= 6 for role in roles):
            level_six.append(dataset_id)
    assert len(morning) >= 4
    assert len(multi) >= 4
    assert len(level_six) >= 4


@pytest.mark.parametrize("dataset_id", CRAFTED_IDS)
def test_crafted_expected_global_at_least_nine_five(dataset_id):
    dataset = load_bench_dataset("crafted", dataset_id)
    result = _expected_result(dataset)
    score = cycle_score(
        PlanningDraft(
            employees=tuple(person for person in dataset.state.employees if person.team == Team.SALLE),
            structures=tuple(item for item in dataset.state.structures if item.team == Team.SALLE),
            hours=dataset.state.hours,
            assignments=dataset.expected,
            legal_rules=default_legal_rules(),
        ),
        result,
    )
    assert score.global_score is not None
    assert score.global_score >= 9.5


@pytest.mark.parametrize("dataset_id", NEW_CRAFTED_IDS)
def test_new_crafted_expected_zero_hours_miss_and_below_role(dataset_id):
    dataset = load_bench_dataset("crafted", dataset_id)
    staff = tuple(person for person in dataset.state.employees if person.team == Team.SALLE)
    structures = tuple(item for item in dataset.state.structures if item.team == Team.SALLE)
    draft = PlanningDraft(
        employees=staff,
        structures=structures,
        hours=dataset.state.hours,
        assignments=dataset.expected,
        legal_rules=default_legal_rules(),
    )
    assert _hours_miss(draft, dataset.expected) == 0.0
    assert _below_role_count(draft, dataset.expected) == 0


def test_run_bench_tight_halles_minimal_has_scores_and_deltas():
    outcome = run_bench("tight", "halles", SearchEffort.MINIMAL)
    assert outcome.category == "tight"
    assert outcome.id == "halles"
    assert outcome.search_effort == SearchEffort.MINIMAL
    assert outcome.score is not None
    assert outcome.expected_score is not None
    assert set(outcome.deltas) == {"couverture", "legal", "contrat", "wellbeing", "roles", "global"}
    assert outcome.facts
    assert outcome.expected_facts
    assert all(
        fact.severity is not WarningSeverity.INTERDIT
        for fact in outcome.expected_facts
        if fact.polarity == "miss"
    )
    assert any(
        fact.polarity == "hit" and fact.kind in {"post_held", "role_gap"}
        for fact in (*outcome.facts, *outcome.expected_facts)
    )
    assert outcome.engine_ref == "core-3"


def test_engine_ref_is_core_three():
    assert engine_ref() == "core-3"


def test_run_bench_atelier_minimal_fewer_saturday_evening_empties():
    outcome = run_bench("crafted", "atelier", SearchEffort.MINIMAL)
    assert outcome.engine_ref == "core-3"
    saturday_evening_empties = [
        fact
        for fact in outcome.facts
        if fact.polarity == "miss"
        and fact.kind == "empty_post"
        and fact.payload.get("weekday") == "saturday"
        and fact.payload.get("service_id") == "evening"
    ]
    assert len(saturday_evening_empties) < 4


def test_run_bench_marais_minimal_hard_max_evenings():
    outcome = run_bench("crafted", "marais", SearchEffort.MINIMAL)
    assert outcome.engine_ref == "core-3"
    assert not any(fact.polarity == "miss" and fact.kind == "max_evenings" for fact in outcome.facts)
    assert not any(shift.employee_id == "e" and shift.service_id == "evening" for shift in outcome.assignments)


def test_run_bench_rivoli_minimal_expected_zero_interdit():
    outcome = run_bench("crafted", "rivoli", SearchEffort.MINIMAL)
    assert all(
        fact.severity is not WarningSeverity.INTERDIT
        for fact in outcome.expected_facts
        if fact.polarity == "miss"
    )


def test_run_bench_campus_minimal_runs():
    outcome = run_bench("wishes", "campus", SearchEffort.MINIMAL)
    assert outcome.engine_ref == "core-3"
    assert outcome.search_effort == SearchEffort.MINIMAL


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


def test_admin_bench_without_database_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    client = _client()
    listed = client.get("/v1/admin/bench/datasets", headers=_bearer("x"))
    assert listed.status_code == 503
    assert listed.json()["detail"] == "Base indisponible."
    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_admin_bench_http_runs_jobs_compare_and_resto_generate(monkeypatch):
    from doux_planning.api.worker import tick_bench_job

    client = _client()
    password = "password1"
    email = f"bench-{secrets.token_hex(4)}@example.com"
    registered = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": email, "password": password},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]
    headers = _bearer(token)
    other = client.post(
        "/v1/auth/register",
        json={"kind": "company", "email": f"user-{secrets.token_hex(4)}@example.com", "password": password},
    )
    assert other.status_code == 201
    forbidden = client.post(
        "/v1/admin/bench/run",
        headers=_bearer(other.json()["token"]),
        json={"scope": "dataset", "category": "tight", "dataset_id": "halles", "search_effort": "minimal"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == DETAIL_ADMIN

    monkeypatch.setenv("ADMIN_EMAIL", email)
    promote_admin_email()
    assert client.get("/v1/me", headers=headers).json()["admin"] is True

    datasets = client.get("/v1/admin/bench/datasets", headers=headers)
    assert datasets.status_code == 200
    assert datasets.json()["engine_ref"] == datasets.json()["app_version"] == "core-3"
    assert len(datasets.json()["datasets"]) == 50
    assert {(item["category"], item["id"]) for item in datasets.json()["datasets"]} == FROZEN_BENCH_PAIRS

    logs_before = _count_rows(GenerateLog)
    runs_before = _count_rows(BenchRun)
    posted = client.post(
        "/v1/admin/bench/run",
        headers=headers,
        json={"scope": "dataset", "category": "tight", "dataset_id": "halles", "search_effort": "minimal"},
    )
    assert posted.status_code == 200
    summaries = posted.json()["runs"]
    assert len(summaries) == 1
    first = summaries[0]
    assert first["category"] == "tight"
    assert first["dataset_id"] == "halles"
    assert first["search_effort"] == "minimal"
    assert first["engine_ref"] == first["app_version"] == "core-3"
    assert "notes" in first["score"] and "resumes" not in first["score"]
    assert "assignments" not in first
    assert _count_rows(GenerateLog) == logs_before
    assert _count_rows(BenchRun) == runs_before + 1

    listed = client.get("/v1/admin/bench/runs", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == first["id"] for item in listed.json()["runs"])
    halles = client.get("/v1/admin/bench/runs", headers=headers, params={"category": "tight", "dataset_id": "halles"})
    assert halles.status_code == 200
    assert all(item["dataset_id"] == "halles" for item in halles.json()["runs"])

    compared = client.get("/v1/admin/bench/compare/tight/halles/minimal", headers=headers)
    assert compared.status_code == 200
    assert compared.json()["id"] == first["id"]
    assert compared.json()["employees"]
    assert all("name" in person and "id" in person for person in compared.json()["employees"])
    model_facts = compared.json()["model"]["facts"]
    manual_facts = compared.json()["manual"]["facts"]
    assert any(item.get("polarity") == "hit" for item in model_facts)
    assert any(item.get("polarity") == "hit" for item in manual_facts)
    assert "facts" not in compared.json()
    assert "assignments" not in compared.json()
    assert "expected" not in compared.json()
    assert "warnings" not in compared.json()
    assert "resumes" not in compared.json()["score"]
    assert "resumes" not in compared.json()["model"]["score"]

    exported = client.get(
        "/v1/admin/bench/export",
        headers=headers,
        params={"scope": "dataset", "category": "tight", "dataset_id": "halles"},
    )
    assert exported.status_code == 200
    pack = exported.json()
    assert pack["export_version"] == 1
    assert pack["kind"] == "bench-pack"
    assert pack["scope"] == "dataset"
    assert pack["engine_ref"] == pack["app_version"] == "core-3"
    assert pack["exported_at"]
    assert len(pack["datasets"]) == 1
    halles_pack = pack["datasets"][0]
    assert halles_pack["category"] == "tight"
    assert halles_pack["id"] == "halles"
    assert halles_pack["context"]
    assert all("invite_token" not in person for person in halles_pack["context"]["employees"])
    assert halles_pack["manual"]["facts"]
    assert halles_pack["efforts"][0]["search_effort"] == "minimal"
    assert halles_pack["efforts"][0]["run_id"] == first["id"]
    assert halles_pack["efforts"][0]["engine_ref"] == "core-3"
    assert "below_manuel" in halles_pack["efforts"][0]
    assert halles_pack["efforts"][0]["model"]["facts"]

    below = client.get("/v1/admin/bench/export", headers=headers, params={"scope": "below_manuel"})
    assert below.status_code == 200
    assert below.json()["kind"] == "bench-pack"
    assert below.json()["scope"] == "below_manuel"
    assert isinstance(below.json()["datasets"], list)

    forbidden_export = client.get(
        "/v1/admin/bench/export",
        headers=_bearer(other.json()["token"]),
        params={"scope": "below_manuel"},
    )
    assert forbidden_export.status_code == 403
    assert forbidden_export.json()["detail"] == DETAIL_ADMIN

    by_id = client.get(f"/v1/admin/bench/runs/{first['id']}", headers=headers)
    assert by_id.status_code == 200
    assert by_id.json()["id"] == first["id"]
    assert by_id.json()["engine_ref"] == by_id.json()["app_version"] == "core-3"
    assert "model" in by_id.json() and "manual" in by_id.json()
    assert any(item.get("polarity") == "hit" for item in by_id.json()["model"]["facts"])
    assert any(item.get("polarity") == "hit" for item in by_id.json()["manual"]["facts"])
    assert "assignments" not in by_id.json()
    assert "facts" not in by_id.json()
    missing_run = client.get("/v1/admin/bench/runs/unknown-run", headers=headers)
    assert missing_run.status_code == 404

    _insert_bench_run(
        app_version="core-1",
        category="tight",
        dataset_id="halles",
        search_effort="minimal",
        score_global=1.0,
        expected_global=8.0,
    )
    versions = client.get("/v1/admin/bench/versions", headers=headers)
    assert versions.status_code == 200
    assert versions.json()["engine_ref"] == "core-3"
    assert "core-3" in versions.json()["engine_refs"]
    assert "core-1" in versions.json()["engine_refs"]
    assert "0.27.0" not in versions.json()["engine_refs"]
    halles_row = next(item for item in versions.json()["datasets"] if item["id"] == "halles")
    assert set(halles_row["by_ref"]) >= {"core-3", "core-1"}
    assert halles_row["by_ref"]["core-3"]["minimal"]["run_id"] == first["id"]
    assert halles_row["by_ref"]["core-1"]["minimal"]["run_id"]
    assert halles_row["by_ref"]["core-1"]["minimal"]["run_id"] != first["id"]
    assert set(halles_row["by_ref"]["core-3"]) == {"minimal", "optimized", "maximal"}
    current_compare = client.get("/v1/admin/bench/compare/tight/halles/minimal", headers=headers)
    assert current_compare.status_code == 200
    assert current_compare.json()["id"] == first["id"]
    assert current_compare.json()["engine_ref"] == "core-3"

    legacy_id = _insert_bench_run(
        app_version="0.27.0",
        category="clock",
        dataset_id="nocturne",
        search_effort="minimal",
        score_global=4.0,
        expected_global=7.0,
    )
    legacy = client.get(f"/v1/admin/bench/runs/{legacy_id}", headers=headers)
    assert legacy.status_code == 200
    assert legacy.json()["engine_ref"] == legacy.json()["app_version"] == "core-0"
    merged = client.get("/v1/admin/bench/versions", headers=headers)
    assert "0.27.0" not in merged.json()["engine_refs"]
    assert "core-0" in merged.json()["engine_refs"]

    forbidden_versions = client.get("/v1/admin/bench/versions", headers=_bearer(other.json()["token"]))
    assert forbidden_versions.status_code == 403
    assert forbidden_versions.json()["detail"] == DETAIL_ADMIN
    forbidden_run = client.get(f"/v1/admin/bench/runs/{first['id']}", headers=_bearer(other.json()["token"]))
    assert forbidden_run.status_code == 403
    assert forbidden_run.json()["detail"] == DETAIL_ADMIN

    first_maximal = client.post(
        "/v1/admin/bench/run",
        headers=headers,
        json={"scope": "dataset", "category": "tight", "dataset_id": "halles", "search_effort": "maximal"},
    )
    assert first_maximal.status_code == 202
    second_maximal = client.post(
        "/v1/admin/bench/run",
        headers=headers,
        json={"scope": "dataset", "category": "tight", "dataset_id": "halles", "search_effort": "maximal"},
    )
    assert second_maximal.status_code == 202
    assert first_maximal.json()["job_ids"] == second_maximal.json()["job_ids"]
    assert len(first_maximal.json()["job_ids"]) == 1

    queued = client.post(
        "/v1/admin/bench/run",
        headers=headers,
        json={"scope": "all", "search_effort": "maximal"},
    )
    assert queued.status_code == 202
    assert queued.json()["status"] == "queued"
    job_ids = queued.json()["job_ids"]
    assert len(job_ids) == 50
    runs_before_tick = _count_rows(BenchRun)
    remaining = set(job_ids)
    for _ in range(60):
        if not remaining:
            break
        job_id = tick_bench_job(run_bench_fn=_stub_run_bench)
        assert job_id is not None
        remaining.discard(job_id)
    assert not remaining
    assert _count_rows(GenerateLog) == logs_before
    run_ids = []
    for job_id in job_ids:
        done = client.get(f"/v1/admin/bench/jobs/{job_id}", headers=headers)
        assert done.status_code == 200
        assert done.json()["status"] == "done"
        assert done.json()["run_id"]
        run_ids.append(done.json()["run_id"])
    assert len(set(run_ids)) == 50
    assert _count_rows(BenchRun) >= runs_before_tick + 50
    crafted = client.post(
        "/v1/admin/bench/run",
        headers=headers,
        json={"scope": "category", "category": "crafted", "search_effort": "maximal"},
    )
    assert crafted.status_code == 202
    assert crafted.json()["status"] == "queued"
    assert len(crafted.json()["job_ids"]) == 26
    hours = client.post(
        "/v1/admin/bench/run",
        headers=headers,
        json={"scope": "category", "category": "hours", "search_effort": "maximal"},
    )
    assert hours.status_code == 202
    assert len(hours.json()["job_ids"]) == 2
    maximal = client.get("/v1/admin/bench/compare/tight/halles/maximal", headers=headers)
    assert maximal.status_code == 200
    assert maximal.json()["search_effort"] == "maximal"
    assert "model" in maximal.json() and "manual" in maximal.json()

    fiche_id = f"emma-{secrets.token_hex(4)}"
    patched = client.patch("/v1/context", headers=headers, json=_salle_patch(fiche_id))
    assert patched.status_code == 200
    generated = client.post(
        "/v1/generate",
        headers=headers,
        json={"team": "salle", "search_effort": "minimal"},
    )
    assert generated.status_code == 200
    assert generated.json()["published"]["salle"]["versions"]["minimal"]["assignments"]
    assert _count_rows(GenerateLog) == logs_before + 1

    example = client.get("/v1/examples/saint-cloud")
    assert example.status_code == 200
    assert example.json()["planning"]["stats"]["assignments"] == 92
