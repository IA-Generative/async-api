import asyncio
import ssl
from typing import Literal

import aiohttp
from pydantic import BaseModel, Field

from listener.core.logger import logger
from listener.services.notifier_service import BaseNotifier, NotificationException


class HttpCallback(BaseModel):
    type: Literal["http"]
    url: str = Field(default=..., description="Url.")
    skip_tls: bool = Field(default=False, description="Disable TLS check.")


# ---------------------------------
# Http Notifier
# ---------------------------------


class HttpNotifier(BaseNotifier):
    def __init__(self, max_retries: int) -> None:
        self.max_retries = max_retries

    def unmarshall_callback(self, callback: dict) -> HttpCallback | None:
        try:
            return HttpCallback.model_validate(callback)
        except Exception as e:
            logger.debug(f"Failed to unmarshall callback: {e}")
            return None

    def accept(self, callback: dict) -> HttpCallback | None:
        return self.unmarshall_callback(callback) is not None

    async def notify(self, callback: dict, message: dict):  # noqa: ANN201
        http_callback = self.unmarshall_callback(callback)
        if http_callback is None:
            raise NotificationException(
                f"Http notifier cannot handle callback: {callback}",
            )
        await self.notify_retry(http_callback, message, 0)

    async def notify_retry(
        self,
        http_callback: HttpCallback,
        message: dict,
        retry: int,
    ) -> None:
        connector = aiohttp.TCPConnector(ssl=self.ssl_context(http_callback.skip_tls))
        try:
            async with aiohttp.ClientSession(connector=connector) as session:  # noqa: SIM117
                async with session.post(http_callback.url, data=message) as response:
                    if response.status != 200:
                        raise NotificationException(
                            f"Bad response status '{response.status}' for callback: {http_callback}",
                        )
                    logger.info("Http notification send successfully.")
        except Exception as e:
            if retry < self.max_retries:
                wait_time = pow(retry + 1, 2)
                logger.debug(
                    f"Failure, about to retry n°{retry + 1}/{self.max_retries} in {wait_time}s...",
                )
                await asyncio.sleep(wait_time)
                await self.notify_retry(http_callback, message, retry + 1)
                return
            logger.debug("No more retries")
            raise NotificationException(
                f"Error during the http call for callback: {http_callback}",
                e,
            ) from e

    def ssl_context(self, skip_tls: bool) -> ssl.SSLContext:
        ssl_context = ssl.create_default_context()
        if skip_tls:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context
