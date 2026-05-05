from __future__ import annotations

import os
import sys

# Make apps/api importable so tasks can use app.* without duplicating code
_api_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api")
if _api_path not in sys.path:
    sys.path.insert(0, _api_path)

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "catalog_ai_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.generate_image", "tasks.generate_video"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=int(os.getenv("WORKER_CONCURRENCY", "4")),
)
