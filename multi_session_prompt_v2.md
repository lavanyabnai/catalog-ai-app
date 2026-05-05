# Multi-session implementation prompt — AI cataloging app (image + video MVP, with Path B foundation)

> **How to use this document.** Each section below is a self-contained session prompt you can paste into Claude Code (or another coding agent) one at a time. Sessions are sequential — do not start session N until session N-1 is complete and its acceptance criteria are met. Between sessions, the agent's context resets, so each session prompt re-establishes the project state via the `PROJECT.md` and `STATE.md` files maintained throughout.
>
> **Scope of this build:** steps 1–4 of the workflow (intake, ingestion, generation, asset bundle assembly), restricted to **image and video generation only**. Copy generation, channel distribution, optimization, and the autonomous ingestion/optimization agents are explicitly out of scope and will be added later.
>
> **Path A vs Path B:** this build delivers Path A (image and video generation tool). However, the data model is shaped to support Path B (full cataloging platform with taxonomy, SEO, marketplace mapping) without future schema rewrites. Three specific Path B foundations are baked in: product/variant hierarchy, typed category and attribute schema, and reserved identifier/SEO columns. These foundations are *invisible to the merchant in the MVP UI* — they exist in the schema only so later sessions can populate and surface them without painful retrofits.
>
> **Total sessions:** 8. Estimated time: 3–5 focused days of agent work, plus your review time between sessions.

---

## Global context (paste at the top of every session)

```
You are working on an AI cataloging application for fashion retailers. The product
takes a flatlay or mannequin photo of a garment and generates on-model imagery and
short product videos that the retailer can use across their sales channels.

Tech stack (locked):
- Frontend: Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui
- Backend: Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic
- Queue: Celery + Redis
- Database: Postgres 16 with pgvector
- Storage: S3-compatible (use MinIO locally, R2 in prod)
- AI inference: fal.ai for FLUX.2 (images) and Kling/Veo (video) via their HTTP APIs
- Auth: Clerk
- Observability: Sentry + Langfuse
- Local dev: Docker Compose

Scope for this build (steps 1-4 of the full workflow only):
1. Garment intake (manual upload via web UI; bulk CSV deferred)
2. Ingestion (segmentation, background removal, attribute capture — manual, NOT agentic)
3. Generation (image variants and short video, via fal.ai)
4. Asset bundle assembly (versioned storage, ready-for-review state)

Path A vs Path B:
This is a Path A build (image/video generation MVP). However the schema bakes in
three Path B foundations to avoid future migrations:
- Product/variant hierarchy (one product, many color/size variants)
- Typed taxonomy (category tree + attribute definitions per category)
- Reserved identifier and SEO columns (GTIN, MPN, brand, slug, meta_title, meta_description)
These foundations are PRESENT in the schema but INVISIBLE in the MVP UI. Do not
build merchant-facing UI for them. They exist so future sessions can layer on
cataloging features (channel mapping, SEO copy, marketplace export) without
rewriting the spine.

Explicitly out of scope:
- Copy / SEO description generation (columns reserved, no generation logic)
- Multi-channel distribution
- A/B testing and optimization
- Ingestion agent, channel agent, optimization agent
- Mobile app
- Public API / SDK
- C2PA watermarking (will be added before launch but not in MVP)
- Inventory and pricing
- Variant-specific imagery (all imagery attaches to Product, not Variant, in MVP)
- Bulk CSV import (deferred to a later build)

Read PROJECT.md and STATE.md before doing anything else. Update STATE.md at
the end of every session with what you completed and what is pending.
```

---

## Session 1 — Repository scaffold and project documentation

**Goal:** establish a clean monorepo, the documentation that subsequent sessions depend on, and a working `docker compose up` that boots the empty stack.

**Prompt to paste:**

```
Read the global context block above.

This is session 1 of 8. The repository is empty.

Tasks:
1. Create a monorepo with this structure:
   /apps/web         (Next.js 14 app)
   /apps/api         (FastAPI app)
   /apps/worker      (Celery worker, shares code with /apps/api)
   /packages/shared  (shared TypeScript types — initially empty)
   /infra/docker     (Docker Compose, Dockerfiles)
   /docs             (architecture notes, ADRs)

2. Initialize:
   - pnpm workspaces at the repo root
   - Next.js 14 in /apps/web with App Router, TypeScript strict, Tailwind, ESLint
   - Python 3.12 project in /apps/api using uv (or poetry — pick one and document)
   - Empty /apps/worker that imports from /apps/api

3. Write /PROJECT.md covering:
   - Product summary (3-4 sentences from the global context)
   - Architecture overview (web → api → queue → worker → fal.ai)
   - Locked tech choices and rationale (one line each)
   - How to run locally (docker compose up, env vars required)
   - Out-of-scope list (copy from global context)
   - Path A vs Path B section explaining the three baked-in foundations and
     the rule that they are schema-only in the MVP

4. Write /STATE.md as a living document. For session 1, populate:
   ## Completed
   - Session 1: scaffolding
   ## In progress
   - (empty)
   ## Pending
   - Sessions 2-8 (list titles only)
   ## Path B foundations status
   - Product/variant hierarchy: not yet built (session 2)
   - Typed taxonomy: not yet built (session 2)
   - Reserved SEO/identifier columns: not yet built (session 2)
   ## Open questions / blockers
   - (empty)

5. Write a docker-compose.yml that boots:
   - Postgres 16 with pgvector
   - Redis 7
   - MinIO (S3-compatible local storage)
   - The web, api, and worker apps (Dockerfiles can be minimal stubs)

6. Add a Makefile with targets: install, dev, test, lint, db-migrate, db-reset.

7. Add .env.example covering all env vars the code will reference (DATABASE_URL,
   REDIS_URL, S3_*, FAL_KEY, CLERK_*, SENTRY_DSN, LANGFUSE_*).

Acceptance criteria:
- `make install` succeeds
- `docker compose up` boots all services without errors
- Visiting localhost:3000 shows the default Next.js page
- Visiting localhost:8000/health returns {"status": "ok"}
- /PROJECT.md and /STATE.md exist and are accurate

Do NOT install AI libraries or build any feature code yet. This session is
infrastructure only.
```

---

## Session 2 — Data model, migrations, and core API contracts

**Goal:** the database schema and the API request/response shapes the rest of the build will use. No business logic yet, just the contracts. **This session also lays the Path B foundations.**

**Prompt to paste:**

