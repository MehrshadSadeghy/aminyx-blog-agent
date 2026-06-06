from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, HttpUrl, model_validator

from aminyx_suggestion_agent.ai_agent.api.v1.dto import ApiModel, BusinessDataDTO, CallbackDTO
from aminyx_suggestion_agent.ai_agent.domain import JobStatus
from aminyx_suggestion_agent.strategy_content.domain import (
    AudienceLevel,
    ContentLength,
    ContentTone,
    CtaGoal,
    SeoOptimizationMode,
    StrategyContentResult,
)


class CreateStrategyContentJobDTO(ApiModel):
    business_data: BusinessDataDTO = Field(alias="businessData")
    strategy_content_text: str = Field(alias="strategyContentText")
    audience_level: AudienceLevel = Field(alias="audienceLevel")
    content_length: ContentLength = Field(alias="contentLength")
    tone: ContentTone
    cta_goal: CtaGoal = Field(alias="ctaGoal")
    seo_optimization_mode: SeoOptimizationMode = Field(alias="seoOptimizationMode")
    correlation_id: str | None = Field(default=None, alias="correlationId")
    callback_url: HttpUrl | None = Field(default=None, alias="callbackUrl")
    callback: CallbackDTO | None = None

    @model_validator(mode="after")
    def require_callback(self) -> CreateStrategyContentJobDTO:
        if self.callback is None and self.callback_url is None:
            raise ValueError("Either callbackUrl or callback is required.")
        return self

    def resolved_callback_url(self) -> HttpUrl:
        if self.callback is not None:
            return self.callback.callback_url
        assert self.callback_url is not None
        return self.callback_url

    def resolved_callback_method(self) -> str:
        if self.callback is not None:
            return self.callback.callback_method.upper()
        return "POST"

    def resolved_callback_headers(self) -> dict[str, str]:
        if self.callback is not None:
            return self.callback.header_map()
        return {}


class StrategyContentResultDTO(ApiModel):
    content: str
    title: str | None = None
    meta_description: str | None = Field(default=None, serialization_alias="metaDescription")
    keywords: list[str] = Field(default_factory=list)


class StrategyJobAcceptedDTO(ApiModel):
    job_id: UUID = Field(serialization_alias="jobId")
    status: JobStatus = JobStatus.PENDING


class StrategyJobStatusDTO(ApiModel):
    job_id: UUID = Field(serialization_alias="jobId")
    status: JobStatus
    correlation_id: str | None = Field(default=None, serialization_alias="correlationId")
    strategy_content_text: str = Field(serialization_alias="strategyContentText")
    audience_level: AudienceLevel = Field(serialization_alias="audienceLevel")
    content_length: ContentLength = Field(serialization_alias="contentLength")
    tone: ContentTone
    cta_goal: CtaGoal = Field(serialization_alias="ctaGoal")
    seo_optimization_mode: SeoOptimizationMode = Field(serialization_alias="seoOptimizationMode")
    result: StrategyContentResultDTO | None = None
    error: str | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    @classmethod
    def from_job(cls, job) -> StrategyJobStatusDTO:
        result = None
        if job.result is not None:
            result = StrategyContentResultDTO(
                content=job.result.content,
                title=job.result.title,
                meta_description=job.result.meta_description,
                keywords=job.result.keywords,
            )
        return cls(
            job_id=job.id,
            status=job.status,
            correlation_id=job.correlation_id,
            strategy_content_text=job.strategy_content_text,
            audience_level=job.audience_level,
            content_length=job.content_length,
            tone=job.tone,
            cta_goal=job.cta_goal,
            seo_optimization_mode=job.seo_optimization_mode,
            result=result,
            error=job.error,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
