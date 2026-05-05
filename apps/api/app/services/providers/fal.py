"""FalProvider — implements GenerationProvider using fal.ai APIs.

External callers import only GenerationProvider (from base.py) and
instantiate FalProvider here. No fal.ai specifics leak outside this module.
"""
from __future__ import annotations

import time
from typing import Any

from app.services.fal_client import FalClient
from app.services.prompts.image_prompts import build_negative_prompt, build_prompt
from app.services.providers.base import (
    ImageGenerationRequest,
    ImageGenerationResult,
    SegmentationRequest,
    SegmentationResult,
    VideoGenerationRequest,
    VideoGenerationResult,
)
from app.services.scenes.video_motions import get_motion

# fal.ai model identifiers
_BIREFNET_MODEL = "fal-ai/birefnet"
_FLUX_IMG2IMG_MODEL = "fal-ai/flux/dev/image-to-image"
# Kling standard image-to-video; swap to v2 or fal-ai/veo2 if unavailable
_KLING_MODEL = "fal-ai/kling-video/v1.6/standard/image-to-video"

# Aspect ratio → pixel dimensions (portrait-first)
_ASPECT_DIMENSIONS: dict[str, tuple[int, int]] = {
    "4:5": (800, 1000),
    "1:1": (1024, 1024),
    "9:16": (576, 1024),
    "16:9": (1024, 576),
}


class FalProvider:
    def __init__(self, client: FalClient | None = None) -> None:
        self._client = client or FalClient()

    # ------------------------------------------------------------------
    # Segmentation
    # ------------------------------------------------------------------

    async def segment_garment(self, request: SegmentationRequest) -> SegmentationResult:
        t0 = time.monotonic()
        result = await self._client.queue_run(
            _BIREFNET_MODEL,
            {
                "image_url": request.source_url,
                "model": "General Use (Light)",
                "operating_resolution": "1024x1024",
                "output_format": "webp",
            },
        )
        latency_ms = int((time.monotonic() - t0) * 1000)

        image_data: dict[str, Any] = result.get("image", {})
        segmented_url: str = image_data.get("url", "")
        if not segmented_url:
            raise ValueError(f"BiRefNet returned no image URL: {result}")

        return SegmentationResult(
            segmented_url=segmented_url,
            cost_cents=0,  # updated when fal.ai adds cost to response
            latency_ms=latency_ms,
            model_id=_BIREFNET_MODEL,
        )

    # ------------------------------------------------------------------
    # Image generation
    # ------------------------------------------------------------------

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        t0 = time.monotonic()

        # Resolve pixel size from aspect ratio
        width, height = _ASPECT_DIMENSIONS.get(request.aspect_ratio, (800, 1000))

        # Build the text prompt
        attrs = request.product_attributes
        prompt_text = build_prompt(
            garment_type=attrs.get("garment_type", attrs.get("category", "garment")),
            color=attrs.get("color"),
            material=attrs.get("material"),
            persona=request.persona,
            pose=request.pose,
            scene=request.scene,
        )
        negative_prompt = build_negative_prompt(scene=request.scene)

        result = await self._client.queue_run(
            _FLUX_IMG2IMG_MODEL,
            {
                "image_url": request.segmented_garment_url,
                "prompt": prompt_text,
                "negative_prompt": negative_prompt,
                "strength": 0.80,
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "num_images": 1,
                "image_size": {"width": width, "height": height},
                "enable_safety_checker": False,
            },
        )
        latency_ms = int((time.monotonic() - t0) * 1000)

        images: list[dict[str, Any]] = result.get("images", [])
        if not images:
            raise ValueError(f"FLUX returned no images: {result}")

        img = images[0]
        return ImageGenerationResult(
            image_url=img["url"],
            width=img.get("width", width),
            height=img.get("height", height),
            model_id=_FLUX_IMG2IMG_MODEL,
            cost_cents=0,
            latency_ms=latency_ms,
        )

    # ------------------------------------------------------------------
    # Video generation — Kling image-to-video
    # ------------------------------------------------------------------

    async def generate_video(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        t0 = time.monotonic()

        motion = get_motion(request.motion)
        prompt_text = motion.prompt_fragment if motion else request.motion

        result = await self._client.queue_run(
            _KLING_MODEL,
            {
                "image_url": request.source_image_url,
                "prompt": prompt_text,
                "duration": str(request.duration_seconds),  # Kling expects "5" or "10"
                "aspect_ratio": "9:16",
            },
        )
        latency_ms = int((time.monotonic() - t0) * 1000)

        # Kling returns {"video": {"url": "...", "duration": 5.0}}
        video_data: dict[str, Any] = result.get("video", {})
        video_url: str = video_data.get("url", "")
        if not video_url:
            raise ValueError(f"Kling returned no video URL: {result}")

        duration_s: float = float(video_data.get("duration", request.duration_seconds))

        return VideoGenerationResult(
            video_url=video_url,
            duration_ms=int(duration_s * 1000),
            model_id=_KLING_MODEL,
            cost_cents=0,
            latency_ms=latency_ms,
        )
