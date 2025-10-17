import asyncio
import logging
import os
import sys
from time import sleep
from typing import Any

from loguru import logger

from mic_worker.typed import (
    AsyncProgressProtocol,
    AsyncTaskInterface,
    HealthCheckConfig,
    IncomingMessage,
    Infinite,
    SyncProgressProtocol,
    SyncTaskInterface,
)
from mic_worker.worker import AsyncWorkerRunner


# --------------------------------
# L'implementation du worker est indépendante du système de logging
# Dans notre exemple, nous voulons utiliser loguru, il nous faut donc
# intercepter les logs du module logging standard et les rediriger vers loguru
# --------------------------------
class InterceptHandler(logging.Handler):
    """Handler pour intercepter les logs du module logging standard et les rediriger vers loguru"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
logger.remove()
logger.add(sys.stdout, level="INFO")


# Implémentation de la task
# "utilisateur" (Sync)


class MySyncTask(SyncTaskInterface):
    def execute(self, incoming_message: IncomingMessage, progress: SyncProgressProtocol) -> Any:  # noqa: ANN401
        # task_id = incoming_message.task_id
        body: dict[Any, Any] = incoming_message.body
        logging.info("Task_id: {task_id}")
        if not body.get("failed"):
            time = body["sleep"]
            logger.info(f"Traitement en cours... ({time}s)")
            sleep(time / 2)
            progress(progress=0.3, payload=None)
            sleep(time / 2)
            progress(progress=0.6, payload=None)
        else:
            raise Exception("Argh")
        return {"hello": "world"}


# -------------------------
# Implémentation de la task
# "utilisateur" (Async)
# -------------------------
class MyAsyncTask(AsyncTaskInterface):
    async def execute(self, incoming_message: IncomingMessage, progress: AsyncProgressProtocol) -> Any:  # noqa: ANN401
        task_id = incoming_message.task_id
        logging.info(msg=f"Task_id: {task_id} --- <timestamp>")
        body: dict[Any, Any] = incoming_message.body

        if not body.get("failed"):
            time = 10
            logger.info(f"Traitement en cours... ({time}s)")
            await asyncio.sleep(delay=time / 2)
            await progress(progress=0.3, payload=None)
            await asyncio.sleep(delay=time / 2)
            await progress(progress=0.6, payload=None)
        else:
            raise Exception("Argh")
        return {"hello": "world"}  # Réponse


OUT_QUEUE_NAME = os.environ.get("OUT_QUEUE_NAME", "")
IN_QUEUE_NAME = os.environ.get("IN_QUEUE_NAME", "")
BROKER_URL = os.environ.get("BROKER_URL", "")
WORKER_CONCURRENCY: int = int(os.environ.get("WORKER_CONCURRENCY", default="5"))
if not BROKER_URL:
    raise ValueError("BROKER_URL environment variable is not set.")


async def main() -> None:
    logger.info("Launch")
    runner = AsyncWorkerRunner(
        # Rabbit mq connection
        amqp_url=BROKER_URL,
        # In out queues
        amqp_in_queue=IN_QUEUE_NAME,
        amqp_out_queue=OUT_QUEUE_NAME,
        task_provider=MyAsyncTask,  # or  lambda:  MySyncTask()
        worker_mode=Infinite(concurrency=WORKER_CONCURRENCY),  # or OnShot(),
        # Optional : HealthCheck
        health_check_config=HealthCheckConfig(host="127.0.0.1", port=8000),  # or None
    )
    await runner.start()
    logger.info("Stopped.")


if __name__ == "__main__":
    asyncio.run(main=main())
