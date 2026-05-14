"""Core logic for the image generation Celery task.

The worker imports and calls run_generate_image_task() via asyncio.run().
All DB, S3, and provider operations live here so the worker stays a thin dispatcher.

Post-processing:
  After each primary on-model image is generated, Pillow crops are produced for
  every additional required aspect ratio in the brand kit.  Each crop becomes an
  image_variant GeneratedAsset row linked to the primary via parent_asset_id.

Model spec:
  Every primary asset stores model_height_cm, model_height_imperial, and
  garment_size_worn in asset_metadata so the studio UI can display them.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from io import BytesIO

from langfuse import Langfuse
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery import enqueue_generate_video
from app.core.config import settings
from app.core.database import async_session_factory
from app.models.catalog import Product
from app.models.enums import AssetKind, JobStatus, JobType, ProductStatus
from app.models.generation import AssetBundle, GeneratedAsset, GenerationJob
from app.services import audit
from app.services.fal_client import FalClient
from app.services.providers.base import ImageGenerationRequest, SegmentationRequest
from app.services.providers.fal import FalProvider
from app.services.storage import download_bytes, object_exists, upload_bytes

_UTC = timezone.utc

_DEFAULT_ASPECT_RATIOS = ["4:5", "1:1", "9:16"]

# Body-type → sample size mapping for model spec display
_BODY_TYPE_SIZE: dict[str, str] = {
    "petite": "XS",
    "slim": "S",
    "athletic": "M",
    "hourglass": "M",
    "curvy": "L",
    "tall-slim": "M",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_langfuse() -> Langfuse | None:
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    return None


def _cm_to_imperial(height_cm: int) -> str:
    """Convert centimetres to feet-and-inches string, e.g. 178 → 5'10\"."""
    total_inches = height_cm / 2.54
    feet = int(total_inches // 12)
    inches = int(round(total_inches % 12))
    if inches == 12:
        feet += 1
        inches = 0
    return f"{feet}'{inches}\""


def _estimate_garment_size(persona: dict, product_attributes: dict) -> str:
    """Return a display-only garment size for the model spec."""
    size_range: str = product_attributes.get("size_range", "")
    if size_range:
        # "XS-XL" → "XS"; "M" → "M"
        return size_range.split("-")[0].strip()
    return _BODY_TYPE_SIZE.get(persona.get("body_type", ""), "M")


def _crop_to_aspect(img_bytes: bytes, target_ratio: str) -> bytes:
    """Crop image bytes to the target aspect ratio using upper-center bias.

    Generates at the full width of the source so faces/heads are preserved.
    Upper-center bias ensures we keep the top of the frame (head) and cut
    from the bottom rather than centering, which would crop the head.
    """
    ratio_w, ratio_h = map(int, target_ratio.split(":"))
    target_float = ratio_w / ratio_h

    with Image.open(BytesIO(img_bytes)) as img:
        img = img.convert("RGB")
        src_w, src_h = img.size
        src_float = src_w / src_h

        if abs(src_float - target_float) < 0.01:
            buf = BytesIO()
            img.save(buf, format="WEBP", quality=90)
            return buf.getvalue()

        if src_float < target_float:
            # Source is taller → reduce height, keep width
            crop_w = src_w
            crop_h = int(crop_w * ratio_h / ratio_w)
        else:
            # Source is wider → reduce width, keep height
            crop_h = src_h
            crop_w = int(crop_h * ratio_w / ratio_h)

        x_start = (src_w - crop_w) // 2
        # Upper-center bias: blend 30% top, 70% center
        center_y = (src_h - crop_h) // 2
        y_start = max(0, int(center_y * 0.7))

        cropped = img.crop((x_start, y_start, x_start + crop_w, y_start + crop_h))
        buf = BytesIO()
        cropped.save(buf, format="WEBP", quality=90)
        return buf.getvalue()


async def _ensure_segmented(
    product: Product,
    provider: FalProvider,
    lf_trace: object | None,
) -> str:
    """Return a fal.ai-accessible URL for the segmented garment.

    Runs BiRefNet the first time; on subsequent calls downloads the cached
    segmented image from S3 and re-uploads it to fal.ai storage.
    """
    seg_key = (
        f"tenants/{product.tenant_id}/products/{product.id}/source_segmented.webp"
    )

    if object_exists(seg_key):
        seg_bytes = download_bytes(seg_key)
        fal_url = await provider._client.upload_file(seg_bytes, "image/webp", "segmented.webp")
        return fal_url

    # First time — segment from source
    source_bytes = download_bytes(product.source_image_key)  # type: ignore[arg-type]
    fal_source_url = await provider._client.upload_file(
        source_bytes, "image/jpeg", "source.jpg"
    )

    span_ctx = None
    if lf_trace is not None:
        span_ctx = lf_trace.span(name="segment_garment")  # type: ignore[union-attr]

    seg_result = await provider.segment_garment(SegmentationRequest(source_url=fal_source_url))

    if span_ctx is not None:
        span_ctx.end(
            output={"segmented_url": seg_result.segmented_url},
            metadata={
                "model_id": seg_result.model_id,
                "latency_ms": seg_result.latency_ms,
                "cost_cents": seg_result.cost_cents,
            },
        )

    seg_bytes = await provider._client.download_url(seg_result.segmented_url)
    upload_bytes(seg_key, seg_bytes, "image/webp")

    return seg_result.segmented_url


async def _create_aspect_variants(
    db: AsyncSession,
    primary_asset: GeneratedAsset,
    img_bytes: bytes,
    primary_ar: str,
    all_required_ars: list[str],
    job: GenerationJob,
    bundle_version: int,
) -> None:
    """Pillow-crop the primary image into each additional required aspect ratio.

    Each crop is stored as a separate image_variant GeneratedAsset row.
    """
    for ar in all_required_ars:
        if ar == primary_ar:
            continue

        crop_bytes = _crop_to_aspect(img_bytes, ar)

        with Image.open(BytesIO(crop_bytes)) as crop_img:
            crop_w, crop_h = crop_img.size

        variant_key = (
            f"tenants/{job.tenant_id}/products/{job.product_id}"
            f"/v{bundle_version}/img_{job.id}_{ar.replace(':', 'x')}.webp"
        )
        variant_url = upload_bytes(variant_key, crop_bytes, "image/webp")

        variant = GeneratedAsset(
            tenant_id=job.tenant_id,
            product_id=job.product_id,
            job_id=job.id,
            kind=AssetKind.image_variant,
            storage_key=variant_url,
            width=crop_w,
            height=crop_h,
            mime_type="image/webp",
            asset_metadata={
                **primary_asset.asset_metadata,
                "aspect_ratio": ar,
                "parent_aspect_ratio": primary_ar,
            },
            version=bundle_version,
            parent_asset_id=primary_asset.id,
        )
        db.add(variant)


async def _check_bundle_complete(db: AsyncSession, job: GenerationJob) -> None:
    """After an image job finishes, check if the whole bundle is done.

    When all IMAGE jobs are terminal:
    - Sets product → ready_for_review if at least one succeeded.
    - If ALL image jobs succeeded → try to enqueue the video job.
      - Hero exists → enqueue immediately.
      - No hero yet → set bundle.video_pending_hero = True.
    """
    bundle_id_str: str | None = job.params.get("bundle_id")
    if not bundle_id_str:
        return

    result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.product_id == job.product_id,
            GenerationJob.tenant_id == job.tenant_id,
        )
    )
    all_jobs = result.scalars().all()
    bundle_jobs = [j for j in all_jobs if j.params.get("bundle_id") == bundle_id_str]

    image_jobs = [j for j in bundle_jobs if j.type == JobType.image]
    video_jobs = [j for j in bundle_jobs if j.type == JobType.video]

    terminal = {JobStatus.succeeded, JobStatus.failed}

    if not image_jobs or not all(j.status in terminal for j in image_jobs):
        return  # image jobs still running

    product = await db.get(Product, job.product_id)

    if any(j.status == JobStatus.succeeded for j in image_jobs):
        # At least one image succeeded → mark product ready_for_review
        if product and product.status == ProductStatus.processing:
            product.status = ProductStatus.ready_for_review
            await audit.record(
                db,
                tenant_id=job.tenant_id,
                actor_id=None,
                entity_type="product",
                entity_id=job.product_id,
                action="ready_for_review",
                payload={"bundle_id": bundle_id_str},
            )
    else:
        # All images failed → reset to draft so the merchant can retry
        if product and product.status == ProductStatus.processing:
            product.status = ProductStatus.draft
            await audit.record(
                db,
                tenant_id=job.tenant_id,
                actor_id=None,
                entity_type="product",
                entity_id=job.product_id,
                action="generation_failed",
                payload={"bundle_id": bundle_id_str},
            )

    # Only proceed to video if ALL image jobs succeeded
    if any(j.status == JobStatus.failed for j in image_jobs):
        # Some images failed — defer video until merchant regenerates failed shots
        if video_jobs:
            bundle = await db.get(AssetBundle, uuid.UUID(bundle_id_str))
            if bundle and not bundle.video_pending_hero:
                bundle.video_pending_hero = True
        return

    if not video_jobs:
        return

    video_job = video_jobs[0]
    bundle_version: int = job.params.get("bundle_version", 1)

    # Check if a hero has already been selected
    hero_result = await db.execute(
        select(GeneratedAsset).where(
            GeneratedAsset.product_id == job.product_id,
            GeneratedAsset.tenant_id == job.tenant_id,
            GeneratedAsset.version == bundle_version,
            GeneratedAsset.is_hero.is_(True),
        )
    )
    hero = hero_result.scalar_one_or_none()

    bundle = await db.get(AssetBundle, uuid.UUID(bundle_id_str))
    if bundle is None:
        return

    if hero:
        bundle.video_pending_hero = False
        await db.flush()
        enqueue_generate_video(str(video_job.id))
        await audit.record(
            db,
            tenant_id=job.tenant_id,
            actor_id=None,
            entity_type="generation_job",
            entity_id=video_job.id,
            action="video_enqueued",
            payload={"triggered_by": "bundle_complete", "hero_asset_id": str(hero.id)},
        )
    else:
        bundle.video_pending_hero = True