```
Read the global context block at the top of this document, then read /PROJECT.md
and /STATE.md.

This is session 2 of 8. Session 1 (scaffold) is complete.

This session is the most important schema decision in the build. We are
delivering Path A (image/video MVP) but baking in three Path B foundations so
future cataloging features can be added without painful rewrites:
A. Product/variant hierarchy
B. Typed taxonomy (categories + attribute definitions)
C. Reserved identifier and SEO columns

The Path B foundations exist in the schema. They are NOT exposed in the MVP UI.
Sessions 3-8 will treat each Product as having exactly one default Variant
created automatically; the merchant never sees variants in this build.

Tasks:

1. Design the Postgres schema. At minimum:

   Core tenancy and identity:
   - tenants (id, name, created_at)
   - users (id, tenant_id, clerk_user_id, email, role, created_at)

   Brand kits:
   - brand_kits (id, tenant_id, name, color_palette JSONB, tone_notes,
     allowed_scenes JSONB, allowed_personas JSONB, required_aspect_ratios JSONB,
     created_at)

   Path B foundation: typed taxonomy
   - categories (id, tenant_id NULLABLE, parent_id, slug, display_name, path,
     created_at)
     Note: tenant_id NULLABLE means categories can be global (system-seeded)
     or tenant-specific. Seed with a global default tree: Apparel → Women →
     Tops → T-shirts; Apparel → Women → Tops → Blouses; Apparel → Women →
     Dresses; Apparel → Men → Tops → T-shirts. Four to six categories total
     is enough.
   - attribute_definitions (id, category_id, key, display_name, value_type,
     is_required, allowed_values JSONB, created_at)
     value_type enum: string, enum, number, boolean, multi_enum
     Seed a few examples per category (e.g. tops have neckline enum, sleeve_length
     enum, fit enum). Keep the seed minimal — three to five attributes per
     category.

   Path B foundation: products and variants
   - products (id, tenant_id, code, name, category_id NULLABLE, brand_kit_id,
     source_image_key, status, attributes JSONB,
     -- Path B reserved columns, nullable in MVP, no generation logic yet:
     gtin NULLABLE, mpn NULLABLE, brand NULLABLE, slug NULLABLE,
     meta_title NULLABLE, meta_description NULLABLE,
     created_at, updated_at)
     status enum: draft, processing, ready_for_review, approved, archived
     The `attributes` JSONB stores category-specific attribute values
     (e.g. {"neckline": "crew", "sleeve_length": "short"}). It is not
     validated against attribute_definitions in the MVP — that's Path B
     enforcement work for a later session. Just store what's given.

   - variants (id, tenant_id, product_id, sku_code, color, size,
     attributes JSONB,
     -- Path B reserved, nullable:
     gtin NULLABLE, mpn NULLABLE,
     created_at, updated_at)
     Every Product has at least one Variant. Sessions 3-8 auto-create a single
     default variant per product (color/size from the product form, or "default"
     if not provided). The merchant does NOT see variants in MVP UI.

   Generation pipeline:
   - generation_jobs (id, tenant_id, product_id, type, status, provider,
     model_id, prompt JSONB, params JSONB, cost_cents, started_at, finished_at,
     error, error_code)
     type enum: image, video. status enum: queued, running, succeeded, failed.
     Note: jobs reference product_id, not variant_id. All MVP imagery is
     product-level. Variant-specific imagery is a Path B feature.

   - generated_assets (id, tenant_id, product_id, job_id, kind, storage_key,
     width, height, duration_ms, mime_type, metadata JSONB, version, is_hero,
     parent_asset_id NULLABLE, created_at)
     kind enum: image_on_model, video_on_model, image_variant
     parent_asset_id links aspect-ratio crops to their source image.

   - asset_bundles (id, tenant_id, product_id, version, status, approved_by,
     approved_at, created_at)

   - audit_events (id, tenant_id, actor_id, entity_type, entity_id, action,
     payload JSONB, created_at)

   Indices and constraints:
   - tenant_id index on every table
   - Partial unique index on products(tenant_id, code) where status != 'archived'
   - Partial unique index on variants(tenant_id, sku_code) where deleted_at IS NULL
     (or use status if you don't add soft-delete)
   - Index on categories(parent_id) for tree traversal
   - Index on attribute_definitions(category_id)

2. Write the SQLAlchemy 2.0 models in /apps/api/app/models/. Group them
   logically: tenancy.py, taxonomy.py (categories, attribute_definitions),
   catalog.py (products, variants), generation.py (jobs, assets, bundles),
   audit.py.

3. Write the initial Alembic migration. `make db-migrate` should apply it.

4. Write a seed script /apps/api/app/seed.py that populates:
   - The default category tree (4-6 categories)
   - Two or three attribute definitions per leaf category
   - Eight default ModelPersonas (covering diverse body types and ethnicities) —
     these are referenced in session 5 but the table can be created here for
     consistency. Define a model_personas table with: id, tenant_id NULLABLE,
     display_name, body_type, ethnicity, age_range, height_cm,
     gender_presentation, hair, system_managed BOOLEAN.
   Add `make db-seed` to the Makefile.

5. Implement Postgres row-level security policies that filter by tenant_id
   based on a session variable `app.current_tenant_id`. For tables with
   nullable tenant_id (categories, attribute_definitions, model_personas),
   the policy must allow rows where tenant_id IS NULL OR tenant_id matches
   the session variable. Document this pattern in
   /docs/adr/0001-row-level-security.md.

6. Define Pydantic schemas in /apps/api/app/schemas/ for every entity above:
   create, update, and read variants where relevant. Keep variant schemas
   internal — they're not exposed via API in the MVP.

7. Define the API surface in OpenAPI (FastAPI auto-generates this — just write
   the route signatures with `pass` or a 501 placeholder body).

   Note the rename from /skus to /products. Internally, every product has a
   default variant, but the API operates on Products in the MVP.

   POST   /api/v1/products
   GET    /api/v1/products
   GET    /api/v1/products/{id}
   PATCH  /api/v1/products/{id}
   POST   /api/v1/products/{id}/upload-url       (presigned S3 upload URL)
   POST   /api/v1/products/{id}/generate         (starts a generation job)
   GET    /api/v1/jobs/{id}
   GET    /api/v1/products/{id}/bundle           (current asset bundle)
   POST   /api/v1/bundles/{id}/approve
   GET    /api/v1/brand-kits
   POST   /api/v1/brand-kits
   GET    /api/v1/categories                     (read-only in MVP, lists tree)

   POST /api/v1/products accepts: name, code, category_id (optional),
   brand_kit_id, color (optional), size (optional), attributes (optional).
   Internally creates the Product row plus one default Variant row.

8. Generate matching TypeScript types into /packages/shared from the OpenAPI
   schema. Use `openapi-typescript`. Wire this into the Makefile as `make types`.

9. Write a /docs/adr/0002-product-variant-foundation.md ADR explaining:
   - Why Product/Variant exists in MVP despite not being user-visible
   - The rule that MVP imagery attaches to Product, not Variant
   - The migration path Path B will take to add variant-specific imagery
     (it's additive: a new generated_assets.variant_id column, nullable, with
     existing rows defaulting to product-level)

Acceptance criteria:
- `make db-migrate` applies cleanly to a fresh database
- `make db-reset` drops, recreates, and re-applies migrations
- `make db-seed` populates categories, attribute_definitions, and
  model_personas without errors
- Visiting localhost:8000/docs shows all routes from task 7
- /packages/shared/types.ts exists and is generated from the live OpenAPI schema
- `pytest -q` runs zero tests but exits 0 (test harness is wired)
- All routes return 501 Not Implemented for now
- A SELECT against the categories table returns the seeded tree
- ADR 0001 (RLS) and ADR 0002 (product/variant foundation) both exist

Update /STATE.md before finishing. Mark all three Path B foundations as
"schema in place, no UI" under the dedicated status section.
```

