import uuid
from datetime import datetime

from app.schemas.common import OrmBase


class PersonaCreate(OrmBase):
    display_name: str
    body_type: str
    ethnicity: str
    age_range: str
    height_cm: int
    gender_presentation: str
    hair: str


class PersonaRead(OrmBase):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    display_name: str
    body_type: str
    ethnicity: str
    age_range: str
    height_cm: int
    gender_presentation: str
    hair: str
    system_managed: bool
    created_at: datetime
