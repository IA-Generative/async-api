"""Test for individual config components URL construction."""

import os
from unittest.mock import patch

from api.core.config import Settings


class TestConfigComponents:
    """Test the construction of URLs from individual components."""

    def test_database_url_from_components_custom(self) -> None:
        """Test database URL construction with custom environment variables."""
        with patch.dict(
            os.environ,
            {
                "DB_HOST": "custom-db",
                "DB_PORT": "9999",
                "DB_NAME": "custom-tasks",
                "DB_USERNAME": "custom-user",
                "DB_PASSWORD": "custom-pass",
                "DB_SCHEME": "postgresql+asyncpg",
                "DATABASE_URL": "postgresql+asyncpg://custom-user:custom-pass@custom-db:9999/custom-tasks",
            },
        ):
            print(os.environ.get("DB_HOST"))  # noqa: T201
            settings = Settings()
            url = str(settings.database_url_from_components)
            assert url == "postgresql+asyncpg://custom-user:***@custom-db:9999/custom-tasks"

    def test_broker_url_from_components_custom(self) -> None:
        """Test broker URL construction with custom environment variables."""
        with patch.dict(
            os.environ,
            {
                "BROKER_HOST": "custom-broker",
                "BROKER_PORT": "5673",
                "BROKER_USERNAME": "custom-user",
                "BROKER_PASSWORD": "custom-pass",
                "BROKER_VHOST": "/custom",
            },
        ):
            settings = Settings()
            url = str(settings.broker_url_from_components)
            assert url == "amqp://custom-user:custom-pass@custom-broker:5673/custom"

    def test_full_url_properties(self) -> None:
        """Test that full URL properties still work."""
        with patch.dict(
            os.environ,
            {
                "BROKER_URL": "postgresql+asyncpg",
                "DATABASE_URL": "postgresql+asyncpg://custom-user:custom-pass@custom-db:9999/custom-tasks",
            },
        ):
            settings = Settings()
            assert hasattr(settings, "DATABASE_URL")
            assert hasattr(settings, "BROKER_URL")
            assert isinstance(settings.DATABASE_URL, str)
            assert isinstance(settings.BROKER_URL, str)