---

## Session 3 — Auth, multi-tenancy, and S3 upload

**Goal:** a real authenticated user can sign in, get a presigned upload URL, drop a flatlay into S3, and create a Product row tied to that file. Still no AI work.

**Prompt to paste:**

```
Read the global context block at the top of this document, read /PROJECT.md and
/STATE.md.

This is session 3 of 8. The schema and API skeleton from session 2 are in place.

Reminder on Path B: Product/variant hierarchy exists in the schema. The MVP UI
only shows products. When the merchant creates a product, the API auto-creates
one default variant under the hood. Do not build any variant UI.

Tasks:
1. Wire Clerk auth into /apps/web. Use Clerk's Next.js SDK. The app should
   require sign-in to view any /app route; the marketing page at / can be public.

2. On the API side, write a FastAPI dependency that validates the Clerk JWT,
   resolves the user, attaches the tenant_id to the request, and sets the
   `app.current_tenant_id` session variable for RLS. Apply it to all /api/v1/*
   routes.

3. Implement tenant provisioning: on first sign-in, create a tenant and a user
   row. Use a Clerk webhook (POST /api/webhooks/clerk) for the user.created event.

4. Implement the S3 upload flow:
   - POST /api/v1/products creates a draft Product row PLUS a default Variant row
     in the same transaction. The variant's color/size come from the request if
     provided, else "default"/"one-size". Returns the Product id only.
   - POST /api/v1/products/{id}/upload-url returns a presigned PUT URL valid for
     5 minutes, scoped to a key like
     `tenants/{tenant_id}/products/{product_id}/source.jpg`
   - The web app uploads directly to S3 using that URL
   - The web app then PATCHes the Product with `source_image_key` set

5. Implement the Product list and detail endpoints (GET /api/v1/products,
   GET /api/v1/products/{id}) with proper RLS. Add pagination (cursor-based,
   page size 20). The detail response includes the default variant inline
   under a `variants` array (always length 1 in MVP) so the response shape is
   already Path B-compatible.

6. Implement GET /api/v1/categories returning the seeded tree as a nested
   structure. Read-only in MVP.

7. Build the minimal web UI:
   - /app  → Product list (table view with code, name, status, thumbnail)
   - /app/new  → upload form matching wireframe B from the spec
     (left side: drop zone; right side: attributes form)
     Form fields: product code, name, garment type (a select that maps to
     category_id under the hood — show display names like "T-shirt", "Blouse",
     "Dress"; do NOT expose the category tree as such in MVP), color, material,
     size range, brand kit selector.
     The category select pulls from GET /api/v1/categories and shows leaf
     categories only. Internally, the form posts category_id; the merchant
     just sees garment-type names.
   - /app/products/{id}  → detail page that shows the source image and metadata
     (the generation studio comes in session 6)

8. Add the audit_events writes for: product.created, product.uploaded,
   product.updated.

Acceptance criteria:
- A new user signs up via Clerk, lands in /app, sees an empty product list
- They click "+ new product", fill attributes, drop an image, and the product
  appears in the list with status `draft` and a thumbnail
- Two different Clerk users in two different tenants cannot see each other's
  products (write a pytest integration test that proves this)
- Each created product has exactly one variant row in the database
  (write a test for this)
- The garment-type dropdown in the form is populated from the seeded
  categories table
- The audit_events table has rows for the actions above

Do NOT call fal.ai or any AI provider yet. The "generate" button on the detail
page can exist but should be disabled or show "coming in next session".

Update /STATE.md.
```

---

## Session 4 — Worker, queue, and fal.ai integration (images only)

**Goal:** a product's source image flows through the Celery worker to fal.ai and comes back as one or more on-model images stored in S3. Wire it end-to-end with one model and one pose, no UI niceties yet.

**Prompt to paste:**

