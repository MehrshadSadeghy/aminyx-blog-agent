"""
StrategyContentJobRepositoryRedis tests.

Dependency graph mirrors suggestion repository:
  create, get, save, update_status, dequeue
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from aminyx_suggestion_agent.ai_agent.domain import JobStatus
from aminyx_suggestion_agent.strategy_content.repository.redis import (
    StrategyContentJobRepositoryRedis,
)
from support.factories import build_completed_strategy_content_job, build_strategy_content_job

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_create_persists_strategy_job(
    strategy_content_repo: StrategyContentJobRepositoryRedis,
) -> None:
    # Input: pending strategy content job
    job = build_strategy_content_job()

    # Act
    created = await strategy_content_repo.create(job)

    # Expected: stored with strategy fields intact
    stored = await strategy_content_repo.get(created.id)
    assert stored is not None
    assert stored.strategy_content_text == job.strategy_content_text
    assert stored.audience_level == job.audience_level
    assert stored.status == JobStatus.PENDING


@pytest.mark.asyncio
async def test_get_returns_none_for_unknown_job(
    strategy_content_repo: StrategyContentJobRepositoryRedis,
) -> None:
    # Input: unknown id
    result = await strategy_content_repo.get(uuid4())

    # Expected: None
    assert result is None


@pytest.mark.asyncio
async def test_update_status_persists_result_and_tokens(
    strategy_content_repo: StrategyContentJobRepositoryRedis,
) -> None:
    # Input: job transitioning to complete with AI result
    job = await strategy_content_repo.create(build_strategy_content_job())
    completed = build_completed_strategy_content_job()
    completed.id = job.id

    # Act
    updated = await strategy_content_repo.update_status(
        job.id,
        status=JobStatus.COMPLETE,
        result=completed.result,
        total_tokens=completed.total_tokens,
        error=None,
    )

    # Expected: result and token usage saved
    assert updated is not None
    assert updated.status == JobStatus.COMPLETE
    assert updated.result is not None
    assert updated.result.content == "Full article body."
    assert updated.total_tokens == 512


@pytest.mark.asyncio
async def test_update_status_returns_none_when_job_missing(
    strategy_content_repo: StrategyContentJobRepositoryRedis,
) -> None:
    # Input: missing job id
    result = await strategy_content_repo.update_status(
        uuid4(),
        status=JobStatus.FAIL,
        error="boom",
    )

    # Expected: None
    assert result is None


@pytest.mark.asyncio
async def test_dequeue_returns_enqueued_job_id(
    strategy_content_repo: StrategyContentJobRepositoryRedis,
) -> None:
    # Input: one queued job
    job = await strategy_content_repo.create(build_strategy_content_job())

    # Act
    dequeued_id = await strategy_content_repo.dequeue(timeout_seconds=1)

    # Expected: matching id
    assert dequeued_id == job.id


@pytest.mark.asyncio
async def test_dequeue_returns_none_on_empty_queue(
    strategy_content_repo: StrategyContentJobRepositoryRedis,
) -> None:
    # Input: empty queue
    dequeued_id = await strategy_content_repo.dequeue(timeout_seconds=1)

    # Expected: None
    assert dequeued_id is None
