import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.storage import LocalStorage
from app.db import SessionLocal
from app.jobs.handlers import HANDLERS
from app.models.job import Job
from app.models.request import MeasureRequest

TICK_SECONDS = 30


def _now_naive_utc() -> datetime:
    # bind as naive UTC so the comparison matches what SQLite actually stored
    # for a DateTime(timezone=True) column (it drops tzinfo on write)
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def run_due_jobs() -> None:
    now = _now_naive_utc()
    async with SessionLocal() as db:
        result = await db.execute(
            select(Job).where(Job.run_at <= now, Job.done_at.is_(None))
        )
        jobs = result.scalars().all()
        for job in jobs:
            handler = HANDLERS.get(job.kind)
            if handler is None:
                continue
            try:
                await handler(job, db)
                job.done_at = now
            except Exception as exc:  # belt-and-braces: one bad job must not kill the poller
                job.attempts += 1
                job.last_error = str(exc)[:255]
        await db.commit()


async def sweep_overdue_photos() -> None:
    """Belt-and-braces pass, independent of the jobs table: deletes any photo
    whose measure_requests.photo_delete_at has already passed, even if its
    job row was somehow lost. Runs at startup and every tick."""
    now = _now_naive_utc()
    async with SessionLocal() as db:
        result = await db.execute(
            select(MeasureRequest).where(
                MeasureRequest.photo_delete_at <= now,
                MeasureRequest.photo_path.is_not(None),
            )
        )
        storage = LocalStorage()
        for request in result.scalars().all():
            storage.delete(request.photo_path)
            request.photo_path = None
        await db.commit()


async def _poll_loop() -> None:
    await sweep_overdue_photos()  # startup sweep for anything overdue while down
    while True:
        await asyncio.sleep(TICK_SECONDS)
        try:
            await run_due_jobs()
            await sweep_overdue_photos()
        except asyncio.CancelledError:
            raise
        except Exception:
            continue


async def start_job_runner() -> asyncio.Task:
    return asyncio.create_task(_poll_loop())


async def stop_job_runner(task: asyncio.Task | None) -> None:
    if task is None:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
