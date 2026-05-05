# catalog-ai

## Product summary

catalog-ai is an AI cataloging application for fashion retailers. It takes a flatlay or mannequin photo of a garment and generates on-model imagery and short product videos that the retailer can use across their sales channels. The MVP covers steps 1–4 of the full cataloging workflow: manual garment intake, attribute capture, AI image and video generation via fal.ai, and versioned asset bundle assembly. The merchant reviews and approves generated assets in a web studio before downloading or distributing them.

## Architecture overview

```
Browser (Next.js)
    │  REST / SSE
    ▼
FastAPI (apps/api)
    │  Celery tasks
    ▼
Redis (queue)
    │
    ▼
Celery Worker (apps/worker)
    │  HTTP
    ▼
fal.ai  ──────────────────────────────► MinIO / S3
(FLUX.2 images, Kling/Veo video)        (generated assets)
    │
    ▼
Postgres 16 + pgvector
(products, jobs, assets, bundles)
```

**Request flow (image generation):**
1. Merchant uploads flatlay → presigned S3 PUT URL → source stored in MinIO
2. POST /generate → API creates `generation_job` rows, enqueues Celery tasks
3. Worker: segmentation → FLUX.2 call → poll completion → write asset to S3 → update DB
4. SSE stream pushes job status to the browser as images arrive
5. Merchant reviews gallery, picks hero, clicks Approve → bundle is frozen

## Locked tech choices

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend | Next.js 14 (App Router) + TypeScript strict + Tailwind + shadcn/ui | SSR, file-based routing, best-in-class DX |
| Backend | Python 3.12 + FastAPI + Pydantic v2 | Fast async API, first-class type safety, large ecosystem |
| ORM / migrations | SQLAlchemy 2.0 + Alembic | Production-grade async ORM, schema version control |
| Queue / workers | Celery + Redis | Battle-tested for long AI jobs; Redis doubles as cache |
| Database | Postgres 16 + pgvector | pgvector reserved for future embedding search on catalog items |
| Storage | MinIO locally / Cloudflare R2 in prod | S3-compatible API, low-cost egress on R2 |
| AI inference | fal.ai (FLUX.2 images, Kling/Veo video) | Serverless GPU, no infra to manage, provider abstraction allows swap |
| Auth | Clerk | Managed auth with JWTs, webhooks, and a good Next.js SDK |
| Observability | Sentry + Langfuse | Sentry for errors; Langfuse for LLM/AI call tracing and cost |
| Package manager (JS) | pnpm workspaces | Fast, deterministic, native monorepo support |
| Package manager (Python) | uv | Fast resolver, lockfiles, replaces pip + virtualenv |
| Local dev | Docker Compose | Single command to boot the full stack |

## How to run locally

### Prerequisites
- Docker Desktop running
- Node 22 + pnpm 10
- Python 3.12 + uv

### First-time setup

```bash
make install          # installs all JS and Python deps; copies .env.example → .env
# Edit .env and fill in FAL_KEY, CLERK_*, etc.
docker compose up     # boots postgres, redis, minio, api, worker, web
```

Services:
- **Web**: http://localhost:3000
- **API**: http://localhost:8000 (OpenAPI: http://localhost:8000/docs)
- **MinIO console**: http://localhost:9001 (user: minioadmin / minioadmin)

### Environment variables required

See `.env.example` for the full list. Minimum to get past the login screen:
```
CLERK_SECRET_KEY
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
```
To actually generate images add `FAL_KEY`. Observability is optional in dev.

### Database

```bash
make db-migrate       # apply migrations
make db-reset         # drop + recreate + migrate (destructive)
make db-seed          # seed categories, attribute_definitions, model_personas
```

## Out of scope (this build)

- Copy / SEO description generation (columns reserved, no generation logic)
- Multi-channel distribution
- A/B testing and optimization
- Ingestion agent, channel agent, optimization agent
- Mobile app
- Public API / SDK
- C2PA watermarking (deferred to pre-launch)
- Inventory and pricing
- Variant-specific imagery (all imagery attaches to Product, not Variant, in MVP)
- Bulk CSV import (deferred)

## Path A vs Path B

**Path A** is what we are building: an image and video generation tool for fashion retailers.

**Path B** is the future cataloging platform: taxonomy, SEO copy, channel mapping, marketplace export.

### Three baked-in Path B foundations

The schema is designed so Path B can be added *without rewriting the spine*. Three foundations are present in the database from session 2 onward but are **invisible to the merchant in the MVP UI**:

| Foundation | Tables / columns | MVP UI | Path B UI |
|------------|-----------------|--------|-----------|
| Product/variant hierarchy | `products`, `variants` | Product-only; one auto-created variant per product | Variant selector, color/size matrix |
| Typed taxonomy | `categories`, `attribute_definitions` | Simple garment-type dropdown (leaf categories only) | Full category tree, attribute editor |
| Reserved identifier/SEO columns | `products.gtin`, `.mpn`, `.brand`, `.slug`, `.meta_title`, `.meta_description` | Not shown | SEO editor, channel mapper |

**Rule:** Do not build merchant-facing UI for any Path B foundation during sessions 1–8. These columns exist in the schema to prevent painful migrations later. They will be populated and surfaced in the next multi-session build.
