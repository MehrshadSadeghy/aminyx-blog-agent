"""Domain object factories for repository and service tests."""

from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import HttpUrl

from aminyx_suggestion_agent.ai_agent.domain import (
    BusinessData,
    BusinessInfo,
    JobStatus,
    SuggestionJob,
    TopicSuggestion,
)
from aminyx_suggestion_agent.strategy_content.domain import (
    AudienceLevel,
    ContentLength,
    ContentTone,
    CtaGoal,
    SeoOptimizationMode,
    StrategyContentJob,
    StrategyContentResult,
)


def sample_business_data_domain() -> BusinessData:
    return BusinessData(
        business_info=BusinessInfo(
            business_name="Acme Growth Labs",
            brand_name="Acme",
            industry="B2B SaaS",
            short_description="Helps SMBs automate lead generation.",
        )
    )


def build_suggestion_job(
    *,
    job_id: UUID | None = None,
    status: JobStatus = JobStatus.PENDING,
    correlation_id: str | None = "corr-001",
) -> SuggestionJob:
    return SuggestionJob(
        id=job_id or uuid4(),
        status=status,
        business_data=sample_business_data_domain(),
        callback_url=HttpUrl("http://test-backend/webhooks/suggestion"),
        correlation_id=correlation_id,
        goal=["increase_leads"],
    )


def build_completed_suggestion_job() -> SuggestionJob:
    job = build_suggestion_job(status=JobStatus.COMPLETE)
    job.topics = [
        TopicSuggestion(
            title="How Acme automates lead scoring",
            description="A practical guide.",
            keywords=["lead scoring"],
        )
    ]
    return job


def build_strategy_content_job(
    *,
    job_id: UUID | None = None,
    status: JobStatus = JobStatus.PENDING,
    correlation_id: str | None = "corr-strat-001",
) -> StrategyContentJob:
    return StrategyContentJob(
        id=job_id or uuid4(),
        status=status,
        business_data=sample_business_data_domain(),
        strategy_content_text="How to grow B2B leads with content marketing",
        audience_level=AudienceLevel.GENERAL_AUDIENCE,
        content_length=ContentLength.MEDIUM,
        tone=ContentTone.PROFESSIONAL,
        cta_goal=CtaGoal.COLLECT_LEADS,
        seo_optimization_mode=SeoOptimizationMode.BALANCED,
        callback_url=HttpUrl("http://test-backend/webhooks/strategy-content"),
        correlation_id=correlation_id,
    )


def build_completed_strategy_content_job() -> StrategyContentJob:
    job = build_strategy_content_job(status=JobStatus.COMPLETE)
    job.result = StrategyContentResult(
        content="Full article body.",
        title="Grow B2B leads",
        meta_description="A guide to content marketing.",
        keywords=["B2B", "leads"],
    )
    job.total_tokens = 512
    return job
