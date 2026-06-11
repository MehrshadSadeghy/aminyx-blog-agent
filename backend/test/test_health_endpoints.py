"""
GET /health endpoint tests.

Function: health_check
  Cyclomatic complexity: 1
  Paths: success
  Dependencies: none
  Risk: low
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_health_returns_ok_status(api_client: AsyncClient) -> None:
    # Input: unauthenticated GET /health
    response = await api_client.get("/health")

    # Expected: 200 with status ok
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
