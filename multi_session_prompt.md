# Multi-session implementation prompt — AI cataloging app (image + video MVP)

> **How to use this document.** Each section below is a self-contained session prompt you can paste into Claude Code (or another coding agent) one at a time. Sessions are sequential — do not start session N until session N-1 is complete and its acceptance criteria are met. Between sessions, the agent's context resets, so each session prompt re-establishes the project state via the `PROJECT.md` and `STATE.md` files maintained throughout.
>
> **Scope of this build:** steps 1–4 of the workflow (intake, ingestion, generation, asset bundle assembly), restricted to **image and video generation only**. Copy generation, channel distribution, optimization, and the autonomous ingestion/optimization agents are explicitly out of scope and will be added later.
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

Explicitly out of scope:
- Copy / SEO description generation
- Multi-channel distribution
- A/B testing and optimization
- Ingestion agent, channel agent, optimization agent
- Mobile app
- Public API / SDK
- C2PA watermarking (will be added before launch but not in MVP)

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

4. Write /STATE.md as a living document. For session 1, populate:
   ## Completed
   - Session 1: scaffolding
   ## In progress
   - (empty)
   ## Pending
   - Sessions 2-8 (list titles only)
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

**Goal:** the database schema and the API request/response shapes the rest of the build will use. No business logic yet, just the contracts.

**Prompt to paste:**

```
Read the global context block at the top of this document, then read /PROJECT.md
and /STATE.md.

This is session 2 of 8. Session 1 (scaffold) is complete.

Tasks:
1. Design the Postgres schema for the MVP. At minimum:
   - tenants (id, name, created_at) — multi-tenancy from day one
   - users (id, tenant_id, clerk_user_id, email, role, created_at)
   - brand_kits (id, tenant_id, name, color_palette JSONB, tone_notes, created_at)
   - skus (id, tenant_id, code, name, garment_type, color, material, size_range,
     attributes JSONB, brand_kit_id, source_image_key, status, created_at, updated_at)
     — status is an enum: draft, processing, ready_for_review, approved, archived
   - generation_jobs (id, tenant_id, sku_id, type, status, provider, model_id,
     prompt JSONB, params JSONB, cost_cents, started_at, finished_at, error)
     — type enum: image, video. status enum: queued, running, succeeded, failed.
   - generated_assets (id, tenant_id, sku_id, job_id, kind, storage_key,
     width, height, duration_ms, mime_type, metadata JSONB, version, is_hero,
     created_at) — kind enum: image_on_model, video_on_model, image_variant.
   - asset_bundles (id, tenant_id, sku_id, version, status, approved_by,
     approved_at, created_at) — links many generated_assets together
   - audit_events (id, tenant_id, actor_id, entity_type, entity_id, action,
     payload JSONB, created_at)

   Add indices on tenant_id everywhere. Add a partial unique index on
   skus(tenant_id, code) where status != 'archived'.

2. Write the SQLAlchemy 2.0 models in /apps/api/app/models/.
3. Write the initial Alembic migration. `make db-migrate` should apply it.
4. Implement Postgres row-level security policies that filter by tenant_id
   based on a session variable `app.current_tenant_id`. Document this pattern
   in /docs/adr/0001-row-level-security.md.
5. Define Pydantic schemas in /apps/api/app/schemas/ for every entity above:
   create, update, and read variants where relevant.
6. Define the API surface in OpenAPI (FastAPI auto-generates this — just write
   the route signatures with `pass` or a 501 placeholder body):
   POST   /api/v1/skus
   GET    /api/v1/skus
   GET    /api/v1/skus/{id}
   PATCH  /api/v1/skus/{id}
   POST   /api/v1/skus/{id}/upload-url       (returns presigned S3 upload URL)
   POST   /api/v1/skus/{id}/generate         (starts a generation job)
   GET    /api/v1/jobs/{id}
   GET    /api/v1/skus/{id}/bundle           (returns current asset bundle)
   POST   /api/v1/bundles/{id}/approve
   GET    /api/v1/brand-kits
   POST   /api/v1/brand-kits
7. Generate matching TypeScript types into /packages/shared from the OpenAPI
   schema. Use `openapi-typescript`. Wire this into the Makefile as `make types`.

Acceptance criteria:
- `make db-migrate` applies cleanly to a fresh database
- `make db-reset` drops, recreates, and re-applies migrations
- Visiting localhost:8000/docs shows all routes from task 6
- /packages/shared/types.ts exists and is generated from the live OpenAPI schema
- `pytest -q` runs zero tests but exits 0 (the test harness is wired)
- All routes return 501 Not Implemented for now — they have signatures only

Update /STATE.md before finishing.
```

