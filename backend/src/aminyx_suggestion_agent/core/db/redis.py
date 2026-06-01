from redis.asyncio import Redis

from aminyx_suggestion_agent.config import RedisConfig


class RedisDatabase:
    def __init__(self, config: RedisConfig) -> None:
        self._config = config

    def create_url(self) -> str:
        password = self._config.password
        auth = f":{password}@" if password else ""
        return (
            f"redis://{auth}{self._config.host}:"
            f"{self._config.port}/{self._config.db}"
        )

    def create_client(self) -> Redis:
        return Redis.from_url(
            self.create_url(),
            decode_responses=self._config.decode_responses,
        )
