# async-worker

Generic API for async tasks with RabbitMQ and loguru.

## Installation

### Depuis PyPI (si publié)

```bash
uv add async-worker
uv add "git+https://github.com/titigmr/async-api.git#subdirectory=workers/python"
# Branch spécifique
uv add "git+https://github.com/titigmr/async-api.git@dev#subdirectory=workers/python"
# Par tag
uv add "git+https://github.com/titigmr/async-api.git@v0.1.0#subdirectory=workers/python"
```

## Utilisation

```python
import asyncio
import logging
import sys
from async_worker.worker import (
    AsyncTaskInterface,
    AsyncWorkerRunner,
    HealthCheckConfig,
    IncomingMessage,
    Infinite,
)
from loguru import logger

class InterceptHandler(logging.Handler):
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

class MyAsyncTask(AsyncTaskInterface):
    async def execute(self, incoming_message: IncomingMessage, progress):
        body = incoming_message.body
        if body["mustSucceed"]:
            time = body["sleep"]
            logger.info(f"Traitement en cours... ({time}s)")
            await asyncio.sleep(time / 2)
            await progress(0.3)
            await asyncio.sleep(time / 2)
            await progress(0.6)
        else:
            raise Exception("Argh")
        return {"hello": "world"}

async def main():
    runner = AsyncWorkerRunner(
        amqp_url="amqp://guest:guest@localhost/",
        amqp_in_queue="in_queue_python",
        amqp_out_queue="example_out_queue",
        task_provider=MyAsyncTask,
        worker_mode=Infinite(concurrency=5),
        health_check_config=HealthCheckConfig(host="127.0.0.1", port=8000),
    )
    await runner.start()

if __name__ == "__main__":
    asyncio.run(main())
```

## Variables d’environnement

* `BROKER_URL` : URL de connexion RabbitMQ (ex : amqp://guest:guest@localhost/)
* `IN_QUEUE_NAME` : nom de la file d’entrée
* `OUT_QUEUE_NAME` : nom de la file de sortie
* `WORKER_CONCURRENCY` : nombre de workers concurrents
