import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import OrmBase


class BrandKitCreate(OrmBase):
    name: str
    color_palette: list[Any] | None = None
    tone_notes: str | None = None
    allowed_scenes: list[str] | None = None
    allowed_personas: list[str] | None = None
    required_aspect_ratios: list[str] = Field(default=["4:5", "1:1", "9:16"])


class BrandKitRead(OrmBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    color_palette: list[Any] | None
    tone_notes: str | None
    allowed_scenes: list[str] | None
    allowed_personas: list[str] | None
    required_aspect_ratios: list[str]
    created_at: datetime
