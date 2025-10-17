"""
Tests pour le HealthCheckServer
"""

import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock

import pytest

from mic_worker.typed import HealthCheckConfig
from mic_worker.worker import HealthCheckServer


class TestHealthCheckServer:
    """Tests pour le serveur de health check."""

    def test_health_check_server_creation(self) -> None:
        """Test de création du serveur health check."""
        config = HealthCheckConfig(host="127.0.0.1", port=8080)
        server = HealthCheckServer(config)

        assert server.host == "127.0.0.1"
        assert server.port == 8080

    @pytest.mark.asyncio
    async def test_health_check_server_start(self) -> None:
        """Test de démarrage du serveur health check."""
        config = HealthCheckConfig(host="127.0.0.1", port=0)  # Port 0 = auto-assign
        server = HealthCheckServer(config)

        # Créer une tâche pour démarrer le serveur
        server_task = asyncio.create_task(server.start())

        # Laisser un peu de temps au serveur pour démarrer
        await asyncio.sleep(0.1)

        # Annuler la tâche du serveur
        server_task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await server_task

    @pytest.mark.asyncio
    async def test_health_check_handler(self) -> None:
        """Test du handler de health check."""
        # Mock des objets reader et writer
        reader = asyncio.StreamReader()

        # Créer un mock pour writer au lieu d'un vrai StreamWriter
        writer = MagicMock()
        writer.write = MagicMock()
        writer.close = MagicMock()
        writer.wait_closed = AsyncMock()
        writer.drain = AsyncMock()  # Ajouter drain()

        # Alimenter le reader avec des données HTTP valides
        reader.feed_data(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        reader.feed_eof()

        # Tester le handler (qui devrait lire jusqu'à \r\n\r\n et fermer)
        await HealthCheckServer.handler_health_check(reader, writer)

        # Le test réussit si aucune exception n'est levée

    @pytest.mark.asyncio
    async def test_health_check_handler_incomplete_read(self) -> None:
        """Test du handler avec lecture incomplète."""
        reader = asyncio.StreamReader()

        # Créer un mock pour writer au lieu d'un vrai StreamWriter
        writer = MagicMock()
        writer.write = MagicMock()
        writer.close = MagicMock()
        writer.wait_closed = AsyncMock()

        # Alimenter le reader avec des données incomplètes
        reader.feed_data(b"GET /health HTTP/1.1\r\n")
        reader.feed_eof()  # EOF avant \r\n\r\n complet

        # Le handler devrait gérer l'IncompleteReadError
        await HealthCheckServer.handler_health_check(reader, writer)

        # Le test réussit si aucune exception n'est levée
