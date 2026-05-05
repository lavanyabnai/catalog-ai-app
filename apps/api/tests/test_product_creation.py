"""Verify that every product is created with exactly one default variant."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Product, Variant
from app.models.tenancy import Tenant


@pytest.mark.asyncio
async def test_product_has_exactly_one_variant(
    db: AsyncSession,
    tenant_a: Tenant,
) -> None:
    product = Product(tenant_id=tenant_a.id, code="SKU-001", name="Test Shirt")
    db.add(product)
    await db.flush()

    variant = Variant(
        tenant_id=tenant_a.id,
        product_id=product.id,
        sku_code="SKU-001",
        color="default",
        size="one-size",
    )
    db.add(variant)
    await db.flush()

    result = await db.execute(
        select(Product)
        .where(Product.id == product.id)
        .options(selectinload(Product.variants))
    )
    loaded = result.scalar_one()
    assert len(loaded.variants) == 1
    assert loaded.variants[0].sku_code == "SKU-001"
    assert loaded.variants[0].color == "default"
    assert loaded.variants[0].size == "one-size"


@pytest.mark.asyncio
async def test_product_code_stored_correctly(
    db: AsyncSession,
    tenant_a: Tenant,
) -> None:
    product = Product(tenant_id=tenant_a.id, code="DRESS-42", name="Summer Dress")
    db.add(product)
    await db.flush()

    result = await db.execute(select(Product).where(Product.id == product.id))
    loaded = result.scalar_one()
    assert loaded.code == "DRESS-42"
    assert loaded.name == "Summer Dress"
    assert loaded.status.value == "draft"
