from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.taxonomy import Category
from app.schemas.taxonomy import CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])


def _build_tree(
    categories: list[Category],
) -> list[CategoryRead]:
    by_id: dict[uuid.UUID, CategoryRead] = {}
    for cat in categories:
        by_id[cat.id] = CategoryRead(
            id=cat.id,
            slug=cat.slug,
            display_name=cat.display_name,
            path=cat.path,
            parent_id=cat.parent_id,
            children=[],
        )

    roots: list[CategoryRead] = []
    for cat in categories:
        node = by_id[cat.id]
        if cat.parent_id is None:
            roots.append(node)
        elif cat.parent_id in by_id:
            by_id[cat.parent_id].children.append(node)

    return roots


@router.get("", response_model=list[CategoryRead])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _: Any = Depends(get_current_user),
) -> list[CategoryRead]:
    """Return the full category tree."""
    result = await db.execute(select(Category).order_by(Category.path))
    categories = result.scalars().all()
    return _build_tree(list(categories))