---

## Session 3 — Auth, multi-tenancy, and S3 upload

**Goal:** a real authenticated user can sign in, get a presigned upload URL, drop a flatlay into S3, and create a SKU row tied to that file. Still no AI work.

**Prompt to paste:**

```
Read the global context block at the top of this document, read /PROJECT.md and
/STATE.md.

This is session 3 of 8. The schema and API skeleton from session 2 are in place.

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
   - POST /api/v1/skus creates a draft SKU row, returns its id
   - POST /api/v1/skus/{id}/upload-url returns a presigned PUT URL valid for
     5 minutes, scoped to a key like `tenants/{tenant_id}/skus/{sku_id}/source.jpg`
   - The web app uploads directly to S3 using that URL
   - The web app then PATCHes the SKU with `source_image_key` set to the final key
5. Implement the SKU list and detail endpoints (GET /api/v1/skus, GET /api/v1/skus/{id})
   with proper RLS. Add pagination (cursor-based, page size 20).
6. Build the minimal web UI:
   - /app  → SKU list (table view with code, name, status, thumbnail)
   - /app/new  → upload form matching wireframe B from the spec
     (left side: drop zone; right side: attributes form)
   - /app/skus/{id}  → detail page that shows the source image and metadata
     (the generation studio comes in session 6)
7. Add the audit_events writes for: sku.created, sku.uploaded, sku.updated.

Acceptance criteria:
- A new user signs up via Clerk, lands in /app, sees an empty SKU list
- They click "+ new SKU", fill attributes, drop an image, and the SKU appears
  in the list with status `draft` and a thumbnail
- Two different Clerk users in two different tenants cannot see each other's SKUs
  (write a pytest integration test that proves this)
- The audit_events table has rows for the actions above

Do NOT call fal.ai or any AI provider yet. The "generate" button on the detail
page can exist but should be disabled or show "coming in next session".

Update /STATE.md.
```

---

## Session 4 — Worker, queue, and fal.ai integration (images only)

**Goal:** a SKU's source image flows through the Celery worker to fal.ai and comes back as one or more on-model images stored in S3. Wire it end-to-end with one model and one pose, no UI niceties yet.

**Prompt to paste:**

