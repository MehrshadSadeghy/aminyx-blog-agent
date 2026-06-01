from __future__ import annotations

import logging
from typing import Any

import httpx

LOGGER = logging.getLogger(__name__)


class CallbackClient:
    def __init__(self, *, timeout_seconds: float = 30.0) -> None:
        self._timeout = timeout_seconds
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def deliver(self, callback_url: str, payload: dict[str, Any]) -> None:
        try:
            response = await self._client.post(callback_url, json=payload)
            response.raise_for_status()
        except Exception:
            LOGGER.exception("Failed to deliver callback to %s", callback_url)
            raise
