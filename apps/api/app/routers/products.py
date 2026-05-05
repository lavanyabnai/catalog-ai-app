from __future__ import annotations

import asyncio
import base64
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import CurrentUser, get_current_user
from app.core.celery import enqueue_generate_image
from app.core.database import async_session_factory, get_db
from app.models.brand_kits import BrandKit
from app.models.catalog import Product, Variant
from app.models.enums import ProductStatus
from app.models.generation import AssetBundle, GeneratedAsset, GenerationJob
from app.models.personas import ModelPersona
from app.schemas.catalog import (
    ProductCreate,
    ProductListItem,
    ProductListResponse,
    ProductRead,
    ProductUpdate,
)
from app.schemas.generation import (
    AssetRead,
    BundleListItem,
    BundleRead,
    GenerateRequest,
    GenerateResponse,
    GenerationShotSpec,
    JobRead,
    PlanRequest,
    PlanResponse,
)
from app.services import audit
from app.services.plan_builder import GenerationShot, build_plan, get_required_aspect_ratios
from app.services.storage import generate_presigned_upload_url

router = APIRouter(prefix="/products", tags=["products"])

_PAGE_SIZE = 20


def _encode_cursor(dt: datetime) -> str:
    return base64.urlsafe_b64encode(dt.isoformat().encode()).decode()


def _decode_cursor(cursor: str) -> datetime:
    return datetime.fromisoformat(base64.urlsafe_b64decode(cursor.encode()).decode())


async def _get_product_or_404(
    product_id: uuid.UUID,
    db: AsyncSession,
    user: CurrentUser,
) -> Product:
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id, Product.tenant_id == user.tenant_id)
        .options(selectinload(Product.variants))
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


async def _load_available_personas(
    db: AsyncSession, tenant_id: uuid.UUID
) -> list[ModelPersona]:
    """Load system personas + the tenant's own personas, ordered by name."""
    result = await db.execute(
        select(ModelPersona)
        .where(
            or_(
                ModelPersona.tenant_id.is_(None),
                ModelPersona.tenant_id == tenant_id,
            )
        )
        .order_by(ModelPersona.system_managed.desc(), ModelPersona.display_name)
    )
    return list(result.scalars().all())


async def _load_brand_kit(db: AsyncSession, product: Product) -> BrandKit | None:
    if not product.brand_kit_id:
        return None
    return await db.get(BrandKit, product.brand_kit_id)


def _shots_to_specs(shots: list[GenerationShot]) -> list[GenerationShotSpec]:
    return [
        GenerationShotSpec(
            persona=s.persona,
            pose=s.pose,
            scene=s.scene,
            primary_aspect_ratio=s.primary_aspect_ratio,
        )
        for s in shots
    ]


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    product = Product(
        tenant_id=user.tenant_id,
        code=body.code,
        name=body.name,
        category_id=body.category_id,
        brand_kit_id=body.brand_kit_id,
        attributes=body.attributes,
    )
    db.add(product)
    await db.flush()

    variant = Variant(
        tenant_id=user.tenant_id,
        product_id=product.id,
        sku_code=body.code,
        color=body.color or "default",
        size=body.size or "one-size",
        attributes={},
    )
    db.add(variant)

    await audit.record(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        entity_type="product",
        entity_id=product.id,
        action="created",
        payload={"code": body.code, "name": body.name},
    )

    await db.flush()
    await db.refresh(product, ["variants"])
    return product


