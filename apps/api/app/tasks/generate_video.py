"""Core logic for the video generation Celery task.

The worker calls run_generate_video_task() via asyncio.run().

Pipeline:
  1. Load job + verify hero asset exists
  2. Check per-tenant daily video cap
  3. Upload hero image to fal.ai storage (conditioning frame)
  4. Call FalProvider.generate_video (Kling image-to-video)
  5. Download resulting mp4 bytes
  6. Extract poster frame via ffmpeg subprocess
  7. Upload mp4 + poster to S3
  8. Create GeneratedAsset rows (video_on_model + image_variant poster)
  9. Mark job succeeded
"""
from __future__ import annotations

import asyncio
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory
from app.models.catalog import Product
from app.models.enums import AssetKind, JobStatus, JobType
from app.models.generation import GeneratedAsset, GenerationJob
from app.models.tenancy import Tenant
from app.services import audit
from app.services.fal_client import FalClient
from app.services.providers.base import VideoGenerationRequest
from app.services.providers.fal import FalProvider
from app.services.storage import download_bytes, upload_bytes

_UTC = timezone.utc
_SYSTEM_DAILY_VIDEO_CAP = 10


class VideoCappedError(Exception):
    """Raised when a tenant has exceeded their daily video generation cap."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _check_daily_cap(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Raise VideoCappedError if the tenant has hit their daily video cap."""
    tenant = await db.get(Tenant, tenant_id)
    cap = (tenant.daily_video_cap if tenant and tenant.daily_video_cap is not None
           else _SYSTEM_DAILY_VIDEO_CAP)

    today_start = datetime.now(_UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    count_result = await db.execute(
        select(func.count()).select_from(
            select(GenerationJob).where(
                GenerationJob.tenant_id == tenant_id,
                GenerationJob.type == JobType.video,
                GenerationJob.created_at >= today_start,
            ).subquery()
        )
    )
    count: int = count_result.scalar_one()
    if count >= cap:
        raise VideoCappedError(
            f"Daily video cap of {cap} reached (used {count} today)"
        )


def _extract_poster_frame(video_bytes: bytes) -> bytes:
    """Extract the first frame of an mp4 as JPEG using ffmpeg.

    Runs synchronously — call via asyncio.to_thread.
    """
    with tempfile.TemporaryDirectory() as tmp:
        video_path = Path(tmp) / "input.mp4"
        poster_path = Path(tmp) / "poster.jpg"
        video_path.write_bytes(video_bytes)

        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vframes", "1", "-q:v", "2",
                str(poster_path),
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg poster extraction failed: {result.stderr.decode()[:500]}"
            )
        return poster_path.read_bytes()


# ---------------------------------------------------------------------------
# Main task
# ---------------------------------------------------------------------------

