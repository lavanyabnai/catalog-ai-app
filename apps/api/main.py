from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import api_router
from app.routers.auth import router as auth_router
from app.services.storage import configure_bucket

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        configure_bucket()
    except Exception as exc:
        logger.warning("Storage bucket setup skipped: %s", exc)
    yield


app = FastAPI(
    title="catalog-ai API",
    version="0.1.0",
    description="AI cataloging backend for fashion retailers.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth routes are public (no Bearer required)
app.include_router(auth_router)

# All other API routes require a valid Bearer token
app.include_router(api_router)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
