"""Minimal FastAPI app for endpoint tests without worker lifespan."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

from fastapi import FastAPI

from aminyx_suggestion_agent.ai_agent.api.v1 import dependency as suggestion_dependency
from aminyx_suggestion_agent.ai_agent.api.v1.router import router as suggestion_router
from aminyx_suggestion_agent.ai_agent.service import SuggestionAgentService
from aminyx_suggestion_agent.strategy_content.api.v1 import dependency as strategy_dependency
from aminyx_suggestion_agent.strategy_content.api.v1.router import router as strategy_router
from aminyx_suggestion_agent.strategy_content.service import StrategyContentAgentService


def create_test_app(
    *,
    suggestion_service: SuggestionAgentService | AsyncMock | None = None,
    strategy_content_service: StrategyContentAgentService | AsyncMock | None = None,
) -> FastAPI:
    application = FastAPI(title="Aminyx Suggestion Agent Test")

    @application.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(suggestion_router)
    application.include_router(strategy_router)

    mock_suggestion = suggestion_service or AsyncMock(spec=SuggestionAgentService)
    mock_strategy = strategy_content_service or AsyncMock(spec=StrategyContentAgentService)

    application.dependency_overrides[suggestion_dependency.get_suggestion_service] = (
        lambda: mock_suggestion
    )
    application.dependency_overrides[strategy_dependency.get_strategy_content_service] = (
        lambda: mock_strategy
    )

    application.state.test_mocks = {
        "suggestion_service": mock_suggestion,
        "strategy_content_service": mock_strategy,
    }
    return application


def get_test_mocks(application: FastAPI) -> dict[str, Any]:
    return application.state.test_mocks
