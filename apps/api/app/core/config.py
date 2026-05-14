from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Walk up from this file (app/core/config.py) to find the nearest .env
_here = Path(__file__).resolve().parent  # .../app/core
_env_candidates = [
    _here.parent.parent / ".env",         # .../apps/api/.env
    _here.parent.parent.parent / ".env",  # .../apps/.env
    _here.parent.parent.parent.parent / ".env",  # repo root .env
]
_env_file = next((str(p) for p in _env_candidates if p.exists()), ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_file, extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/catalog_ai"
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint_url: str = "http://localhost:9000"
    # Public-facing URL for presigned URLs (differs from internal Docker URL in prod)
    s3_public_endpoint_url: str = ""
    s3_bucket: str = "catalog-ai"
    s3_access_key_id: str = "minioadmin"
    s3_secret_access_key: str = "minioadmin"
    s3_region: str = "us-east-1"

    cloudinary_url: str = ""

    fal_key: str = ""
    anthropic_api_key: str = ""

    sentry_dsn: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    debug: bool = False


settings = Settings()