```
Read the global context block at the top of this document, read /PROJECT.md
and /STATE.md.

This is session 4 of 8. Auth, upload, and SKU CRUD are working.

Tasks:
1. Add fal.ai client setup in /apps/api/app/services/fal_client.py. Use httpx
   async. Read FAL_KEY from env. Wrap the client so the rest of the codebase
   never imports fal-specific code directly — the abstraction must allow
   swapping to Replicate or self-hosted later.

2. Define a `GenerationProvider` protocol in /apps/api/app/services/providers/base.py:
       async def generate_image(request: ImageGenerationRequest) -> ImageGenerationResult
       async def generate_video(request: VideoGenerationRequest) -> VideoGenerationResult
   Implement FalProvider in /apps/api/app/services/providers/fal.py.

3. For images, use FLUX.2 dev/pro on fal (whatever is current). The request
   should accept:
   - source_image_url (the flatlay)
   - garment metadata (type, color, material)
   - model attributes (body type, ethnicity, age range, gender)
   - pose (front, three-quarter, walking)
   - scene (studio_white for now — additional scenes in session 5)
   - aspect_ratio (default 4:5)
   The provider builds an appropriate prompt internally — keep prompt-engineering
   logic in /apps/api/app/services/prompts/image_prompts.py so it's testable.

4. Implement the generation pipeline:
   - POST /api/v1/skus/{id}/generate accepts a list of "shots" the merchant
     wants. For now hardcode the default to: 4 model variants × 1 pose × 1 scene
     = 4 images.
   - The endpoint creates one generation_job per shot (status=queued), enqueues
     a Celery task per job, returns the job ids and a bundle id.
   - The Celery task in /apps/worker/tasks/generate_image.py:
       a. Loads the job, sets status=running
       b. Downloads the source from S3 (or passes a signed URL to fal)
       c. Calls FalProvider.generate_image
       d. Polls for completion (fal jobs can take 10-60s)
       e. Downloads the resulting image, writes to S3 at
          tenants/{tenant_id}/skus/{sku_id}/v{version}/img_{job_id}.webp
       f. Creates a generated_assets row
       g. Sets job status=succeeded, records cost_cents
       h. On failure, sets status=failed and stores the error
   - Update the SKU status to `processing` when the first job starts and to
     `ready_for_review` when all jobs in the bundle finish.

5. Add idempotency: if the same SKU is generated twice, create a new bundle
   with version = max(existing versions) + 1. Old bundles are retained.

6. Add Langfuse tracing: every fal call wraps in a Langfuse span with prompt,
   model, latency, cost, and output asset id. This is non-negotiable — agent
   debugging depends on it later.

7. Write tests:
   - Unit test for the prompt builder (snapshot test of the prompt string for
     a fixed garment + model + pose input)
   - Integration test using a mocked FalProvider that returns a fixture image,
     end-to-end from POST /generate to ready_for_review
   - Failure-path test: provider raises, job goes to failed, SKU status is
     unchanged from `processing` and there's an audit event

Acceptance criteria:
- With a real FAL_KEY in .env, hitting POST /api/v1/skus/{id}/generate on a
  SKU that has a source image returns within 200ms with job ids
- 30-90 seconds later, the SKU has 4 generated_assets rows and status
  ready_for_review
- The generated images are visible in MinIO under the expected prefix
- Langfuse shows 4 spans for the run with cost and latency

Do NOT build the studio UI yet — verify via API and the existing detail page,
which can render thumbnails of all generated_assets for the SKU.

Update /STATE.md and add a /docs/adr/0002-provider-abstraction.md ADR.
```

---

## Session 5 — Image generation: scenes, poses, and brand kits

**Goal:** turn the single-shot pipeline into a real generation surface that produces a full bundle of varied images per SKU and respects brand kit constraints.

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
   compatible_garment_types, lighting_notes.

2. Expand pose options similarly in poses/library.py: front, three_quarter,
   back, walking, sitting, hands_in_pockets, looking_away.

3. Expand model attribute handling. Add a `ModelPersona` concept that bundles
   body_type, ethnicity, age_range, height_cm, gender_presentation, hair into
   a single named persona. Seed the database with 8 default personas covering
   diverse body types and ethnicities. Tenants can later create their own.

4. Implement brand kit application:
   - A brand kit defines: preferred scenes (whitelist), preferred personas
     (or "diverse default"), tone_notes (free text), required_aspect_ratios
     (list, default ['4:5', '1:1', '9:16']).
   - When a SKU is generated, the prompt builder reads the brand kit and
     constrains the output: only allowed scenes, only allowed personas, all
     required aspect ratios produced.

