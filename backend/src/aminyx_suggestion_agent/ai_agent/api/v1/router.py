from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from aminyx_suggestion_agent.ai_agent.api.v1.dependency import (
    get_suggestion_service,
    require_bearer,
)
from aminyx_suggestion_agent.ai_agent.api.v1.dto import (
    CreateSuggestionJobDTO,
    JobAcceptedDTO,
    JobStatusDTO,
)
from aminyx_suggestion_agent.ai_agent.domain import JobStatus
from aminyx_suggestion_agent.ai_agent.service import SuggestionAgentService

router = APIRouter(
    prefix="/api/v1/agent",
    tags=["agent"],
    dependencies=[Depends(require_bearer)],
)


@router.post(
    "/suggestions",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobAcceptedDTO,
    response_model_by_alias=True,
)
async def create_suggestion_job(
    body: CreateSuggestionJobDTO,
    service: Annotated[SuggestionAgentService, Depends(get_suggestion_service)],
) -> JobAcceptedDTO:
    job = await service.create_job(
        business_data=body.business_data.to_domain(),
        callback_url=body.callback_url,
        correlation_id=body.correlation_id,
    )
    return JobAcceptedDTO(job_id=job.id, status=JobStatus.PENDING)


@router.get(
    "/suggestions/{job_id}",
    response_model=JobStatusDTO,
    response_model_by_alias=True,
)
async def get_suggestion_job_status(
    job_id: UUID,
    service: Annotated[SuggestionAgentService, Depends(get_suggestion_service)],
) -> JobStatusDTO:
    job = await service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobStatusDTO.from_job(job)
