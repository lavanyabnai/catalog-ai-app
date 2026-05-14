from __future__ import annotations

import base64

import boto3
import cloudinary
import cloudinary.uploader
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings


def upload_image_b64(image_b64: str, public_id: str, media_type: str = "image/jpeg") -> str:
    """Upload a base64-encoded image and return its public URL.

    Uses Cloudinary when CLOUDINARY_URL is set, otherwise falls back to S3.
    """
    if settings.cloudinary_url:
        cloudinary.config(cloudinary_url=settings.cloudinary_url)
        result = cloudinary.uploader.upload(
            f"data:{media_type};base64,{image_b64}",
            public_id=public_id,
            overwrite=True,
        )
        return result["secure_url"]

    # S3 fallback
    data = base64.b64decode(image_b64)
    upload_bytes(public_id, data, media_type)
    public_endpoint = settings.s3_public_endpoint_url or settings.s3_endpoint_url
    return f"{public_endpoint}/{settings.s3_bucket}/{public_id}"

_s3_client = None

_BOTO_CONFIG = Config(connect_timeout=3, read_timeout=10, retries={"max_attempts": 1})


def _get_client():  # type: ignore[return]
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
            config=_BOTO_CONFIG,
        )
    return _s3_client


def configure_bucket() -> None:
    """Create the bucket if it doesn't exist and set CORS for browser uploads."""
    client = _get_client()
    try:
        client.head_bucket(Bucket=settings.s3_bucket)
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
            client.create_bucket(Bucket=settings.s3_bucket)
        else:
            raise

    client.put_bucket_cors(
        Bucket=settings.s3_bucket,
        CORSConfiguration={
            "CORSRules": [
                {
                    "AllowedHeaders": ["*"],
                    "AllowedMethods": ["PUT", "GET", "HEAD"],
                    "AllowedOrigins": ["*"],
                    "ExposeHeaders": ["ETag"],
                    "MaxAgeSeconds": 3600,
                }
            ]
        },
    )


def upload_bytes(key: str, data: bytes, content_type: str = "image/webp") -> str:
    """Upload raw bytes and return the public URL.

    Uses Cloudinary when CLOUDINARY_URL is set, otherwise S3.
    The returned URL should be stored as the asset's storage_key.
    """
    if settings.cloudinary_url:
        cloudinary.config(cloudinary_url=settings.cloudinary_url)
        image_b64 = base64.b64encode(data).decode()
        result = cloudinary.uploader.upload(
            f"data:{content_type};base64,{image_b64}",
            public_id=key.replace("/", "_").replace(".", "_"),
            overwrite=True,
            resource_type="auto",
        )
        return result["secure_url"]  # type: ignore[return-value]

    _get_client().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    public_endpoint = settings.s3_public_endpoint_url or settings.s3_endpoint_url
    return f"{public_endpoint}/{settings.s3_bucket}/{key}"


def download_bytes(key: str) -> bytes:
    """Download bytes from a full URL (Cloudinary/fal.ai) or an S3 key."""
    if key.startswith("http"):
        import httpx
        response = httpx.get(key, follow_redirects=True, timeout=30)
        response.raise_for_status()
        return response.content
    response = _get_client().get_object(Bucket=settings.s3_bucket, Key=key)
    return response["Body"].read()  # type: ignore[return-value]


def object_exists(key: str) -> bool:
    """Return True if the object exists in storage.

    Always returns False when using Cloudinary — segmentation cache is S3-only.
    """
    if settings.cloudinary_url:
        return False
    try:
        _get_client().head_object(Bucket=settings.s3_bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return False
        raise


def generate_presigned_download_url(key: str, expiry: int = 3600) -> str:
    """Return a presigned S3 GET URL valid for the given number of seconds."""
    public_endpoint = settings.s3_public_endpoint_url or settings.s3_endpoint_url
    client = boto3.client(
        "s3",
        endpoint_url=public_endpoint,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name=settings.s3_region,
    )
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expiry,
    )


def generate_presigned_upload_url(key: str, content_type: str = "image/jpeg") -> str:
    """Return a presigned S3 PUT URL valid for 5 minutes."""
    public_endpoint = settings.s3_public_endpoint_url or settings.s3_endpoint_url

    # Build a separate client pointing at the public endpoint for URL generation
    client = boto3.client(
        "s3",
        endpoint_url=public_endpoint,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name=settings.s3_region,
    )
    return client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": key,
        },
        ExpiresIn=300,
    )
