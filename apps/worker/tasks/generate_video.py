"""Video generation Celery task."""
from __future__ import annotations

import asyncio

from celery_app import celery_app


@celery_app.task(
    name="tasks.generate_video",
    bind=True,
    max_retries=0,
    acks_late=True,
)
def generate_video(self, job_id: str) -> dict:  # type: ignore[type-arg]
    from app.tasks.generate_video import run_generate_video_task

    return asyncio.run(run_generate_video_task(job_id))
