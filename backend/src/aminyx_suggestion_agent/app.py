"""ASGI app factory for uvicorn multi-worker mode."""

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aminyx_suggestion_agent.ai_agent.api.v1.router import router as ai_router
from aminyx_suggestion_agent.strategy_content.api.v1.router import router as strategy_content_router
from aminyx_suggestion_agent.container import AppContainer

level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, level, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    stream=sys.stdout,
)
LOGGER = logging.getLogger(__name__)

container = AppContainer()
container.validate_service_registry()


@asynccontextmanager
async def lifespan(application: FastAPI):
    LOGGER.info("Worker starting — setting up infrastructure")

    managers = container.get_managers()
    infra_managers = managers[:-1]

    for manager in infra_managers:
        await manager.setup()

    container.validate_runtime()

    worker = container.get_suggestion_worker()
    worker.start()
    application.state.suggestion_worker = worker

    strategy_worker = container.get_strategy_content_worker()
    strategy_worker.start()
    application.state.strategy_content_worker = strategy_worker

    LOGGER.info("Worker ready")
    yield
    LOGGER.info("Worker shutting down")

    await worker.stop()
    await strategy_worker.stop()

    for manager in infra_managers:
        await manager.teardown()
    await container.shutdown()


config = container.get_config()
api_cfg = config.api

app = FastAPI(
    debug=api_cfg.debug,
    title=api_cfg.title,
    version=api_cfg.version,
    lifespan=lifespan,
)

cors_origins = list(api_cfg.cors_origins)
env_cors = os.environ.get("CORS_ORIGINS", "").strip()
if env_cors:
    cors_origins = [origin.strip() for origin in env_cors.split(",") if origin.strip()]

allow_credentials = "*" not in cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(ai_router)
app.include_router(strategy_content_router)
app.state.container = container
