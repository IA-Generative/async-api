"""
Fixtures et configuration partagée pour les tests mic_worker
"""

import asyncio
import logging
import os
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator
from typing import Any

import pytest
import pytest_asyncio
from aio_pika import connect_robust
from aio_pika.abc import AbstractRobustConnection

from mic_worker.typed import HealthCheckConfig


def pytest_configure(config: pytest.Config) -> None:
    """Configuration des marqueurs personnalisés pour pytest."""
    config.addinivalue_line(
        "markers",
        "integration: marqueur pour les tests d'intégration",
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    """Créer un event loop pour toute la session de tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def health_config() -> HealthCheckConfig:
    """Configuration pour les health checks de test."""
    return HealthCheckConfig(host="127.0.0.1", port=0)  # Port 0 = auto-assign


@pytest_asyncio.fixture
async def rabbitmq_connection() -> AsyncGenerator[AbstractRobustConnection]:
    """Connection RabbitMQ pour les tests."""

    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

    try:
        connection = await connect_robust(rabbitmq_url)
        yield connection
    except Exception as e:
        pytest.skip(f"RabbitMQ non disponible: {e}")


@pytest.fixture
def sample_message_data() -> dict[str, Any]:
    """Données de message de test."""
    return {
        "task_id": "test-task-123",
        "data": {"param1": "value1", "param2": 42},
        "timestamp": "2025-10-17T10:00:00Z",
    }


@pytest.fixture
def mock_task_success() -> Callable[[Any], Awaitable[str]]:
    """Mock d'une tâche qui réussit."""

    async def task(message: Any) -> str: # noqa: ANN401
        await asyncio.sleep(0.1)  # Simule du travail
        return f"Processed: {message.body.decode()}"

    return task


@pytest.fixture
def mock_task_failure() -> Callable[[Any], Awaitable[None]]:
    """Mock d'une tâche qui échoue."""

    async def task(message: Any) -> None: # noqa: ANN401, ARG001
        await asyncio.sleep(0.1)
        raise Exception("Simulated task failure")

    return task


@pytest.fixture
def mock_sync_task() -> Callable[[Any], str]:
    """Mock d'une tâche synchrone."""

    def task(message: Any) -> str: # noqa: ANN401, 
        return f"Sync processed: {message.body.decode()}"

    return task


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
