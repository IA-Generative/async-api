from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from api.core.security import auth_guard
from api.main import app
from api.services.storage_service import StorageService


@pytest.fixture
def client() -> TestClient:
    mock_service = Mock(spec=StorageService)
    mock_service.upload_file.return_value = "test_client/fake-uuid/test.pdf"

    app.dependency_overrides[auth_guard] = lambda: "test_client"
    app.dependency_overrides[StorageService] = lambda: mock_service

    yield TestClient(app)
    app.dependency_overrides.clear()


def test_upload_file_returns_201(client: TestClient) -> None:
    response = client.post(
        "/storage/upload",
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["file_id"] == "test_client/fake-uuid/test.pdf"


def test_upload_file_requires_auth() -> None:
    app.dependency_overrides.clear()
    unauthenticated_client = TestClient(app)
    response = unauthenticated_client.post(
        "/storage/upload",
        files={"file": ("test.pdf", b"content", "application/pdf")},
    )
    assert response.status_code == 401
