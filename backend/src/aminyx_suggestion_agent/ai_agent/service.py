from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from pydantic import HttpUrl

from aminyx_suggestion_agent.ai_agent.domain import (
    BusinessData,
    JobStatus,
    SuggestionJob,
    TopicSuggestion,
)
from aminyx_suggestion_agent.ai_agent.infrastructure.callback_client import CallbackClient
from aminyx_suggestion_agent.ai_agent.infrastructure.gemini_client import GeminiClient
from aminyx_suggestion_agent.ai_agent.repository.redis import SuggestionJobRepositoryRedis

LOGGER = logging.getLogger(__name__)


class SuggestionAgentService:
    def __init__(
        self,
        *,
        jobs: SuggestionJobRepositoryRedis,
        gemini: GeminiClient,
        callback_client: CallbackClient,
        parallel_gate: asyncio.Semaphore | None = None,
    ) -> None:
        self._jobs = jobs
        self._gemini = gemini
        self._callback = callback_client
        self._parallel_gate = parallel_gate

    async def create_job(
        self,
        *,
        business_data: BusinessData,
        callback_url: HttpUrl,
        correlation_id: str | None = None,
        callback_method: str = "POST",
        callback_headers: dict[str, str] | None = None,
        goal: list[str] | None = None,
    ) -> SuggestionJob:
        job = SuggestionJob(
            business_data=business_data,
            callback_url=callback_url,
            correlation_id=correlation_id,
            callback_method=callback_method,
            callback_headers=callback_headers or {},
            goal=goal or [],
        )
        return await self._jobs.create(job)

    async def get_job(self, job_id: UUID) -> SuggestionJob | None:
        return await self._jobs.get(job_id)

    async def dequeue_next(self, timeout_seconds: int = 1) -> UUID | None:
        return await self._jobs.dequeue(timeout_seconds=timeout_seconds)

    async def process_job(self, job_id: UUID) -> None:
        job = await self._jobs.get(job_id)
        if job is None:
            LOGGER.warning("Job %s not found — skipping", job_id)
            return
        if job.status != JobStatus.PENDING:
            LOGGER.info("Job %s already processed with status %s", job_id, job.status)
            return

        try:
            topics = await self._generate_topics(job.business_data, job.goal)
            job = await self._jobs.update_status(
                job_id,
                status=JobStatus.COMPLETE,
                topics=topics,
                error=None,
            )
            if job is None:
                return
            await self._deliver_callback(job)
        except Exception as exc:
            LOGGER.exception("Job %s failed", job_id)
            job = await self._jobs.update_status(
                job_id,
                status=JobStatus.FAIL,
                error=str(exc),
            )
            if job is not None:
                await self._deliver_callback(job)

    async def _generate_topics(
        self,
        business_data: BusinessData,
        goal: list[str] | None = None,
    ) -> list[TopicSuggestion]:
        prompt = self._build_prompt(business_data, goal)
        content = await self._run(self._gemini.generate_text(prompt))
        return self._parse_topics(content, business_data)

    def _build_prompt(
        self,
        business_data: BusinessData,
        goal: list[str] | None = None,
    ) -> str:
        payload = business_data.model_dump(mode="json", exclude_none=True)
        goal_line = ""
        if goal:
            goal_line = f"Content goals: {', '.join(goal)}\n\n"
        return (
            "You are a content strategist. Based on the business website data below, "
            "suggest 5 to 8 blog or content topic ideas that would attract the target audience "
            "and support SEO goals.\n\n"
            f"{goal_line}"
            f"Business data JSON:\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
            "Return ONLY a JSON array of objects with this shape:\n"
            '[{"title": "...", "description": "...", "keywords": ["...", "..."]}]\n'
            "Do not include markdown or any text outside the JSON array."
        )

    def _parse_topics(
        self,
        content: str,
        business_data: BusinessData,
    ) -> list[TopicSuggestion]:
        content = content.strip()
        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(content[start : end + 1])
                if isinstance(parsed, list) and parsed:
                    topics: list[TopicSuggestion] = []
                    for item in parsed:
                        if isinstance(item, str):
                            topics.append(TopicSuggestion(title=item))
                        elif isinstance(item, dict) and item.get("title"):
                            topics.append(
                                TopicSuggestion(
                                    title=str(item["title"]),
                                    description=item.get("description"),
                                    keywords=[
                                        str(k)
                                        for k in (item.get("keywords") or [])
                                        if k
                                    ],
                                )
                            )
                    if topics:
                        return topics
            except json.JSONDecodeError:
                pass

        LOGGER.warning("Could not parse topics from Gemini response — using fallback")
        return self._fallback_topics(business_data)

    def _fallback_topics(self, business_data: BusinessData) -> list[TopicSuggestion]:
        info = business_data.business_info
        brand = info.brand_name or info.business_name or "your business"
        keywords = business_data.branding.keywords[:3]
        services = business_data.offerings.services[:3]
        pain_points = business_data.audience.pain_points[:2]

        topics: list[TopicSuggestion] = []
        for service in services:
            topics.append(
                TopicSuggestion(
                    title=f"How {brand} helps with {service}",
                    description=f"A practical guide to {service.lower()} for your audience.",
                    keywords=keywords or [service.lower()],
                )
            )
        for pain in pain_points:
            topics.append(
                TopicSuggestion(
                    title=f"Solving {pain} with modern web solutions",
                    description=f"How {brand} addresses {pain.lower()}.",
                    keywords=keywords,
                )
            )
        if not topics:
            topics.append(
                TopicSuggestion(
                    title=f"Why choose {brand} for your next digital project",
                    description=info.short_description or info.tagline,
                    keywords=keywords,
                )
            )
        return topics[:8]

    async def _deliver_callback(self, job: SuggestionJob) -> None:
        payload = {
            "jobId": str(job.id),
            "correlationId": job.correlation_id,
            "status": job.status.value,
            "topics": [topic.model_dump(mode="json") for topic in job.topics] or None,
            "error": job.error,
        }
        try:
            await self._callback.deliver(
                str(job.callback_url),
                payload,
                method=job.callback_method,
                headers=job.callback_headers or None,
            )
        except Exception:
            LOGGER.exception("Callback delivery failed for job %s", job.id)

    async def _run(self, coro):
        if self._parallel_gate:
            async with self._parallel_gate:
                return await coro
        return await coro
