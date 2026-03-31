from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status

from api.core.security import admin_auth_guard
from api.services.client_service import ClientService
from api.models.client import Client, ClientServiceAuthorization
from api.repositories.client_repository import ClientRepository
from api.schemas.client import ClientCreateRequest, ClientResponse, ClientUpdateRequest
from api.schemas.errors import ClientNotFound

router = APIRouter(tags=["Clients"])


@router.post(
    path="/clients",
    status_code=status.HTTP_201_CREATED,
    summary="Créer un client",
)
async def create_client(
    body: Annotated[ClientCreateRequest, Body()],
    client_service: Annotated[ClientService, Depends(ClientService)],
    _admin: Annotated[str, Depends(admin_auth_guard)],
) -> ClientResponse:
    return await client_service.create_client(body)


@router.get(
    path="/clients",
    summary="Lister les clients actifs",
)
async def list_clients(
    client_service: Annotated[ClientService, Depends(ClientService)],
    _admin: Annotated[str, Depends(admin_auth_guard)],
) -> list[ClientResponse]:
    return await client_service.list_clients()


@router.get(
    path="/clients/{client_id}",
    summary="Détail d'un client",
)
async def get_client(
    client_id: Annotated[str, Path(description="Identifiant du client")],
    client_service: Annotated[ClientService, Depends(ClientService)],
    _admin: Annotated[str, Depends(admin_auth_guard)],
) -> ClientResponse:
    return await client_service.get_client(client_id)


@router.put(
    path="/clients/{client_id}",
    summary="Modifier un client",
)
async def update_client(
    client_id: Annotated[str, Path(description="Identifiant du client")],
    body: Annotated[ClientUpdateRequest, Body()],
    client_repository: Annotated[ClientRepository, Depends(ClientRepository)],
    _admin: Annotated[str, Depends(admin_auth_guard)],
) -> ClientResponse:
    client = await client_repository.get_client_by_client_id(client_id)
    if not client:
        raise ClientNotFound(details=f"Client '{client_id}' not found.")

    if body.client_secret is not None:
        client.client_secret = body.client_secret

    if body.is_active is not None:
        client.is_active = body.is_active

    if body.authorizations is not None:
        client.authorizations = [
            ClientServiceAuthorization(service=auth.service, quotas=auth.quotas) for auth in body.authorizations
        ]

    client = await client_repository.update_client(client)
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
