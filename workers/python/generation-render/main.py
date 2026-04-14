import asyncio

import src.logger  # noqa: F401 — side-effect: configure logging
from loguru import logger
from src.config import settings
from src.s3_client import S3Client
from src.task import GenerationRenderTask

from mic_worker.typed import HealthCheckConfig, Infinite
from mic_worker.worker import AsyncWorkerRunner


def build_s3_client() -> S3Client:
    return S3Client(
        endpoint_url=settings.S3_ENDPOINT_URL,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION_NAME,
        bucket_name=settings.S3_BUCKET_NAME,
    )


async def main() -> None:
    logger.info("Starting generation-render worker")

    s3_client = build_s3_client()

    runner = AsyncWorkerRunner(
        amqp_url=settings.BROKER_URL,
        amqp_in_queue=settings.IN_QUEUE_NAME,
        amqp_out_queue=settings.OUT_QUEUE_NAME,
        task_provider=lambda: GenerationRenderTask(s3_client=s3_client),
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
