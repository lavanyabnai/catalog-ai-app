import uuid
from datetime import datetime

from pydantic import EmailStr

from app.models.enums import UserRole
from app.schemas.common import OrmBase


class TenantRead(OrmBase):
    id: uuid.UUID
    name: str
    created_at: datetime


class UserRead(OrmBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    clerk_user_id: str
    email: EmailStr
    role: UserRole
    created_at: datetime
