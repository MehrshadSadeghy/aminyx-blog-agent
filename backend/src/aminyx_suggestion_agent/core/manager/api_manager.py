import logging
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from raya_faraz_agent.config import APIConfig
from raya_faraz_agent.core.manager.base import Manager

if TYPE_CHECKING:
    from raya_faraz_agent.container import AppContainer

LOGGER = logging.getLogger(__name__)


class APIManager(Manager):
    def __init__(
        self, api_config: APIConfig, container: "AppContainer", routers: list[APIRouter]
    ) -> None:
        self._config = api_config
        self._container = container
        self._routers = routers
        self._app: FastAPI | None = None
        self._uvicorn_server: uvicorn.Server | None = None

    async def setup(self) -> None:
        LOGGER.info("Setting up API Manager")

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            LOGGER.info("FastAPI lifespan startup")
            try:
                self._container.validate_runtime()
            except Exception:
                LOGGER.exception("Container validation failed during startup")
                raise
            yield
            LOGGER.info("FastAPI lifespan shutdown")

        self._app = FastAPI(
            debug=self._config.debug,
            title=self._config.title,
            version=self._config.version,
            lifespan=lifespan,
        )

        cors_origins = list(self._config.cors_origins)
        env_cors = os.environ.get("CORS_ORIGINS", "").strip()
        if env_cors:
            cors_origins = [origin.strip() for origin in env_cors.split(",") if origin.strip()]

        allow_credentials = "*" not in cors_origins

        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=allow_credentials,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self._app.get("/health", tags=["system"])
        async def health_check() -> dict[str, str]:
            return {"status": "ok"}

        for router in self._routers:
            self._app.include_router(router)

        self._app.state.container = self._container
        LOGGER.info("API Manager ready")

    async def run(self):
        LOGGER.info("Running API Manager")
        if self._app is None:
            raise ValueError("APIManager is not setup")

        self._uvicorn_server = uvicorn.Server(
            config=uvicorn.Config(
                app=self._app,
                host=self._config.host,
                port=self._config.port,
                backlog=self._config.backlog,
            )
        )
        await self._uvicorn_server.serve()

    async def teardown(self) -> None:
        LOGGER.info("Tearing down API Manager")
