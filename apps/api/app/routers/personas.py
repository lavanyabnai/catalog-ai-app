from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.models.personas import ModelPersona
from app.schemas.personas import PersonaCreate, PersonaRead

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("", response_model=list[PersonaRead])
async def list_personas(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    """Return all system-managed personas plus the tenant's own personas."""
    result = await db.execute(
        select(ModelPersona)
        .where(
            or_(
                ModelPersona.tenant_id.is_(None),
                ModelPersona.tenant_id == user.tenant_id,
            )
        )
        .order_by(ModelPersona.system_managed.desc(), ModelPersona.display_name)
    )
    return result.scalars().all()


@router.post("", response_model=PersonaRead, status_code=status.HTTP_201_CREATED)
async def create_persona(
    body: PersonaCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    """Create a tenant-specific persona. System-managed personas cannot be created via API."""
    persona = ModelPersona(
        tenant_id=user.tenant_id,
        display_name=body.display_name,
        body_type=body.body_type,
        ethnicity=body.ethnicity,
        age_range=body.age_range,
        height_cm=body.height_cm,
        gender_presentation=body.gender_presentation,
        hair=body.hair,
        system_managed=False,
    )
    db.add(persona)
    await db.flush()
    await db.refresh(persona)
    return persona


@router.get("/{persona_id}", response_model=PersonaRead)
async def get_persona(
    persona_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    """Get a single persona — system or tenant-owned."""
    result = await db.execute(
        select(ModelPersona).where(
            ModelPersona.id == persona_id,
            or_(
                ModelPersona.tenant_id.is_(None),
                ModelPersona.tenant_id == user.tenant_id,
            ),
        )
    )
    persona = result.scalar_one_or_none()
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
    return persona
