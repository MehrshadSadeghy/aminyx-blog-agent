"""
SuggestionJobRepositoryRedis tests.

Dependency graph:
  create -> setex, lpush
  get -> get
  save -> setex
  update_status -> get, save
  dequeue -> brpop

Cyclomatic complexity (approx.):
  create: 1 | get: 2 | save: 1 | update_status: 3 | dequeue: 2
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from aminyx_suggestion_agent.ai_agent.domain import JobStatus
from aminyx_suggestion_agent.ai_agent.repository.redis import SuggestionJobRepositoryRedis
from support.factories import build_completed_suggestion_job, build_suggestion_job

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_create_persists_job_and_enqueues_id(suggestion_repo: SuggestionJobRepositoryRedis) -> None:
    # Input: new pending job
    job = build_suggestion_job()

    # Act
    created = await suggestion_repo.create(job)

    # Expected: same job returned; retrievable with pending status
    stored = await suggestion_repo.get(created.id)
    assert stored is not None
    assert stored.id == created.id
    assert stored.status == JobStatus.PENDING
    assert stored.correlation_id == "corr-001"


@pytest.mark.asyncio
async def test_get_returns_none_for_unknown_job(suggestion_repo: SuggestionJobRepositoryRedis) -> None:
    # Input: random UUID never stored
    missing_id = uuid4()

    # Act
    result = await suggestion_repo.get(missing_id)

    # Expected: None
    assert result is None


@pytest.mark.asyncio
async def test_save_updates_existing_job(suggestion_repo: SuggestionJobRepositoryRedis) -> None:
    # Input: persisted job with modified correlation id
    job = await suggestion_repo.create(build_suggestion_job())
    job.correlation_id = "updated-corr"

    # Act
    saved = await suggestion_repo.save(job)

    # Expected: updated value round-trips
    stored = await suggestion_repo.get(saved.id)
    assert stored is not None
    assert stored.correlation_id == "updated-corr"
    assert stored.updated_at >= job.created_at


@pytest.mark.asyncio
async def test_update_status_sets_topics_and_clears_error(
    suggestion_repo: SuggestionJobRepositoryRedis,
) -> None:
    # Input: pending job promoted to complete with topics
    job = await suggestion_repo.create(build_suggestion_job())
    completed = build_completed_suggestion_job()
    completed.id = job.id

    # Act
    updated = await suggestion_repo.update_status(
        job.id,
        status=JobStatus.COMPLETE,
        topics=completed.topics,
        error=None,
    )

    # Expected: complete status with topics persisted
    assert updated is not None
    assert updated.status == JobStatus.COMPLETE
    assert len(updated.topics) == 1
    assert updated.topics[0].title == completed.topics[0].title
    assert updated.error is None


@pytest.mark.asyncio
async def test_update_status_returns_none_when_job_missing(
    suggestion_repo: SuggestionJobRepositoryRedis,
) -> None:
    # Input: unknown job id
    missing_id = uuid4()

    # Act
    result = await suggestion_repo.update_status(
        missing_id,
        status=JobStatus.FAIL,
        error="not found",
    )

    # Expected: None (early return path)
    assert result is None


@pytest.mark.asyncio
async def test_dequeue_returns_enqueued_job_id(suggestion_repo: SuggestionJobRepositoryRedis) -> None:
    # Input: one enqueued job
    job = await suggestion_repo.create(build_suggestion_job())

    # Act
    dequeued_id = await suggestion_repo.dequeue(timeout_seconds=1)

    # Expected: same job id
    assert dequeued_id == job.id


@pytest.mark.asyncio
async def test_dequeue_returns_none_on_empty_queue(suggestion_repo: SuggestionJobRepositoryRedis) -> None:
    # Input: empty queue

    # Act
    dequeued_id = await suggestion_repo.dequeue(timeout_seconds=1)

    # Expected: None
    assert dequeued_id is None
