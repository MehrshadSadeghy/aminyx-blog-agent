from fastapi import Request

from aminyx_suggestion_agent.strategy_content.service import StrategyContentAgentService


def get_strategy_content_service(request: Request) -> StrategyContentAgentService:
    container = request.app.state.container
    return container.get_strategy_content_service()
