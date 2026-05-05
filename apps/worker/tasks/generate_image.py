"""Image generation Celery task.

Thin dispatcher: receives job_id, runs the async core logic from apps/api,
returns a summary dict that Celery stores in the result backend.
"""
from __future__ import annotations

import asyncio

from celery_app import celery_app


@celery_app.task(
    name="tasks.generate_image",
    bind=True,
    max_retries=0,  # No automatic retries — failures are recorded in DB
    acks_late=True,  # Only ack after task completes
)
def generate_image(self, job_id: str) -> dict:  # type: ignore[type-arg]
    from app.tasks.generate_image import run_generate_image_task

    return asyncio.run(run_generate_image_task(job_id))
