"""Minimal Celery app used by the API to dispatch tasks.

The API process never runs workers — it only sends messages to the broker.
"""
from celery import Celery

from app.core.config import settings

_celery = Celery(broker=settings.redis_url, backend=settings.redis_url)
_celery.conf.update(task_serializer="json", accept_content=["json"])


def enqueue_generate_image(job_id: str) -> None:
    _celery.send_task("tasks.generate_image", args=[job_id], queue="image_queue")


def enqueue_generate_video(job_id: str) -> None:
    _celery.send_task("tasks.generate_video", args=[job_id], queue="video_queue")
