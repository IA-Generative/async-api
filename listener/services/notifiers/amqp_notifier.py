import asyncio
import json
from typing import Literal

import aio_pika
from pydantic import BaseModel, Field

from listener.core.logger import logger
from listener.services.notifier_service import BaseNotifier, NotificationException


class AmqpCallback(BaseModel):
    type: Literal["amqp"]
    url: str = Field(default=..., description="url")
    queue: str = Field(default=..., description="queue")


class AmqpNotifier(BaseNotifier):
    def __init__(self, max_retries: int) -> None:
        self.max_retries = max_retries

    def unmarshall_callback(self, callback: dict) -> AmqpCallback | None:
        try:
            return AmqpCallback.model_validate(callback)
        except Exception as e:
            logger.debug(f"Failed to unmarshall callback: {e}")
            return None

    def accept(self, callback: dict) -> AmqpCallback | None:
        return self.unmarshall_callback(callback) is not None

    async def notify(self, callback: dict, message: dict) -> None:
        amqp_callback = self.unmarshall_callback(callback)
        if amqp_callback is None:
            raise NotificationException(
                f"Amqp notifier cannot handle callback: {callback}",
            )
        await self.notify_retry(amqp_callback, message, 0)

    async def notify_retry(
        self,
        amqp_callback: AmqpCallback,
        message: dict,
        retry: int,
    ) -> None:
        try:
            connection = await aio_pika.connect_robust(amqp_callback.url)
            async with connection:
                channel = await connection.channel()
                await channel.declare_queue(amqp_callback.queue, durable=True)
                pika_message = aio_pika.Message(body=json.dumps(message).encode())
                await channel.default_exchange.publish(
                    pika_message,
                    routing_key=amqp_callback.queue,
                )
                logger.info("Amqp notification send successfully.")

        except Exception as e:
            if retry < self.max_retries:
                wait_time = pow(retry + 1, 2)
                logger.debug(
                    f"Failure, about to retry n°{retry + 1}/{self.max_retries} in {wait_time}s...",
                )
                await asyncio.sleep(wait_time)
                await self.notify_retry(amqp_callback, message, retry + 1)
                return
            logger.debug("No more retries")
            raise NotificationException(
                f"Error during the amqp call for callback: {amqp_callback}",
                e,
            ) from e
