"""Low-level httpx wrapper for the fal.ai queue API.

Only this file knows the fal.ai wire format — all other code uses providers/base.py types.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from app.core.config import settings

_QUEUE_BASE = "https://queue.fal.run"
_REST_BASE = "https://fal.run"
_STORAGE_INITIATE = "https://rest.alpha.fal.ai/storage/upload/initiate"
_POLL_INTERVAL = 2.0
_POLL_MAX_SECONDS = 180


class FalError(Exception):
    """Raised when fal.ai returns an error response."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"fal.ai {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


class FalClient:
    """Async HTTP client for fal.ai.  Instantiate once per task invocation."""

    def __init__(self, api_key: str | None = None) -> None:
        self._key = api_key or settings.fal_key
        self._headers = {
            "Authorization": f"Key {self._key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Queue API: submit → poll → result
    # ------------------------------------------------------------------

    async def queue_run(self, model_id: str, input_payload: dict[str, Any]) -> dict[str, Any]:
        """Submit a job to fal.ai queue, poll until done, return result dict."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            request_id = await self._submit(client, model_id, input_payload)
            await self._poll(client, model_id, request_id)
            return await self._result(client, model_id, request_id)

    async def _submit(
        self, client: httpx.AsyncClient, model_id: str, payload: dict[str, Any]
    ) -> str:
        url = f"{_QUEUE_BASE}/{model_id}"
        r = await client.post(url, json=payload, headers=self._headers)
        if r.status_code not in (200, 201):
            raise FalError(r.status_code, r.text[:500])
        data = r.json()
        request_id: str = data["request_id"]
        return request_id

    async def _poll(
        self, client: httpx.AsyncClient, model_id: str, request_id: str
    ) -> None:
        url = f"{_QUEUE_BASE}/{model_id}/requests/{request_id}/status"
        deadline = time.monotonic() + _POLL_MAX_SECONDS
        while time.monotonic() < deadline:
            r = await client.get(url, headers=self._headers)
            if r.status_code != 200:
                raise FalError(r.status_code, r.text[:500])
            data = r.json()
            status: str = data.get("status", "")
            if status == "COMPLETED":
                return
            if status == "FAILED":
                raise FalError(500, data.get("error", "fal.ai job failed"))
            await asyncio.sleep(_POLL_INTERVAL)
        raise TimeoutError(f"fal.ai job {request_id} timed out after {_POLL_MAX_SECONDS}s")

    async def _result(
        self, client: httpx.AsyncClient, model_id: str, request_id: str
    ) -> dict[str, Any]:
        url = f"{_QUEUE_BASE}/{model_id}/requests/{request_id}"
        r = await client.get(url, headers=self._headers)
        if r.status_code != 200:
            raise FalError(r.status_code, r.text[:500])
        return r.json()  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # File storage: upload bytes → get a publicly-accessible fal.ai URL
    # ------------------------------------------------------------------

    async def upload_file(
        self, data: bytes, content_type: str, filename: str = "file"
    ) -> str:
        """Upload bytes to fal.ai storage.  Returns a public URL valid for ≥24 h."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. Initiate
            r = await client.post(
                _STORAGE_INITIATE,
                json={"content_type": content_type, "file_name": filename},
                headers=self._headers,
            )
            if r.status_code != 200:
                raise FalError(r.status_code, r.text[:500])
            init_data = r.json()
            upload_url: str = init_data["upload_url"]
            file_url: str = init_data["file_url"]

            # 2. PUT the bytes
            put_r = await client.put(
                upload_url,
                content=data,
                headers={"Content-Type": content_type},
            )
            if put_r.status_code not in (200, 204):
                raise FalError(put_r.status_code, put_r.text[:300])

            return file_url

    # ------------------------------------------------------------------
    # Convenience: download a URL to bytes (used for results + segmentation)
    # ------------------------------------------------------------------

    async def download_url(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.content
