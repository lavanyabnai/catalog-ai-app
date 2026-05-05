"""RLS integration test: two tenants cannot see each other's products.

Requires a running Postgres instance with the schema applied.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Product, Variant
from app.models.tenancy import Tenant, User


@pytest.mark.asyncio
async def test_tenant_isolation(
    db: AsyncSession,
    tenant_a: Tenant,
    tenant_b: Tenant,
) -> None:
    # Insert one product per tenant as superuser (no RLS active yet)
    product_a = Product(tenant_id=tenant_a.id, code="PROD-A", name="Product A")
    product_b = Product(tenant_id=tenant_b.id, code="PROD-B", name="Product B")
    db.add_all([product_a, product_b])
    await db.flush()

    # Add required default variants
    db.add(Variant(tenant_id=tenant_a.id, product_id=product_a.id, sku_code="PROD-A"))
    db.add(Variant(tenant_id=tenant_b.id, product_id=product_b.id, sku_code="PROD-B"))
    await db.flush()

    # Switch RLS context to tenant_a — should only see product_a
    await db.execute(
        text("SET LOCAL app.current_tenant_id = :tid"),
        {"tid": str(tenant_a.id)},
    )
    result = await db.execute(select(Product))
    visible = {p.code for p in result.scalars().all()}
    assert "PROD-A" in visible
    assert "PROD-B" not in visible

    # Switch to tenant_b — should only see product_b
    await db.execute(
        text("SET LOCAL app.current_tenant_id = :tid"),
        {"tid": str(tenant_b.id)},
    )
    result = await db.execute(select(Product))
    visible = {p.code for p in result.scalars().all()}
    assert "PROD-B" in visible
    assert "PROD-A" not in visible
