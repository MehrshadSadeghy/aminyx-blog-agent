import asyncio
import logging
import os
import sys

from aminyx_suggestion_agent.container import AppContainer

LOGGER = logging.getLogger(__name__)


def configure_logging() -> None:
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stdout,
    )


async def main() -> None:
    configure_logging()
    LOGGER.info("Starting Aminyx Suggestion Agent")

    container = AppContainer()
    container.validate_service_registry()

    managers = container.get_managers()
    infra_managers = managers[:-1]
    api_manager = managers[-1]

    worker = None
    try:
        await asyncio.gather(*[manager.setup() for manager in infra_managers])
        await api_manager.setup()
        worker = container.get_suggestion_worker()
        worker.start()
        await asyncio.gather(*[manager.run() for manager in infra_managers], api_manager.run())
    except Exception:
        LOGGER.exception("Application runtime error")
        raise
    finally:
        if worker is not None:
            await worker.stop()
        await asyncio.gather(*[manager.teardown() for manager in managers])
        await container.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
