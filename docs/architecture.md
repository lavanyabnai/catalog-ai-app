# Architecture overview

See `/PROJECT.md` for the full architecture diagram and rationale.

## Key design decisions

### Why Celery over async tasks in FastAPI?
AI generation jobs take 30–90 seconds per image and up to 5 minutes per bundle. Celery lets the HTTP request return immediately (job IDs), decouples retry/error logic, and allows independent worker scaling. The API enqueues; the worker executes.

### Why pgvector?
Reserved for future semantic search over the product catalog (search by garment similarity, not just text). No vector operations in the MVP.

### Why MinIO locally, R2 in prod?
Both expose the same S3-compatible API so the code path is identical. R2 has zero egress fees, which matters when serving many generated images.

### Why uv over poetry?
uv is significantly faster at dependency resolution and lockfile generation, and its interface is closer to pip. Poetry's PEP 517 build backend adds indirection that uv avoids.

## Session-by-session build order

See `/STATE.md` for the current session state and pending work.
