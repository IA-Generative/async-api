from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status

from api.core.security import admin_auth_guard
from api.models.client import Client, ClientServiceAuthorization
from api.repositories.client_repository import ClientRepository
from api.schemas.client import ClientCreateRequest, ClientResponse
from api.schemas.errors import ClientAlreadyExists, ClientNotFound

router = APIRouter(tags=["Clients"])


@router.post(
    path="/clients",
    status_code=status.HTTP_201_CREATED,
    summary="Créer un client",
)
async def create_client(
    body: Annotated[ClientCreateRequest, Body()],
    client_repository: Annotated[ClientRepository, Depends(ClientRepository)],
    _admin: Annotated[str, Depends(admin_auth_guard)],
) -> ClientResponse:
    if await client_repository.client_id_exists(body.client_id):
        raise ClientAlreadyExists(details=f"Client '{body.client_id}' already exists.")

    client = Client(
        client_id=body.client_id,
        name=body.name,
        client_secret=body.client_secret,
        is_active=body.is_active,
        authorizations=[
            ClientServiceAuthorization(service=auth.service, quotas=auth.quotas) for auth in body.authorizations
        ],
    )
    client = await client_repository.create_client(client)
    return _to_response(client)


@router.get(
    path="/clients",
    summary="Lister les clients actifs",
)
async def list_clients(
    client_repository: Annotated[ClientRepository, Depends(ClientRepository)],
    _admin: Annotated[str, Depends(admin_auth_guard)],
) -> list[ClientResponse]:
    clients = await client_repository.get_all_clients()
    return [_to_response(c) for c in clients]


@router.get(
    path="/clients/{client_id}",
    summary="Détail d'un client",
)
async def get_client(
    client_id: Annotated[str, Path(description="Identifiant du client")],
    client_repository: Annotated[ClientRepository, Depends(ClientRepository)],
    _admin: Annotated[str, Depends(admin_auth_guard)],
) -> ClientResponse:
    client = await client_repository.get_client_by_client_id(client_id)
    if not client:
        raise ClientNotFound(details=f"Client '{client_id}' not found.")
    return _to_response(client)


def _to_response(client: Client) -> ClientResponse:
    return ClientResponse(
        client_id=client.client_id,
        name=client.name,
        is_active=client.is_active,
        created_at=client.created_at,
        updated_at=client.updated_at,
        authorizations=[
            {"service": auth.service, "quotas": auth.quotas} for auth in client.authorizations
        ],
    )
