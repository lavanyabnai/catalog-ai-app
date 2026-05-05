import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ModelPersona(Base):
    __tablename__ = "model_personas"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # NULL = global system persona; set = tenant-specific
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    body_type: Mapped[str] = mapped_column(String(100), nullable=False)
    ethnicity: Mapped[str] = mapped_column(String(100), nullable=False)
    age_range: Mapped[str] = mapped_column(String(50), nullable=False)
    height_cm: Mapped[int] = mapped_column(Integer, nullable=False)
    gender_presentation: Mapped[str] = mapped_column(String(50), nullable=False)
    hair: Mapped[str] = mapped_column(String(255), nullable=False)
    system_managed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
