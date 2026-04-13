import asyncio
import logging
import os
import sys
from typing import Any

from loguru import logger

from mic_worker.typed import (
    AsyncProgressProtocol,
    AsyncTaskInterface,
    HealthCheckConfig,
    IncomingMessage,
    Infinite,
)
from mic_worker.worker import AsyncWorkerRunner


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
logger.add(sys.stdout, level="INFO")


class GenerationRenderTask(AsyncTaskInterface):
    """Worker stub : ne fait rien pour l'instant, retourne un résultat vide.

    La logique métier (download S3, templating ODT, upload résultat)
    sera ajoutée dans les tickets suivants.
    """

    async def execute(
        self,
        incoming_message: IncomingMessage,
        progress: AsyncProgressProtocol,
    ) -> Any:  # noqa: ANN401
        logger.info(f"Task received: task_id={incoming_message.task_id}")
        return {}


BROKER_URL = os.environ["BROKER_URL"]
IN_QUEUE_NAME = os.environ["IN_QUEUE_NAME"]
OUT_QUEUE_NAME = os.environ["OUT_QUEUE_NAME"]
WORKER_CONCURRENCY = int(os.environ.get("WORKER_CONCURRENCY", "3"))
HEALTH_CHECK_HOST = os.environ.get("HEALTH_CHECK_HOST", "0.0.0.0")
HEALTH_CHECK_PORT = int(os.environ.get("HEALTH_CHECK_PORT", "8083"))


async def main() -> None:
    logger.info("Starting generation-render worker")
    runner = AsyncWorkerRunner(
        amqp_url=BROKER_URL,
        amqp_in_queue=IN_QUEUE_NAME,
        amqp_out_queue=OUT_QUEUE_NAME,
        task_provider=GenerationRenderTask,
        worker_mode=Infinite(concurrency=WORKER_CONCURRENCY),
        health_check_config=HealthCheckConfig(host=HEALTH_CHECK_HOST, port=HEALTH_CHECK_PORT),
    )
    await runner.start()
    logger.info("generation-render worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
