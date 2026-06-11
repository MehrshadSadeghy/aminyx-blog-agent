"""
System-level workflow tests across HTTP API + in-memory service layer.

Workflows:
  1. Create suggestion job -> poll status (pending)
  2. Create strategy content job -> poll status (pending)
  3. Auth failure on protected routes
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from aminyx_suggestion_agent.ai_agent.domain import JobStatus
from aminyx_suggestion_agent.ai_agent.service import SuggestionAgentService
from aminyx_suggestion_agent.strategy_content.service import StrategyContentAgentService
from support.app_factory import create_test_app
from support.factories import build_suggestion_job, build_strategy_content_job
from support.payloads import strategy_content_job_payload, suggestion_job_payload

from conftest import open_api_client

pytestmark = pytest.mark.system


@pytest.mark.asyncio
async def test_suggestion_job_create_then_poll_workflow(auth_headers: dict[str, str]) -> None:
    """
    Components: POST /suggestions, GET /suggestions/{id}, SuggestionAgentService mock.
    Expected workflow: client receives 202 then can read pending job by id.
    """
    job = build_suggestion_job(correlation_id="system-sugg-001")
    suggestion_service = AsyncMock(spec=SuggestionAgentService)
    suggestion_service.create_job = AsyncMock(return_value=job)
    suggestion_service.get_job = AsyncMock(return_value=job)
    app = create_test_app(suggestion_service=suggestion_service)

    async with open_api_client(app) as client:
        create_response = await client.post(
            "/api/v1/agent/suggestions",
            json=suggestion_job_payload(correlation_id="system-sugg-001"),
            headers=auth_headers,
        )
        assert create_response.status_code == 202
        job_id = create_response.json()["jobId"]

        poll_response = await client.get(
            f"/api/v1/agent/suggestions/{job_id}",
            headers=auth_headers,
        )

    assert poll_response.status_code == 200
    body = poll_response.json()
    assert body["jobId"] == job_id
    assert body["status"] == JobStatus.PENDING.value
    assert body["correlationId"] == "system-sugg-001"


@pytest.mark.asyncio
async def test_strategy_content_job_create_then_poll_workflow(auth_headers: dict[str, str]) -> None:
    """
    Components: POST /strategy-content, GET /strategy-content/{id}.
    Expected workflow: accepted job remains queryable with input parameters echoed.
    """
    job = build_strategy_content_job(correlation_id="system-strat-001")
    strategy_service = AsyncMock(spec=StrategyContentAgentService)
    strategy_service.create_job = AsyncMock(return_value=job)
    strategy_service.get_job = AsyncMock(return_value=job)
    app = create_test_app(strategy_content_service=strategy_service)

    async with open_api_client(app) as client:
        create_response = await client.post(
            "/api/v1/agent/strategy-content",
            json=strategy_content_job_payload(correlation_id="system-strat-001"),
            headers=auth_headers,
        )
        assert create_response.status_code == 202
        job_id = create_response.json()["jobId"]

        poll_response = await client.get(
            f"/api/v1/agent/strategy-content/{job_id}",
            headers=auth_headers,
        )

    assert poll_response.status_code == 200
    body = poll_response.json()
    assert body["jobId"] == job_id
    assert body["audienceLevel"] == "general_audience"
    assert body["contentLength"] == "medium"


@pytest.mark.asyncio
async def test_protected_routes_reject_anonymous_health_still_public(
    auth_headers: dict[str, str],
) -> None:
    """
    Components: /health (public), agent routes (protected).
    Expected: health works anonymously; agent routes require bearer token.
    """
    job = build_suggestion_job(correlation_id="authorized")
    suggestion_service = AsyncMock(spec=SuggestionAgentService)
    suggestion_service.create_job = AsyncMock(return_value=job)
    app = create_test_app(suggestion_service=suggestion_service)

    async with open_api_client(app) as client:
        health = await client.get("/health")
        anonymous_create = await client.post(
            "/api/v1/agent/suggestions",
            json=suggestion_job_payload(),
        )
        authorized_create = await client.post(
            "/api/v1/agent/suggestions",
            json=suggestion_job_payload(correlation_id="authorized"),
            headers=auth_headers,
        )

    assert health.status_code == 200
    assert anonymous_create.status_code == 401
    # Mock service returns default AsyncMock — still proves auth gate passed
    assert authorized_create.status_code == 202