```
Read the global context block at the top of this document, read /PROJECT.md
and /STATE.md.

This is session 4 of 8. Auth, upload, and Product CRUD are working.

Reminder: imagery in MVP attaches to Product, not Variant. The variant exists
in the schema but is not referenced by the generation pipeline.

Tasks:
1. Add fal.ai client setup in /apps/api/app/services/fal_client.py. Use httpx
   async. Read FAL_KEY from env. Wrap the client so the rest of the codebase
   never imports fal-specific code directly — the abstraction must allow
   swapping to Replicate or self-hosted later.

2. Define a `GenerationProvider` protocol in /apps/api/app/services/providers/base.py:
       async def segment_garment(request: SegmentationRequest) -> SegmentationResult
       async def generate_image(request: ImageGenerationRequest) -> ImageGenerationResult
       async def generate_video(request: VideoGenerationRequest) -> VideoGenerationResult
   Implement FalProvider in /apps/api/app/services/providers/fal.py.

3. Pre-process the source image with a segmentation step before passing to FLUX.
   Use fal's BiRefNet (or rembg as a fallback) to remove the background and
   isolate the garment. Cache the segmented version in S3 alongside the
   original. The on-model generation uses the segmented garment as input;
   this materially improves output quality compared to feeding raw flatlays
   with cluttered backgrounds.

4. For images, use FLUX.2 dev/pro on fal (whatever is current). The request
   should accept:
   - segmented_garment_url
   - product metadata (category, color, material, attributes)
   - model attributes (body type, ethnicity, age range, gender)
   - pose (front, three-quarter, walking)
   - scene (studio_white for now — additional scenes in session 5)
   - aspect_ratio (default 4:5)
   The provider builds an appropriate prompt internally — keep prompt-engineering
   logic in /apps/api/app/services/prompts/image_prompts.py so it's testable.

5. Implement the generation pipeline:
   - POST /api/v1/products/{id}/generate accepts a list of "shots" the merchant
     wants. For now hardcode the default to: 4 model variants × 1 pose × 1 scene
     = 4 images.
   - The endpoint creates one generation_job per shot (status=queued), enqueues
     a Celery task per job, returns the job ids and a bundle id.
   - The Celery task in /apps/worker/tasks/generate_image.py:
       a. Loads the job, sets status=running
       b. Ensures a segmented version of the source exists (segment if not)
       c. Calls FalProvider.generate_image with the segmented garment
       d. Polls for completion (fal jobs can take 10-60s)
       e. Downloads the resulting image, writes to S3 at
          tenants/{tenant_id}/products/{product_id}/v{version}/img_{job_id}.webp
       f. Creates a generated_assets row
       g. Sets job status=succeeded, records cost_cents
       h. On failure, sets status=failed and stores the error
   - Update the product status to `processing` when the first job starts and to
     `ready_for_review` when all jobs in the bundle finish.

6. Add idempotency: if the same product is generated twice, create a new bundle
   with version = max(existing versions) + 1. Old bundles are retained.

7. Add Langfuse tracing: every fal call (segmentation, image gen) wraps in a
   Langfuse span with prompt, model, latency, cost, and output asset id.

8. Write tests:
   - Unit test for the prompt builder (snapshot test of the prompt string for
     a fixed garment + model + pose input)
   - Unit test that segmentation runs before image generation when no
     segmented version exists
   - Integration test using a mocked FalProvider that returns a fixture image,
     end-to-end from POST /generate to ready_for_review
   - Failure-path test: provider raises, job goes to failed, product status is
     unchanged from `processing` and there's an audit event

Acceptance criteria:
- With a real FAL_KEY in .env, hitting POST /api/v1/products/{id}/generate on a
  product that has a source image returns within 200ms with job ids
- A segmented version of the source appears in S3 within seconds of the first
  generation request
- 30-90 seconds later, the product has 4 generated_assets rows and status
  ready_for_review
- The generated images are visible in MinIO under the expected prefix
- Langfuse shows segmentation and image-gen spans for the run with cost and latency

Do NOT build the studio UI yet — verify via API and the existing detail page,
which can render thumbnails of all generated_assets for the product.

Update /STATE.md and add a /docs/adr/0003-provider-abstraction.md ADR.
```

---

## Session 5 — Image generation: scenes, poses, and brand kits

**Goal:** turn the single-shot pipeline into a real generation surface that produces a full bundle of varied images per product and respects brand kit constraints.

**Prompt to paste:**

```
Read the global context block at the top of this document, read /PROJECT.md
and /STATE.md.

This is session 5 of 8. Single-shot image generation works end-to-end.

Tasks:
1. Expand the scene library. Define scenes as data, not code, in
   /apps/api/app/services/scenes/library.py:
   - studio_white
   - studio_neutral
   - coastal_cafe
   - sunlit_street
   - golden_hour_outdoor
   - urban_loft_interior
   Each scene has: id, display_name, prompt_fragment, negative_prompt_fragment,
   compatible_garment_categories (list of category slugs), lighting_notes.

2. Expand pose options similarly in poses/library.py: front, three_quarter,
   back, walking, sitting, hands_in_pockets, looking_away.

3. The model_personas table was created in session 2 and seeded with 8 default
   personas. In this session, add:
   - GET /api/v1/personas (returns global personas + tenant's own)
   - POST /api/v1/personas (creates a tenant-specific persona)
   Tenants can create their own personas; system_managed personas are read-only.

4. Implement brand kit application:
   - A brand kit defines: allowed_scenes (whitelist by scene id), allowed_personas
     (whitelist by persona id, or "diverse_default"), tone_notes (free text),
     required_aspect_ratios (list, default ['4:5', '1:1', '9:16']).
   - When a product is generated, the prompt builder reads the brand kit and
     constrains the output: only allowed scenes, only allowed personas, all
     required aspect ratios produced.

5. Replace the hardcoded "4 model variants × 1 pose × 1 scene" plan with a
   plan-builder service:
   - Input: Product + brand kit + optional overrides
   - Output: list of GenerationShot specs (persona, pose, scene, aspect_ratio)
   - Default plan: 4 personas × 2 poses × 1 hero scene = 8 shots, plus
     1 detail/back shot = 9 image jobs per bundle.
   - Surface the generated plan to the API caller before enqueueing so the
     client can edit it. Add POST /api/v1/products/{id}/plan that returns the
     plan without enqueueing, and POST /api/v1/products/{id}/generate that
     takes a plan (or builds the default if absent) and enqueues.

6. Add aspect-ratio post-processing: every image is generated at the model's
   native resolution and then auto-cropped to all aspect ratios in the brand
   kit's required list. Use Pillow for the crop; center on the model's bounding
   box (use a simple person-detection — fal provides this, or use a lightweight
   ONNX yolo). Each crop is its own generated_assets row with kind=image_variant
   and a `parent_asset_id`.

7. Add the "model spec" feature: for every primary on-model image, store the
   persona's height and the size of the garment used in the prompt. Expose it
   on the asset metadata (e.g.
   `{"model_height_cm": 178, "model_height_imperial": "5'10\"",
     "garment_size_worn": "S"}`). The studio UI in session 6 will render this.

Acceptance criteria:
- A single POST /api/v1/products/{id}/generate produces 9 primary images plus
  N variants per image (one per required aspect ratio)
- All images respect the brand kit (verified by checking the prompt log
  against the brand kit's allowed scenes/personas)
- Each generated_assets row has the model spec metadata populated
- Generation cost per bundle is logged and visible per tenant
- A test confirms that two products with different brand kits produce visibly
  different scene/persona distributions
- A tenant can create a custom persona via API, and a product generation can
  use it via plan override

Update /STATE.md.
```

---

## Session 6 — Generation studio UI

**Goal:** the merchant-facing screen where humans review, regenerate, and approve. Match wireframe C from the spec.

**Prompt to paste:**

