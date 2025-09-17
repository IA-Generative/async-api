"""
Async Worker package for RabbitMQ task processing.

This package provides classes and interfaces for creating asynchronous workers
that process tasks from RabbitMQ queues.
"""

from .worker import (
    AsyncTaskInterface,
    AsyncWorkerRunner,
    HealthCheckConfig,
    IncomingMessage,
    Infinite,
    OnShot,
    SyncTaskInterface,
    TaskInterface,
    WorkerMode,
)

__version__ = "0.1.0"

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
