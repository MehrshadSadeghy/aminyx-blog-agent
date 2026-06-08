"""API call tasks that simulate a user/backend calling the agent service."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

from call_test.client import AgentApiClient
from call_test.payloads import strategy_content_job_payload, suggestion_job_payload

TaskResult = dict[str, Any]


@dataclass
class TaskOutcome:
    name: str
    ok: bool
    detail: str
    data: TaskResult | None = None


async def task_health_check(client: AgentApiClient) -> TaskOutcome:
    response = await client.health()
    body = response.json()
    ok = response.status_code == 200 and body.get("status") == "ok"
    return TaskOutcome(
        name="health_check",
        ok=ok,
        detail=f"GET /health -> {response.status_code}",
        data=body,
    )


async def task_unauthorized_request(client: AgentApiClient) -> TaskOutcome:
    response = await client.request_without_auth(
        "POST",
        "/api/v1/agent/suggestions",
        json=suggestion_job_payload(),
    )
    ok = response.status_code == 401
    return TaskOutcome(
        name="unauthorized_request",
        ok=ok,
        detail=f"POST /suggestions without auth -> {response.status_code}",
        data=response.json() if response.content else None,
    )


async def task_create_suggestion_job(client: AgentApiClient) -> TaskOutcome:
    response = await client.create_suggestion_job(suggestion_job_payload())
    body = response.json()
    ok = response.status_code == 202 and body.get("status") == "pending" and body.get("jobId")
    return TaskOutcome(
        name="create_suggestion_job",
        ok=ok,
        detail=f"POST /suggestions -> {response.status_code}",
        data=body,
    )


async def task_poll_suggestion_job(
    client: AgentApiClient,
    job_id: str,
    *,
    wait_for_complete: bool = False,
    poll_interval_seconds: float = 2.0,
    timeout_seconds: float = 180.0,
) -> TaskOutcome:
    deadline = time.monotonic() + timeout_seconds
    last_body: dict[str, Any] = {}

    while True:
        response = await client.get_suggestion_job(job_id)
        last_body = response.json()
        status = last_body.get("status")

        if response.status_code != 200:
            return TaskOutcome(
                name="poll_suggestion_job",
                ok=False,
                detail=f"GET /suggestions/{job_id} -> {response.status_code}",
                data=last_body,
            )

        if not wait_for_complete or status in {"complete", "fail"}:
            ok = status in {"pending", "processing", "complete", "fail"}
            return TaskOutcome(
                name="poll_suggestion_job",
                ok=ok,
                detail=f"GET /suggestions/{job_id} -> status={status}",
                data=last_body,
            )

        if time.monotonic() >= deadline:
            return TaskOutcome(
                name="poll_suggestion_job",
                ok=False,
                detail=f"Timed out waiting for job {job_id} (last status={status})",
                data=last_body,
            )

        await asyncio.sleep(poll_interval_seconds)


async def task_create_strategy_content_job(client: AgentApiClient) -> TaskOutcome:
    response = await client.create_strategy_content_job(strategy_content_job_payload())
    body = response.json()
    ok = response.status_code == 202 and body.get("status") == "pending" and body.get("jobId")
    return TaskOutcome(
        name="create_strategy_content_job",
        ok=ok,
        detail=f"POST /strategy-content -> {response.status_code}",
        data=body,
    )


async def task_poll_strategy_content_job(
    client: AgentApiClient,
    job_id: str,
    *,
    wait_for_complete: bool = False,
    poll_interval_seconds: float = 2.0,
    timeout_seconds: float = 180.0,
) -> TaskOutcome:
    deadline = time.monotonic() + timeout_seconds
    last_body: dict[str, Any] = {}

    while True:
        response = await client.get_strategy_content_job(job_id)
        last_body = response.json()
        status = last_body.get("status")

        if response.status_code != 200:
            return TaskOutcome(
                name="poll_strategy_content_job",
                ok=False,
                detail=f"GET /strategy-content/{job_id} -> {response.status_code}",
                data=last_body,
            )

        if not wait_for_complete or status in {"complete", "fail"}:
            ok = status in {"pending", "processing", "complete", "fail"}
            return TaskOutcome(
                name="poll_strategy_content_job",
                ok=ok,
                detail=f"GET /strategy-content/{job_id} -> status={status}",
                data=last_body,
            )

        if time.monotonic() >= deadline:
            return TaskOutcome(
                name="poll_strategy_content_job",
                ok=False,
                detail=f"Timed out waiting for job {job_id} (last status={status})",
                data=last_body,
            )

        await asyncio.sleep(poll_interval_seconds)


async def task_get_unknown_job(client: AgentApiClient) -> TaskOutcome:
    unknown_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get_suggestion_job(unknown_id)
    ok = response.status_code == 404
    return TaskOutcome(
        name="get_unknown_job",
        ok=ok,
        detail=f"GET /suggestions/{unknown_id} -> {response.status_code}",
        data=response.json() if response.content else None,
    )


async def run_user_flow(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    wait_for_complete: bool = False,
) -> list[TaskOutcome]:
    outcomes: list[TaskOutcome] = []

    async with AgentApiClient(base_url=base_url, api_key=api_key) as client:
        for task in (
            task_health_check,
            task_unauthorized_request,
            task_get_unknown_job,
        ):
            outcomes.append(await task(client))

        create_suggestion = await task_create_suggestion_job(client)
        outcomes.append(create_suggestion)

        if create_suggestion.ok and create_suggestion.data:
            job_id = str(create_suggestion.data["jobId"])
            outcomes.append(
                await task_poll_suggestion_job(
                    client,
                    job_id,
                    wait_for_complete=wait_for_complete,
                )
            )

        create_strategy = await task_create_strategy_content_job(client)
        outcomes.append(create_strategy)

        if create_strategy.ok and create_strategy.data:
            job_id = str(create_strategy.data["jobId"])
            outcomes.append(
                await task_poll_strategy_content_job(
                    client,
                    job_id,
                    wait_for_complete=wait_for_complete,
                )
            )

    return outcomes


def print_outcomes(outcomes: list[TaskOutcome]) -> int:
    failed = 0
    for outcome in outcomes:
        status = "PASS" if outcome.ok else "FAIL"
        print(f"[{status}] {outcome.name}: {outcome.detail}")
        if outcome.data:
            print(f"       response: {outcome.data}")
        if not outcome.ok:
            failed += 1
    return failed
