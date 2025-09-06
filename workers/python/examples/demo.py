import asyncio
import logging
import os
import sys
from collections.abc import Awaitable, Callable
from time import sleep
from typing import Any

from async_worker.worker import (
    AsyncTaskInterface,
    AsyncWorkerRunner,
    HealthCheckConfig,
    IncomingMessage,
    Infinite,
    SyncTaskInterface,
)
from loguru import logger


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
    def execute(self, incoming_message: IncomingMessage, progress: Callable[[float], None]) -> Any:  # noqa: ANN401
        # task_id = incoming_message.task_id
        body: dict[Any, Any] = incoming_message.body
        logging.info("Task_id: {task_id}")
        if body["mustSucceed"]:
            time = body["sleep"]
            logger.info(f"Traitement en cours... ({time}s)")
            sleep(time / 2)
            progress(30.0)
            sleep(time / 2)
            progress(30.0)
        else:
            # Exception "fonctionnelle", le message ne sera pas retraité, la tâche aura le status failure
            raise Exception("Argh")
        return {"hello": "world"}  # Réponse


# -------------------------
# Implémentation de la task
# "utilisateur" (Async)
# -------------------------
class MyAsyncTask(AsyncTaskInterface):
    async def execute(self, incoming_message: IncomingMessage, progress: Callable[[float], Awaitable]) -> Any:  # noqa: ANN401
        # task_id = incoming_message.task_id
        body: dict[Any, Any] = incoming_message.body

        if body["mustSucceed"]:
            time = body["sleep"]
            logger.info(f"Traitement en cours... ({time}s)")
            await asyncio.sleep(time / 2)
            await progress(0.3)
            await asyncio.sleep(time / 2)
            await progress(0.6)
        else:
            # Exception "fonctionnelle", le message ne sera pas retraité, la tâche aura le status failure
            raise Exception("Argh")
        return {"hello": "world"}  # Réponse


OUT_QUEUE_NAME = os.environ.get("OUT_QUEUE_NAME", "example_out_queue")
IN_QUEUE_NAME = os.environ.get("IN_QUEUE_NAME", "in_queue_python")
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


# Main
if __name__ == "__main__":
    asyncio.run(main())
