from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BrandKit(Base):
    __tablename__ = "brand_kits"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color_palette: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    tone_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Whitelists: list of scene/persona ids, or ["diverse_default"] sentinel
    allowed_scenes: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    allowed_personas: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    # e.g. ["4:5", "1:1", "9:16"]
    required_aspect_ratios: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=lambda: ["4:5", "1:1", "9:16"])
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
