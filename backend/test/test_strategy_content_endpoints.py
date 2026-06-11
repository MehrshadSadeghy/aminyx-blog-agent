"""
Strategy content endpoint tests.

Nodes:
  require_bearer (shared)
  create_strategy_content_job (CC=1)
  get_strategy_content_job_status (CC=2)
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from aminyx_suggestion_agent.ai_agent.domain import JobStatus
from support.app_factory import create_test_app
from support.factories import build_completed_strategy_content_job, build_strategy_content_job
from support.payloads import strategy_content_job_payload

from conftest import open_api_client

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_create_strategy_content_job_returns_202(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
    service_mocks: dict,
) -> None:
    # Input: valid strategy content payload
    job = build_strategy_content_job()
    service_mocks["strategy_content_service"].create_job = AsyncMock(return_value=job)

    # Act
    response = await api_client.post(
        "/api/v1/agent/strategy-content",
        json=strategy_content_job_payload(),
        headers=auth_headers,
    )

    # Expected: accepted job envelope
    assert response.status_code == 202
    body = response.json()
    assert body["jobId"] == str(job.id)
    assert body["status"] == JobStatus.PENDING.value


@pytest.mark.asyncio
async def test_create_strategy_content_job_rejects_missing_callback(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    # Input: payload missing callback configuration
    payload = strategy_content_job_payload(include_callback=False)

    # Act
    response = await api_client.post(
        "/api/v1/agent/strategy-content",
        json=payload,
        headers=auth_headers,
    )

    # Expected: validation failure
    assert response.status_code == 422


@pytest.mark.parametrize(
    "field,value",
    [
        ("audienceLevel", "invalid_level"),
        ("contentLength", "extra_long"),
        ("tone", "sarcastic"),
        ("ctaGoal", "unknown_goal"),
        ("seoOptimizationMode", "none"),
    ],
)
@pytest.mark.asyncio
async def test_create_strategy_content_job_rejects_invalid_enum_values(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
    field: str,
    value: str,
) -> None:
    # Input: one invalid enum field per parametrized case
    payload = strategy_content_job_payload()
    payload[field] = value

    # Act
    response = await api_client.post(
        "/api/v1/agent/strategy-content",
        json=payload,
        headers=auth_headers,
    )

    # Expected: validation error
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_strategy_content_job_returns_status_dto(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
    service_mocks: dict,
) -> None:
    # Input: completed strategy job
    job = build_completed_strategy_content_job()
    service_mocks["strategy_content_service"].get_job = AsyncMock(return_value=job)

    # Act
    response = await api_client.get(
        f"/api/v1/agent/strategy-content/{job.id}",
        headers=auth_headers,
    )

    # Expected: full status projection
    assert response.status_code == 200
    body = response.json()
    assert body["jobId"] == str(job.id)
    assert body["status"] == JobStatus.COMPLETE.value
    assert body["strategyContentText"] == job.strategy_content_text
    assert body["result"]["content"] == "Full article body."


@pytest.mark.asyncio
async def test_get_strategy_content_job_returns_404_when_missing(
    api_client: AsyncClient,
    auth_headers: dict[str, str],
    service_mocks: dict,
) -> None:
    # Input: unknown job id
    missing_id = uuid4()
    service_mocks["strategy_content_service"].get_job = AsyncMock(return_value=None)

    # Act
    response = await api_client.get(
        f"/api/v1/agent/strategy-content/{missing_id}",
        headers=auth_headers,
    )

    # Expected: not found
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found."


@pytest.mark.asyncio
async def test_strategy_content_routes_require_authorization(api_client: AsyncClient) -> None:
    # Input: no auth header
    response = await api_client.post(
        "/api/v1/agent/strategy-content",
        json=strategy_content_job_payload(),
    )

    # Expected: unauthorized
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_strategy_content_routes_return_503_without_server_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Input: ADMIN_API_KEY unset
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    app = create_test_app()

    async with open_api_client(app) as client:
        response = await client.get(
            f"/api/v1/agent/strategy-content/{uuid4()}",
            headers={"Authorization": "Bearer token"},
        )

    # Expected: service unavailable
    assert response.status_code == 503
