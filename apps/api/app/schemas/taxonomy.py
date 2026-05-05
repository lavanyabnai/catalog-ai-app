import uuid
from datetime import datetime
from typing import Any

from app.models.enums import AttributeValueType
from app.schemas.common import OrmBase


class AttributeDefinitionRead(OrmBase):
    id: uuid.UUID
    category_id: uuid.UUID
    key: str
    display_name: str
    value_type: AttributeValueType
    is_required: bool
    allowed_values: list[Any] | None


class CategoryRead(OrmBase):
    id: uuid.UUID
    slug: str
    display_name: str
    path: str
    parent_id: uuid.UUID | None
    children: list["CategoryRead"] = []

    model_config = {"from_attributes": True}


CategoryRead.model_rebuild()