5. Replace the hardcoded "4 model variants × 1 pose × 1 scene" plan with a
   plan-builder service:
   - Input: SKU + brand kit + optional overrides
   - Output: list of GenerationShot specs (persona, pose, scene, aspect_ratio)
   - Default plan: 4 personas × 2 poses × 1 hero scene = 8 shots, plus
     1 detail/back shot = 9 image jobs per bundle.
   - Surface the generated plan to the API caller before enqueueing so the
     client can edit it. Add POST /api/v1/skus/{id}/plan that returns the plan
     without enqueueing, and POST /api/v1/skus/{id}/generate that takes a plan
     (or builds the default if absent) and enqueues.

6. Add aspect-ratio post-processing: every image is generated at the model's
   native resolution (whatever FLUX.2 returns) and then auto-cropped to all
   aspect ratios in the brand kit's required list. Use Pillow for the crop;
   center on the model's bounding box (use a simple person-detection — fal
   provides this, or use a lightweight ONNX yolo). Each crop is its own
   generated_assets row with kind=image_variant and a `parent_asset_id`.

7. Add the "model spec" feature you flagged as differentiating: for every
   primary on-model image, store the persona's height and the size of the
   garment used in the prompt. Expose it on the asset metadata
   (e.g. `{"model_height_cm": 178, "garment_size_worn": "S"}`). The studio
   UI in session 6 will render this as "5'10", wearing size S".

Acceptance criteria:
- A single POST /api/v1/skus/{id}/generate produces 9 primary images plus
  N variants per image (one per required aspect ratio)
