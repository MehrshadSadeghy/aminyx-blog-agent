from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class JobStatus(StrEnum):
    PENDING = "pending"
    COMPLETE = "complete"
    FAIL = "fail"


class Testimonial(BaseModel):
    text: str = ""
    author: str | None = None
    company: str | None = None
    role: str | None = None
    avatar: str | None = None
    rating: float | None = None


class BusinessOfferings(BaseModel):
    services: list[str] = Field(default_factory=list)
    service_categories: list[str] = Field(default_factory=list)
    pricing_model: str | None = None
    price_range: str | None = None
    delivery_method: str | None = None


class BusinessAudience(BaseModel):
    target_audience: str | None = None
    target_segments: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    needs: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    customer_goals: list[str] = Field(default_factory=list)
    target_geography: list[str] = Field(default_factory=list)
    industry_focus: str | None = None


class BusinessBranding(BaseModel):
    tone: str | None = None
    brand_voice: str | None = None
    core_message: str | None = None
    value_proposition: str | None = None
    usp: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    brand_personality: str | None = None


class BusinessTrust(BaseModel):
    testimonials: list[Testimonial] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)
    years_of_experience: int | None = None


class BusinessLocation(BaseModel):
    country: str | None = None
    city: str | None = None


class BusinessOperations(BaseModel):
    location: BusinessLocation | None = None
    service_areas: list[str] = Field(default_factory=list)
    working_hours: str | None = None
    delivery_time: str | None = None
    process: str | None = None
    tools_technologies: list[str] = Field(default_factory=list)
    support_type: str | None = None


class BusinessContact(BaseModel):
    email: str | None = None
    phone: str | None = None
    whats_app: str | None = None
    physical_address: str | None = None


class BusinessSocialMedia(BaseModel):
    twitter: str | None = None
    instagram: str | None = None
    linkedin: str | None = None


class BusinessMarketing(BaseModel):
    cta: str | None = None
    lead_magnet: str | None = None


class BusinessSeoMetadata(BaseModel):
    page_title: str | None = None
    meta_description: str | None = None


class BusinessVisual(BaseModel):
    primary: str | None = None
    secondary: str | None = None
    accent: str | None = None
    background: str | None = None


class BusinessMetadata(BaseModel):
    site_id: str | None = None
    published_at: datetime | None = None
    template_name: str | None = None
    last_ai_update: datetime | None = None
    layout: str | None = None
    default_language: str | None = None
    domain: str | None = None


class BusinessInfo(BaseModel):
    business_name: str | None = None
    brand_name: str | None = None
    tagline: str | None = None
    short_description: str | None = None
    full_description: str | None = None
    industry: str | None = None
    sub_industry: str | None = None
    business_type: str | None = None
    company_size: str | None = None
    year_founded: int | None = None
    founder_team: str | None = None


class BusinessData(BaseModel):
    business_info: BusinessInfo = Field(default_factory=BusinessInfo)
    offerings: BusinessOfferings = Field(default_factory=BusinessOfferings)
    audience: BusinessAudience = Field(default_factory=BusinessAudience)
    branding: BusinessBranding = Field(default_factory=BusinessBranding)
    trust: BusinessTrust = Field(default_factory=BusinessTrust)
    operations: BusinessOperations = Field(default_factory=BusinessOperations)
    contact: BusinessContact = Field(default_factory=BusinessContact)
    social_media: BusinessSocialMedia = Field(default_factory=BusinessSocialMedia)
    marketing: BusinessMarketing = Field(default_factory=BusinessMarketing)
    seo_metadata: BusinessSeoMetadata = Field(default_factory=BusinessSeoMetadata)
    visual: BusinessVisual = Field(default_factory=BusinessVisual)
    generated_content: dict[str, Any] | None = None
    metadata: BusinessMetadata = Field(default_factory=BusinessMetadata)


class TopicSuggestion(BaseModel):
    title: str
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)


class SuggestionJob(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    status: JobStatus = JobStatus.PENDING
    business_data: BusinessData
    callback_url: HttpUrl
    callback_method: str = "POST"
    callback_headers: dict[str, str] = Field(default_factory=dict)
    goal: list[str] = Field(default_factory=list)
    correlation_id: str | None = None
    topics: list[TopicSuggestion] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
