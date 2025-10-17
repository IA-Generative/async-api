from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class IncomingMessage:
    task_id: str
    body: dict


class AsyncProgressProtocol(Protocol):
    async def __call__(self, *, progress: float, payload: dict | None = None) -> None: ...


class SyncProgressProtocol(Protocol):
    def __call__(self, *, progress: float, payload: dict | None = None) -> None: ...


class AsyncTaskInterface:
    async def execute(
        self,
        incoming_message: IncomingMessage,
        progress: AsyncProgressProtocol,
    ) -> Any:  # noqa: ANN401
        pass


class SyncTaskInterface:
    def execute(
        self,
        incoming_message: IncomingMessage,
        progress: SyncProgressProtocol,
    ) -> Any:  # noqa: ANN401
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
