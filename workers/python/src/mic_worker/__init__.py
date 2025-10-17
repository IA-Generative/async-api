"""
Async Worker package for RabbitMQ task processing.

This package provides classes and interfaces for creating asynchronous workers
that process tasks from RabbitMQ queues.
"""

from .typed import (
    AsyncTaskInterface,
    HealthCheckConfig,
    IncomingMessage,
    Infinite,
    OnShot,
    SyncTaskInterface,
    TaskInterface,
    WorkerMode,
)
from .worker import AsyncWorkerRunner

__all__: list[str] = [
    "AsyncTaskInterface",
    "AsyncWorkerRunner",
    "HealthCheckConfig",
    "IncomingMessage",
    "Infinite",
    "OnShot",
    "SyncTaskInterface",
    "TaskInterface",
    "WorkerMode",
]
