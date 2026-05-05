"""Integration tests for the generation pipeline using a mocked FalProvider.

These tests do NOT call fal.ai — they use a mock provider that returns a
fixture image so the full DB path (job → asset → product status) is exercised.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Product, Variant
from app.models.enums import JobStatus, ProductStatus
from app.models.generation import AssetBundle, GeneratedAsset, GenerationJob
from app.models.tenancy import Tenant
from app.services.providers.base import (
    ImageGenerationRequest,
    ImageGenerationResult,
    SegmentationRequest,
    SegmentationResult,
)

# A 1×1 white WEBP in raw bytes (valid image, ≈ 30 bytes)
_FIXTURE_IMAGE = (
    b"RIFF$\x00\x00\x00WEBPVP8 "
    b"\x18\x00\x00\x000\x01\x00\x9d\x01*\x01\x00\x01\x00\x00"
    b"7\x00\xfe\xfb\x94\x00\x00"
)

_UTC = timezone.utc


@pytest.fixture
async def provisioned_product(db: AsyncSession, tenant_a: Tenant) -> tuple[Product, str]:
    """A product with a source_image_key, plus its tenant_id."""
    product = Product(
        tenant_id=tenant_a.id,
        code="TEST-GEN-001",
        name="Test Shirt",
        source_image_key=f"tenants/{tenant_a.id}/products/test/source.jpg",
        attributes={"color": "red", "material": "cotton", "garment_type": "T-Shirts"},
    )
    db.add(product)
    await db.flush()
    db.add(
        Variant(
            tenant_id=tenant_a.id,
            product_id=product.id,
            sku_code="TEST-GEN-001",
            color="red",
            size="one-size",
        )
    )
    await db.flush()
    return product, str(tenant_a.id)


@pytest.fixture
async def queued_job(db: AsyncSession, provisioned_product) -> GenerationJob:
    product, _tid = provisioned_product
    bundle = AssetBundle(
        tenant_id=product.tenant_id,
        product_id=product.id,
        version=1,
    )
    db.add(bundle)
    await db.flush()

    job = GenerationJob(
        tenant_id=product.tenant_id,
        product_id=product.id,
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
            "pose": "front",
            "scene": "studio_white",
            "aspect_ratio": "4:5",
        },
        params={
            "bundle_id": str(bundle.id),
            "bundle_version": 1,
            # Single required ratio = no Pillow variant crops (fixture image is 1×1)
            "required_aspect_ratios": ["4:5"],
        },
    )
    db.add(job)
    await db.flush()
    await db.commit()
    return job


class _MockProvider:
    """Mock FalProvider that returns fixture data without calling fal.ai."""

    async def segment_garment(self, request: SegmentationRequest) -> SegmentationResult:
        return SegmentationResult(
            segmented_url="https://fal.media/mock/segmented.webp",
            cost_cents=0,
            latency_ms=100,
            model_id="fal-ai/birefnet",
        )

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        return ImageGenerationResult(
            image_url="https://fal.media/mock/generated.webp",
            width=800,
            height=1000,
            model_id="fal-ai/flux/dev/image-to-image",
            cost_cents=0,
            latency_ms=200,
        )


@pytest.mark.asyncio
async def test_segmentation_runs_before_image_gen(
    queued_job: GenerationJob,
) -> None:
    """Segmentation is called when no cached segmented version exists."""
    mock_provider = _MockProvider()
    seg_spy = AsyncMock(wraps=mock_provider.segment_garment)
    gen_spy = AsyncMock(wraps=mock_provider.generate_image)
    mock_provider.segment_garment = seg_spy
    mock_provider.generate_image = gen_spy

    fake_client = MagicMock()
    fake_client.upload_file = AsyncMock(return_value="https://fal.media/mock/source.jpg")
    fake_client.download_url = AsyncMock(return_value=_FIXTURE_IMAGE)
    mock_provider._client = fake_client

    with (
        patch("app.tasks.generate_image.FalProvider", return_value=mock_provider),
        patch("app.tasks.generate_image.FalClient", return_value=fake_client),
        patch("app.tasks.generate_image.object_exists", return_value=False),
        patch("app.tasks.generate_image.download_bytes", return_value=_FIXTURE_IMAGE),
        patch("app.tasks.generate_image.upload_bytes"),
    ):
        from app.tasks.generate_image import run_generate_image_task
        await run_generate_image_task(str(queued_job.id))

    seg_spy.assert_awaited_once()
    gen_spy.assert_awaited_once()


@pytest.mark.asyncio
async def test_segmentation_skipped_when_cached(
    queued_job: GenerationJob,
) -> None:
    """When a segmented version is already in S3, BiRefNet is NOT called again."""
    mock_provider = _MockProvider()
    seg_spy = AsyncMock(wraps=mock_provider.segment_garment)
    mock_provider.segment_garment = seg_spy

    fake_client = MagicMock()
    fake_client.upload_file = AsyncMock(return_value="https://fal.media/mock/seg_cached.webp")
    fake_client.download_url = AsyncMock(return_value=_FIXTURE_IMAGE)
    mock_provider._client = fake_client

    with (
        patch("app.tasks.generate_image.FalProvider", return_value=mock_provider),
        patch("app.tasks.generate_image.FalClient", return_value=fake_client),
        patch("app.tasks.generate_image.object_exists", return_value=True),
        patch("app.tasks.generate_image.download_bytes", return_value=_FIXTURE_IMAGE),
        patch("app.tasks.generate_image.upload_bytes"),
    ):
        from app.tasks.generate_image import run_generate_image_task
        await run_generate_image_task(str(queued_job.id))

    seg_spy.assert_not_awaited()


@pytest.mark.asyncio
async def test_pipeline_end_to_end(
    db: AsyncSession,
    queued_job: GenerationJob,
) -> None:
    """Full path: queued → succeeded, GeneratedAsset row created, status ready_for_review."""
    mock_provider = _MockProvider()
    fake_client = MagicMock()
    fake_client.upload_file = AsyncMock(return_value="https://fal.media/mock/source.jpg")
    fake_client.download_url = AsyncMock(return_value=_FIXTURE_IMAGE)
    mock_provider._client = fake_client

    with (
        patch("app.tasks.generate_image.FalProvider", return_value=mock_provider),
        patch("app.tasks.generate_image.FalClient", return_value=fake_client),
        patch("app.tasks.generate_image.object_exists", return_value=False),
        patch("app.tasks.generate_image.download_bytes", return_value=_FIXTURE_IMAGE),
        patch("app.tasks.generate_image.upload_bytes"),
    ):
        from app.tasks.generate_image import run_generate_image_task
        result = await run_generate_image_task(str(queued_job.id))

    assert result["status"] == "succeeded"

    # Job should be succeeded
    await db.refresh(queued_job)
    assert queued_job.status == JobStatus.succeeded
    assert queued_job.finished_at is not None

    # A GeneratedAsset row should exist
    asset_result = await db.execute(
        select(GeneratedAsset).where(GeneratedAsset.job_id == queued_job.id)
    )
    assets = asset_result.scalars().all()
    assert len(assets) == 1
    assert assets[0].width == 800
    assert assets[0].height == 1000

    # Product status should be ready_for_review (only job in bundle)
    product_result = await db.execute(
        select(Product).where(Product.id == queued_job.product_id)
    )
    product = product_result.scalar_one()
    assert product.status == ProductStatus.ready_for_review


@pytest.mark.asyncio
async def test_failure_path(
    db: AsyncSession,
    queued_job: GenerationJob,
) -> None:
    """When the provider raises, job → failed, product stays processing, audit event written."""
    from app.models.audit import AuditEvent

    # Force product into processing status first
    product_result = await db.execute(
        select(Product).where(Product.id == queued_job.product_id)
    )
    product = product_result.scalar_one()
    product.status = ProductStatus.processing
    await db.commit()

    async def _boom(request: Any) -> Any:
        raise RuntimeError("fal.ai service unavailable")

    mock_provider = _MockProvider()
    mock_provider.generate_image = _boom  # type: ignore[method-assign]

    fake_client = MagicMock()
    fake_client.upload_file = AsyncMock(return_value="https://fal.media/mock/source.jpg")
    fake_client.download_url = AsyncMock(return_value=_FIXTURE_IMAGE)
    mock_provider._client = fake_client

    with (
        patch("app.tasks.generate_image.FalProvider", return_value=mock_provider),
        patch("app.tasks.generate_image.FalClient", return_value=fake_client),
        patch("app.tasks.generate_image.object_exists", return_value=False),
        patch("app.tasks.generate_image.download_bytes", return_value=_FIXTURE_IMAGE),
        patch("app.tasks.generate_image.upload_bytes"),
        pytest.raises(RuntimeError, match="fal.ai service unavailable"),
    ):
        from app.tasks.generate_image import run_generate_image_task
        await run_generate_image_task(str(queued_job.id))

    await db.refresh(queued_job)
    assert queued_job.status == JobStatus.failed
    assert "fal.ai service unavailable" in queued_job.error

    # Product must still be processing (one failed job ≠ all done with success)
    await db.refresh(product)
    assert product.status == ProductStatus.processing

    # Audit event for failure
    audit_result = await db.execute(
        select(AuditEvent).where(
            AuditEvent.entity_id == queued_job.id,
            AuditEvent.action == "failed",
        )
    )
    events = audit_result.scalars().all()
    assert len(events) >= 1
