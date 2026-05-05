"""Tests for the video generation pipeline."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Product, Variant
from app.models.enums import AssetKind, JobStatus
from app.models.generation import AssetBundle, GeneratedAsset, GenerationJob
from app.models.tenancy import Tenant
from app.services.providers.base import VideoGenerationResult

_UTC = timezone.utc
_FAKE_HERO_BYTES = b"fake_hero_image"
_FAKE_VIDEO_BYTES = b"fake_mp4_bytes"
_FAKE_POSTER_BYTES = b"fake_poster_jpeg"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def video_product(db: AsyncSession, tenant_a: Tenant) -> Product:
    product = Product(
        tenant_id=tenant_a.id,
        code="VID-001",
        name="Video Shirt",
        source_image_key=f"tenants/{tenant_a.id}/products/vid001/source.jpg",
        attributes={"color": "blue", "garment_type": "T-Shirts"},
    )
    db.add(product)
    await db.flush()
    db.add(
        Variant(
            tenant_id=tenant_a.id,
            product_id=product.id,
            sku_code="VID-001",
            color="blue",
            size="one-size",
        )
    )
    await db.flush()
    return product


@pytest.fixture
async def video_bundle(db: AsyncSession, video_product: Product) -> AssetBundle:
    bundle = AssetBundle(
        tenant_id=video_product.tenant_id,
        product_id=video_product.id,
        version=1,
        video_pending_hero=False,
    )
    db.add(bundle)
    await db.flush()
    return bundle


@pytest.fixture
async def video_job(
    db: AsyncSession, video_product: Product, video_bundle: AssetBundle
) -> GenerationJob:
    job = GenerationJob(
        tenant_id=video_product.tenant_id,
        product_id=video_product.id,
        type="video",
        status="queued",
        provider="fal",
        model_id="fal-ai/kling-video/v1.6/standard/image-to-video",
        prompt={"motion": "confident_walk", "scene": "studio_white", "duration_seconds": 5},
        params={"bundle_id": str(video_bundle.id), "bundle_version": 1},
    )
    db.add(job)
    await db.flush()
    await db.commit()
    return job


@pytest.fixture
async def hero_asset(
    db: AsyncSession, video_product: Product, video_job: GenerationJob
) -> GeneratedAsset:
    img_job = GenerationJob(
        tenant_id=video_product.tenant_id,
        product_id=video_product.id,
        type="image",
        status="succeeded",
        provider="fal",
        model_id="fal-ai/flux/dev/image-to-image",
        prompt={"pose": "front", "scene": "studio_white", "aspect_ratio": "4:5"},
        params={"bundle_version": 1},
    )
    db.add(img_job)
    await db.flush()

    asset = GeneratedAsset(
        tenant_id=video_product.tenant_id,
        product_id=video_product.id,
        job_id=img_job.id,
        kind=AssetKind.image_on_model,
        storage_key=f"tenants/{video_product.tenant_id}/products/{video_product.id}/v1/hero.webp",
        mime_type="image/webp",
        width=800,
        height=1000,
        version=1,
        is_hero=True,
        asset_metadata={},
    )
    db.add(asset)
    await db.flush()
    await db.commit()
    return asset


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_video_pipeline_end_to_end(
    db: AsyncSession,
    video_job: GenerationJob,
    hero_asset: GeneratedAsset,
) -> None:
    """Full happy path: hero exists → video job succeeds, assets created."""
    fake_client = MagicMock()
    fake_client.upload_file = AsyncMock(return_value="https://fal.media/hero.webp")
    fake_client.download_url = AsyncMock(return_value=_FAKE_VIDEO_BYTES)

    mock_video_result = VideoGenerationResult(
        video_url="https://fal.media/output.mp4",
        duration_ms=5000,
        model_id="fal-ai/kling-video/v1.6/standard/image-to-video",
        cost_cents=50,
        latency_ms=8000,
    )

    with (
        patch("app.tasks.generate_video.FalClient", return_value=fake_client),
        patch("app.tasks.generate_video.FalProvider") as MockProvider,
        patch("app.tasks.generate_video.download_bytes", return_value=_FAKE_HERO_BYTES),
        patch("app.tasks.generate_video.upload_bytes"),
        patch(
            "app.tasks.generate_video._extract_poster_frame",
            return_value=_FAKE_POSTER_BYTES,
        ),
    ):
        mock_provider_instance = MagicMock()
        mock_provider_instance.generate_video = AsyncMock(return_value=mock_video_result)
        MockProvider.return_value = mock_provider_instance

        from app.tasks.generate_video import run_generate_video_task

        result = await run_generate_video_task(str(video_job.id))

    assert result["status"] == "succeeded"

    await db.refresh(video_job)
    assert video_job.status == JobStatus.succeeded
    assert video_job.finished_at is not None
    assert video_job.cost_cents == 50

    # Should have video_on_model + image_variant (poster) rows
    assets_result = await db.execute(
        select(GeneratedAsset).where(GeneratedAsset.job_id == video_job.id)
    )
    assets = assets_result.scalars().all()
    kinds = {a.kind for a in assets}
    assert AssetKind.video_on_model in kinds
    assert AssetKind.image_variant in kinds

    video_asset = next(a for a in assets if a.kind == AssetKind.video_on_model)
    assert video_asset.duration_ms == 5000
    assert video_asset.mime_type == "video/mp4"
    assert "poster_key" in video_asset.asset_metadata


@pytest.mark.asyncio
async def test_video_cap_exceeded(
    db: AsyncSession,
    video_job: GenerationJob,
    hero_asset: GeneratedAsset,
    tenant_a: Tenant,
) -> None:
    """Daily cap of 0 → job fails immediately with error_code video_cap_exceeded."""
    tenant_a.daily_video_cap = 0
    db.add(tenant_a)
    await db.commit()

    with (
        patch("app.tasks.generate_video.FalClient"),
        patch("app.tasks.generate_video.FalProvider"),
        patch("app.tasks.generate_video.download_bytes", return_value=_FAKE_HERO_BYTES),
        patch("app.tasks.generate_video.upload_bytes"),
        patch("app.tasks.generate_video._extract_poster_frame", return_value=_FAKE_POSTER_BYTES),
        pytest.raises(Exception, match="Daily video cap"),
    ):
        from app.tasks.generate_video import run_generate_video_task
        await run_generate_video_task(str(video_job.id))

    await db.refresh(video_job)
    assert video_job.status == JobStatus.failed
    assert video_job.error_code == "video_cap_exceeded"


@pytest.mark.asyncio
async def test_video_no_hero_raises(
    db: AsyncSession,
    video_job: GenerationJob,
) -> None:
    """No hero asset → ValueError, job fails before any external calls."""
    fake_client = MagicMock()

    with (
        patch("app.tasks.generate_video.FalClient", return_value=fake_client),
        patch("app.tasks.generate_video.FalProvider"),
        patch("app.tasks.generate_video.download_bytes"),
        patch("app.tasks.generate_video.upload_bytes"),
        patch("app.tasks.generate_video._extract_poster_frame"),
        pytest.raises(ValueError, match="No hero asset"),
    ):
        from app.tasks.generate_video import run_generate_video_task
        await run_generate_video_task(str(video_job.id))

    await db.refresh(video_job)
    assert video_job.status == JobStatus.failed
    assert "No hero asset" in (video_job.error or "")


@pytest.mark.asyncio
async def test_image_failure_sets_video_pending_hero(
    db: AsyncSession,
    video_product: Product,
    video_bundle: AssetBundle,
) -> None:
    """When one image job fails after others succeed, video_pending_hero is set True.

    The last image job to succeed calls _check_bundle_complete, which detects a
    sibling failure and defers video generation by setting the flag.
    """
    bundle_id_str = str(video_bundle.id)

    failed_job = GenerationJob(
        tenant_id=video_product.tenant_id,
        product_id=video_product.id,
        type="image",
        status="failed",
        provider="fal",
        model_id="fal-ai/flux/dev/image-to-image",
        prompt={"pose": "front", "scene": "studio_white", "aspect_ratio": "4:5"},
        params={"bundle_id": bundle_id_str, "bundle_version": 1, "required_aspect_ratios": ["4:5"]},
    )
    db.add(failed_job)

    queued_job = GenerationJob(
        tenant_id=video_product.tenant_id,
        product_id=video_product.id,
        type="image",
        status="queued",
        provider="fal",
        model_id="fal-ai/flux/dev/image-to-image",
        prompt={
            "persona": {
                "id": str(uuid.uuid4()),
                "display_name": "Aisha",
                "body_type": "hourglass",
                "ethnicity": "Black / African",
                "age_range": "25-35",
                "height_cm": 170,
                "gender_presentation": "feminine",
                "hair": "long braids",
            },
            "pose": "back",
            "scene": "studio_white",
            "aspect_ratio": "4:5",
        },
        params={"bundle_id": bundle_id_str, "bundle_version": 1, "required_aspect_ratios": ["4:5"]},
    )
    db.add(queued_job)

    video_job = GenerationJob(
        tenant_id=video_product.tenant_id,
        product_id=video_product.id,
        type="video",
        status="queued",
        provider="fal",
        model_id="fal-ai/kling-video/v1.6/standard/image-to-video",
        prompt={"motion": "confident_walk", "scene": "studio_white", "duration_seconds": 5},
        params={"bundle_id": bundle_id_str, "bundle_version": 1},
    )
    db.add(video_job)

    video_product.status = "processing"  # type: ignore[assignment]
    await db.flush()
    await db.commit()

    _FIXTURE_IMAGE = (
        b"RIFF$\x00\x00\x00WEBPVP8 "
        b"\x18\x00\x00\x000\x01\x00\x9d\x01*\x01\x00\x01\x00\x00"
        b"7\x00\xfe\xfb\x94\x00\x00"
    )

    fake_client = MagicMock()
    fake_client.upload_file = AsyncMock(return_value="https://fal.media/mock/seg.webp")
    fake_client.download_url = AsyncMock(return_value=_FIXTURE_IMAGE)

    class _MockProvider:
        async def segment_garment(self, req):
            from app.services.providers.base import SegmentationResult
            return SegmentationResult(segmented_url="https://fal.media/mock/seg.webp", cost_cents=0, latency_ms=0, model_id="birefnet")

        async def generate_image(self, req):
            from app.services.providers.base import ImageGenerationResult
            return ImageGenerationResult(image_url="https://fal.media/mock/img.webp", width=800, height=1000, model_id="flux", cost_cents=0, latency_ms=0)

    mock_provider = _MockProvider()

    with (
        patch("app.tasks.generate_image.FalProvider", return_value=mock_provider),
        patch("app.tasks.generate_image.FalClient", return_value=fake_client),
        patch("app.tasks.generate_image.object_exists", return_value=False),
        patch("app.tasks.generate_image.download_bytes", return_value=_FIXTURE_IMAGE),
        patch("app.tasks.generate_image.upload_bytes"),
        patch("app.tasks.generate_image._make_langfuse", return_value=None),
        patch("app.core.celery.enqueue_generate_video"),
    ):
        from app.tasks.generate_image import run_generate_image_task
        await run_generate_image_task(str(queued_job.id))

    await db.refresh(video_bundle)
    assert video_bundle.video_pending_hero is True
