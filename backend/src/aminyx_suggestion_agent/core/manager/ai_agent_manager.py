import asyncio
import logging

from aminyx_suggestion_agent.config import MetisConfig
from aminyx_suggestion_agent.core.manager.base import Manager

LOGGER = logging.getLogger(__name__)


class AIManager(Manager):
    """Lifecycle hook for Metis concurrency gate (no LangChain model)."""

    def __init__(self, metis_config: MetisConfig) -> None:
        self._metis_config = metis_config
        self._parallel_gate: asyncio.Semaphore | None = None

    async def setup(self) -> None:
        MetisConfig.resolved_api_key()
        bot_id = self._metis_config.resolved_bot_id()
        if not bot_id:
            raise RuntimeError("METIS_BOT_ID is not set in environment or config.")

        limit = self._metis_config.max_parallel_requests
        self._parallel_gate = asyncio.Semaphore(limit) if limit is not None else None
        LOGGER.info("AIManager ready (Metis bot_id=%s)", bot_id[:8] + "…")

    async def run(self) -> None:
        pass

    async def teardown(self) -> None:
        pass

    def parallel_invoke_gate(self) -> asyncio.Semaphore | None:
        return self._parallel_gate
