    """pytest fixtures for httpx API call tests."""

from __future__ import annotations

import os

import pytest

from call_test.client import AgentApiClient


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--agent-base-url",
        action="store",
        default=os.environ.get("AGENT_BASE_URL", "http://localhost:8085"),
        help="Base URL of the running agent service",
    )
    parser.addoption(
        "--agent-api-key",
        action="store",
        default=os.environ.get("ADMIN_API_KEY", ""),
        help="ADMIN_API_KEY used for Bearer auth",
    )


@pytest.fixture
def agent_base_url(request: pytest.FixtureRequest) -> str:
    return str(request.config.getoption("--agent-base-url")).rstrip("/")


@pytest.fixture
def agent_api_key(request: pytest.FixtureRequest) -> str:
    return str(request.config.getoption("--agent-api-key"))


@pytest.fixture
async def api_client(agent_base_url: str, agent_api_key: str) -> AgentApiClient:
    if not agent_api_key:
        pytest.skip("ADMIN_API_KEY is not set")
    async with AgentApiClient(base_url=agent_base_url, api_key=agent_api_key) as client:
        yield client
