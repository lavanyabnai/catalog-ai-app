"""Bundle operations: approval and zip download."""
from __future__ import annotations

import asyncio
import io
import json
import uuid
import zipfile
from datetime import datetime, timezone
from math import gcd
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.models.catalog import Product
from app.models.enums import AssetKind, BundleStatus, ProductStatus
from app.models.generation import AssetBundle, GeneratedAsset, GenerationJob
from app.schemas.generation import AssetRead, BundleRead, JobRead
from app.services import audit
from app.services.storage import download_bytes

router = APIRouter(prefix="/bundles", tags=["bundles"])


async def _get_bundle_or_404(
    bundle_id: uuid.UUID,
    db: AsyncSession,
    user: CurrentUser,
) -> AssetBundle:
    bundle = await db.get(AssetBundle, bundle_id)
    if bundle is None or bundle.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")
    return bundle


async def _load_bundle_detail(
    bundle: AssetBundle,
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> BundleRead:
    assets_result = await db.execute(
        select(GeneratedAsset).where(
            GeneratedAsset.product_id == bundle.product_id,
            GeneratedAsset.tenant_id == tenant_id,
            GeneratedAsset.version == bundle.version,
        )
    )
    assets = assets_result.scalars().all()

    jobs_result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.product_id == bundle.product_id,
            GenerationJob.tenant_id == tenant_id,
            GenerationJob.params["bundle_id"].astext == str(bundle.id),
        )
    )
    jobs = jobs_result.scalars().all()

    return BundleRead(
        id=bundle.id,
        tenant_id=bundle.tenant_id,
        product_id=bundle.product_id,
        version=bundle.version,
        status=bundle.status,
        approved_by=bundle.approved_by,
        approved_at=bundle.approved_at,
        created_at=bundle.created_at,
        assets=[AssetRead.model_validate(a) for a in assets],
        jobs=[JobRead.model_validate(j) for j in jobs],
    )


@router.post("/{bundle_id}/approve", response_model=BundleRead)
async def approve_bundle(
    bundle_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    """Approve a bundle — requires a hero asset to be selected first."""
    bundle = await _get_bundle_or_404(bundle_id, db, user)

    if bundle.status == BundleStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Bundle is already approved",
        )

    hero_result = await db.execute(
        select(GeneratedAsset).where(
            GeneratedAsset.product_id == bundle.product_id,
            GeneratedAsset.tenant_id == user.tenant_id,
            GeneratedAsset.version == bundle.version,
            GeneratedAsset.is_hero.is_(True),
        )
    )
    hero = hero_result.scalar_one_or_none()
    if hero is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Select a hero image before approving the bundle",
        )

    bundle.status = BundleStatus.approved
    bundle.approved_by = user.id
    bundle.approved_at = datetime.now(timezone.utc)

    product = await db.get(Product, bundle.product_id)
    if product:
        product.status = ProductStatus.approved

    await db.flush()

    await audit.record(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        entity_type="asset_bundle",
        entity_id=bundle.id,
        action="approved",
        payload={"hero_asset_id": str(hero.id)},
    )

    await db.commit()
    await db.refresh(bundle)

    return await _load_bundle_detail(bundle, db, user.tenant_id)


@router.get("/{bundle_id}/download")
async def download_bundle(
    bundle_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    """Stream an approved bundle as a zip file.

    Folder layout: metadata.json + one folder per aspect ratio (e.g. 4x5/, 9x16/).
    """
    bundle = await _get_bundle_or_404(bundle_id, db, user)

    if bundle.status != BundleStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only approved bundles can be downloaded",
        )

    assets_result = await db.execute(
        select(GeneratedAsset).where(
            GeneratedAsset.product_id == bundle.product_id,
            GeneratedAsset.tenant_id == user.tenant_id,
            GeneratedAsset.version == bundle.version,
        )
    )
    assets = list(assets_result.scalars().all())

    metadata: dict[str, Any] = {
        "bundle_id": str(bundle.id),
        "product_id": str(bundle.product_id),
        "version": bundle.version,
        "approved_at": bundle.approved_at.isoformat() if bundle.approved_at else None,
        "assets": [
            {
                "id": str(a.id),
                "kind": a.kind.value,
                "storage_key": a.storage_key,
                "width": a.width,
                "height": a.height,
                "is_hero": a.is_hero,
                "parent_asset_id": str(a.parent_asset_id) if a.parent_asset_id else None,
                "model_spec": a.asset_metadata,
            }
            for a in assets
        ],
    }

    # Snapshot values for the thread (avoids closing-over SQLAlchemy ORM objects)
    asset_snapshots = [
        (a.storage_key, a.width, a.height, a.is_hero, str(a.id), a.kind)
        for a in assets
        if a.kind != AssetKind.image_variant  # skip poster frames; they're inside the mp4
    ]

    def _build_zip() -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))
            for storage_key, width, height, is_hero, asset_id, kind in asset_snapshots:
                if kind == AssetKind.video_on_model:
                    filename = f"video/{asset_id}.mp4"
                else:
                    folder = _ar_folder(width, height)
                    suffix = "_hero" if is_hero else ""
                    filename = f"{folder}/{asset_id}{suffix}.webp"
                try:
                    zf.writestr(filename, download_bytes(storage_key))
                except Exception:
                    pass  # skip assets that fail to download
        buf.seek(0)
        return buf.read()

    zip_bytes = await asyncio.to_thread(_build_zip)

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=bundle_{bundle_id}.zip",
            "Content-Length": str(len(zip_bytes)),
        },
    )


def _ar_folder(width: int | None, height: int | None) -> str:
    if not width or not height:
        return "other"
    g = gcd(width, height)
    return f"{width // g}x{height // g}"