```
Read the global context block at the top of this document, read /PROJECT.md
and /STATE.md.

This is session 6 of 8. The image generation backend is complete.

Reference: wireframe C from the product spec describes this screen. Match its
layout: 200px left rail (model + scene controls), center variant gallery
(4-column grid), 220px right rail (auto-generated metadata, model spec,
compliance placeholder).

Tasks:
1. Build /app/products/{id}/studio in /apps/web. Layout matches wireframe C:
   - Header: product name, code, time elapsed for current bundle, two buttons
     ("Regenerate" and "Approve bundle")
   - Left rail (200px): Model controls (persona selector, pose multi-select,
     scene picker), each control updates the plan via PATCH /api/v1/products/{id}/plan
   - Center: Variant gallery in a 4-column grid. Each tile shows the image
     thumbnail, badges indicating pose and scene, and a "set as hero" action
   - Right rail (220px): Auto-generated metadata card showing model spec
     ("5'10", wearing size S") and a placeholder "Compliance" card that says
     "Watermarking added in v2"

2. Implement real-time job status updates. Use server-sent events from
   /api/v1/products/{id}/events. The studio page subscribes; tiles transition
   from skeleton → loading spinner → image as their job completes. Closing the
   page does not cancel jobs.

3. Implement single-asset regeneration: clicking a tile and choosing
   "Regenerate this shot" enqueues a single generate-image job for that shot
   spec, replaces the asset on success, and increments the asset's version
   (the bundle version stays the same).

4. Implement hero image selection: clicking "Set as hero" on a tile writes
   is_hero=true on that asset and is_hero=false on all others in the bundle.
   At most one hero per bundle. Hero selection is REQUIRED before video
   generation in session 7 — block the video flow if no hero is set.

5. Implement bundle approval: POST /api/v1/bundles/{id}/approve marks the
   bundle as approved, sets the product status to `approved`, freezes the asset
   list (no more regenerations against this bundle — a new bundle is required),
   and writes audit events. Approval requires a hero to be set; return 400 if not.

6. Implement bundle download: on approval, generate a downloadable zip
   manifest containing all approved assets organized into folders by aspect
   ratio (e.g. /4x5/, /1x1/, /9x16/) plus a sidecar metadata.json with the
   model spec, persona, scene, and generation parameters per asset.
   Expose GET /api/v1/bundles/{id}/download that returns a presigned URL to
   the zip. Add a "Download bundle" button to approved bundles.

7. Implement bundle history: a small "Bundles" tab on the product page lists
   every bundle (v1, v2, v3) with their generation date, cost, hero image,
   and approval status. Approved bundles are read-only.

8. Add empty/loading/error states for every async surface. Use shadcn/ui
   skeletons.

9. Add basic accessibility: every image has alt text built from
   `{product_name} on {persona.display_name}, {pose}, {scene}`. Keyboard
   navigation through the gallery works.

Acceptance criteria:
- Full happy path works in a browser: upload → studio shows 9 tiles
  populating live → user picks a hero → user clicks approve → product status
  is `approved`, bundle is frozen, download zip is available
- Approval without a hero returns a clear error and does not change state
- Regenerating a single tile works and replaces only that asset
- Bundle history shows all prior bundles for a product
- The downloaded zip contains the expected folder structure and metadata.json

Do NOT add a bulk approval flow or multi-product operations yet.

Update /STATE.md.
```

---

## Session 7 — Video generation

**Goal:** add short product video to the bundle. One video per product bundle, 5 seconds, vertical 9:16 format suitable for Reels and TikTok.

**Prompt to paste:**

