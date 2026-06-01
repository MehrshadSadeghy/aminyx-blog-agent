import logging

from redis.asyncio import Redis

from aminyx_suggestion_agent.core.db.redis import RedisDatabase
from aminyx_suggestion_agent.core.manager.base import Manager

LOGGER = logging.getLogger(__name__)


class RedisManager(Manager):
    def __init__(self, provider: RedisDatabase) -> None:
        self._provider = provider
        self._client: Redis | None = None

    @property
    def is_ready(self) -> bool:
        return self._client is not None

    async def setup(self) -> None:
        LOGGER.info("Setting up RedisManager")
        client = self._provider.create_client()
        await client.ping()
        self._client = client
        LOGGER.info("RedisManager ready")

    async def run(self) -> None:
        pass

    async def teardown(self) -> None:
        LOGGER.info("Tearing down RedisManager")
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def get_client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("RedisManager is not set up yet")
        return self._client
