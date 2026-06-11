"""Fixtures for live-server API call tests."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest

from call_test.client import AgentApiClient


@pytest.fixture
def agent_base_url(request: pytest.FixtureRequest) -> str:
    return str(request.config.getoption("--agent-base-url")).rstrip("/")


@pytest.fixture
def agent_api_key(request: pytest.FixtureRequest) -> str:
    return str(request.config.getoption("--agent-api-key"))


@pytest.fixture
async def api_client(agent_base_url: str, agent_api_key: str) -> AsyncIterator[AgentApiClient]:
    if not agent_api_key:
        pytest.skip("ADMIN_API_KEY is not set")
    async with AgentApiClient(base_url=agent_base_url, api_key=agent_api_key) as client:
        yield client
