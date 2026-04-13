import asyncio
import logging
import sys
from typing import Any

from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict

from mic_worker.typed import (
    AsyncProgressProtocol,
    AsyncTaskInterface,
    HealthCheckConfig,
    IncomingMessage,
    Infinite,
)
from mic_worker.worker import AsyncWorkerRunner


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    BROKER_URL: str
    IN_QUEUE_NAME: str
    OUT_QUEUE_NAME: str
    WORKER_CONCURRENCY: int = 3
    HEALTH_CHECK_HOST: str = "0.0.0.0"  # noqa: S104
    HEALTH_CHECK_PORT: int = 8083
    LOG_LEVEL: str = "INFO"


settings = Settings()


class InterceptHandler(logging.Handler):
    """Redirige les logs du module logging standard vers loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
logger.remove()
logger.add(sys.stdout, level=settings.LOG_LEVEL)


class GenerationRenderTask(AsyncTaskInterface):
    """Worker stub : ne fait rien pour l'instant, retourne un résultat vide.

    La logique métier (download S3, templating ODT, upload résultat)
    sera ajoutée dans les tickets suivants.
    """

    async def execute(
        self,
        incoming_message: IncomingMessage,
        progress: AsyncProgressProtocol,  # noqa: ARG002
    ) -> Any:  # noqa: ANN401
        logger.info(f"Task received: task_id={incoming_message.task_id}")
        return {}


async def main() -> None:
    logger.info("Starting generation-render worker")
    runner = AsyncWorkerRunner(
        amqp_url=settings.BROKER_URL,
        amqp_in_queue=settings.IN_QUEUE_NAME,
        amqp_out_queue=settings.OUT_QUEUE_NAME,
        task_provider=GenerationRenderTask,
        worker_mode=Infinite(concurrency=settings.WORKER_CONCURRENCY),
        health_check_config=HealthCheckConfig(
            host=settings.HEALTH_CHECK_HOST,
            port=settings.HEALTH_CHECK_PORT,
        ),
    )
    await runner.start()
    logger.info("generation-render worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
