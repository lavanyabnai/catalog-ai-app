# ADR 0003 — Generation Provider Abstraction

**Date:** 2026-05-04
**Status:** Accepted

## Context

The MVP uses fal.ai for all AI inference (BiRefNet segmentation, FLUX image generation, Kling/Veo video). However:

- fal.ai may change their API, pricing, or availability
- We may want to A/B test providers (e.g. fal.ai FLUX vs Replicate FLUX vs self-hosted)
- The worker task logic should not be littered with HTTP calls to a specific vendor

If we let `fal.ai` endpoints leak throughout the codebase, switching providers later means hunting down dozens of call sites.

## Decision

All AI inference is accessed through a **`GenerationProvider` protocol** defined in `app/services/providers/base.py`. The protocol exposes three methods:

```python
class GenerationProvider(Protocol):
    async def segment_garment(request: SegmentationRequest) -> SegmentationResult
    async def generate_image(request: ImageGenerationRequest) -> ImageGenerationResult
    async def generate_video(request: VideoGenerationRequest) -> VideoGenerationResult
```

The only concrete implementation in session 4 is `FalProvider` in `app/services/providers/fal.py`. It uses a thin `FalClient` (in `app/services/fal_client.py`) that wraps the fal.ai queue HTTP API.

### Layering rule

```
task / router
    └── GenerationProvider (Protocol)
            └── FalProvider
                    └── FalClient  ← only file that knows fal.ai wire format
```

Nothing outside `app/services/providers/fal.py` and `app/services/fal_client.py` may reference fal.ai model IDs, endpoint URLs, or response shapes. All request/result types come from `base.py`.

### Provider selection

For MVP, `FalProvider` is instantiated directly in the task. In a future session this can be replaced with a factory:

```python
def get_provider(name: str) -> GenerationProvider:
    if name == "fal":
        return FalProvider()
    if name == "replicate":
        return ReplicateProvider()
    raise ValueError(f"Unknown provider: {name}")
```

The task's `params["provider"]` column already stores the provider name for this reason.

## Prompt isolation

Prompt-engineering logic lives exclusively in `app/services/prompts/image_prompts.py`. It is a pure function — no HTTP, no DB — and is fully unit-tested with snapshot tests. This separation makes it safe to iterate on prompts without touching the provider or task code.

## File upload for local dev

In local Docker, MinIO is not reachable from fal.ai's servers. The task therefore uploads source and segmented images to **fal.ai's own storage** (via `FalClient.upload_file`) before passing them as URLs to inference endpoints. In production (Cloudflare R2 with public access) this extra upload could be skipped, but keeping the same code path in all environments simplifies testing.

## Consequences

**Good:**
- Switching from fal.ai FLUX to Replicate or a self-hosted model requires only a new `providers/*.py` file and changing the `provider` field on `GenerationJob`
- Prompt engineering is testable in isolation — no network required
- All fal.ai specifics (model IDs, queue polling, file upload) are in two files

**Watch out for:**
- The `GenerationProvider` protocol uses `@runtime_checkable`, so `isinstance(x, GenerationProvider)` works for basic sanity checks, but Python's structural typing means the check only verifies method names exist, not signatures
- `FalProvider.generate_video` raises `NotImplementedError` until session 7; callers must not invoke it before then
- fal.ai `upload_file` URLs currently expire after ~24 hours; the segmented image is cached in our S3 for this reason
