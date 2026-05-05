import uuid
from datetime import datetime
from typing import Any

from app.models.enums import AssetKind, BundleStatus, JobStatus, JobType
from app.schemas.common import OrmBase


class JobRead(OrmBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    product_id: uuid.UUID
    type: JobType
    status: JobStatus
    provider: str
    model_id: str
    prompt: dict[str, Any]
    params: dict[str, Any]
    cost_cents: int | None
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None
    error_code: str | None
    created_at: datetime


class GenerationShotSpec(OrmBase):
    """One shot spec — returned by /plan, submitted to /generate."""
    persona: dict[str, Any]
    pose: str = "front"
    scene: str = "studio_white"
    primary_aspect_ratio: str = "9:16"


class PlanRequest(OrmBase):
    shots: list[GenerationShotSpec] | None = None


class PlanResponse(OrmBase):
    shots: list[GenerationShotSpec]
    required_aspect_ratios: list[str]
    total_primary_images: int
    total_variant_images: int


class GenerateRequest(OrmBase):
    shots: list[GenerationShotSpec] | None = None


class GenerateResponse(OrmBase):
    bundle_id: uuid.UUID
    job_ids: list[uuid.UUID]
    plan: list[GenerationShotSpec]


class AssetRead(OrmBase):
    id: uuid.UUID
    job_id: uuid.UUID
    kind: AssetKind
    storage_key: str
    width: int | None
    height: int | None
    duration_ms: int | None
    mime_type: str
    asset_metadata: dict[str, Any]
    version: int
    is_hero: bool
    parent_asset_id: uuid.UUID | None
    created_at: datetime


class BundleRead(OrmBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    product_id: uuid.UUID
    version: int
    status: BundleStatus
    approved_by: uuid.UUID | None
    approved_at: datetime | None
    created_at: datetime
    assets: list[AssetRead] = []
    jobs: list[JobRead] = []


class BundleListItem(OrmBase):
    """Minimal bundle data for the history tab."""
    id: uuid.UUID
    version: int
    status: BundleStatus
    created_at: datetime
    total_assets: int
    hero_storage_key: str | None


class RegenerateResponse(OrmBase):
    """Returned when a single shot is re-queued for regeneration."""
    job_id: uuid.UUID
    bundle_id: str