# ---------------------------------------------------------------------------
# Main task
# ---------------------------------------------------------------------------

async def run_generate_image_task(job_id: str) -> dict[str, str]:
    """Execute one image generation job end-to-end."""
    lf = _make_langfuse()
    lf_trace = None
    if lf is not None:
        lf_trace = lf.trace(
            name="generate_image_task",
            id=job_id,
            metadata={"job_id": job_id},
        )

    async with async_session_factory() as db:
        job = await db.get(GenerationJob, uuid.UUID(job_id))
        if job is None:
            raise ValueError(f"GenerationJob {job_id} not found")

        job.status = JobStatus.running
        job.started_at = datetime.now(_UTC)
        await db.commit()

        try:
            product = await db.get(Product, job.product_id)
            if product is None or not product.source_image_key:
                raise ValueError(f"Product {job.product_id} has no source_image_key")

            client = FalClient()
            provider = FalProvider(client)

            # --- Segmentation (cached) ---
            fal_segmented_url = await _ensure_segmented(product, provider, lf_trace)

            # --- Build generation request ---
            persona: dict = job.prompt.get("persona", {})
            pose: str = job.prompt.get("pose", "front")
            scene: str = job.prompt.get("scene", "studio_white")
            primary_ar: str = job.prompt.get("aspect_ratio", "9:16")
            bundle_version: int = job.params.get("bundle_version", 1)
            required_ars: list[str] = job.params.get(
                "required_aspect_ratios", _DEFAULT_ASPECT_RATIOS
            )

            gen_request = ImageGenerationRequest(
                segmented_garment_url=fal_segmented_url,
                product_attributes=product.attributes,
                persona=persona,
                pose=pose,
                scene=scene,
                aspect_ratio=primary_ar,
            )

            # --- Generate primary image ---
            gen_span = None
            if lf_trace is not None:
                gen_span = lf_trace.span(name="generate_image")  # type: ignore[union-attr]

            gen_result = await provider.generate_image(gen_request)

            if gen_span is not None:
                gen_span.end(
                    output={"image_url": gen_result.image_url},
                    metadata={
                        "model_id": gen_result.model_id,
                        "latency_ms": gen_result.latency_ms,
                        "cost_cents": gen_result.cost_cents,
                        "width": gen_result.width,
                        "height": gen_result.height,
                    },
                )

            # --- Download primary image bytes ---
            img_bytes = await client.download_url(gen_result.image_url)

            # --- Upload primary image ---
            asset_key = (
                f"tenants/{job.tenant_id}/products/{job.product_id}"
                f"/v{bundle_version}/img_{job_id}.webp"
            )
            asset_url = upload_bytes(asset_key, img_bytes, "image/webp")

            # --- Model spec metadata ---
            height_cm: int = persona.get("height_cm", 0)
            model_spec = {
                "model_height_cm": height_cm,
                "model_height_imperial": _cm_to_imperial(height_cm) if height_cm else "",
                "garment_size_worn": _estimate_garment_size(persona, product.attributes),
            }

            # --- Create primary asset row ---
            primary_asset = GeneratedAsset(
                tenant_id=job.tenant_id,
                product_id=job.product_id,
                job_id=job.id,
                kind=AssetKind.image_on_model,
                storage_key=asset_url,
                width=gen_result.width,
                height=gen_result.height,
                mime_type="image/webp",
                asset_metadata={
                    "persona_name": persona.get("display_name", ""),
                    "persona_id": persona.get("id", ""),
                    "pose": pose,
                    "scene": scene,
                    "aspect_ratio": primary_ar,
                    "model_id": gen_result.model_id,
                    "latency_ms": gen_result.latency_ms,
                    **model_spec,
                },
                version=bundle_version,
            )
            db.add(primary_asset)
            await db.flush()  # populate primary_asset.id before creating variants

            # --- Aspect-ratio variants ---
            await _create_aspect_variants(
                db, primary_asset, img_bytes, primary_ar, required_ars, job, bundle_version
            )

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
                    "asset_url": asset_url,
                    "model_id": gen_result.model_id,
                    "variants_created": len(required_ars) - 1,
                },
            )
            await db.commit()

            # --- Check bundle completion ---
            async with async_session_factory() as db2:
                job2 = await db2.get(GenerationJob, uuid.UUID(job_id))
                if job2:
                    await _check_bundle_complete(db2, job2)
                    await db2.commit()

        except Exception as exc:
            job.status = JobStatus.failed
            job.error = str(exc)[:2000]
            job.error_code = type(exc).__name__
            job.finished_at = datetime.now(_UTC)
            await db.commit()

            await audit_failure(str(job.tenant_id), str(job.product_id), job_id, exc)
            raise

        finally:
            if lf is not None:
                lf.flush()

    return {"job_id": job_id, "status": "succeeded"}


async def audit_failure(
    tenant_id: str, product_id: str, job_id: str, exc: Exception
) -> None:
    """Write a failure audit event in its own session (original session may be bad)."""
    try:
        async with async_session_factory() as db:
            await audit.record(
                db,
                tenant_id=uuid.UUID(tenant_id),
                actor_id=None,
                entity_type="generation_job",
                entity_id=uuid.UUID(job_id),
                action="failed",
                payload={"error": str(exc)[:500], "error_code": type(exc).__name__},
            )
            await db.commit()
    except Exception:
        pass  # best-effort; don't mask the original exception
