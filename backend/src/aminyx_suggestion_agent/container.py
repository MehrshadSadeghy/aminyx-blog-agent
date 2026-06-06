import logging
import os
from functools import lru_cache

from redis.asyncio import Redis

from aminyx_suggestion_agent.ai_agent.api.v1.router import router as ai_router
from aminyx_suggestion_agent.strategy_content.api.v1.router import router as strategy_content_router
from aminyx_suggestion_agent.ai_agent.infrastructure.callback_client import CallbackClient
from aminyx_suggestion_agent.ai_agent.infrastructure.gemini_client import GeminiClient
from aminyx_suggestion_agent.ai_agent.repository.redis import SuggestionJobRepositoryRedis
from aminyx_suggestion_agent.ai_agent.service import SuggestionAgentService
from aminyx_suggestion_agent.ai_agent.worker import SuggestionJobWorker
from aminyx_suggestion_agent.strategy_content.infrastructure.prompt_loader import (
    StrategyContentPromptLoader,
)
from aminyx_suggestion_agent.strategy_content.repository.redis import (
    StrategyContentJobRepositoryRedis,
)
from aminyx_suggestion_agent.strategy_content.service import StrategyContentAgentService
from aminyx_suggestion_agent.strategy_content.worker import StrategyContentJobWorker
from aminyx_suggestion_agent.config import Config, GeminiConfig
from aminyx_suggestion_agent.core.db.redis import RedisDatabase
from aminyx_suggestion_agent.core.manager.ai_agent_manager import AIManager
from aminyx_suggestion_agent.core.manager.api_manager import APIManager
from aminyx_suggestion_agent.core.manager.base import Manager
from aminyx_suggestion_agent.core.manager.redis_manager import RedisManager

LOGGER = logging.getLogger(__name__)

singleton = lru_cache

REQUIRED_SERVICE_GETTERS: tuple[str, ...] = (
    "get_config",
    "get_redis_manager",
    "get_ai_manager",
    "get_suggestion_service",
    "get_strategy_content_service",
)


class AppContainer:

    @singleton
    def get_config(self) -> Config:
        environment = os.environ.get("RAYA_TRADE_ENVIRONMENT", "config")
        return Config.from_yaml(environment=environment)

    @singleton
    def get_api_manager(self) -> APIManager:
        return APIManager(
            api_config=self.get_config().api,
            container=self,
            routers=[ai_router, strategy_content_router],
        )

    @singleton
    def get_redis_config(self):
        return self.get_config().redis

    @singleton
    def get_redis_provider(self) -> RedisDatabase:
        return RedisDatabase(self.get_redis_config())

    @singleton
    def get_redis_manager(self) -> RedisManager:
        return RedisManager(provider=self.get_redis_provider())

    def get_redis(self) -> Redis:
        return self.get_redis_manager().get_client()

    @singleton
    def get_managers(self) -> list[Manager]:
        return [
            self.get_ai_manager(),
            self.get_redis_manager(),
            self.get_api_manager(),
        ]

    @singleton
    def get_ai_manager(self) -> AIManager:
        return AIManager(gemini_config=self.get_config().gemini)

    @singleton
    def get_gemini_client(self) -> GeminiClient:
        gemini_cfg = self.get_config().gemini
        return GeminiClient(
            api_key=GeminiConfig.resolved_api_key(),
            model=gemini_cfg.resolved_model(),
            temperature=gemini_cfg.temperature,
            max_output_tokens=gemini_cfg.max_output_tokens,
        )

    @singleton
    def get_callback_client(self) -> CallbackClient:
        cfg = self.get_config().suggestion
        return CallbackClient(timeout_seconds=cfg.callback_timeout_seconds)

    @singleton
    def get_job_repository(self) -> SuggestionJobRepositoryRedis:
        cfg = self.get_config().suggestion
        return SuggestionJobRepositoryRedis(
            redis=self.get_redis(),
            ttl_seconds=cfg.job_ttl_seconds,
        )

    @singleton
    def get_suggestion_service(self) -> SuggestionAgentService:
        return SuggestionAgentService(
            jobs=self.get_job_repository(),
            gemini=self.get_gemini_client(),
            callback_client=self.get_callback_client(),
            parallel_gate=self.get_ai_manager().parallel_invoke_gate(),
        )

    @singleton
    def get_suggestion_worker(self) -> SuggestionJobWorker:
        return SuggestionJobWorker(self.get_suggestion_service())

    @singleton
    def get_strategy_content_prompt_loader(self) -> StrategyContentPromptLoader:
        cfg = self.get_config().strategy_content
        return StrategyContentPromptLoader(cfg.system_prompt_path)

    @singleton
    def get_strategy_content_job_repository(self) -> StrategyContentJobRepositoryRedis:
        cfg = self.get_config().strategy_content
        return StrategyContentJobRepositoryRedis(
            redis=self.get_redis(),
            ttl_seconds=cfg.job_ttl_seconds,
        )

    @singleton
    def get_strategy_content_service(self) -> StrategyContentAgentService:
        return StrategyContentAgentService(
            jobs=self.get_strategy_content_job_repository(),
            gemini=self.get_gemini_client(),
            callback_client=self.get_callback_client(),
            prompt_loader=self.get_strategy_content_prompt_loader(),
            parallel_gate=self.get_ai_manager().parallel_invoke_gate(),
        )

    @singleton
    def get_strategy_content_worker(self) -> StrategyContentJobWorker:
        return StrategyContentJobWorker(self.get_strategy_content_service())

    def validate_service_registry(self) -> None:
        missing = [
            name
            for name in REQUIRED_SERVICE_GETTERS
            if not callable(getattr(self, name, None))
        ]
        if missing:
            raise RuntimeError(
                f"AppContainer is missing required service getters: {', '.join(missing)}"
            )
        LOGGER.debug("Service registry validated (%d getters)", len(REQUIRED_SERVICE_GETTERS))

    def validate_runtime(self) -> None:
        self.validate_service_registry()
        GeminiConfig.resolved_api_key()
        if not Config.resolved_admin_api_key():
            raise RuntimeError("ADMIN_API_KEY is not configured.")
        self.get_strategy_content_prompt_loader().load()
        LOGGER.info("Container runtime validation passed")

    async def shutdown(self) -> None:
        await self.get_callback_client().aclose()
        await self.get_gemini_client().aclose()
