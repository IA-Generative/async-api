from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class IncomingMessage:
    task_id: str
    body: dict


class AsyncTaskInterface:
    async def execute(self, _incoming_message: IncomingMessage, progress: Callable[[float], Awaitable]) -> Any:  # noqa: ANN401
        pass


class SyncTaskInterface:
    def execute(self, _incoming_message: IncomingMessage, progress: Callable[[float], None]) -> Any:  # noqa: ANN401
        pass


type TaskInterface = AsyncTaskInterface | SyncTaskInterface


class OnShot:
    pass


@dataclass
class Infinite:
    concurrency: int = 1


type WorkerMode = OnShot | Infinite


class SendException(Exception):
    pass


class IncomingMessageException(Exception):
    pass


class TaskException(Exception):
    pass


@dataclass
class HealthCheckConfig:
    host: str
    port: int
