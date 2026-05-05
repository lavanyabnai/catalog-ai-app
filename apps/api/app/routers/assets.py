"""Asset-level operations: hero selection and single-shot regeneration."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.celery import enqueue_generate_image, enqueue_generate_video
from app.core.database import get_db
from app.models.enums import AssetKind, BundleStatus, JobStatus, JobType, ProductStatus
from app.models.generation import AssetBundle, GeneratedAsset, GenerationJob
from app.schemas.generation import AssetRead, JobRead, RegenerateResponse
from app.services import audit

router = APIRouter(prefix="/assets", tags=["assets"])


async def _get_asset_or_404(
    asset_id: uuid.UUID,
    db: AsyncSession,
    user: CurrentUser,
) -> GeneratedAsset:
    result = await db.execute(
        select(GeneratedAsset).where(
            GeneratedAsset.id == asset_id,
            GeneratedAsset.tenant_id == user.tenant_id,
        )
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


@router.get("/{asset_id}", response_model=AssetRead)
async def get_asset(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    return await _get_asset_or_404(asset_id, db, user)


@router.post("/{asset_id}/hero", response_model=AssetRead)
async def set_hero(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    """Mark this asset as the hero image for its bundle.

    Clears hero on all other assets in the same bundle/version.
    Only image_on_model assets can be set as hero.
    """
    asset = await _get_asset_or_404(asset_id, db, user)

    if asset.kind != AssetKind.image_on_model:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only primary on-model images can be set as hero",
        )

    # Verify the owning job succeeded
    job = await db.get(GenerationJob, asset.job_id)
    if job is None or job.status != JobStatus.succeeded:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Hero can only be set on a successfully generated image",
        )

    # Check bundle is not yet approved
    bundle_id_str: str = job.params.get("bundle_id", "")
    if bundle_id_str:
        try:
            bundle = await db.get(AssetBundle, uuid.UUID(bundle_id_str))
            if bundle and bundle.status == BundleStatus.approved:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Bundle is already approved — create a new bundle to make changes",
                )
        except ValueError:
            pass

    # Clear hero on all assets in this bundle/version
    sibling_result = await db.execute(
        select(GeneratedAsset).where(
            GeneratedAsset.product_id == asset.product_id,
            GeneratedAsset.tenant_id == user.tenant_id,
            GeneratedAsset.version == asset.version,
            GeneratedAsset.is_hero.is_(True),
        )
    )
    for sibling in sibling_result.scalars().all():
        sibling.is_hero = False

    asset.is_hero = True
    await db.flush()

    # If images are all done but video was deferred waiting for a hero, enqueue now
    bundle_id_str: str = job.params.get("bundle_id", "")
    if bundle_id_str:
        try:
            bundle = await db.get(AssetBundle, uuid.UUID(bundle_id_str))
            if bundle and bundle.video_pending_hero:
                # Find the queued video job
                video_result = await db.execute(
                    select(GenerationJob).where(
                        GenerationJob.product_id == asset.product_id,
                        GenerationJob.tenant_id == user.tenant_id,
                        GenerationJob.params["bundle_id"].astext == bundle_id_str,
                        GenerationJob.type == JobType.video,
                        GenerationJob.status == JobStatus.queued,
                    )
                )
                video_job = video_result.scalar_one_or_none()
                if video_job:
                    bundle.video_pending_hero = False
                    await db.flush()
                    enqueue_generate_video(str(video_job.id))
                    await audit.record(
                        db,
                        tenant_id=user.tenant_id,
                        actor_id=user.id,
                        entity_type="generation_job",
                        entity_id=video_job.id,
                        action="video_enqueued_after_hero",
                        payload={"hero_asset_id": str(asset.id)},
                    )
        except ValueError:
            pass

    await db.refresh(asset)
    return asset


@router.delete("/{asset_id}/hero", response_model=AssetRead)
async def unset_hero(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    """Remove hero status from this asset."""
    asset = await _get_asset_or_404(asset_id, db, user)
    asset.is_hero = False
    await db.flush()
    await db.refresh(asset)
    return asset


@router.post("/{asset_id}/regenerate", response_model=RegenerateResponse)
async def regenerate_asset(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    """Re-queue a single shot for regeneration within the same bundle.

    Creates a new GenerationJob with the same prompt and params as the
    original job, then enqueues it. The bundle version is unchanged;
    the new asset will appear alongside the old one in the gallery.
    """
    asset = await _get_asset_or_404(asset_id, db, user)

    if asset.kind != AssetKind.image_on_model:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only primary on-model images can be regenerated",
        )

    original_job = await db.get(GenerationJob, asset.job_id)
    if original_job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original generation job not found",
        )

    # Prevent regenerating into an approved bundle
    bundle_id_str: str = original_job.params.get("bundle_id", "")
    if bundle_id_str:
        try:
            bundle = await db.get(AssetBundle, uuid.UUID(bundle_id_str))
            if bundle and bundle.status == BundleStatus.approved:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Bundle is approved — create a new bundle instead",
                )
        except ValueError:
            pass

    new_job = GenerationJob(
        tenant_id=user.tenant_id,
        product_id=original_job.product_id,
        type=original_job.type,
        status=JobStatus.queued,
        provider=original_job.provider,
        model_id=original_job.model_id,
        prompt=dict(original_job.prompt),
        params=dict(original_job.params),
    )
    db.add(new_job)

    # Reset product to processing so it doesn't show as ready_for_review
    from app.models.catalog import Product
    product = await db.get(Product, original_job.product_id)
    if product and product.status in (ProductStatus.ready_for_review,):
        product.status = ProductStatus.processing

    await db.flush()

    await audit.record(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        entity_type="generation_job",
        entity_id=new_job.id,
        action="regeneration_requested",
        payload={
            "original_job_id": str(original_job.id),
            "original_asset_id": str(asset.id),
            "bundle_id": bundle_id_str,
        },
    )

    await db.commit()
    enqueue_generate_image(str(new_job.id))

    return RegenerateResponse(job_id=new_job.id, bundle_id=bundle_id_str)
