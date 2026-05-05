# Import order matters: leaf tables first, tables with FKs after.
# All models must be imported here so Base.metadata is fully populated
# before Alembic autogenerate or migration runs.

from app.models.base import Base
from app.models.enums import (
    AssetKind,
    AttributeValueType,
    BundleStatus,
    JobStatus,
    JobType,
    ProductStatus,
    UserRole,
)
from app.models.tenancy import Tenant, User
from app.models.taxonomy import AttributeDefinition, Category
from app.models.personas import ModelPersona
from app.models.brand_kits import BrandKit
from app.models.catalog import Product, Variant
from app.models.generation import AssetBundle, GeneratedAsset, GenerationJob
from app.models.audit import AuditEvent

__all__ = [
    "Base",
    "AssetKind",
    "AttributeValueType",
    "BundleStatus",
    "JobStatus",
    "JobType",
    "ProductStatus",
    "UserRole",
    "Tenant",
    "User",
    "Category",
    "AttributeDefinition",
    "ModelPersona",
    "BrandKit",
    "Product",
    "Variant",
    "GenerationJob",
    "GeneratedAsset",
    "AssetBundle",
    "AuditEvent",
]