```
Read the global context block at the top of this document, read /PROJECT.md
and /STATE.md.

This is session 7 of 8. Image generation and the studio are complete.

Prerequisite: video generation requires a hero image to be selected on the
bundle (see session 6). Block the video flow if no hero exists.

Before you start — read these files:
- apps/api/app/services/providers/base.py — VideoGenerationRequest/VideoGenerationResult
  already defined; source_image_url is the conditioning frame.
- apps/api/app/services/providers/fal.py — generate_video() at line 124 is a
  NotImplementedError stub ready to be implemented.
- apps/api/app/tasks/generate_image.py — _check_bundle_complete() is the
  bundle-completion hook to extend for video triggering. Do NOT add a Celery
  chord — extend this function instead (see Task 3).
- apps/worker/tasks/generate_video.py — thin Celery dispatcher stub ready to
  be wired to a real task function.
- apps/api/app/core/celery.py — only has enqueue_generate_image; add
  enqueue_generate_video here.
- apps/api/app/routers/assets.py — set_hero endpoint already exists; extend it
  to trigger video when bundle.video_pending_hero is set.
- apps/web/app/app/products/[id]/studio/_components/studio-view.tsx — gallery
  renders bundle.jobs in a 4-col grid as AssetTile. The video job (type=video)
  needs a separate VideoTile component — split jobs by type, not by position.

Tasks:
1. Implement Kling video generation in FalProvider.
   Fill in generate_video() in apps/api/app/services/providers/fal.py.
   Use fal-ai/kling-video/v1.6/standard/image-to-video (or
   fal-ai/kling-video/v2/standard/image-to-video if available — check fal.ai
   docs at build time). If Kling is unavailable fall back to fal-ai/veo2.
   The swap is one constant at the top of fal.py.

   Parameters: image_url (conditioning frame uploaded to fal.ai storage),
   prompt (built from the motion spec), duration = 5 seconds (Kling supports
   5s and 10s; do not use 8s — it is not a valid option), aspect_ratio = "9:16".
   Return VideoGenerationResult with duration_ms=5000.

2. Define video motion specs.
   New file apps/api/app/services/scenes/video_motions.py — frozen dataclasses,
   same pattern as scenes/library.py and poses/library.py:
   - slow_turn_360: "slowly rotating 360 degrees in place, studio white background"
   - confident_walk: "walking confidently toward camera, lifestyle setting"
   - product_pickup: "close-up hand adjusting garment detail, soft focus background"
   - golden_hour_pose: "outdoor lifestyle pose, golden hour light, gentle breeze"
   Each has: id, display_name, prompt_fragment.
   Provide get_motion(id) and get_all_motions() helpers.
   Update VideoGenerationRequest in base.py: rename motion default from
   "gentle_walk" to "confident_walk" to match the new ID.

3. Video pipeline — extend _check_bundle_complete, no Celery chord.
   Do NOT add a Celery chord. Extend _check_bundle_complete in
   apps/api/app/tasks/generate_image.py instead. After setting
   product.status = ready_for_review:

   a. Check if all image jobs (type=image) in the bundle succeeded.
   b. If yes, look up the bundle's hero asset (GeneratedAsset with is_hero=True
      and version=bundle.version).
   c. If hero found → find the bundle's video job (GenerationJob with type=video
      and params["bundle_id"] == bundle_id) and call
      enqueue_generate_video(str(video_job.id)).
   d. If no hero yet → set bundle.video_pending_hero = True (new column, see
      Task 5) and commit.

   Video job creation — update POST /products/{id}/generate in products.py to
   create one additional GenerationJob with type=video, status=queued, and
   prompt = {"motion": "confident_walk", "scene": brand_kit scene or
   "studio_white", "duration_seconds": 5}. This job stays queued until
   _check_bundle_complete fires — do NOT pass it to enqueue_generate_image.
   The job IS included in bundle.jobs so it appears in the studio as the video
   tile (in pending/waiting state).

   Extend set_hero in apps/api/app/routers/assets.py — after confirming the
   hero, query the bundle. If bundle.video_pending_hero is True: set it to
   False, find the bundle's video job, call enqueue_generate_video. Write an
   audit event "video_enqueued_after_hero".

4. New Celery task: run_generate_video_task.
   New file apps/api/app/tasks/generate_video.py (analogous to
   generate_image.py):
   1. Load job, mark running. Verify a hero asset exists for the bundle
      (query version=job.params["bundle_version"], is_hero=True). If none,
      mark job failed with error_code="no_hero" and return.
   2. Download hero asset bytes from S3 (download_bytes(hero_asset.storage_key)).
   3. Upload to fal.ai storage via provider._client.upload_file — returns a
      short-lived fal.ai URL for the conditioning frame.
   4. Check per-tenant daily video cap (Task 5) — raise VideoCappedError if
      exceeded.
   5. Call provider.generate_video(VideoGenerationRequest(source_image_url=
      fal_hero_url, motion="confident_walk", duration_seconds=5)).
   6. Download video bytes from result URL.
   7. Extract a poster frame: ffmpeg -i input.mp4 -vframes 1 -q:v 2 -f
      image2pipe -vcodec mjpeg pipe:1 via asyncio.to_thread(subprocess.run).
      Store poster at tenants/{tid}/products/{pid}/v{version}/
      video_{job_id}_poster.jpg.
   8. Upload video to S3 at tenants/{tid}/products/{pid}/v{version}/
      video_{job_id}.mp4, mime_type="video/mp4".
   9. Create GeneratedAsset with kind=video_on_model, mime_type="video/mp4",
      duration_ms=5000, asset_metadata={"motion": motion, "poster_key":
      poster_key, "hero_asset_id": str(hero_asset.id)}.
   10. Create a second GeneratedAsset for the poster with kind=image_variant,
       parent_asset_id=video_asset.id.
   11. Mark job succeeded.

   Wire apps/worker/tasks/generate_video.py to call
   asyncio.run(run_generate_video_task(job_id)).
   Add ffmpeg to infra/docker/Dockerfile.worker.

5. Schema — new Alembic migration 0002_video_fields.py.
   Two additions:
   - asset_bundles.video_pending_hero: Boolean NOT NULL DEFAULT false
   - tenants.daily_video_cap: Integer NULLABLE (NULL = system default of 10)
   Add the corresponding mapped columns to the SQLAlchemy models in
   generation.py (AssetBundle) and tenancy.py (Tenant).

   Per-tenant daily cap check: count GenerationJob rows where tenant_id=X AND
   type='video' AND created_at >= start of today UTC. Compare against
   tenant.daily_video_cap ?? 10. If at or over the cap raise
   VideoCappedError("Daily video cap reached"). Catch in the task, mark job
   failed with error_code="video_cap_exceeded", emit an audit event.

6. Studio UI — video tile.
   Split bundle.jobs by type in studio-view.tsx:
   - Image jobs (job.type === "image") → AssetTile in 4-column grid (existing)
   - Video job (job.type === "video") → new VideoTile, rendered full-width
     below the image grid

   Add job.type to JobRead schema in apps/api/app/schemas/generation.py
   (the field is on the model but not currently in the schema).

   New file apps/web/app/app/products/[id]/studio/_components/video-tile.tsx:
   - No hero selected → "Select a hero image to generate the video" placeholder
   - Job queued/running → spinner + "Generating video…"
   - Job succeeded → poster frame thumbnail with ▷ play button overlay;
     clicking opens a <dialog> modal with a <video> element
   - Job failed → error message + "Regenerate video" button
   - "Regenerate video" button (when succeeded, bundle not approved) calls
     POST /api/v1/assets/{video_asset_id}/regenerate — the existing regenerate
     endpoint clones the original job prompt, which is correct; the task
     re-fetches the current hero at execution time (step 1 of Task 4)

7. Update bundle download zip.
   In apps/api/app/routers/bundles.py, add kind to the asset snapshot tuple
   in _build_zip. When kind == "video_on_model", place the file under video/
   instead of the aspect-ratio folder. The poster (image_variant child with
   parent_asset_id pointing to the video asset) also goes under video/.

8. Tests:
   - test_video_pipeline.py — mock provider returns a fixture mp4; assert
     GeneratedAsset row created with kind=video_on_model, job succeeded, poster
     asset created.
   - test_video_cap.py — seed N video jobs for today exceeding the cap; assert
     task raises VideoCappedError and marks job error_code="video_cap_exceeded".
   - test_video_no_hero.py — bundle with no hero; call _check_bundle_complete;
     assert bundle.video_pending_hero=True and video job NOT enqueued. Then
     call set_hero; assert video_pending_hero=False and video job enqueued.
   - test_video_image_failure.py — one image job fails; assert
     _check_bundle_complete does NOT enqueue the video task (policy: all image
     jobs must succeed; if any fail, set video_pending_hero=True so the
     merchant can regenerate the failed shot first).

Acceptance criteria:
- A new product run produces 9 images plus 1 video (after hero is selected)
- Total bundle generation time is under 5 minutes for a typical run
- The video is playable in the studio modal and downloads as a watermark-free
  mp4 (watermarking comes later)
- Cost meter for the bundle reflects both image and video provider charges
- The download zip includes video/{job_id}.mp4 and video/{job_id}_poster.jpg
- TypeScript check and all new tests pass

Update /STATE.md.
```

---

## Session 8 — Hardening, observability, and a deployable build

**Goal:** the MVP is feature-complete. Make it boring and shippable. **Also: produce the input document that drives the next multi-session prompt, including the Path B roadmap.**

**Prompt to paste:**

