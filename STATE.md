# State — catalog-ai

> Living document. Updated at the end of every session. Read this before starting any session.

## Completed

- **Session 1: Repository scaffold and project documentation**
  - Monorepo created: `/apps/web`, `/apps/api`, `/apps/worker`, `/packages/shared`, `/infra/docker`, `/docs`
  - pnpm workspaces configured at repo root
  - Next.js 14 initialized in `/apps/web` (App Router, TypeScript strict, Tailwind, ESLint)
  - Python 3.12 project initialized in `/apps/api` using **uv** (`[tool.uv] package = false`)
  - `/apps/worker` stub created (Celery app wired, tasks are `NotImplementedError` stubs)
  - `/packages/shared` stub created (empty TypeScript types; generated from OpenAPI via `make types`)
  - `docker-compose.yml` boots: Postgres 16 + pgvector, Redis 7, MinIO, api, worker, web
  - `Makefile` with targets: `install`, `dev`, `test`, `lint`, `db-migrate`, `db-reset`, `db-seed`, `types`
  - `.env.example` covering all env vars
  - `/PROJECT.md` and `/STATE.md` written

- **Session 2: Data model, migrations, and core API contracts**
  - SQLAlchemy 2.0 models in `/apps/api/app/models/`:
    - `base.py` (DeclarativeBase), `enums.py` (all enum types as Python `str` enums)
    - `tenancy.py` (Tenant, User), `taxonomy.py` (Category, AttributeDefinition)
    - `personas.py` (ModelPersona), `brand_kits.py` (BrandKit)
    - `catalog.py` (Product, Variant), `generation.py` (GenerationJob, GeneratedAsset, AssetBundle)
    - `audit.py` (AuditEvent)
  - Async DB engine + session factory at `app/core/database.py` (asyncpg)
  - `alembic/env.py` updated: imports `Base`, reads `DATABASE_URL` from env, strips asyncpg driver for psycopg2
  - Manual Alembic migration `0001_initial_schema.py` covering all tables, enums, partial unique indexes, RLS policies, and `updated_at` trigger
  - Seed script `app/seed.py`: 6-node category tree, 12 attribute definitions, 8 diverse system-managed ModelPersonas
  - RLS: all tables enabled, `tenant_isolation` policy per table, nullable-tenant tables allow `IS NULL` rows
  - Pydantic v2 schemas in `app/schemas/`: catalog, generation, taxonomy, brand_kits, tenancy
  - FastAPI route skeletons in `app/routers/` (all return 501); mounted at `/api/v1` in `main.py`
  - `make types` fixed (Windows-safe Python helper `scripts/gen_types.py`)
  - ADR 0001: Row-level security pattern (`docs/adr/0001-row-level-security.md`)
  - ADR 0002: Product/variant foundation (`docs/adr/0002-product-variant-foundation.md`)
  - `pytest -q` passes (1 test, test_health); all 12 API routes visible at `/docs`

- **Session 3: Auth, multi-tenancy, and S3 upload**
  - `app/core/auth.py`: `get_current_user` FastAPI dependency — Clerk JWKS fetch (1-hr TTL), JWT verify via python-jose, User lookup, `SET LOCAL app.current_tenant_id` on DB session, returns `CurrentUser` dataclass
  - `api_router` now requires `get_current_user` globally; `POST /api/webhooks/clerk` is outside the router (no auth)
  - Clerk webhook (`POST /api/webhooks/clerk`): svix signature verification, `user.created` → Tenant + User rows in single transaction (idempotent)
  - `app/services/storage.py`: boto3 S3 client, `configure_bucket()` (create + CORS), `generate_presigned_upload_url(key, content_type)` — respects `S3_PUBLIC_ENDPOINT_URL` for Docker/prod URL separation
  - `app/services/audit.py`: async `record()` writing `AuditEvent` rows
  - `S3_PUBLIC_ENDPOINT_URL` added to `config.py` and `.env.example`
  - `app/services/__init__.py` created (empty)
  - Products router fully implemented: `POST /` (create product + default variant in one transaction), `GET /` (cursor pagination, 20/page, `created_at` desc), `GET /{id}`, `PATCH /{id}` (audit on change), `POST /{id}/upload-url` (presigned PUT URL). `POST /{id}/generate` and `GET /{id}/bundle` remain 501 (session 4).
  - Categories router fully implemented: loads all Category rows, builds nested tree in Python
  - `main.py`: uses `lifespan` context manager (replaces deprecated `@on_event`), calls `configure_bucket()` on startup
  - Frontend: `@clerk/nextjs`, `clsx`, `tailwind-merge`, `lucide-react` installed
  - `apps/web/middleware.ts`: Clerk middleware protecting `/app/*`
  - `apps/web/app/layout.tsx`: `<ClerkProvider>` wrapper
  - `apps/web/components.json`: shadcn/ui config
  - `apps/web/app/globals.css`: full shadcn CSS variable set
  - `apps/web/tailwind.config.ts`: shadcn-compatible color tokens
  - `apps/web/lib/utils.ts`: `cn()` helper
  - `apps/web/lib/api.ts`: `apiGet`, `apiPost`, `apiPatch` with Bearer token
  - `apps/web/app/app/layout.tsx`: authenticated layout with top nav + `<UserButton>`
  - `apps/web/app/app/page.tsx`: product list (server component, table + empty state)
  - `apps/web/app/app/new/page.tsx` + `_components/upload-form.tsx`: multi-step upload (create product → presigned PUT → patch key)
  - `apps/web/app/app/products/[id]/page.tsx`: product detail (source image + metadata, disabled Generate button)
  - Tests: `tests/conftest.py` (async DB fixtures), `tests/test_tenant_isolation.py` (RLS), `tests/test_product_creation.py`
  - `pytest tests/test_health.py` passes; TypeScript check passes
  - `GET /api/v1/brand-kits` and `POST /api/v1/brand-kits` implemented (tenant-scoped)
  - `product.uploaded` audit event fires when `source_image_key` transitions null → set via PATCH
  - Upload form rebuilt to wireframe B layout: two-column grid (left = garment photo drop zone with preview and tip; right = attributes panel with product name, SKU code, garment type select populated from leaf categories API, color + material 2-col, size range, brand kit select)
  - `new/page.tsx` is a server component that fetches categories and brand kits, extracts leaf nodes, passes both as props to client `UploadForm`

