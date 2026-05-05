from __future__ import annotations

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings

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


def upload_bytes(key: str, data: bytes, content_type: str = "image/webp") -> None:
    """Write raw bytes to S3 at the given key."""
    _get_client().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )


def download_bytes(key: str) -> bytes:
    """Download the object at key and return its raw bytes."""
    response = _get_client().get_object(Bucket=settings.s3_bucket, Key=key)
    return response["Body"].read()  # type: ignore[return-value]


def object_exists(key: str) -> bool:
    """Return True if the object exists in the bucket."""
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
            "ContentType": content_type,
        },
        ExpiresIn=300,
    )