- All images respect the brand kit (verified by checking the prompt log
  against the brand kit's allowed scenes/personas)
- Each generated_assets row has the model spec metadata populated
- Generation cost per bundle is logged and visible per tenant
- A test confirms that two SKUs with different brand kits produce visibly
  different scene/persona distributions

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

Tasks:
1. Build /app/skus/{id}/studio in /apps/web. Layout matches wireframe C:
   - Header: SKU name, code, time elapsed for current bundle, two buttons
     ("Regenerate" and "Approve bundle")
   - Left rail (200px): Model controls (persona selector, pose multi-select,
     scene picker), each control updates the plan via PATCH /api/v1/skus/{id}/plan
   - Center: Variant gallery in a 4-column grid. Each tile shows the image
     thumbnail, badges indicating pose and scene, and a "set as hero" action
   - Right rail (220px): Auto-generated metadata card showing model spec
     ("5'10", wearing size S") and a placeholder "Compliance" card that says
     "Watermarking added in v2" for now

2. Implement real-time job status updates. Use server-sent events from
   /api/v1/skus/{id}/events. The studio page subscribes; tiles transition from
   skeleton → loading spinner → image as their job completes. Closing the page
   does not cancel jobs.

3. Implement single-asset regeneration: clicking a tile and choosing
   "Regenerate this shot" enqueues a single generate-image job for that shot
   spec, replaces the asset on success, and increments the asset's version
   (the bundle version stays the same).

4. Implement bundle approval: POST /api/v1/bundles/{id}/approve marks the
   bundle as approved, sets the SKU status to `approved`, freezes the asset
   list (no more regenerations against this bundle — a new bundle is required),
   and writes audit events.

5. Implement bundle history: a small "Bundles" tab on the SKU page lists every
   bundle (v1, v2, v3) with their generation date, cost, hero image, and
   approval status. Approved bundles are read-only.

6. Add empty/loading/error states for every async surface. Use shadcn/ui
   skeletons.

7. Add basic accessibility: every image has alt text built from
   `{garment_name} on {persona.display_name}, {pose}, {scene}`. Keyboard
   navigation through the gallery works.

Acceptance criteria:
- Full happy path works in a browser: upload → studio shows 9 tiles
  populating live → user picks a hero → user clicks approve → SKU status
  is `approved`, bundle is frozen
- Regenerating a single tile works and replaces only that asset
- Bundle history shows all prior bundles for a SKU

Do NOT add a bulk approval flow or multi-SKU operations yet.

Update /STATE.md.
```

---

## Session 7 — Video generation

**Goal:** add short product video to the bundle. One video per SKU bundle, 6-10 seconds, vertical 9:16 format suitable for Reels and TikTok.

**Prompt to paste:**

```
Read the global context block at the top of this document, read /PROJECT.md
and /STATE.md.

This is session 7 of 8. Image generation and the studio are complete.

Tasks:
1. Add Kling video generation via fal.ai (or Veo if Kling isn't available on
   fal at build time — provider abstraction should make this swappable). Add
   `generate_video` to the FalProvider implementation.

2. Define video shot specs in /apps/api/app/services/scenes/video_motions.py:
   - slow_turn_360 (model rotates in studio)
   - confident_walk (model walks toward camera, lifestyle scene)
   - product_pickup (close-up on garment detail with hand gesture)
   - golden_hour_pose (static-ish lifestyle, light wind)

3. Pipeline:
   - The default plan from session 5 now includes one VideoShot at the end:
     hero persona × confident_walk × the brand kit's hero scene, 8 seconds,
     9:16 aspect ratio.
   - The video is generated AFTER all images succeed. Implement this as a
     Celery chord: 9 image tasks → callback that enqueues the video task.
     The video uses the approved hero image as a conditioning frame so the
     model and outfit are consistent with the stills.
   - On completion, the video is stored as a generated_assets row with
     kind=video_on_model, mime_type=video/mp4, duration_ms set.

4. Studio UI updates:
   - Add a 9th tile slot in the gallery dedicated to the video. Show a play
     button overlay on the thumbnail. Clicking opens a modal with the video
     player.
   - Auto-generate a poster frame from the first frame of the video (use
     ffmpeg in the worker; add ffmpeg to the worker Dockerfile).

5. Add cost guardrails: video is materially more expensive than images.
   Implement a per-tenant per-day video generation cap (default 50 videos/day).
   When exceeded, the video shot is skipped and the merchant sees a banner.
   Cap is configurable per tenant in the database.

6. Add a "regenerate video" action in the studio that uses the currently
   selected hero image as the conditioning frame. Same single-asset semantics
   as image regeneration in session 6.

7. Tests:
   - Integration test with mocked video provider that returns a fixture mp4
   - Cost cap test: generating beyond the daily cap is blocked
   - Chord test: image failures do not cascade to video; video runs only when
     all images succeeded

Acceptance criteria:
- A new SKU run produces 9 images plus 1 video
- Total bundle generation time is under 5 minutes for a typical run
- The video is playable in the studio modal and downloads as a watermark-free
  mp4 (watermarking comes later)
- Cost meter for the bundle reflects both image and video provider charges

Update /STATE.md.
```

---

## Session 8 — Hardening, observability, and a deployable build

**Goal:** the MVP is feature-complete. Make it boring and shippable.

**Prompt to paste:**

```
Read the global context block at the top of this document, read /PROJECT.md
and /STATE.md.

This is session 8 of 8. All image and video generation features are complete.

Tasks:
1. Error handling pass. Audit every Celery task and FastAPI endpoint for:
   - Network errors to fal.ai → exponential backoff retry up to 3 times
   - Timeouts → mark job as failed with a clear error_code, surface in UI
   - S3 upload/download errors → retry up to 5 times, then fail loudly
   - Quota / rate limit errors from fal → surface to the merchant with
     a "try again in N minutes" message
   Add an `error_code` enum field on generation_jobs for these cases.

2. Observability pass:
   - Sentry on web, api, and worker with source maps
   - OpenTelemetry traces from web → api → worker, exported to Honeycomb or
     Grafana Cloud (configurable via env)
   - Langfuse traces for every fal call (already done in session 4 — verify
     completeness)
   - A /admin/cost dashboard that shows per-tenant GPU spend for the current
     billing month, broken down by image vs video
   - A /admin/jobs dashboard listing recent failed jobs with their error_code
     for triage

3. Performance pass:
   - Image thumbnails served via Cloudflare Images or imgproxy, never original
     resolution unless the user explicitly downloads
   - Studio gallery virtualized if >50 tiles
   - Database indices reviewed; add indices on generation_jobs(sku_id, created_at)
     and generated_assets(bundle_id) if not present
   - Worker concurrency tuned: image tasks default to 8 concurrent, video
     tasks default to 2 (configurable via env)

4. Security pass:
   - Verify RLS is enforced on every table (write a test that bypasses the
     tenant filter and confirms it gets zero rows from other tenants)
   - Presigned URLs are scoped to tenant prefix and expire in 5 minutes
   - Rate limit the generate endpoints to 60/hour per tenant for the MVP
   - All env vars loaded via pydantic-settings, no os.getenv scattered around
   - Run `pip-audit` and `pnpm audit`; fix or document every high-severity finding

5. Deployment artifacts:
   - Production-ready Dockerfiles (multi-stage, non-root user, healthchecks)
   - Helm chart OR Render/Fly.io configs (pick one, document the choice)
   - Postgres migration runs as a pre-deploy job, not on app boot
   - A /docs/runbook.md covering: deploying, rolling back, common incidents
     (fal outage, Postgres connection saturation, Redis OOM)

6. Documentation pass:
   - Update /PROJECT.md to reflect the actual built system
   - /docs/api.md auto-generated from the FastAPI OpenAPI schema
   - /docs/architecture.md with the sequence diagram for a full image+video run
   - A /CHANGELOG.md starting at v0.1.0
   - /docs/next-steps.md describing exactly what comes next (copy generation,
     channel agents, optimization agent, mobile app, C2PA watermarking) — this
     becomes the input for future multi-session prompts

7. Smoke test script in /scripts/smoke-test.sh:
   - Creates a tenant, user, brand kit
   - Uploads a fixture flatlay
   - Triggers generation
   - Polls until ready_for_review
   - Asserts 9 images and 1 video exist
   - Approves the bundle
   - Cleans up

Acceptance criteria:
- /scripts/smoke-test.sh passes against a clean docker-compose stack
- A staging deployment exists that boots from a clean database and survives
  the smoke test
- Sentry, Langfuse, and the OTel collector all receive data from a real run
- /admin/cost shows real numbers for the smoke-test tenant
- The runbook is good enough that someone unfamiliar with the codebase could
  deploy the app following only that document

Update /STATE.md to mark all 8 sessions complete and reference next-steps.md
for the path forward.
```

---

## Inter-session protocol

A few rules that make this work in practice rather than in theory:

1. **Always have the agent re-read `STATE.md` first.** Without this, sessions drift. STATE.md is your durable memory between Claude Code sessions whose context resets.
2. **Review between sessions.** Run the acceptance criteria yourself before starting the next session. If a session finished but acceptance criteria failed, file the gap in STATE.md under "Open questions / blockers" before moving on, or ask the agent to do another pass.
3. **Don't compress sessions.** Each session is sized to fit comfortably in one context window. Combining two sessions usually causes the agent to skip steps in both.
4. **Keep the global context block at the top of every prompt.** It re-establishes scope boundaries the agent will otherwise drift past — especially the out-of-scope list, which is what stops it from accidentally building a channel agent in session 5.
5. **Save the agent's terminal output.** When something goes wrong in session N+2, the failure is often rooted in a quiet decision the agent made in session N. Logged output makes that recoverable.

## What's deferred (the input to your next multi-session prompt)

After session 8 ships, the natural next builds are:
- Copy generation (titles, descriptions, alt text, multi-language)
- C2PA watermarking and EU AI Act disclosure
- Channel agent (push to Amazon, Instagram, TikTok, etc.)
- Ingestion agent (autonomous SKU pickup from supplier feeds)
- Optimization agent (A/B testing and underperformer refresh)
- Mobile app for capture and approval
- Public API and SDK

Each of these is its own multi-session prompt of similar shape — establish scope, lock the tech, lay schema and contracts, build incrementally, harden, ship.
