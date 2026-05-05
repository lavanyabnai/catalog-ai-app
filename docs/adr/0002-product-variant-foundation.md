# ADR 0002 — Product/Variant Hierarchy as a Path B Foundation

**Date:** 2026-05-04
**Status:** Accepted

## Context

The MVP (Path A) is an image and video generation tool. Merchants interact with **Products**: they upload a flatlay, generate on-model images and a video, then approve and download the bundle.

However, fashion retail inherently has a product/variant model: one product exists in multiple colors, sizes, and materials. If we model products as flat rows now and add variants later, we face a painful migration: renaming columns, adding a join table, moving foreign keys, and rewriting every query and UI component.

## Decision

**Introduce the Product/Variant split from the very first migration, even though the MVP UI shows only Products.**

The schema contains:

```
products (id, tenant_id, code, name, category_id, …)
    └── variants (id, tenant_id, product_id, sku_code, color, size, …)
```

### MVP rules

1. **Every Product has exactly one Variant.** The API auto-creates a single default variant when a product is created. The variant uses `color` and `size` from the request, or `"default"` / `"one-size"` if not provided.

2. **The merchant never sees variants in this build.** No variant selector, no variant management UI, no variant-specific generation. The variant table exists in the database; its primary purpose is to hold the `sku_code` and to make future migrations additive.

3. **All MVP imagery attaches to `products`, not `variants`.** The `generated_assets` and `generation_jobs` tables have `product_id` foreign keys, not `variant_id`.

4. **Variant schemas are internal.** `ProductRead` includes a `variants` array (always length 1 in MVP) so the JSON shape is Path B-compatible; the frontend only renders the product-level data.

## Why not just add variants later?

The alternatives and their problems:

| Alternative | Problem |
|-------------|---------|
| No variants now, add table later | Requires adding a FK on `generated_assets`, migrating existing rows, updating every query |
| Variants as JSONB on Product | Can't FK, can't index, messy to query in Path B |
| Flat product with sku_code | `sku_code` uniqueness breaks when you introduce colors |

Adding the table now costs one extra join that no one exercises yet. The join is cheap; the future migration it prevents is expensive.

## Migration path for variant-specific imagery (Path B)

When Path B adds variant-specific generation:

1. Add a **nullable** `variant_id` column to `generated_assets`:

   ```sql
   ALTER TABLE generated_assets ADD COLUMN variant_id uuid REFERENCES variants(id);
   ```

2. Existing rows have `variant_id = NULL`, meaning "product-level" (backward compatible).

3. New variant-specific generation jobs set `variant_id` to the target variant.

4. The studio UI gains a variant selector. Selecting a variant filters the gallery to assets where `variant_id = selected_variant OR variant_id IS NULL`.

No existing row needs to be rewritten. No existing query breaks. The migration is purely additive.

## Consequences

**Good:**
- Future variants work is additive, not a rewrite.
- API response shape is already Path B-compatible (the `variants` array is present).
- SKU-code uniqueness is enforced per tenant from day one.

**Bad / Watch out for:**
- Every `POST /api/v1/products` must transactionally create both a Product row and a Variant row. If the variant insert fails and the product insert succeeds, the invariant "every product has at least one variant" is broken. Always use a single DB transaction.
- Session 3+ must never expose the variant table in merchant-facing UI. The variant exists for the schema only.
