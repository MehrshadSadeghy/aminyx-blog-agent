from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from pydantic import HttpUrl

from aminyx_suggestion_agent.ai_agent.domain import BusinessData, JobStatus
from aminyx_suggestion_agent.ai_agent.infrastructure.callback_client import CallbackClient
from aminyx_suggestion_agent.ai_agent.infrastructure.gemini_client import GeminiClient
from aminyx_suggestion_agent.strategy_content.domain import (
    CONTENT_LENGTH_CHAR_RANGES,
    AudienceLevel,
    ContentLength,
    ContentTone,
    CtaGoal,
    SeoOptimizationMode,
    StrategyContentJob,
    StrategyContentResult,
)
from aminyx_suggestion_agent.strategy_content.infrastructure.prompt_loader import (
    StrategyContentPromptLoader,
)
from aminyx_suggestion_agent.strategy_content.repository.redis import (
    StrategyContentJobRepositoryRedis,
)

LOGGER = logging.getLogger(__name__)

_CONTENT_LENGTH_MAX_TOKENS: dict[ContentLength, int] = {
    ContentLength.SHORT: 1024,
    ContentLength.MEDIUM: 2048,
    ContentLength.LONG: 4096,
}


class StrategyContentAgentService:
    def __init__(
        self,
        *,
        jobs: StrategyContentJobRepositoryRedis,
        gemini: GeminiClient,
        callback_client: CallbackClient,
        prompt_loader: StrategyContentPromptLoader,
        parallel_gate: asyncio.Semaphore | None = None,
    ) -> None:
        self._jobs = jobs
        self._gemini = gemini
        self._callback = callback_client
        self._prompt_loader = prompt_loader
        self._parallel_gate = parallel_gate

    async def create_job(
        self,
        *,
        business_data: BusinessData,
        strategy_content_text: str,
        audience_level: AudienceLevel,
        content_length: ContentLength,
        tone: ContentTone,
        cta_goal: CtaGoal,
        seo_optimization_mode: SeoOptimizationMode,
        callback_url: HttpUrl,
        correlation_id: str | None = None,
        callback_method: str = "POST",
        callback_headers: dict[str, str] | None = None,
    ) -> StrategyContentJob:
        job = StrategyContentJob(
            business_data=business_data,
            strategy_content_text=strategy_content_text,
            audience_level=audience_level,
            content_length=content_length,
            tone=tone,
            cta_goal=cta_goal,
            seo_optimization_mode=seo_optimization_mode,
            callback_url=callback_url,
            correlation_id=correlation_id,
            callback_method=callback_method,
            callback_headers=callback_headers or {},
        )
        return await self._jobs.create(job)

    async def get_job(self, job_id: UUID) -> StrategyContentJob | None:
        return await self._jobs.get(job_id)

    async def dequeue_next(self, timeout_seconds: int = 1) -> UUID | None:
        return await self._jobs.dequeue(timeout_seconds=timeout_seconds)

    async def process_job(self, job_id: UUID) -> None:
        job = await self._jobs.get(job_id)
        if job is None:
            LOGGER.warning("Strategy content job %s not found — skipping", job_id)
            return
        if job.status != JobStatus.PENDING:
            LOGGER.info(
                "Strategy content job %s already processed with status %s",
                job_id,
                job.status,
            )
            return

        try:
            result, total_tokens = await self._generate_content(job)
            job = await self._jobs.update_status(
                job_id,
                status=JobStatus.COMPLETE,
                result=result,
                total_tokens=total_tokens,
                error=None,
            )
            if job is None:
                return
            await self._deliver_callback(job)
        except Exception as exc:
            LOGGER.exception("Strategy content job %s failed", job_id)
            job = await self._jobs.update_status(
                job_id,
                status=JobStatus.FAIL,
                error=str(exc),
            )
            if job is not None:
                await self._deliver_callback(job)

    async def _generate_content(
        self,
        job: StrategyContentJob,
    ) -> tuple[StrategyContentResult, int | None]:
        system_prompt = self._prompt_loader.load()
        user_prompt = self._build_user_prompt(job)
        max_tokens = _CONTENT_LENGTH_MAX_TOKENS[job.content_length]
        generation = await self._run(
            self._gemini.generate(
                user_prompt,
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
            )
        )
        result = self._parse_result(generation.text, job)
        return result, generation.total_tokens

    def _build_user_prompt(self, job: StrategyContentJob) -> str:
        min_chars, max_chars = CONTENT_LENGTH_CHAR_RANGES[job.content_length]
        business_payload = job.business_data.model_dump(mode="json", exclude_none=True)
        return (
            "Write a complete article based on the inputs below.\n\n"
            f"Topic / brief:\n{job.strategy_content_text}\n\n"
            f"Audience level: {job.audience_level.value}\n"
            f"Content length: {job.content_length.value} ({min_chars}–{max_chars} characters)\n"
            f"Tone: {job.tone.value}\n"
            f"CTA goal: {job.cta_goal.value}\n"
            f"SEO optimization mode: {job.seo_optimization_mode.value}\n\n"
            f"Business profile JSON:\n{json.dumps(business_payload, ensure_ascii=False, indent=2)}\n\n"
            "Return ONLY the JSON object described in your system instructions."
        )

    def _parse_result(
        self,
        content: str,
        job: StrategyContentJob,
    ) -> StrategyContentResult:
        content = content.strip()
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(content[start : end + 1])
                if isinstance(parsed, dict) and parsed.get("content"):
                    return StrategyContentResult.model_validate(parsed)
            except (json.JSONDecodeError, ValueError):
                pass

        LOGGER.warning(
            "Could not parse strategy content from Gemini response — using raw text fallback"
        )
        brand = (
            job.business_data.business_info.brand_name
            or job.business_data.business_info.business_name
            or "Article"
        )
        return StrategyContentResult(
            content=content,
            title=job.strategy_content_text or brand,
            meta_description=job.business_data.business_info.short_description,
            keywords=job.business_data.branding.keywords[:5],
        )

    async def _deliver_callback(self, job: StrategyContentJob) -> None:
        payload: dict = {
            "jobId": str(job.id),
            "correlationId": job.correlation_id,
            "status": job.status.value,
        }
        if job.status == JobStatus.COMPLETE and job.result is not None:
            payload["result"] = {
                "content": job.result.content,
                "title": job.result.title,
                "metaDescription": job.result.meta_description,
                "keywords": job.result.keywords,
            }
            if job.total_tokens is not None:
                payload["token_usage"] = {"total_tokens": job.total_tokens}
        else:
            payload["error"] = job.error

        try:
            await self._callback.deliver(
                str(job.callback_url),
                payload,
                method=job.callback_method,
                headers=job.callback_headers or None,
            )
        except Exception:
            LOGGER.exception("Callback delivery failed for strategy content job %s", job.id)

    async def _run(self, coro):
        if self._parallel_gate:
            async with self._parallel_gate:
                return await coro
        return await coro
