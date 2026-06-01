from fastapi import Depends, Header, HTTPException, Request

from raya_faraz_agent.ai_agent.service import SuggestionAgentService
from raya_faraz_agent.config import Config


def require_bearer(
    authorization: str | None = Header(default=None),
) -> None:
    expected = Config.resolved_admin_api_key()
    if not expected:
        raise HTTPException(status_code=503, detail="API key not configured on server.")

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header.")

    token = authorization.removeprefix("Bearer ").strip()
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid credentials.")


def get_suggestion_service(request: Request) -> SuggestionAgentService:
    container = request.app.state.container
    return container.get_suggestion_service()
