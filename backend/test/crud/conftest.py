"""Redis-backed repository fixtures using fakeredis."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from fakeredis.aioredis import FakeRedis

from aminyx_suggestion_agent.ai_agent.repository.redis import SuggestionJobRepositoryRedis
from aminyx_suggestion_agent.strategy_content.repository.redis import (
    StrategyContentJobRepositoryRedis,
)


@pytest_asyncio.fixture
async def fake_redis() -> AsyncIterator[FakeRedis]:
    client = FakeRedis(decode_responses=True)
    yield client
    await client.aclose()


@pytest_asyncio.fixture
async def suggestion_repo(fake_redis: FakeRedis) -> SuggestionJobRepositoryRedis:
    return SuggestionJobRepositoryRedis(fake_redis, ttl_seconds=3600)


@pytest_asyncio.fixture
async def strategy_content_repo(fake_redis: FakeRedis) -> StrategyContentJobRepositoryRedis:
    return StrategyContentJobRepositoryRedis(fake_redis, ttl_seconds=3600)
