"""httpx client that mimics how the Aminyx backend calls the agent APIs."""

from __future__ import annotations

import os
from typing import Any

import httpx


class AgentApiClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("AGENT_BASE_URL", "http://localhost:8085")
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("ADMIN_API_KEY", "")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._auth_headers(),
        )

    def _auth_headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AgentApiClient:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()

    async def health(self) -> httpx.Response:
        return await self._client.get("/health")

    async def create_suggestion_job(self, payload: dict[str, Any]) -> httpx.Response:
        return await self._client.post("/api/v1/agent/suggestions", json=payload)

    async def get_suggestion_job(self, job_id: str) -> httpx.Response:
        return await self._client.get(f"/api/v1/agent/suggestions/{job_id}")

    async def create_strategy_content_job(self, payload: dict[str, Any]) -> httpx.Response:
        return await self._client.post("/api/v1/agent/strategy-content", json=payload)

    async def get_strategy_content_job(self, job_id: str) -> httpx.Response:
        return await self._client.get(f"/api/v1/agent/strategy-content/{job_id}")

    async def request_without_auth(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self._client.timeout) as anon:
            return await anon.request(method, path, **kwargs)
