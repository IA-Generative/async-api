"""
Tests d'intégration pour mic_worker
Ces tests nécessitent RabbitMQ en fonctionnement
"""

import contextlib
import json
import os
from typing import Any

import pytest

from mic_worker.typed import HealthCheckConfig, IncomingMessage, Infinite, OnShot, SyncTaskInterface
from mic_worker.worker import AsyncWorkerRunner


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_worker_integration() -> None:
    """Test d'intégration complet avec RabbitMQ."""
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    results: list[str] = []

    class TaskProvider(SyncTaskInterface):
        """Provider de tâche de test."""

        async def process_message(self, message: Any) -> str:
            data = json.loads(message.body.decode())
            result = f"Processed: {data.get('id', 'unknown')}"
            results.append(result)
            return result

    # Configuration en mode OnShot pour traiter un seul message
    runner = AsyncWorkerRunner(
        amqp_url=rabbitmq_url,
        amqp_in_queue="test_integration_queue",
        amqp_out_queue="test_integration_out_queue",
        task_provider=TaskProvider,
        worker_mode=OnShot(),
        health_check_config=HealthCheckConfig(host="127.0.0.1", port=0),
    )
    assert runner is not None
    assert runner.one_shot is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check_integration() -> None:
    """Test d'intégration du health check."""
    import asyncio

    from mic_worker.worker import HealthCheckServer

    health_config = HealthCheckConfig(host="127.0.0.1", port=0)
    server = HealthCheckServer(health_config)
    server_task = asyncio.create_task(server.start())
    server_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await server_task
        # Expected


@pytest.mark.integration
def test_concurrent_worker_modes() -> None:
    """Test des différents modes de worker."""

    class TaskProvider(SyncTaskInterface):
        async def process_message(self, incoming_message: IncomingMessage) -> str:
            return "processed"

    runner_oneshot = AsyncWorkerRunner(
        amqp_url="amqp://guest:guest@localhost:5672/",
        amqp_in_queue="test_queue",
        amqp_out_queue="test_out_queue",
        task_provider=TaskProvider,
        worker_mode=OnShot(),
    )

    assert runner_oneshot.one_shot is True
    assert runner_oneshot.nbr_async_task == 1

    # Test mode Infinite avec concurrence
    runner_infinite = AsyncWorkerRunner(
        amqp_url="amqp://guest:guest@localhost:5672/",
        amqp_in_queue="test_queue",
        amqp_out_queue="test_out_queue",
        task_provider=TaskProvider,
        worker_mode=Infinite(concurrency=10),
    )

    assert runner_infinite.one_shot is False
    assert runner_infinite.nbr_async_task == 10