- **Session 5: Scenes, poses, plan builder, brand kits, aspect-ratio variants, model spec**
  - `app/services/scenes/library.py`: 6 scenes as frozen dataclasses — `studio_white`, `studio_neutral`, `coastal_cafe`, `sunlit_street`, `golden_hour_outdoor`, `urban_loft_interior`; each has `prompt_fragment`, `negative_prompt_fragment`, `compatible_garment_categories`, `lighting_notes`
  - `app/services/poses/library.py`: 7 poses — `front`, `three_quarter`, `back`, `walking`, `sitting`, `hands_in_pockets`, `looking_away`; each has `prompt_fragment`
  - `app/services/prompts/image_prompts.py`: updated `build_prompt()` and `build_negative_prompt(scene)` to resolve fragments from the scene/pose libraries instead of inline dicts
  - `app/services/plan_builder.py`: `build_plan(product, personas, brand_kit, overrides)` — default plan: 4 personas × 2 poses × 1 hero scene = 8 shots + 1 back = 9 jobs; brand kit constrains scene + persona whitelists + primary aspect ratio (`pick_primary_aspect` selects tallest); `overrides` path used for custom persona/plan submission
  - `app/schemas/generation.py`: added `GenerationShotSpec`, `PlanRequest`, `PlanResponse` (with total_primary/total_variant counts), updated `GenerateRequest`/`GenerateResponse` to carry plan
  - `app/routers/products.py`: `POST /{id}/plan` returns plan preview without enqueueing; `POST /{id}/generate` uses plan builder + brand kit + loads system+tenant personas; stores `required_aspect_ratios` in job.params
  - `app/routers/personas.py`: `GET /api/v1/personas` returns system + tenant's own personas; `POST /api/v1/personas` creates tenant-specific persona; `GET /api/v1/personas/{id}` single lookup
  - `app/schemas/personas.py`: `PersonaRead`, `PersonaCreate`
  - `app/tasks/generate_image.py`: generates at primary (tallest) aspect ratio; Pillow crops to all other required ratios via `_create_aspect_variants()` (upper-center bias crop); each crop → `image_variant` asset row with `parent_asset_id`; primary asset now includes model spec in `asset_metadata`: `model_height_cm`, `model_height_imperial`, `garment_size_worn`
  - Tests: `test_plan_builder.py` — 34 unit tests covering plan shape, brand kit scene/persona filtering, diverse_default sentinel, custom persona overrides, height conversion, garment size estimation, Pillow crop dimensions
  - All 43 unit tests pass; TypeScript check passes

