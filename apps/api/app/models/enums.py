import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    member = "member"


class ProductStatus(str, enum.Enum):
    draft = "draft"
    processing = "processing"
    ready_for_review = "ready_for_review"
    approved = "approved"
    archived = "archived"


class AttributeValueType(str, enum.Enum):
    string = "string"
    enum = "enum"
    number = "number"
    boolean = "boolean"
    multi_enum = "multi_enum"


class JobType(str, enum.Enum):
    image = "image"
    video = "video"


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class AssetKind(str, enum.Enum):
    image_on_model = "image_on_model"
    video_on_model = "video_on_model"
    image_variant = "image_variant"


class BundleStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
