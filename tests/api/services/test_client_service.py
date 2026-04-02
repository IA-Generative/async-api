from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from api.models.client import Client, ClientServiceAuthorization
from api.schemas.client import AuthorizationRequest, ClientCreateRequest, ClientUpdateRequest
from api.schemas.errors import ClientAlreadyExists, ClientNotFound
from api.services.client_service import ClientService


def _make_client(
    id: int,
    client_id: str,
    name: str,
    *,
    client_secret: str | None = None,
    authorizations: list[ClientServiceAuthorization] | None = None,
) -> Client:
    return Client(
        id=id,
        client_id=client_id,
        client_secret=client_secret,
        name=name,
        is_active=True,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
        authorizations=authorizations or [],
    )


CLIENT1 = _make_client(1, "client1_id", "Client 1", client_secret="client1_secret")
CLIENT2 = _make_client(2, "client2_id", "Client 2")
CLIENT3 = _make_client(
    3,
    "client3_id",
    "Client 3",
    client_secret="client3_secret",
    authorizations=[
        ClientServiceAuthorization(id=1, client_id=3, service="example_service", quotas=100),
        ClientServiceAuthorization(id=2, client_id=3, service="another_service", quotas=None),
    ],
)
CLIENT4 = _make_client(
    4,
    "client4_id",
    "Client 4",
    client_secret="client4_secret",
    authorizations=[
        ClientServiceAuthorization(id=3, client_id=4, service="all", quotas=100),
    ],
)

_DATA = {
    "client1_id": CLIENT1,
    "client2_id": CLIENT2,
    "client3_id": CLIENT3,
    "client4_id": CLIENT4,
}


@pytest.fixture
def client_repository_mock() -> AsyncMock:
    mock = AsyncMock()
    mock.get_active_client_by_client_id.side_effect = lambda client_id: _DATA.get(client_id)
    mock.get_client_by_client_id.side_effect = lambda client_id: _DATA.get(client_id)
    mock.get_all_clients.return_value = list(_DATA.values())
    mock.client_id_exists.return_value = False

    def _fake_persist(client: Client) -> Client:
        client.created_at = client.created_at or datetime(2026, 1, 1)
        client.updated_at = datetime(2026, 1, 1)
        return client

    mock.create_client.side_effect = _fake_persist
    mock.update_client.side_effect = _fake_persist
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


@pytest.mark.asyncio
async def test_create_client(client_repository_mock: AsyncMock) -> None:
    service = ClientService(client_repository_mock)

    body = ClientCreateRequest(
        client_id="new_client",
        name="New Client",
        client_secret="secret",
        is_active=True,
        authorizations=[AuthorizationRequest(service="example_service", quotas=10)],
    )
    response = await service.create_client(body)

    assert response.client_id == "new_client"
    assert response.name == "New Client"
    assert len(response.authorizations) == 1
    assert response.authorizations[0].service == "example_service"
    client_repository_mock.create_client.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_client_with_empty_authorizations(client_repository_mock: AsyncMock) -> None:
    service = ClientService(client_repository_mock)

    body = ClientCreateRequest(
        client_id="new_client",
        name="New Client",
        authorizations=[],
    )
    response = await service.create_client(body)

    assert response.client_id == "new_client"
    assert response.name == "New Client"
    assert response.authorizations == []
    client_repository_mock.create_client.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_client_already_exists(client_repository_mock: AsyncMock) -> None:
    service = ClientService(client_repository_mock)
    client_repository_mock.client_id_exists.return_value = True

    body = ClientCreateRequest(client_id="client1_id", name="Duplicate")

    with pytest.raises(ClientAlreadyExists):
        await service.create_client(body)


@pytest.mark.asyncio
async def test_list_clients(client_repository_mock: AsyncMock) -> None:
    service = ClientService(client_repository_mock)

    result = await service.list_clients()

    assert len(result) == 4
    assert result[0].client_id == "client1_id"
    client_repository_mock.get_all_clients.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_client(client_repository_mock: AsyncMock) -> None:
    service = ClientService(client_repository_mock)

    result = await service.get_client("client3_id")

    assert result.client_id == "client3_id"
    assert result.name == "Client 3"
    assert len(result.authorizations) == 2


@pytest.mark.asyncio
async def test_get_client_not_found(client_repository_mock: AsyncMock) -> None:
    service = ClientService(client_repository_mock)

    with pytest.raises(ClientNotFound):
        await service.get_client("unknown_client")


@pytest.mark.asyncio
async def test_update_client(client_repository_mock: AsyncMock) -> None:
    service = ClientService(client_repository_mock)

    body = ClientUpdateRequest(
        client_secret="new_secret",
        is_active=False,
        authorizations=[AuthorizationRequest(service="new_service", quotas=50)],
    )
    result = await service.update_client("client1_id", body)

    assert result.client_id == "client1_id"
    assert result.is_active is False
    assert len(result.authorizations) == 1
    assert result.authorizations[0].service == "new_service"
    client_repository_mock.update_client.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_client_partial(client_repository_mock: AsyncMock) -> None:
    service = ClientService(client_repository_mock)

    body = ClientUpdateRequest(is_active=False)
    result = await service.update_client("client3_id", body)

    assert result.is_active is False
    assert len(result.authorizations) == 2


@pytest.mark.asyncio
async def test_update_client_not_found(client_repository_mock: AsyncMock) -> None:
    service = ClientService(client_repository_mock)

    body = ClientUpdateRequest(is_active=False)
    with pytest.raises(ClientNotFound):
        await service.update_client("unknown_client", body)
