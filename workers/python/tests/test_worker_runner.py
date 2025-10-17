"""
Tests pour AsyncWorkerRunner
"""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from mic_worker.typed import AsyncTaskInterface, HealthCheckConfig, IncomingMessage, Infinite, OnShot
from mic_worker.worker import AsyncWorkerRunner


class TestAsyncWorkerRunner:
    """Tests pour le runner de worker asynchrone."""

    def test_worker_runner_creation(self) -> None:
        """Test de création du worker runner."""
        health_config = HealthCheckConfig(host="127.0.0.1", port=8080)

        class TaskProvider(AsyncTaskInterface):
            async def execute(
                self,
                incoming_message: IncomingMessage,
                progress: Any,
            ) -> str:
                return "processed"

        runner = AsyncWorkerRunner(
            amqp_url="amqp://guest:guest@localhost:5672/",
            amqp_in_queue="test_in_queue",
            amqp_out_queue="test_out_queue",
            task_provider=TaskProvider,
            worker_mode=Infinite(),
            health_check_config=health_config,
        )

        assert runner.amqp_url == "amqp://guest:guest@localhost:5672/"
        assert runner.amqp_in_queue == "test_in_queue"
        assert runner.amqp_out_queue == "test_out_queue"
        assert runner.health_check_config == health_config

    def test_worker_runner_with_one_shot_mode(self) -> None:
        """Test du worker runner en mode OnShot."""

        class TaskProvider(AsyncTaskInterface):
            async def execute(
                self,
                incoming_message: IncomingMessage,  # noqa: ARG002
                progress: Any,  # noqa: ARG002, ANN401
            ) -> str:
                return "processed"

        runner = AsyncWorkerRunner(
            amqp_url="amqp://guest:guest@localhost:5672/",
            amqp_in_queue="test_in_queue",
            amqp_out_queue="test_out_queue",
            task_provider=TaskProvider,
            worker_mode=OnShot(),
        )

        assert runner.one_shot is True
        assert runner.nbr_async_task == 1

        class TaskProvider2(AsyncTaskInterface):
            async def execute(
                self,
                incoming_message: IncomingMessage,  # noqa: ARG002
                progress: Any,  # noqa: ARG002, ANN401
            ) -> str:
                return "processed"

        concurrency = 5
        runner = AsyncWorkerRunner(
            amqp_url="amqp://guest:guest@localhost:5672/",
            amqp_in_queue="test_in_queue",
            amqp_out_queue="test_out_queue",
            task_provider=TaskProvider2,
            worker_mode=Infinite(concurrency=concurrency),
        )

        assert runner.one_shot is False
        assert runner.nbr_async_task == concurrency

    def test_worker_runner_without_health_config(self) -> None:
        """Test sans configuration health check."""

        class MockTaskProvider(AsyncTaskInterface):
            async def execute(
                self,
                incoming_message: IncomingMessage,  # noqa: ARG002
                progress: Any,  # noqa: ARG002, ANN401
            ) -> str:
                return "processed"

        runner = AsyncWorkerRunner(
            amqp_url="amqp://guest:guest@localhost:5672/",
            amqp_in_queue="test_in_queue",
            amqp_out_queue="test_out_queue",
            task_provider=MockTaskProvider,
            worker_mode=Infinite(),
        )

        assert runner.health_check_config is None

    @pytest.mark.asyncio
    @patch("aio_pika.connect_robust")
    async def test_wait_for_connection_success(self, mock_connect: AsyncMock) -> None:
        """Test de connexion réussie."""

        class MockTaskProvider(AsyncTaskInterface):
            async def execute(
                self,
                incoming_message: IncomingMessage,  # noqa: ARG002
                progress: Any,  # noqa: ARG002, ANN401
            ) -> str:
                return "processed"

        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection

        runner = AsyncWorkerRunner(
            amqp_url="amqp://guest:guest@localhost:5672/",
            amqp_in_queue="test_in_queue",
            amqp_out_queue="test_out_queue",
            task_provider=MockTaskProvider,
            worker_mode=OnShot(),
        )

        connection = await runner.wait_for_connection()

        assert connection == mock_connection
        mock_connect.assert_called_once_with(url=runner.amqp_url)

    @pytest.mark.asyncio
    @patch("aio_pika.connect_robust")
    @patch("asyncio.sleep")
    async def test_wait_for_connection_retry(self, mock_sleep: AsyncMock, mock_connect: AsyncMock) -> None:
        """Test de retry de connexion."""

        def mock_task_provider():
            async def task(message: Any):
                return "processed"

            return task

        mock_connection = AsyncMock()
        # Première tentative échoue, deuxième réussit
        mock_connect.side_effect = [Exception("Connection failed"), mock_connection]

        runner = AsyncWorkerRunner(
            amqp_url="amqp://guest:guest@localhost:5672/",
            amqp_in_queue="test_in_queue",
            amqp_out_queue="test_out_queue",
            task_provider=mock_task_provider,
            worker_mode=OnShot(),
        )

        connection = await runner.wait_for_connection()

        assert connection == mock_connection
        assert mock_connect.call_count == 2
        mock_sleep.assert_called_once_with(5)
