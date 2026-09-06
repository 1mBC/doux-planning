from __future__ import annotations

import time
from collections.abc import Callable

from sqlalchemy import select

from doux_planning.api.db import GenerateJob, session_scope
from doux_planning.api.generate import DETAIL_NOT_READY, iso_log, persist_maximal_result
from doux_planning.context import TeamNotReady, generate_team
from doux_planning.types import Team

GenerateFn = Callable[..., object]
DETAIL_JOB_FAILED = "Le calcul a échoué."


def _set_job(job_id: str, status: str, error: str | None = None) -> None:
    with session_scope() as db:
        job = db.get(GenerateJob, job_id)
        if job is None:
            return
        job.status = status
        job.error = error


def tick_generate_job(*, generate_team_fn: GenerateFn | None = None) -> str | None:
    generate_fn = generate_team_fn or generate_team
    with session_scope() as db:
        job = db.scalars(
            select(GenerateJob)
            .where(GenerateJob.status == "queued")
            .order_by(GenerateJob.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        ).first()
        if job is None:
            return None
        job.status = "running"
        job_id = job.id
        restaurant_id = job.restaurant_id
        team_value = job.team
    iso_log("job taken", job_id=job_id, team=team_value, restaurant_id=restaurant_id)
    iso_log("generate start", job_id=job_id, team=team_value)
    started = time.perf_counter()
    try:
        persist_maximal_result(restaurant_id, Team(team_value), generate_fn=generate_fn)
    except TeamNotReady:
        duration = round(time.perf_counter() - started, 3)
        iso_log("generate end", job_id=job_id, duration_s=duration, status="failed", error=DETAIL_NOT_READY)
        _set_job(job_id, "failed", DETAIL_NOT_READY)
        return job_id
    except Exception:
        duration = round(time.perf_counter() - started, 3)
        iso_log("generate end", job_id=job_id, duration_s=duration, status="failed", error=DETAIL_JOB_FAILED)
        _set_job(job_id, "failed", DETAIL_JOB_FAILED)
        return job_id
    duration = round(time.perf_counter() - started, 3)
    iso_log("generate end", job_id=job_id, duration_s=duration, status="done")
    _set_job(job_id, "done")
    return job_id


def run_worker_loop(*, idle_seconds: float = 1.0) -> None:
    iso_log("worker start")
    while True:
        if tick_generate_job() is None:
            time.sleep(idle_seconds)


if __name__ == "__main__":
    run_worker_loop()
