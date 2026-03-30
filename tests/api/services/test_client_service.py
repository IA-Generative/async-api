from unittest.mock import AsyncMock

import pytest

from api.models.client import Client, ClientServiceAuthorization
from api.services.client_service import ClientService


@pytest.fixture
def client_repository_mock() -> AsyncMock:
    mock = AsyncMock()

    client1 = Client(
        id=1,
        client_id="client1_id",
        client_secret="client1_secret",
        name="Client 1",
        is_active=True,
        authorizations=[],
    )
    client2 = Client(
        id=2,
        client_id="client2_id",
        client_secret=None,
        name="Client 2",
        is_active=True,
        authorizations=[],
    )
    client3 = Client(
        id=3,
        client_id="client3_id",
        client_secret="client3_secret",
        name="Client 3",
        is_active=True,
        authorizations=[
            ClientServiceAuthorization(id=1, client_id=3, service="example_service", quotas=100),
            ClientServiceAuthorization(id=2, client_id=3, service="another_service", quotas=None),
        ],
    )
    client4 = Client(
        id=4,
        client_id="client4_id",
        client_secret="client4_secret",
        name="Client 4",
        is_active=True,
        authorizations=[
            ClientServiceAuthorization(id=3, client_id=4, service="all", quotas=100),
        ],
    )

    data = {
        "client1_id": client1,
        "client2_id": client2,
        "client3_id": client3,
        "client4_id": client4,
    }
    mock.get_client_by_client_id.side_effect = lambda client_id: data.get(client_id)
    return mock


@pytest.mark.asyncio
async def test_is_valid_client_id_with_secret(client_repository_mock: AsyncMock) -> None:
    service = ClientService(client_repository_mock)

    assert await service.is_valid_client_id("client1_id", "client1_secret")
    assert await service.is_valid_client_id("client2_id", None)
    assert await service.is_valid_client_id("client2_id", "bob")
    assert not await service.is_valid_client_id("invalid_client_id", "bob")
    assert not await service.is_valid_client_id("client1_id", "bad_secret")


@pytest.mark.asyncio
async def test_get_client_authorization_for_service(client_repository_mock: AsyncMock) -> None:
    service = ClientService(client_repository_mock)

    # Existing client without authorization
    authorization = await service.get_client_authorization_for_service("client1_id", "example_service")
    assert authorization is None

    # Invalid client
    authorization = await service.get_client_authorization_for_service("invalid_client_id", "example_service")
    assert authorization is None

    # Client with specific service authorization
    authorization = await service.get_client_authorization_for_service("client3_id", "example_service")
    assert authorization is not None
    assert authorization.service == "example_service"
    assert authorization.quotas == 100

    authorization = await service.get_client_authorization_for_service("client3_id", "another_service")
    assert authorization is not None
    assert authorization.service == "another_service"
    assert authorization.quotas is None

    # All access
    authorization = await service.get_client_authorization_for_service("client4_id", "another_service")
    assert authorization is not None
    assert authorization.service == "all"
    assert authorization.quotas == 100
