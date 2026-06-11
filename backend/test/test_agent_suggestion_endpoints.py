"""
Suggestion agent endpoint tests.

Nodes:
  require_bearer (CC=4): missing key config, missing header, invalid token, success
  create_suggestion_job (CC=1): delegates to service
  get_suggestion_job_status (CC=2): found, not found (404)
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from aminyx_suggestion_agent.ai_agent.domain import JobStatus
from support.app_factory import create_test_app
from support.factories import build_completed_suggestion_job, build_suggestion_job
from support.payloads import suggestion_job_payload

from conftest import open_api_client

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_create_suggestion_job_returns_202_with_pending_status(
    asgi_client: AsyncClient,
    auth_headers: dict[str, str],
    service_mocks: dict,
) -> None:
    # Input: valid payload and bearer token
    job = build_suggestion_job()
    service_mocks["suggestion_service"].create_job = AsyncMock(return_value=job)
    payload = suggestion_job_payload()

    # Act
    response = await asgi_client.post(
        "/api/v1/agent/suggestions",
        json=payload,
        headers=auth_headers,
    )

    # Expected: accepted with job id and pending status
    assert response.status_code == 202
    body = response.json()
    assert body["jobId"] == str(job.id)
    assert body["status"] == JobStatus.PENDING.value
    service_mocks["suggestion_service"].create_job.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_suggestion_job_rejects_missing_callback(
    asgi_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    # Input: payload without callbackUrl or callback object
    payload = suggestion_job_payload(include_callback=False)

    # Act
    response = await asgi_client.post(
        "/api/v1/agent/suggestions",
        json=payload,
        headers=auth_headers,
    )

    # Expected: validation error
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_suggestion_job_returns_job_status(
    asgi_client: AsyncClient,
    auth_headers: dict[str, str],
    service_mocks: dict,
) -> None:
    # Input: existing completed job id
    job = build_completed_suggestion_job()
    service_mocks["suggestion_service"].get_job = AsyncMock(return_value=job)

    # Act
    response = await asgi_client.get(
        f"/api/v1/agent/suggestions/{job.id}",
        headers=auth_headers,
    )

    # Expected: 200 with serialized job fields
    assert response.status_code == 200
    body = response.json()
    assert body["jobId"] == str(job.id)
    assert body["status"] == JobStatus.COMPLETE.value
    assert body["correlationId"] == job.correlation_id
    assert body["topics"] is not None
    assert len(body["topics"]) == 1


@pytest.mark.asyncio
async def test_get_suggestion_job_returns_404_when_missing(
    asgi_client: AsyncClient,
    auth_headers: dict[str, str],
    service_mocks: dict,
) -> None:
    # Input: unknown job id
    missing_id = uuid4()
    service_mocks["suggestion_service"].get_job = AsyncMock(return_value=None)

    # Act
    response = await asgi_client.get(
        f"/api/v1/agent/suggestions/{missing_id}",
        headers=auth_headers,
    )

    # Expected: not found
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found."


@pytest.mark.asyncio
async def test_suggestion_routes_require_authorization_header(asgi_client: AsyncClient) -> None:
    # Input: request without Authorization header
    response = await asgi_client.post(
        "/api/v1/agent/suggestions",
        json=suggestion_job_payload(),
    )

    # Expected: unauthorized
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing Authorization header."


@pytest.mark.asyncio
async def test_suggestion_routes_reject_invalid_bearer_token(asgi_client: AsyncClient) -> None:
    # Input: wrong bearer token
    bad_headers = {"Authorization": "Bearer wrong-token"}

    # Act
    response = await asgi_client.post(
        "/api/v1/agent/suggestions",
        json=suggestion_job_payload(),
        headers=bad_headers,
    )

    # Expected: unauthorized
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials."


@pytest.mark.asyncio
async def test_suggestion_routes_return_503_when_api_key_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Input: server without ADMIN_API_KEY
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    app = create_test_app()

    async with open_api_client(app) as client:
        response = await client.post(
            "/api/v1/agent/suggestions",
            json=suggestion_job_payload(),
            headers={"Authorization": "Bearer any"},
        )

    # Expected: service unavailable
    assert response.status_code == 503
    assert response.json()["detail"] == "API key not configured on server."


@pytest.mark.parametrize(
    "invalid_job_id",
    [
        "not-a-uuid",
        "12345",
    ],
)
@pytest.mark.asyncio
async def test_get_suggestion_job_rejects_invalid_uuid(
    asgi_client: AsyncClient,
    auth_headers: dict[str, str],
    invalid_job_id: str,
) -> None:
    # Input: malformed job id path parameter
    response = await asgi_client.get(
        f"/api/v1/agent/suggestions/{invalid_job_id}",
        headers=auth_headers,
    )

    # Expected: validation error from FastAPI path parsing
    assert response.status_code == 422