```
Read the global context block at the top of this document, read /PROJECT.md
and /STATE.md.

This is session 8 of 8. All image and video generation features are complete.

Before you start — read these files to understand the exact current state:
- apps/api/main.py — CORS origins are hardcoded to localhost:3000; Sentry is
  in config but not initialized. Fix both here.
- apps/api/app/core/config.py — already uses pydantic-settings for all API
  env vars. Add cors_origins, otel_endpoint, and otel_service_name here.
- apps/worker/celery_app.py — uses os.getenv directly; this is intentional for
  a standalone Celery process and does not need pydantic-settings. But it needs
  queue routing added for the per-task concurrency split.
- apps/api/app/services/fal_client.py — FalError is already defined;
  _POLL_MAX_SECONDS=180 is the current timeout. Retry logic should live here.
- apps/api/app/models/generation.py — error_code on GenerationJob is a
  String(100) nullable column, not an enum.
- infra/docker/Dockerfile.api — has a healthcheck, runs as root. Add non-root user.
- infra/docker/Dockerfile.worker — no healthcheck, runs as root. Both need fixing.
- infra/docker/Dockerfile.web — multi-stage, no healthcheck. Add one.

Tasks:
1. Error handling pass.
   Add retry logic in FalClient (apps/api/app/services/fal_client.py) — not
   in the tasks — since it is the only layer that knows the wire format:
   - Network errors / transient HTTP 5xx / 429: exponential backoff up to 3
     retries in _submit, _result, upload_file, and download_url.
     Use asyncio.sleep(2 ** attempt) between retries.
   - HTTP 429: detect via FalError.status_code. Log Retry-After if present;
     set error_code="rate_limited" on the job row. Surface to the merchant via
     the SSE stream as a job_status event with error = "Rate limited — try
     again in N minutes."
   - Poll timeout (TimeoutError already raised at 180s): catch in both task
     functions; set error_code="timeout".
   - S3 errors: wrap upload_bytes and download_bytes calls in
     generate_image.py and generate_video.py with up to 5 retries with
     backoff; on final failure set error_code="s3_error".

   Standardise error_code values: "rate_limited", "timeout", "s3_error",
   "no_hero", "video_cap_exceeded", "provider_error" (catch-all).

   In the studio UI, propagate error and error_code from SSE job_status events
   to AssetTile. For rate_limited show "Rate limited — try again in N min."
   For timeout show "Timed out — try regenerating."

2. Observability pass.
   Sentry:
   In main.py, initialise Sentry early if settings.sentry_dsn is set:
     import sentry_sdk
     if settings.sentry_dsn:
         sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)
   In apps/worker/celery_app.py, do the same using the SENTRY_DSN env var.
   For the Next.js web app, add sentry.server.config.ts, sentry.client.config.ts,
   and sentry.edge.config.ts per the Sentry Next.js v8 SDK docs.

   OpenTelemetry:
   Add otel_endpoint: str = "" and otel_service_name: str = "catalog-ai-api"
   to apps/api/app/core/config.py. In main.py, if otel_endpoint is set,
   initialise opentelemetry-sdk with an OTLP HTTP exporter (Honeycomb and
   Grafana Cloud both accept standard OTLP). Instrument httpx, SQLAlchemy, and
   FastAPI. Apply the same pattern in the worker.

   Langfuse:
   Verify completeness: run_generate_image_task already wraps segment_garment
   and generate_image spans. Add the same span pattern to run_generate_video_task.
   Confirm lf.flush() is in the finally block of both tasks.

   Admin dashboards:
   Add apps/api/app/routers/admin.py with two endpoints, both restricted to
   user.role == UserRole.admin:
   - GET /api/v1/admin/cost — aggregate cost_cents from generation_jobs grouped
     by tenant_id and type (image vs video) for the current calendar month
     (created_at >= date_trunc('month', now())). Return list of
     {tenant_id, tenant_name, image_cost_cents, video_cost_cents, total_cost_cents}.
   - GET /api/v1/admin/jobs/failed — return the 100 most recent generation_jobs
     with status=failed, including error_code, error, product_id, tenant_id,
     created_at.
   Add Next.js pages at apps/web/app/admin/cost/page.tsx and
   apps/web/app/admin/jobs/page.tsx (server components, call admin API).
   Protect /admin in middleware.ts (auth required; backend enforces admin role).
   Register the admin router in apps/api/app/routers/__init__.py.

3. Performance pass.
   Image thumbnails:
   Add imgproxy to docker-compose.yml (darthsim/imgproxy image). Add
   IMGPROXY_KEY and IMGPROXY_SALT to .env.example. Add imgproxy_url: str = ""
   to config.py. Add GET /api/v1/assets/{id}/thumbnail?w=400 that generates a
   signed imgproxy URL from the asset's storage_key and returns 302. In
   production, Cloudflare Images replaces imgproxy; the redirect keeps client
   code identical. Update AssetTile to use this endpoint instead of direct S3.

   Gallery virtualisation:
   If bundle.jobs.length > 50, render the image grid using @tanstack/virtual
   (add to apps/web/package.json). Below 50, keep the current plain grid.

   Database indices:
   Add Alembic migration 0003_indices.py:
     CREATE INDEX IF NOT EXISTS ix_generation_jobs_product_created
       ON generation_jobs (product_id, created_at DESC);
     CREATE INDEX IF NOT EXISTS ix_generated_assets_product_version
       ON generated_assets (product_id, version);
   Note: there is no bundle_id column on generated_assets — assets relate to
   bundles via (product_id, version). Do not index a non-existent column.

   Worker concurrency:
   Add task routing to celery_app.py:
     celery_app.conf.task_routes = {
         "tasks.generate_image": {"queue": "image_queue"},
         "tasks.generate_video": {"queue": "video_queue"},
     }
   Pass queue="image_queue" / queue="video_queue" in apps/api/app/core/celery.py.
   In docker-compose.yml, run two worker containers — one with
   --queues image_queue --concurrency 8 and one with
   --queues video_queue --concurrency 2.

4. Security pass.
   RLS test:
   Write tests/test_rls.py: open a raw asyncpg connection without setting
   app.current_tenant_id. SELECT from every tenant-scoped table. Assert zero
   rows are returned. This verifies the Alembic migration's RLS policies work.

   Presigned URLs:
   Upload URLs already expire in 300s (5 min) — no change needed. Download
   URLs use 3600s (1 hr) — intentional for smooth studio UX. Document both
   values in the runbook; do not change download URL expiry.

   Rate limiting:
   Add slowapi to apps/api/pyproject.toml. Attach a Limiter keyed on
   user.tenant_id (not IP). Apply @limiter.limit("60/hour") to
   POST /api/v1/products/{id}/generate and POST /api/v1/assets/{id}/regenerate.
   Return 429 with body {"detail": "Rate limit exceeded", "retry_after": N}.

   Environment variables:
   The API already uses pydantic-settings exclusively. Add
   cors_origins: list[str] = ["http://localhost:3000"] to config.py and
   replace the hardcoded list in main.py. The worker's os.getenv usage is
   intentional (standalone Celery process) and does not need to change.

   Audits:
   Run uv run pip-audit in apps/api and pnpm audit --audit-level=high at repo
   root. Fix or document every high-severity finding in docs/security-notes.md.

5. Deployment artifacts.
   Dockerfiles:
   Add a non-root user to all three Dockerfiles:
     RUN adduser --disabled-password --gecos "" appuser && USER appuser
   Worker healthcheck: celery -A celery_app inspect ping -d celery@$HOSTNAME
   Web healthcheck: wget -qO- http://localhost:3000/api/health || exit 1
   (add a trivial /api/health route to the Next.js app).

   Deployment config:
   Use Fly.io fly.toml configs (simpler than Helm for an MVP; document that
   Helm is the right next step when moving to k8s). Create fly.api.toml,
   fly.worker-image.toml, fly.worker-video.toml, and fly.web.toml. In each
   API config add:
     [deploy]
     release_command = "alembic upgrade head"
   so migrations run as a pre-deploy step, not on app boot.

   Runbook:
   Write /docs/runbook.md covering: initial deploy, rolling back (fly releases
   rollback), and these incidents:
   - fal.ai outage: failed jobs stay at error_code=provider_error; requeue
     via admin jobs UI once fal is back
   - Postgres connection saturation: check pg_stat_activity; SSE connections
     hold one DB connection per open studio tab — document the limit and the
     env var to tune the pool
   - Redis OOM: clear result backend (redis-cli FLUSHDB) if result accumulation
     is the cause; Celery results are not consumed by default

6. Documentation pass.
   - Update /PROJECT.md to reflect the actual built system (all 8 sessions).
   - Write /scripts/gen_api_docs.py that fetches the live OpenAPI JSON from
     the running API and saves it as /docs/api.md. Add make api-docs target.
   - /docs/architecture.md — Mermaid sequence diagram for a full image + video
     run: browser → API → Celery → fal.ai → S3 → SSE → browser.
   - /CHANGELOG.md starting at v0.1.0 covering all 8 sessions.
   - /docs/next-steps.md with three tracks as listed below.
   - /docs/path-b-readiness.md auditing each Path B feature against the
     current schema: is the schema ready as-is or does it need extension?
     What is the additive work? Use the current models (Product, Variant,
     Category, AttributeDefinition, BrandKit, GeneratedAsset, AssetBundle)
     as the baseline.

   next-steps.md tracks:

   PATH A continuation (image/video generation polish):
   - C2PA watermarking and EU AI Act disclosure
   - Color/material variant generation (recolor without reshoot)
   - Bulk CSV import with validation
   - Brand kit creation/edit UI (currently seeded only)
   - Mobile companion app

   PATH B build-out (cataloging features — requires deliberate scope decision):
   - SEO copy generation (titles, descriptions, alt text, meta tags,
     schema.org Product markup)
   - Multi-language copy
   - Variant-specific imagery (currently all imagery is product-level)
   - Variant management UI (color/size matrix, exposing the variant table
     that already exists)
   - Channel attribute mapping (Amazon, Google Shopping, Meta — uses the
     categories and attribute_definitions tables already in place)
   - Multi-channel distribution (Channel agent)
   - Inventory and pricing
   - Compliance attributes (country of origin, materials composition, care)
   - GTIN/MPN/brand population (columns already reserved)

   AGENTIC LAYER (deferred regardless of path):
   - Ingestion agent (autonomous SKU pickup from supplier feeds)
   - Optimization agent (A/B testing, underperformer refresh)

7. Smoke test script in /scripts/smoke-test.sh.
   Calls real API endpoints via curl, requires jq. Steps:
   1. Create a brand kit: POST /api/v1/brand-kits
   2. Create a product: POST /api/v1/products
   3. Get upload URL: POST /api/v1/products/{id}/upload-url → S3 PUT of
      fixture flatlay image
   4. Patch source key: PATCH /api/v1/products/{id}
   5. Trigger generation: POST /api/v1/products/{id}/generate
   6. Poll GET /api/v1/products/{id} until status == ready_for_review
      (timeout 10 min)
   7. Fetch bundle: GET /api/v1/products/{id}/bundle — assert 9
      image_on_model assets exist
   8. Select hero: POST /api/v1/assets/{hero_asset_id}/hero
   9. Poll bundle until video job status == succeeded (timeout 5 min)
   10. Approve: POST /api/v1/bundles/{bundle_id}/approve
   11. Download zip: GET /api/v1/bundles/{bundle_id}/download — assert
       video/*.mp4 present in zip contents
   12. Document manual teardown (no delete endpoint in MVP)

   The script requires a running docker-compose up stack with a valid FAL_KEY.
   Document how to obtain a Clerk dev JWT for the test user (Clerk dashboard
   → Users → Impersonate → copy session token).

Acceptance criteria:
- /scripts/smoke-test.sh passes against a clean docker-compose up stack
- Sentry, Langfuse, and the OTel collector all show events from a smoke-test run
- /admin/cost shows real cost_cents from the smoke-test tenant
- The runbook is accurate enough for someone unfamiliar with the codebase to deploy
- All new tests pass; TypeScript check passes
- /docs/next-steps.md and /docs/path-b-readiness.md exist and are accurate

Update /STATE.md to mark all 8 sessions complete and reference next-steps.md
and path-b-readiness.md for the path forward.
```

