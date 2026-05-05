"""GenerationProvider protocol + request/result dataclasses.

Any provider (fal.ai, Replicate, self-hosted) must satisfy this interface.
Nothing outside app/services/providers/ should import provider-specific code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------

@dataclass
class SegmentationRequest:
    source_url: str  # publicly-accessible URL of the source garment image


@dataclass
class SegmentationResult:
    segmented_url: str  # URL of the background-removed image
    cost_cents: int = 0
    latency_ms: int = 0
    model_id: str = ""


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

@dataclass
class ImageGenerationRequest:
    segmented_garment_url: str
    product_attributes: dict[str, Any]  # color, material, size_range, etc.
    persona: dict[str, Any]  # body_type, ethnicity, age_range, gender_presentation, hair
    pose: str = "front"  # "front" | "three-quarter" | "walking"
    scene: str = "studio_white"
    aspect_ratio: str = "4:5"


@dataclass
class ImageGenerationResult:
    image_url: str
    width: int
    height: int
    model_id: str
    cost_cents: int = 0
    latency_ms: int = 0


# ---------------------------------------------------------------------------
# Video generation (implemented in session 7)
# ---------------------------------------------------------------------------

@dataclass
class VideoGenerationRequest:
    source_image_url: str  # fal.ai-accessible URL of the hero image (conditioning frame)
    product_attributes: dict[str, Any] = field(default_factory=dict)
    motion: str = "confident_walk"
    scene: str = "studio_white"
    duration_seconds: int = 5


@dataclass
class VideoGenerationResult:
    video_url: str
    duration_ms: int
    model_id: str
    cost_cents: int = 0
    latency_ms: int = 0


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class GenerationProvider(Protocol):
    async def segment_garment(self, request: SegmentationRequest) -> SegmentationResult: ...
    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult: ...
    async def generate_video(self, request: VideoGenerationRequest) -> VideoGenerationResult: ...
