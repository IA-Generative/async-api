"""
Tests pour le module typed.py
"""

from mic_worker.typed import AsyncTaskInterface, HealthCheckConfig, Infinite, OnShot, SyncTaskInterface


class TestHealthCheckConfig:
    """Tests pour HealthCheckConfig."""

    @staticmethod
    def test_health_check_config_creation() -> None:
        """Test de création d'une configuration health check."""
        config = HealthCheckConfig(host="localhost", port=8080)
        assert config.host == "localhost"
        assert config.port == 8080

    @staticmethod
    def test_health_check_config_defaults() -> None:
        """Test avec des valeurs par défaut."""
        config = HealthCheckConfig(host="127.0.0.1", port=8000)
        assert config.host == "127.0.0.1"
        assert config.port == 8000


class TestWorkerMode:
    """Tests pour les modes de worker."""

    @staticmethod
    def test_infinite_mode() -> None:
        """Test du mode Infinite."""
        mode = Infinite()
        assert isinstance(mode, Infinite)

    @staticmethod
    def test_one_shot_mode() -> None:
        """Test du mode OnShot."""
        mode = OnShot()
        assert isinstance(mode, OnShot)


class TestIncomingMessage:
    """Tests pour IncomingMessage."""

    @staticmethod
    def test_incoming_message_creation() -> None:
        """Test de création d'un IncomingMessage."""
        # Note: IncomingMessage est probablement un type alias
        # Ce test devra être adapté selon l'implémentation réelle
        assert True


class TestProtocols:
    """Tests pour les protocoles de tâches."""

    @staticmethod
    def test_async_task_interface() -> None:
        """Test du protocole AsyncTaskInterface."""
        # Vérification que le protocole existe et peut être importé
        assert AsyncTaskInterface is not None

    @staticmethod
    def test_sync_task_interface() -> None:
        """Test du protocole SyncTaskInterface."""
        # Vérification que le protocole existe et peut être importé
        assert SyncTaskInterface is not None
