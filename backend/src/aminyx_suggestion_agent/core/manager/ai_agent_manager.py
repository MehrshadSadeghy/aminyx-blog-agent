import asyncio
import logging

from aminyx_suggestion_agent.config import GeminiConfig
from aminyx_suggestion_agent.core.manager.base import Manager

LOGGER = logging.getLogger(__name__)


class AIManager(Manager):
    """Lifecycle hook for Gemini concurrency gate."""

    def __init__(self, gemini_config: GeminiConfig) -> None:
        self._gemini_config = gemini_config
        self._parallel_gate: asyncio.Semaphore | None = None

    async def setup(self) -> None:
        GeminiConfig.resolved_api_key()
        model = self._gemini_config.resolved_model()
        limit = self._gemini_config.max_parallel_requests
        self._parallel_gate = asyncio.Semaphore(limit) if limit is not None else None
        LOGGER.info("AIManager ready (Gemini model=%s)", model)

    async def run(self) -> None:
        pass

    async def teardown(self) -> None:
        pass

    def parallel_invoke_gate(self) -> asyncio.Semaphore | None:
        return self._parallel_gate
