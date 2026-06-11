"""Shared pytest fixtures for endpoint, CRUD, system, and call_test suites."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from support.app_factory import create_test_app, get_test_mocks

DEFAULT_TEST_API_KEY = "local-test-admin-key"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--agent-base-url",
        action="store",
        default=os.environ.get("AGENT_BASE_URL", "http://localhost:8085"),
        help="Base URL of the running agent service (call_test)",
    )
    parser.addoption(
        "--agent-api-key",
        action="store",
        default=os.environ.get("ADMIN_API_KEY", ""),
        help="ADMIN_API_KEY used for Bearer auth (call_test)",
    )


@pytest.fixture(autouse=True)
def admin_api_key_env(monkeypatch: pytest.MonkeyPatch) -> str:
    """Ensure bearer auth is configured for every test module."""
    api_key = os.environ.get("ADMIN_API_KEY", DEFAULT_TEST_API_KEY)
    monkeypatch.setenv("ADMIN_API_KEY", api_key)
    return api_key


@pytest.fixture
def auth_headers(admin_api_key_env: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_api_key_env}"}


@pytest.fixture
def test_app():
    return create_test_app()


@pytest.fixture
async def api_client(test_app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def service_mocks(test_app) -> dict[str, Any]:
    return get_test_mocks(test_app)


@asynccontextmanager
async def open_api_client(app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
