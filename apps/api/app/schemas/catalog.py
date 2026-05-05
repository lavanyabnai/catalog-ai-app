import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.models.enums import ProductStatus
from app.schemas.common import OrmBase


# ---------------------------------------------------------------------------
# Variants — internal, never exposed directly in MVP API responses
# ---------------------------------------------------------------------------

class _VariantInternal(OrmBase):
    id: uuid.UUID
    sku_code: str
    color: str | None
    size: str | None
    attributes: dict[str, Any]
    created_at: datetime


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

class ProductCreate(OrmBase):
    name: str
    code: str
    category_id: uuid.UUID | None = None
    brand_kit_id: uuid.UUID | None = None
    # Optional variant fields; if omitted the API uses "default" / "one-size"
    color: str | None = None
    size: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ProductUpdate(OrmBase):
    name: str | None = None
    code: str | None = None
    category_id: uuid.UUID | None = None
    brand_kit_id: uuid.UUID | None = None
    source_image_key: str | None = None
    attributes: dict[str, Any] | None = None
    status: ProductStatus | None = None


class ProductRead(OrmBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    code: str
    name: str
    category_id: uuid.UUID | None
    brand_kit_id: uuid.UUID | None
    source_image_key: str | None
    status: ProductStatus
    attributes: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    # Includes the default variant so the shape is Path B-compatible.
    # Sessions 3-8 always return exactly one variant.
    variants: list[_VariantInternal] = []


class ProductListItem(OrmBase):
    id: uuid.UUID
    code: str
    name: str
    status: ProductStatus
    source_image_key: str | None
    created_at: datetime


class ProductListResponse(OrmBase):
    items: list[ProductListItem]
    total: int
    cursor: str | None = None
