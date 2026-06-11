"""HTTP request payloads for endpoint and system tests."""

from __future__ import annotations

from typing import Any


def sample_business_data() -> dict[str, Any]:
    return {
        "businessInfo": {
            "businessName": "Acme Growth Labs",
            "brandName": "Acme",
            "industry": "B2B SaaS",
            "shortDescription": "Helps SMBs automate lead generation.",
        },
        "offerings": {
            "services": ["Lead scoring", "Email automation"],
            "pricingModel": "subscription",
        },
        "audience": {
            "targetAudience": "Small business owners",
            "painPoints": ["Low conversion rates", "Manual follow-up"],
            "targetGeography": ["US", "UK"],
        },
        "branding": {
            "tone": "professional",
            "keywords": ["lead generation", "B2B", "automation"],
        },
    }


def suggestion_job_payload(
    *,
    correlation_id: str = "sugg_test_001",
    callback_url: str = "http://test-backend:8600/api/internal/webhooks/suggestion-agent",
    include_callback: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "businessData": sample_business_data(),
        "goal": ["increase_leads", "build_authority"],
        "correlationId": correlation_id,
    }
    if include_callback:
        payload["callback"] = {
            "callbackUrl": callback_url,
            "callbackMethod": "POST",
            "callbackHeaders": [["Authorization", "Bearer test-callback-secret"]],
        }
    return payload


def strategy_content_job_payload(
    *,
    correlation_id: str = "strat_test_001",
    callback_url: str = "http://test-backend:8600/api/internal/webhooks/strategy-content-agent",
    include_callback: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "businessData": sample_business_data(),
        "strategyContentText": "How to grow B2B leads with content marketing",
        "audienceLevel": "general_audience",
        "contentLength": "medium",
        "tone": "professional",
        "ctaGoal": "collect_leads",
        "seoOptimizationMode": "balanced",
        "correlationId": correlation_id,
    }
    if include_callback:
        payload["callback"] = {
            "callbackUrl": callback_url,
            "callbackMethod": "POST",
            "callbackHeaders": [["Authorization", "Bearer test-callback-secret"]],
        }
    return payload