---

## Inter-session protocol

A few rules that make this work in practice rather than in theory:

1. **Always have the agent re-read `STATE.md` first.** Without this, sessions drift. STATE.md is your durable memory between Claude Code sessions whose context resets.
2. **Review between sessions.** Run the acceptance criteria yourself before starting the next session. If a session finished but acceptance criteria failed, file the gap in STATE.md under "Open questions / blockers" before moving on, or ask the agent to do another pass.
3. **Don't compress sessions.** Each session is sized to fit comfortably in one context window. Combining two sessions usually causes the agent to skip steps in both.
4. **Keep the global context block at the top of every prompt.** It re-establishes scope boundaries the agent will otherwise drift past — especially the out-of-scope list and the rule that Path B foundations are *schema-only* in this build.
5. **Do not let the agent build merchant-facing UI for Path B foundations.** The variant table, the category tree beyond a simple dropdown, the reserved SEO/identifier columns — none of these get UI in this build. If the agent starts building a "manage variants" page in session 6 because it sees the table exists, redirect it. The discipline is what keeps the MVP shippable on time.
6. **Save the agent's terminal output.** When something goes wrong in session N+2, the failure is often rooted in a quiet decision the agent made in session N. Logged output makes that recoverable.

## What's deferred (the input to your next multi-session prompt)

After session 8 ships, you have two natural directions that share the same foundation:

**Path A continuation** — polish the image/video product: watermarking, color variants, bulk import, brand kit UI, mobile.

**Path B build-out** — turn the image/video product into a real cataloging platform: SEO copy, variant management surface, channel mapping, multi-channel distribution. Most of this is additive work because the schema already supports it.

The agentic layer (ingestion, channel, optimization agents) sits on top of either path and becomes meaningful once Path B is partially built — there isn't much for an agent to optimize when the product is purely image generation.

`docs/path-b-readiness.md` produced in session 8 is the document that drives the scope of the next multi-session prompt.
