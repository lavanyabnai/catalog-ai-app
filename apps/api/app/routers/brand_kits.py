from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.models.brand_kits import BrandKit
from app.schemas.brand_kits import BrandKitCreate, BrandKitRead

router = APIRouter(prefix="/brand-kits", tags=["brand-kits"])


@router.get("", response_model=list[BrandKitRead])
async def list_brand_kits(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    result = await db.execute(
        select(BrandKit)
        .where(BrandKit.tenant_id == user.tenant_id)
        .order_by(BrandKit.name)
    )
    return result.scalars().all()


@router.post("", response_model=BrandKitRead, status_code=status.HTTP_201_CREATED)
async def create_brand_kit(
    body: BrandKitCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    kit = BrandKit(
        tenant_id=user.tenant_id,
        name=body.name,
        color_palette=body.color_palette,
        tone_notes=body.tone_notes,
        allowed_scenes=body.allowed_scenes,
        allowed_personas=body.allowed_personas,
        required_aspect_ratios=body.required_aspect_ratios,
    )
    db.add(kit)
    await db.flush()
    return kit
