from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from api.core.security import admin_auth_guard
from api.main import app
from api.schemas.usage import ClientUsageResponse, ServiceUsage
from api.services.usage_service import UsageService


@pytest.fixture
def client() -> TestClient:
    mock_service = AsyncMock(spec=UsageService)
    mock_service.get_client_usage.return_value = ClientUsageResponse(
        client_id="test_client",
        period_days=30,
        services=[
            ServiceUsage(service="ocr", success_count=10, failure_count=2),
            ServiceUsage(service="translation", success_count=5, failure_count=0),
        ],
    )

    app.dependency_overrides[admin_auth_guard] = lambda: "admin"
    app.dependency_overrides[UsageService] = lambda: mock_service

    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_usage_returns_200(client: TestClient) -> None:
    response = client.get("/internal/usage/test_client")

    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == "test_client"
    assert data["period_days"] == 30
    assert len(data["services"]) == 2
    assert data["services"][0]["service"] == "ocr"
    assert data["services"][0]["success_count"] == 10
    assert data["services"][0]["failure_count"] == 2


def test_get_usage_with_custom_days(client: TestClient) -> None:
    response = client.get("/internal/usage/test_client?days=7")

    assert response.status_code == 200


def test_get_usage_requires_admin_auth() -> None:
    app.dependency_overrides.clear()
    unauthenticated_client = TestClient(app)
    response = unauthenticated_client.get("/internal/usage/test_client")

    assert response.status_code == 401


def test_get_usage_invalid_days_zero() -> None:
    app.dependency_overrides[admin_auth_guard] = lambda: "admin"
    app.dependency_overrides[UsageService] = lambda: AsyncMock(spec=UsageService)
    test_client = TestClient(app)

    response = test_client.get("/internal/usage/test_client?days=0")
    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_get_usage_invalid_days_too_large() -> None:
    app.dependency_overrides[admin_auth_guard] = lambda: "admin"
    app.dependency_overrides[UsageService] = lambda: AsyncMock(spec=UsageService)
    test_client = TestClient(app)

    response = test_client.get("/internal/usage/test_client?days=400")
    assert response.status_code == 422

    app.dependency_overrides.clear()
