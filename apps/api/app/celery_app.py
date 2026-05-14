"""Celery worker application.

Run from apps/api/:
    celery -A app.celery_app worker --pool=solo -Q image_queue,video_queue --loglevel=info
"""
from __future__ import annotations

import asyncio

from celery import Celery

from app.core.config import settings

celery_app = Celery(broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_expires=3600,
)


@celery_app.task(name="tasks.generate_image", queue="image_queue")
def generate_image_task(job_id: str) -> dict:
    from app.tasks.generate_image import run_generate_image_task  # noqa: PLC0415
    return asyncio.run(run_generate_image_task(job_id))


@celery_app.task(name="tasks.generate_video", queue="video_queue")
def generate_video_task(job_id: str) -> dict:
    from app.tasks.generate_video import run_generate_video_task  # noqa: PLC0415
    return asyncio.run(run_generate_video_task(job_id))
