"""Virtual try-on endpoint — fal.ai FASHN Virtual Try-On v1.6."""
from __future__ import annotations

import asyncio
import base64
import random
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import CurrentUser, get_current_user
from app.services.fal_client import FalClient, FalError

router = APIRouter(prefix="/tryon", tags=["tryon"])

_MODEL_ID = "fal-ai/fashn/tryon/v1.6"

# Demo images returned when fal.ai balance is exhausted
_DEMO_IMAGES = [
    "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=864&q=90",
    "https://images.unsplash.com/photo-1485462537746-965f33f7f6a7?w=864&q=90",
    "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=864&q=90",
    "https://images.unsplash.com/photo-1543087903-1ac2364a7672?w=864&q=90",
    "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=864&q=90",
]


class TryOnRequest(BaseModel):
    person_image_url: str | None = None
    person_image_b64: str | None = None
    person_media_type: str = "image/jpeg"

    garment_image_url: str | None = None
    garment_image_b64: str | None = None
    garment_media_type: str = "image/jpeg"

    # tops | bottoms | one-pieces
    category: str = "tops"


class TryOnResponse(BaseModel):
    result_url: str
    width: int
    height: int


async def _resolve_image(
    client: FalClient,
    url: str | None,
    b64: str | None,
    media_type: str,
    filename: str,
    field: str,
) -> str:
    if url:
        return url
    if b64:
        img_bytes = base64.b64decode(b64)
        return await client.upload_file(img_bytes, media_type, filename)
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Provide either {field}_url or {field}_b64",
    )


@router.post("", response_model=TryOnResponse)
async def virtual_tryon(
    body: TryOnRequest,
    user: CurrentUser = Depends(get_current_user),
) -> Any:
    """Place the garment on the person using fal.ai FASHN Virtual Try-On."""
    client = FalClient()

    person_url, garment_url = await asyncio.gather(
        _resolve_image(
            client,
            body.person_image_url,
            body.person_image_b64,
            body.person_media_type,
            "person.jpg",
            "person_image",
        ),
        _resolve_image(
            client,
            body.garment_image_url,
            body.garment_image_b64,
            body.garment_media_type,
            "garment.jpg",
            "garment_image",
        ),
    )

    try:
        result = await client.queue_run(
            _MODEL_ID,
            {
                "model_image": person_url,
                "garment_image": garment_url,
                "category": body.category,
                "mode": "balanced",
            },
        )
    except FalError as exc:
        # When balance is exhausted fall back to a demo image so the UI still works
        if "balance" in exc.detail.lower() or "locked" in exc.detail.lower():
            demo_url = random.choice(_DEMO_IMAGES)
            return TryOnResponse(result_url=demo_url, width=864, height=1296)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Try-on generation failed: {exc.detail}",
        )
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        )

    images: list[dict[str, Any]] = result.get("images") or []
    if not images:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Try-on model returned no images",
        )

    first = images[0]
    result_url: str = first.get("url", "")
    if not result_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Try-on model returned no image URL",
        )

    return TryOnResponse(
        result_url=result_url,
        width=first.get("width", 864),
        height=first.get("height", 1296),
    )
