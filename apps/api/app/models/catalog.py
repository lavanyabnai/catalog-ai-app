from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ProductStatus

if TYPE_CHECKING:
    from app.models.generation import AssetBundle, GeneratedAsset, GenerationJob


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    brand_kit_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("brand_kits.id"), nullable=True)
    source_image_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[ProductStatus] = mapped_column(SAEnum(ProductStatus, name="product_status", create_type=False), nullable=False, default=ProductStatus.draft)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Path B reserved — nullable in MVP, no generation logic
    gtin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mpn: Mapped[str | None] = mapped_column(String(100), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slug: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    variants: Mapped[list[Variant]] = relationship("Variant", back_populates="product", cascade="all, delete-orphan")
    generation_jobs: Mapped[list[GenerationJob]] = relationship("GenerationJob", back_populates="product")
    generated_assets: Mapped[list[GeneratedAsset]] = relationship("GeneratedAsset", back_populates="product")
    asset_bundles: Mapped[list[AssetBundle]] = relationship("AssetBundle", back_populates="product")


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    sku_code: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Path B reserved — nullable in MVP
    gtin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mpn: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Soft-delete for partial unique index on sku_code
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped[Product] = relationship("Product", back_populates="variants")