async def run_generate_video_task(job_id: str) -> dict[str, str]:
    """Execute one video generation job end-to-end."""
    async with async_session_factory() as db:
        job = await db.get(GenerationJob, uuid.UUID(job_id))
        if job is None:
            raise ValueError(f"GenerationJob {job_id} not found")

        job.status = JobStatus.running
        job.started_at = datetime.now(_UTC)
        await db.commit()

        try:
            # --- Verify hero asset exists ---
            bundle_version: int = job.params.get("bundle_version", 1)
            hero_result = await db.execute(
                select(GeneratedAsset).where(
                    GeneratedAsset.product_id == job.product_id,
                    GeneratedAsset.tenant_id == job.tenant_id,
                    GeneratedAsset.version == bundle_version,
                    GeneratedAsset.is_hero.is_(True),
                )
            )
            hero = hero_result.scalar_one_or_none()
            if hero is None:
                raise ValueError("No hero asset set — cannot generate video without a hero")

            # --- Check daily cap ---
            await _check_daily_cap(db, job.tenant_id)

            # --- Download hero bytes and upload to fal.ai storage ---
            hero_bytes = download_bytes(hero.storage_key)
            client = FalClient()
            provider = FalProvider(client)
            fal_hero_url = await client.upload_file(hero_bytes, "image/webp", "hero.webp")

            # --- Generate video ---
            motion: str = job.prompt.get("motion", "confident_walk")
            scene: str = job.prompt.get("scene", "studio_white")
            duration_s: int = int(job.prompt.get("duration_seconds", 5))

            gen_result = await provider.generate_video(
                VideoGenerationRequest(
                    source_image_url=fal_hero_url,
                    motion=motion,
                    scene=scene,
                    duration_seconds=duration_s,
                )
            )

            # --- Download mp4 bytes ---
            video_bytes = await client.download_url(gen_result.video_url)

            # --- Extract poster frame in a thread (subprocess/IO) ---
            poster_bytes = await asyncio.to_thread(_extract_poster_frame, video_bytes)

            # --- Upload to S3 ---
            base_prefix = (
                f"tenants/{job.tenant_id}/products/{job.product_id}/v{bundle_version}"
            )
            video_key = f"{base_prefix}/video_{job_id}.mp4"
            poster_key = f"{base_prefix}/video_{job_id}_poster.jpg"

            video_url = upload_bytes(video_key, video_bytes, "video/mp4")
            poster_url = upload_bytes(poster_key, poster_bytes, "image/jpeg")

            # --- Create video asset row ---
            video_asset = GeneratedAsset(
                tenant_id=job.tenant_id,
                product_id=job.product_id,
                job_id=job.id,
                kind=AssetKind.video_on_model,
                storage_key=video_url,
                mime_type="video/mp4",
                duration_ms=gen_result.duration_ms,
                asset_metadata={
                    "motion": motion,
                    "scene": scene,
                    "poster_url": poster_url,
                    "hero_asset_id": str(hero.id),
                    "model_id": gen_result.model_id,
                    "latency_ms": gen_result.latency_ms,
                },
                version=bundle_version,
            )
            db.add(video_asset)
            await db.flush()

            # --- Create poster asset row (image_variant child of video) ---
            poster_asset = GeneratedAsset(
                tenant_id=job.tenant_id,
                product_id=job.product_id,
                job_id=job.id,
                kind=AssetKind.image_variant,
                storage_key=poster_url,
                mime_type="image/jpeg",
                asset_metadata={"role": "video_poster"},
                version=bundle_version,
                parent_asset_id=video_asset.id,
            )
            db.add(poster_asset)

            # --- Finalize job ---
            job.status = JobStatus.succeeded
            job.finished_at = datetime.now(_UTC)
            job.cost_cents = gen_result.cost_cents
            job.model_id = gen_result.model_id
            await db.flush()

            await audit.record(
                db,
                tenant_id=job.tenant_id,
                actor_id=None,
                entity_type="generation_job",
                entity_id=job.id,
                action="succeeded",
                payload={
                    "video_url": video_url,
                    "poster_url": poster_url,
                    "duration_ms": gen_result.duration_ms,
                    "model_id": gen_result.model_id,
                },
            )
            await db.commit()

        except VideoCappedError as exc:
            job.status = JobStatus.failed
            job.error = str(exc)
            job.error_code = "video_cap_exceeded"
            job.finished_at = datetime.now(_UTC)
            await db.commit()
            await _audit_failure(str(job.tenant_id), job_id, exc, "video_cap_exceeded")
            raise

        except Exception as exc:
            job.status = JobStatus.failed
            job.error = str(exc)[:2000]
            job.error_code = type(exc).__name__
            job.finished_at = datetime.now(_UTC)
            await db.commit()
            await _audit_failure(str(job.tenant_id), job_id, exc, job.error_code or "error")
            raise

    return {"job_id": job_id, "status": "succeeded"}


async def _audit_failure(
    tenant_id: str, job_id: str, exc: Exception, error_code: str
) -> None:
    try:
        async with async_session_factory() as db:
            await audit.record(
                db,
                tenant_id=uuid.UUID(tenant_id),
                actor_id=None,
                entity_type="generation_job",
                entity_id=uuid.UUID(job_id),
                action="failed",
                payload={"error": str(exc)[:500], "error_code": error_code},
            )
            await db.commit()
    except Exception:
        pass