@router.get("", response_model=ProductListResponse)
async def list_products(
    cursor: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    base_q = select(Product).where(Product.tenant_id == user.tenant_id)

    total_result = await db.execute(
        select(func.count()).select_from(
            select(Product).where(Product.tenant_id == user.tenant_id).subquery()
        )
    )
    total = total_result.scalar_one()

    q = base_q.order_by(Product.created_at.desc()).limit(_PAGE_SIZE + 1)
    if cursor:
        try:
            cursor_dt = _decode_cursor(cursor)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid cursor")
        q = q.where(Product.created_at < cursor_dt)

    result = await db.execute(q)
    rows = result.scalars().all()

    has_more = len(rows) > _PAGE_SIZE
    items = rows[:_PAGE_SIZE]
    next_cursor = _encode_cursor(items[-1].created_at) if has_more and items else None

    return ProductListResponse(
        items=[ProductListItem.model_validate(p) for p in items],
        total=total,
        cursor=next_cursor,
    )


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    return await _get_product_or_404(product_id, db, user)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    product = await _get_product_or_404(product_id, db, user)

    changed: dict[str, Any] = {}
    image_uploaded = False
    for field, value in body.model_dump(exclude_none=True).items():
        if getattr(product, field) != value:
            if field == "source_image_key" and product.source_image_key is None:
                image_uploaded = True
            setattr(product, field, value)
            changed[field] = value

    if changed:
        product.updated_at = datetime.now(timezone.utc)
        await audit.record(
            db,
            tenant_id=user.tenant_id,
            actor_id=user.id,
            entity_type="product",
            entity_id=product.id,
            action="updated",
            payload=changed,
        )
        if image_uploaded:
            await audit.record(
                db,
                tenant_id=user.tenant_id,
                actor_id=user.id,
                entity_type="product",
                entity_id=product.id,
                action="uploaded",
                payload={"source_image_key": changed["source_image_key"]},
            )

    await db.flush()
    await db.refresh(product, ["variants"])
    return product


@router.post("/{product_id}/upload-url")
async def get_upload_url(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    """Return a presigned S3 PUT URL valid for 5 minutes."""
    await _get_product_or_404(product_id, db, user)
    key = f"tenants/{user.tenant_id}/products/{product_id}/source.jpg"
    url = generate_presigned_upload_url(key, content_type="image/jpeg")
    return {"url": url, "key": key}


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

@router.post("/{product_id}/plan", response_model=PlanResponse)
async def get_plan(
    product_id: uuid.UUID,
    body: PlanRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    """Preview the generation plan without enqueueing any jobs.

    Returns the list of shots (persona, pose, scene, primary_aspect_ratio) that
    would be generated, plus the required aspect ratios for the brand kit.
    The client can edit the plan and resubmit it to POST /{id}/generate.
    """
    product = await _get_product_or_404(product_id, db, user)
    personas = await _load_available_personas(db, user.tenant_id)
    brand_kit = await _load_brand_kit(db, product)

    overrides = [s.model_dump() for s in body.shots] if body.shots else None
    shots = build_plan(product, personas, brand_kit, overrides=overrides)
    required_ars = get_required_aspect_ratios(brand_kit)

    return PlanResponse(
        shots=_shots_to_specs(shots),
        required_aspect_ratios=required_ars,
        total_primary_images=len(shots),
        total_variant_images=len(shots) * (len(required_ars) - 1),
    )


@router.post(
    "/{product_id}/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate(
    product_id: uuid.UUID,
    body: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    product = await _get_product_or_404(product_id, db, user)

    if not product.source_image_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Product has no source image — upload one before generating",
        )

    personas = await _load_available_personas(db, user.tenant_id)
    brand_kit = await _load_brand_kit(db, product)

    # Build the plan (use provided shots or build default)
    overrides = [s.model_dump() for s in body.shots] if body.shots else None
    shots = build_plan(product, personas, brand_kit, overrides=overrides)
    required_ars = get_required_aspect_ratios(brand_kit)

    # Determine next bundle version
    existing_result = await db.execute(
        select(func.max(AssetBundle.version)).where(
            AssetBundle.product_id == product_id,
            AssetBundle.tenant_id == user.tenant_id,
        )
    )
    max_version: int = existing_result.scalar_one_or_none() or 0
    bundle_version = max_version + 1

    # Create bundle
    bundle = AssetBundle(
        tenant_id=user.tenant_id,
        product_id=product_id,
        version=bundle_version,
    )
    db.add(bundle)
    await db.flush()

    # Create one job per shot
    jobs: list[GenerationJob] = []
    for shot in shots:
        job = GenerationJob(
            tenant_id=user.tenant_id,
            product_id=product_id,
            type="image",
            status="queued",
            provider="fal",
            model_id="fal-ai/flux/dev/image-to-image",
            prompt={
                "persona": shot.persona,
                "pose": shot.pose,
                "scene": shot.scene,
                "aspect_ratio": shot.primary_aspect_ratio,
            },
            params={
                "bundle_id": str(bundle.id),
                "bundle_version": bundle_version,
                "required_aspect_ratios": required_ars,
            },
        )
        db.add(job)
        jobs.append(job)

    # Create the video job — stays queued until images complete and hero is selected
    default_scene = shots[0].scene if shots else "studio_white"
    video_job = GenerationJob(
        tenant_id=user.tenant_id,
        product_id=product_id,
        type="video",
        status="queued",
        provider="fal",
        model_id="fal-ai/kling-video/v1.6/standard/image-to-video",
        prompt={"motion": "confident_walk", "scene": default_scene, "duration_seconds": 5},
        params={"bundle_id": str(bundle.id), "bundle_version": bundle_version},
    )
    db.add(video_job)
    jobs.append(video_job)

    product.status = ProductStatus.processing
    await db.flush()

    await audit.record(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        entity_type="product",
        entity_id=product_id,
        action="generation_requested",
        payload={
            "bundle_id": str(bundle.id),
            "num_jobs": len(jobs),
            "required_aspect_ratios": required_ars,
        },
    )

    await db.commit()

    # Enqueue after commit so the worker sees all rows
    for job in jobs:
        enqueue_generate_image(str(job.id))

    return GenerateResponse(
        bundle_id=bundle.id,
        job_ids=[j.id for j in jobs],
        plan=_shots_to_specs(shots),
    )


@router.get("/{product_id}/bundle", response_model=BundleRead)
async def get_bundle(
    product_id: uuid.UUID,
    version: int | None = Query(default=None, description="Bundle version; omit for latest"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    """Return an asset bundle for the product (latest by default, or a specific version)."""
    q = select(AssetBundle).where(
        AssetBundle.product_id == product_id,
        AssetBundle.tenant_id == user.tenant_id,
    )
    if version is not None:
        q = q.where(AssetBundle.version == version)
    else:
        q = q.order_by(AssetBundle.version.desc()).limit(1)

    result = await db.execute(q)
    bundle = result.scalar_one_or_none()
    if bundle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No bundle found")

    assets_result = await db.execute(
        select(GeneratedAsset).where(
            GeneratedAsset.product_id == product_id,
            GeneratedAsset.tenant_id == user.tenant_id,
            GeneratedAsset.version == bundle.version,
        )
    )
    assets = assets_result.scalars().all()

    jobs_result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.product_id == product_id,
            GenerationJob.tenant_id == user.tenant_id,
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


@router.get("/{product_id}/bundles", response_model=list[BundleListItem])
async def list_bundles(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    """Return all bundles for a product, newest first, with asset counts."""
    await _get_product_or_404(product_id, db, user)

    bundles_result = await db.execute(
        select(AssetBundle)
        .where(
            AssetBundle.product_id == product_id,
            AssetBundle.tenant_id == user.tenant_id,
        )
        .order_by(AssetBundle.version.desc())
    )
    bundles = bundles_result.scalars().all()

    items: list[BundleListItem] = []
    for bundle in bundles:
        assets_result = await db.execute(
            select(GeneratedAsset).where(
                GeneratedAsset.product_id == product_id,
                GeneratedAsset.tenant_id == user.tenant_id,
                GeneratedAsset.version == bundle.version,
            )
        )
        assets = list(assets_result.scalars().all())
        hero = next((a for a in assets if a.is_hero), None)
        items.append(
            BundleListItem(
                id=bundle.id,
                version=bundle.version,
                status=bundle.status,
                created_at=bundle.created_at,
                total_assets=len(assets),
                hero_storage_key=hero.storage_key if hero else None,
            )
        )

    return items


@router.get("/{product_id}/events")
async def stream_product_events(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    """SSE stream: emits job_status and bundle_status events every 2 s.

    Use fetch() + ReadableStream on the client — EventSource doesn't support
    Authorization headers. The initial db session from get_db is held open
    for the connection lifetime (one connection per active studio tab; MVP tradeoff).
    """
    await _get_product_or_404(product_id, db, user)
    tenant_id = user.tenant_id

    async def _gen() -> AsyncGenerator[str, None]:
        while True:
            try:
                async with async_session_factory() as session:
                    bundle_result = await session.execute(
                        select(AssetBundle)
                        .where(
                            AssetBundle.product_id == product_id,
                            AssetBundle.tenant_id == tenant_id,
                        )
                        .order_by(AssetBundle.version.desc())
                        .limit(1)
                    )
                    bundle = bundle_result.scalar_one_or_none()

                    if bundle is None:
                        yield f"event: waiting\ndata: {{}}\n\n"
                    else:
                        bundle_payload = json.dumps({
                            "bundle_id": str(bundle.id),
                            "status": bundle.status,
                            "version": bundle.version,
                        })
                        yield f"event: bundle_status\ndata: {bundle_payload}\n\n"

                        jobs_result = await session.execute(
                            select(GenerationJob).where(
                                GenerationJob.product_id == product_id,
                                GenerationJob.tenant_id == tenant_id,
                                GenerationJob.params["bundle_id"].astext == str(bundle.id),
                            )
                        )
                        bundle_jobs = list(jobs_result.scalars().all())

                        for job in bundle_jobs:
                            job_payload = json.dumps({
                                "job_id": str(job.id),
                                "status": job.status,
                                "error": job.error,
                            })
                            yield f"event: job_status\ndata: {job_payload}\n\n"

                        # All terminal → send done and stop
                        if bundle_jobs and all(
                            j.status in ("succeeded", "failed") for j in bundle_jobs
                        ):
                            yield "event: done\ndata: {}\n\n"
                            return

            except Exception as exc:
                yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"
                return

            await asyncio.sleep(2)

    return StreamingResponse(
        _gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
