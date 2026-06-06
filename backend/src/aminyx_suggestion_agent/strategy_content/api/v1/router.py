from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from aminyx_suggestion_agent.ai_agent.api.v1.dependency import require_bearer
from aminyx_suggestion_agent.strategy_content.api.v1.dependency import (
    get_strategy_content_service,
)
from aminyx_suggestion_agent.strategy_content.api.v1.dto import (
    CreateStrategyContentJobDTO,
    StrategyJobAcceptedDTO,
    StrategyJobStatusDTO,
)
from aminyx_suggestion_agent.ai_agent.domain import JobStatus
from aminyx_suggestion_agent.strategy_content.service import StrategyContentAgentService

router = APIRouter(
    prefix="/api/v1/agent",
    tags=["strategy-content"],
    dependencies=[Depends(require_bearer)],
)


@router.post(
    "/strategy-content",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=StrategyJobAcceptedDTO,
    response_model_by_alias=True,
)
async def create_strategy_content_job(
    body: CreateStrategyContentJobDTO,
    service: Annotated[StrategyContentAgentService, Depends(get_strategy_content_service)],
) -> StrategyJobAcceptedDTO:
    job = await service.create_job(
        business_data=body.business_data.to_domain(),
        strategy_content_text=body.strategy_content_text,
        audience_level=body.audience_level,
        content_length=body.content_length,
        tone=body.tone,
        cta_goal=body.cta_goal,
        seo_optimization_mode=body.seo_optimization_mode,
        callback_url=body.resolved_callback_url(),
        correlation_id=body.correlation_id,
        callback_method=body.resolved_callback_method(),
        callback_headers=body.resolved_callback_headers(),
    )
    return StrategyJobAcceptedDTO(job_id=job.id, status=JobStatus.PENDING)


@router.get(
    "/strategy-content/{job_id}",
    response_model=StrategyJobStatusDTO,
    response_model_by_alias=True,
)
async def get_strategy_content_job_status(
    job_id: UUID,
    service: Annotated[StrategyContentAgentService, Depends(get_strategy_content_service)],
) -> StrategyJobStatusDTO:
    job = await service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return StrategyJobStatusDTO.from_job(job)