- **Session 7: Video generation**
  - `alembic/versions/0002_video_fields.py`: migration adds `asset_bundles.video_pending_hero` (boolean, default false) and `tenants.daily_video_cap` (integer, nullable)
  - `app/models/generation.py`: `AssetBundle.video_pending_hero` column
  - `app/models/tenancy.py`: `Tenant.daily_video_cap` column
  - `app/services/scenes/video_motions.py` (NEW): 4 motion specs — `slow_turn_360`, `confident_walk`, `product_pickup`, `golden_hour_pose`; `get_motion()` + `get_all_motions()` helpers
  - `app/services/providers/base.py`: `VideoGenerationRequest` updated — `scene` field added, `duration_seconds` default 5, `motion` default `confident_walk`
  - `app/services/providers/fal.py`: `generate_video()` implemented — Kling `fal-ai/kling-video/v1.6/standard/image-to-video`, aspect_ratio 9:16, resolves motion prompt fragment via `get_motion()`
  - `app/core/celery.py`: added `enqueue_generate_video()` → sends to `video_queue`
  - `app/tasks/generate_image.py`: `_check_bundle_complete()` extended — after all image jobs terminal: if any failed → set `bundle.video_pending_hero = True`; if all succeeded → check hero → enqueue video immediately or set `video_pending_hero = True`
  - `app/tasks/generate_video.py` (NEW): full `run_generate_video_task()` — daily cap check (`VideoCappedError`), hero verify, upload hero to fal.ai storage, `FalProvider.generate_video()`, download mp4, extract poster frame via ffmpeg subprocess (`asyncio.to_thread`), upload mp4 + poster to S3, create `video_on_model` + `image_variant` (poster) `GeneratedAsset` rows, mark job succeeded
  - `app/routers/assets.py`: `set_hero` extended — when `bundle.video_pending_hero` is True, find queued video job, clear flag, call `enqueue_generate_video()`, write audit event
  - `app/routers/products.py`: `POST /{id}/generate` now creates one additional `GenerationJob(type=video)` per bundle (stays `queued` until images complete + hero set)
  - `app/routers/bundles.py`: `GET /{id}/download` zip updated — `video_on_model` assets go under `video/` folder; `image_variant` poster frames excluded from zip
  - `apps/worker/tasks/generate_video.py`: wired — calls `asyncio.run(run_generate_video_task(job_id))`
  - `infra/docker/Dockerfile.worker`: ffmpeg installed via apt-get
  - `apps/web/…/studio/_components/video-tile.tsx` (NEW): VideoTile component — queued/running/succeeded/failed states; succeeded state shows `<video>` with poster and download link
  - `apps/web/…/studio/_components/studio-view.tsx` (UPDATED): splits jobs by type — image jobs in 4-col grid, video job below as VideoTile; left rail uses image jobs only
  - `tests/test_video_pipeline.py` (NEW): 4 tests — happy path E2E, daily cap exceeded, no hero raises, image failure sets video_pending_hero

