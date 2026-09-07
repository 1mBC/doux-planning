from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable

from sqlalchemy import select

from doux_planning.api.db import GenerateJob, session_scope
from doux_planning.api.generate import DETAIL_NOT_READY, iso_log, persist_maximal_result
from doux_planning.context import TeamNotReady, generate_team
from doux_planning.engine import SEARCH_PROGRESS
from doux_planning.types import Team

GenerateFn = Callable[..., object]
DETAIL_JOB_FAILED = "Le calcul a échoué."
PROGRESS_EVERY_S = 10.0


def _rss_mb() -> float | None:
    try:
        with open("/proc/self/status", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return round(int(line.split()[1]) / 1024.0, 1)
    except OSError:
        return None
    return None


def _heartbeat(stop: threading.Event, started: float, job_id: str, team: str) -> None:
    while not stop.wait(PROGRESS_EVERY_S):
        iso_log(
            "generate progress",
            job_id=job_id,
            team=team,
            elapsed_s=round(time.perf_counter() - started, 1),
            calendars=SEARCH_PROGRESS.get("calendars", 0),
            rss_mb=_rss_mb(),
        )


def _set_job(job_id: str, status: str, error: str | None = None) -> None:
    with session_scope() as db:
        job = db.get(GenerateJob, job_id)
        if job is None:
            return
        job.status = status
        job.error = error


def reclaim_stale_running_jobs() -> int:
    """If the worker died (OOM / restart) mid-job, put `running` back to `queued`."""
    n = 0
    with session_scope() as db:
        jobs = list(db.scalars(select(GenerateJob).where(GenerateJob.status == "running")))
        for job in jobs:
            job.status = "queued"
            job.error = None
            n += 1
            iso_log("job requeued", job_id=job.id, team=job.team, reason="stale_running")
    return n


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
    iso_log("generate start", job_id=job_id, team=team_value, rss_mb=_rss_mb())
    started = time.perf_counter()
    stop = threading.Event()
    beat = threading.Thread(target=_heartbeat, args=(stop, started, job_id, team_value), daemon=True)
    beat.start()
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
    finally:
        stop.set()
        beat.join(timeout=0.2)
    duration = round(time.perf_counter() - started, 3)
    iso_log(
        "generate end",
        job_id=job_id,
        duration_s=duration,
        status="done",
        calendars=SEARCH_PROGRESS.get("calendars", 0),
        rss_mb=_rss_mb(),
    )
    _set_job(job_id, "done")
    return job_id


def run_worker_loop(*, idle_seconds: float = 1.0) -> None:
    iso_log("worker start", pid=os.getpid(), rss_mb=_rss_mb())
    reclaim_stale_running_jobs()
    while True:
        if tick_generate_job() is None:
            time.sleep(idle_seconds)


if __name__ == "__main__":
    run_worker_loop()
