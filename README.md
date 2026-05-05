# catalog-ai

AI-powered catalog generation for fashion retailers. Upload product images and generate professional on-model photos and videos ready for e-commerce.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14, Tailwind CSS, TypeScript |
| Backend API | FastAPI, SQLAlchemy, Alembic |
| Worker | Celery + Redis |
| Database | PostgreSQL + pgvector |
| Storage | MinIO (local) / Cloudflare R2 (prod) |
| AI generation | fal.ai |

---

## Prerequisites

- [Node.js 18+](https://nodejs.org) and [pnpm](https://pnpm.io) (`npm i -g pnpm`)
- [Python 3.12+](https://python.org) and [uv](https://docs.astral.sh/uv/) (`pip install uv`)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Postgres, Redis, MinIO)

---

## 1 — Start backing services (Docker)

```bash
docker compose up -d
```

This starts Postgres on `5432`, Redis on `6379`, and MinIO on `9000`.

---

## 2 — Frontend

```bash
# from repo root
cd apps/web

# install dependencies
pnpm install

# copy env and fill in values
cp ../../.env.example .env.local

# start dev server → http://localhost:3000
pnpm dev
```

### Frontend build

```bash
pnpm build
pnpm start
```

---

## 3 — Backend API

```bash
# from repo root
cd apps/api

# install dependencies
uv sync

# copy env and fill in values
cp ../../.env.example .env

# run database migrations
uv run alembic upgrade head

# start API server → http://localhost:8000
uv run uvicorn main:app --reload
```

Interactive docs available at `http://localhost:8000/docs`.

### Run API tests

```bash
cd apps/api
uv run pytest
```

---

## 4 — Celery Worker

```bash
# from repo root
cd apps/worker

# install dependencies
uv sync

# copy env
cp ../../.env.example .env

# start worker
uv run celery -A celery_app worker --loglevel=info
```

---

## 5 — Run everything at once (Make)

```bash
# start all services
make dev
```

See `Makefile` for individual targets (`make api`, `make web`, `make worker`).

---

## Environment variables

Copy `.env.example` to `.env` (backend) and `apps/web/.env.local` (frontend) and fill in:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/catalogai
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
FAL_API_KEY=your_fal_key
```

---

## Project structure

```
catalog-ai/
├── apps/
│   ├── web/          # Next.js frontend
│   ├── api/          # FastAPI backend
│   └── worker/       # Celery worker
├── packages/
│   └── shared/       # Shared TypeScript types
├── infra/
│   └── docker/       # Dockerfiles
├── docs/             # Architecture & ADRs
└── docker-compose.yml
```
