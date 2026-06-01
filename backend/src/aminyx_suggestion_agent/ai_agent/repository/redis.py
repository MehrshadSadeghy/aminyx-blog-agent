from __future__ import annotations

from uuid import UUID

from redis.asyncio import Redis

from aminyx_suggestion_agent.ai_agent.domain import JobStatus, SuggestionJob

_JOB_KEY_PREFIX = "raya:suggestion:job:"
_QUEUE_KEY = "raya:suggestion:queue"


class SuggestionJobRepositoryRedis:
    def __init__(self, redis: Redis, *, ttl_seconds: int = 86_400) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    @staticmethod
    def queue_key() -> str:
        return _QUEUE_KEY

    def _job_key(self, job_id: UUID | str) -> str:
        return f"{_JOB_KEY_PREFIX}{job_id}"

    async def create(self, job: SuggestionJob) -> SuggestionJob:
        await self._redis.setex(
            self._job_key(job.id),
            self._ttl_seconds,
            job.model_dump_json(),
        )
        await self._redis.lpush(_QUEUE_KEY, str(job.id))
        return job

    async def get(self, job_id: UUID) -> SuggestionJob | None:
        raw = await self._redis.get(self._job_key(job_id))
        if raw is None:
            return None
        return SuggestionJob.model_validate_json(raw)

    async def save(self, job: SuggestionJob) -> SuggestionJob:
        job.touch()
        await self._redis.setex(
            self._job_key(job.id),
            self._ttl_seconds,
            job.model_dump_json(),
        )
        return job

    async def update_status(
        self,
        job_id: UUID,
        *,
        status: JobStatus,
        topics: list | None = None,
        error: str | None = None,
    ) -> SuggestionJob | None:
        job = await self.get(job_id)
        if job is None:
            return None
        job.status = status
        if topics is not None:
            job.topics = topics
        job.error = error
        return await self.save(job)

    async def dequeue(self, timeout_seconds: int = 1) -> UUID | None:
        result = await self._redis.brpop(_QUEUE_KEY, timeout=timeout_seconds)
        if result is None:
            return None
        _, job_id = result
        return UUID(job_id)
