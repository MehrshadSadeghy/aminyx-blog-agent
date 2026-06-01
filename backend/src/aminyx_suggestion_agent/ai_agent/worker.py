from __future__ import annotations

import asyncio
import logging

from raya_faraz_agent.ai_agent.service import SuggestionAgentService

LOGGER = logging.getLogger(__name__)


class SuggestionJobWorker:
    def __init__(
        self,
        service: SuggestionAgentService,
        *,
        poll_timeout_seconds: int = 1,
    ) -> None:
        self._service = service
        self._poll_timeout_seconds = poll_timeout_seconds
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name="suggestion-job-worker")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        LOGGER.info("Suggestion job worker started")
        while not self._stop_event.is_set():
            try:
                job_id = await self._service.dequeue_next(
                    timeout_seconds=self._poll_timeout_seconds
                )
            except Exception:
                LOGGER.exception("Failed to dequeue suggestion job")
                await asyncio.sleep(1)
                continue

            if job_id is None:
                continue

            try:
                await self._service.process_job(job_id)
            except Exception:
                LOGGER.exception("Unhandled error processing job %s", job_id)

        LOGGER.info("Suggestion job worker stopped")