- **Session 6: Generation studio UI**
  - `app/routers/assets.py` (NEW): `GET /assets/{id}`, `POST /assets/{id}/hero` (validates kind, job status, bundle not approved; clears sibling hero flags), `DELETE /assets/{id}/hero`, `POST /assets/{id}/regenerate` (creates new job with same prompt/params, resets product to processing)
  - `app/routers/bundles.py` (REWRITTEN): `POST /bundles/{id}/approve` (requires hero asset, marks bundle+product approved, writes audit event), `GET /bundles/{id}/download` (builds in-memory zip via `asyncio.to_thread` + zipfile; folders named by aspect ratio e.g. `4x5/`, `9x16/`; streams as `application/zip`)
  - `app/routers/products.py` (UPDATED): `GET /{id}/events` SSE stream (polls DB every 2s with fresh sessions; emits `job_status`, `bundle_status`, `done` events; uses `fetch`+ReadableStream on client — `EventSource` can't send Authorization header); `GET /{id}/bundles` bundle history list (returns `list[BundleListItem]` with total_assets and hero_storage_key); `GET /{id}/bundle` now accepts optional `?version=N` param and includes `jobs` in response
  - `app/routers/__init__.py` (UPDATED): added assets router
  - `app/schemas/generation.py` (UPDATED from session 5): `JobRead` with prompt/params, `BundleRead` with jobs list, `BundleListItem`, `RegenerateResponse`
  - `apps/web/lib/api.ts` (UPDATED): added `apiDelete`, `openSSEStream` (fetch-based SSE helper with event name parsing and cancel function)
  - `apps/web/app/app/products/[id]/studio/page.tsx` (NEW): server component — fetches product, latest bundle (with jobs), personas; passes to StudioView
  - `apps/web/app/app/products/[id]/studio/_components/studio-view.tsx` (NEW): client component — SSE subscription, useReducer state for job statuses + assets, hero/regen/approve handlers, 3-panel layout (left rail / gallery / right rail), Gallery/History tab switcher
  - `apps/web/app/app/products/[id]/studio/_components/asset-tile.tsx` (NEW): tile for each job — skeleton/spinner (queued/running), image with hero ☆ overlay and regenerate ↺ button (succeeded), error state with retry (failed)
  - `apps/web/app/app/products/[id]/studio/_components/left-rail.tsx` (NEW): 200px rail showing deduplicated personas and poses used in current bundle
  - `apps/web/app/app/products/[id]/studio/_components/right-rail.tsx` (NEW): 220px rail — bundle status badge, hero thumbnail with model spec (height/garment size), Approve button (requires hero), Download zip anchor (approved bundles only)
  - `apps/web/app/app/products/[id]/studio/_components/bundle-history.tsx` (NEW): client component — fetches `/products/{id}/bundles`, renders version list with hero thumbnail, status badge, asset count
  - `apps/web/app/app/products/[id]/page.tsx` (UPDATED): added "Open Studio →" link (visible when a bundle exists)
  - 43 unit tests pass; TypeScript check passes

## In progress

*(none)*

- **Session 4: Worker, queue, and fal.ai integration (images only)**
  - `app/services/fal_client.py`: async httpx FalClient — `queue_run()` (submit → poll → result), `upload_file()` (bytes → fal.ai CDN URL), `download_url()`. Only file that knows fal.ai wire format.
  - `app/services/providers/base.py`: `GenerationProvider` Protocol + typed dataclasses for all three operation types (segmentation, image, video)
  - `app/services/providers/fal.py`: FalProvider — `segment_garment()` calls `fal-ai/birefnet`, `generate_image()` calls `fal-ai/flux/dev/image-to-image`, `generate_video()` raises NotImplementedError (session 7)
  - `app/services/prompts/image_prompts.py`: `build_prompt()` and `build_negative_prompt()` — pure functions, fully testable, isolated from HTTP layer
  - `app/services/storage.py`: added `upload_bytes()`, `download_bytes()`, `object_exists()` helpers
  - `app/core/celery.py`: minimal Celery dispatcher — `enqueue_generate_image(job_id)` sends task to broker
  - `app/tasks/generate_image.py`: async `run_generate_image_task()` — full end-to-end: loads job, marks running, ensures segmented image (cached in S3; uploads to fal.ai storage for local-dev access), calls FalProvider, downloads result, uploads to `tenants/{tid}/products/{pid}/v{version}/img_{job_id}.webp`, creates GeneratedAsset row, marks job succeeded, checks bundle completion → sets product `ready_for_review`; on any exception marks job `failed` and writes audit event
  - `app/routers/products.py`: `POST /{id}/generate` implemented — validates source image exists, loads 4 system personas, creates AssetBundle (version = max+1), creates one GenerationJob per persona (prompt+params in JSONB), sets product `processing`, commits, then enqueues tasks; `GET /{id}/bundle` implemented
  - `app/routers/jobs.py`: `GET /{id}` implemented (tenant-scoped)
  - `apps/worker/pyproject.toml`: added sqlalchemy, asyncpg, boto3, pydantic, pydantic-settings, langfuse, pillow
  - `apps/worker/celery_app.py`: adds `apps/api` to sys.path so worker can import `app.*`
  - `apps/worker/tasks/generate_image.py`: thin Celery task wrapper calling `asyncio.run(run_generate_image_task(job_id))`
  - Langfuse tracing: optional (skipped when keys not set); `segment_garment` and `generate_image` each wrapped in a Langfuse span with latency/cost/model metadata
  - Tests: `test_prompt_builder.py` (8 unit + 1 snapshot test), `test_generate_pipeline.py` (segmentation runs on first call, skipped when cached, full E2E with mock provider, failure path → job failed + audit event + product stays processing)
  - `apps/api/pyproject.toml`: added pillow
  - `docs/adr/0003-provider-abstraction.md`: documents layering rule, prompt isolation, file upload strategy
  - `apps/web/app/app/products/[id]/page.tsx`: updated to show generated asset thumbnails grid (2-col, 4:5 aspect) with persona/pose labels; Generate button wired as client component
  - All 9 tests pass; TypeScript check passes

## Pending

- **Session 8: Hardening, observability, and deployable build**
  - Error handling pass (retries, backoff, error codes)
  - Observability pass (Sentry, OTel, Langfuse completeness, admin dashboards)
  - Performance pass (thumbnails via imgproxy, DB indices, worker concurrency)
  - Security pass (RLS tests, rate limits, pip-audit, pnpm audit)
  - Production Dockerfiles + Helm chart / Render config
  - Full documentation pass
  - `/scripts/smoke-test.sh`
  - `/docs/next-steps.md` and `/docs/path-b-readiness.md`

## Path B foundations status

| Foundation | Status |
|------------|--------|
| Product/variant hierarchy | Schema in place, no UI — `products` + `variants` tables, auto-created default variant per product |
| Typed taxonomy (categories + attribute definitions) | Schema in place, no UI — `categories` + `attribute_definitions` tables, seeded global tree |
| Reserved SEO/identifier columns | Schema in place, no UI — `gtin`, `mpn`, `brand`, `slug`, `meta_title`, `meta_description` nullable on `products` |

## Open questions / blockers

*(none)*
