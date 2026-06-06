from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl

from aminyx_suggestion_agent.ai_agent.domain import BusinessData, JobStatus


class AudienceLevel(StrEnum):
    BEGINNER = "beginner"
    GENERAL_AUDIENCE = "general_audience"
    PROFESSIONAL = "professional"


class ContentLength(StrEnum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ContentTone(StrEnum):
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    EDUCATIONAL = "educational"
    PERSUASIVE = "persuasive"
    AUTHORITY_BUILDING = "authority_building"


class CtaGoal(StrEnum):
    COLLECT_LEADS = "collect_leads"
    EDUCATE_AUDIENCE = "educate_audience"
    PROMOTE_SERVICE = "promote_service"
    PROMOTE_PRODUCT = "promote_product"
    BUILD_AUTHORITY = "build_authority"


class SeoOptimizationMode(StrEnum):
    BALANCED = "balanced"
    MAXIMUM_SEO = "maximum_seo"
    NATURAL_READABILITY = "natural_readability"


CONTENT_LENGTH_CHAR_RANGES: dict[ContentLength, tuple[int, int]] = {
    ContentLength.SHORT: (600, 900),
    ContentLength.MEDIUM: (1200, 1800),
    ContentLength.LONG: (2500, 3500),
}


class StrategyContentResult(BaseModel):
    content: str
    title: str | None = None
    meta_description: str | None = Field(default=None, alias="metaDescription")
    keywords: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class StrategyContentJob(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    status: JobStatus = JobStatus.PENDING
    business_data: BusinessData
    strategy_content_text: str
    audience_level: AudienceLevel
    content_length: ContentLength
    tone: ContentTone
    cta_goal: CtaGoal
    seo_optimization_mode: SeoOptimizationMode
    callback_url: HttpUrl
    callback_method: str = "POST"
    callback_headers: dict[str, str] = Field(default_factory=dict)
    correlation_id: str | None = None
    result: StrategyContentResult | None = None
    total_tokens: int | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
