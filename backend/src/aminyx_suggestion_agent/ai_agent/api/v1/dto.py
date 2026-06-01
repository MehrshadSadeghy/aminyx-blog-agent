from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from aminyx_suggestion_agent.ai_agent.domain import BusinessData, JobStatus


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class TestimonialDTO(ApiModel):
    text: str = ""
    author: str | None = None
    company: str | None = None
    role: str | None = None
    avatar: str | None = None
    rating: float | None = None


class BusinessInfoDTO(ApiModel):
    business_name: str | None = Field(default=None, alias="businessName")
    brand_name: str | None = Field(default=None, alias="brandName")
    tagline: str | None = None
    short_description: str | None = Field(default=None, alias="shortDescription")
    full_description: str | None = Field(default=None, alias="fullDescription")
    industry: str | None = None
    sub_industry: str | None = Field(default=None, alias="subIndustry")
    business_type: str | None = Field(default=None, alias="businessType")
    company_size: str | None = Field(default=None, alias="companySize")
    year_founded: int | None = Field(default=None, alias="yearFounded")
    founder_team: str | None = Field(default=None, alias="founderTeam")


class BusinessOfferingsDTO(ApiModel):
    services: list[str] = Field(default_factory=list)
    service_categories: list[str] = Field(default_factory=list, alias="serviceCategories")
    pricing_model: str | None = Field(default=None, alias="pricingModel")
    price_range: str | None = Field(default=None, alias="priceRange")
    delivery_method: str | None = Field(default=None, alias="deliveryMethod")


class BusinessAudienceDTO(ApiModel):
    target_audience: str | None = Field(default=None, alias="targetAudience")
    target_segments: list[str] = Field(default_factory=list, alias="targetSegments")
    pain_points: list[str] = Field(default_factory=list, alias="painPoints")
    needs: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list, alias="useCases")
    customer_goals: list[str] = Field(default_factory=list, alias="customerGoals")
    target_geography: list[str] = Field(default_factory=list, alias="targetGeography")
    industry_focus: str | None = Field(default=None, alias="industryFocus")


class BusinessBrandingDTO(ApiModel):
    tone: str | None = None
    brand_voice: str | None = Field(default=None, alias="brandVoice")
    core_message: str | None = Field(default=None, alias="coreMessage")
    value_proposition: str | None = Field(default=None, alias="valueProposition")
    usp: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    brand_personality: str | None = Field(default=None, alias="brandPersonality")


class BusinessTrustDTO(ApiModel):
    testimonials: list[TestimonialDTO] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list, alias="successMetrics")
    years_of_experience: int | None = Field(default=None, alias="yearsOfExperience")


class BusinessLocationDTO(ApiModel):
    country: str | None = None
    city: str | None = None


class BusinessOperationsDTO(ApiModel):
    location: BusinessLocationDTO | None = None
    service_areas: list[str] = Field(default_factory=list, alias="serviceAreas")
    working_hours: str | None = Field(default=None, alias="workingHours")
    delivery_time: str | None = Field(default=None, alias="deliveryTime")
    process: str | None = None
    tools_technologies: list[str] = Field(default_factory=list, alias="toolsTechnologies")
    support_type: str | None = Field(default=None, alias="supportType")


class BusinessContactDTO(ApiModel):
    email: str | None = None
    phone: str | None = None
    whats_app: str | None = Field(default=None, alias="whatsApp")
    physical_address: str | None = Field(default=None, alias="physicalAddress")


class BusinessSocialMediaDTO(ApiModel):
    twitter: str | None = None
    instagram: str | None = None
    linkedin: str | None = None


class BusinessMarketingDTO(ApiModel):
    cta: str | None = None
    lead_magnet: str | None = Field(default=None, alias="leadMagnet")


class BusinessSeoMetadataDTO(ApiModel):
    page_title: str | None = Field(default=None, alias="pageTitle")
    meta_description: str | None = Field(default=None, alias="metaDescription")


class BusinessVisualDTO(ApiModel):
    primary: str | None = None
    secondary: str | None = None
    accent: str | None = None
    background: str | None = None


class BusinessMetadataDTO(ApiModel):
    site_id: str | None = Field(default=None, alias="siteId")
    published_at: datetime | None = Field(default=None, alias="publishedAt")
    template_name: str | None = Field(default=None, alias="templateName")
    last_ai_update: datetime | None = Field(default=None, alias="lastAIUpdate")
    layout: str | None = None
    default_language: str | None = Field(default=None, alias="defaultLanguage")
    domain: str | None = None


class BusinessDataDTO(ApiModel):
    business_info: BusinessInfoDTO = Field(default_factory=BusinessInfoDTO, alias="businessInfo")
    offerings: BusinessOfferingsDTO = Field(default_factory=BusinessOfferingsDTO)
    audience: BusinessAudienceDTO = Field(default_factory=BusinessAudienceDTO)
    branding: BusinessBrandingDTO = Field(default_factory=BusinessBrandingDTO)
    trust: BusinessTrustDTO = Field(default_factory=BusinessTrustDTO)
    operations: BusinessOperationsDTO = Field(default_factory=BusinessOperationsDTO)
    contact: BusinessContactDTO = Field(default_factory=BusinessContactDTO)
    social_media: BusinessSocialMediaDTO = Field(default_factory=BusinessSocialMediaDTO, alias="socialMedia")
    marketing: BusinessMarketingDTO = Field(default_factory=BusinessMarketingDTO)
    seo_metadata: BusinessSeoMetadataDTO = Field(default_factory=BusinessSeoMetadataDTO, alias="seoMetadata")
    visual: BusinessVisualDTO = Field(default_factory=BusinessVisualDTO)
    generated_content: dict | None = Field(default=None, alias="generatedContent")
    metadata: BusinessMetadataDTO = Field(default_factory=BusinessMetadataDTO)

    def to_domain(self) -> BusinessData:
        return BusinessData.model_validate(self.model_dump(by_alias=False))


class CreateSuggestionJobDTO(ApiModel):
    business_data: BusinessDataDTO = Field(alias="businessData")
    callback_url: HttpUrl = Field(alias="callbackUrl")
    correlation_id: str | None = Field(default=None, alias="correlationId")


class TopicSuggestionDTO(ApiModel):
    title: str
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)


class JobAcceptedDTO(ApiModel):
    job_id: UUID = Field(serialization_alias="jobId")
    status: JobStatus = JobStatus.PENDING


class JobStatusDTO(ApiModel):
    job_id: UUID = Field(serialization_alias="jobId")
    status: JobStatus
    correlation_id: str | None = Field(default=None, serialization_alias="correlationId")
    topics: list[TopicSuggestionDTO] | None = None
    error: str | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    @classmethod
    def from_job(cls, job) -> JobStatusDTO:
        topics = None
        if job.topics:
            topics = [TopicSuggestionDTO.model_validate(t.model_dump()) for t in job.topics]
        return cls(
            job_id=job.id,
            status=job.status,
            correlation_id=job.correlation_id,
            topics=topics,
            error=job.error,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
