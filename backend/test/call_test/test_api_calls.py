"""pytest wrappers around the httpx API call tasks."""

from __future__ import annotations

import pytest

from call_test.client import AgentApiClient
from call_test.tasks import (
    task_create_strategy_content_job,
    task_create_suggestion_job,
    task_get_unknown_job,
    task_health_check,
    task_poll_strategy_content_job,
    task_poll_suggestion_job,
    task_unauthorized_request,
)

pytestmark = pytest.mark.asyncio


async def test_health_check(api_client: AgentApiClient) -> None:
    outcome = await task_health_check(api_client)
    assert outcome.ok, outcome.detail


async def test_unauthorized_request(api_client: AgentApiClient) -> None:
    outcome = await task_unauthorized_request(api_client)
    assert outcome.ok, outcome.detail


async def test_get_unknown_job_returns_404(api_client: AgentApiClient) -> None:
    outcome = await task_get_unknown_job(api_client)
    assert outcome.ok, outcome.detail


async def test_create_and_poll_suggestion_job(api_client: AgentApiClient) -> None:
    created = await task_create_suggestion_job(api_client)
    assert created.ok, created.detail
    assert created.data is not None

    polled = await task_poll_suggestion_job(api_client, str(created.data["jobId"]))
    assert polled.ok, polled.detail
    assert polled.data is not None
    assert polled.data["status"] in {"pending", "processing", "complete", "fail"}


async def test_create_and_poll_strategy_content_job(api_client: AgentApiClient) -> None:
    created = await task_create_strategy_content_job(api_client)
    assert created.ok, created.detail
    assert created.data is not None

    polled = await task_poll_strategy_content_job(api_client, str(created.data["jobId"]))
    assert polled.ok, polled.detail
    assert polled.data is not None
    assert polled.data["status"] in {"pending", "processing", "complete", "fail"}
