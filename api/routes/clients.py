from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status

from api.core.security import admin_auth_guard
from api.schemas.client import ClientCreateRequest, ClientResponse, ClientUpdateRequest
from api.services.client_service import ClientService

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
    client_service: Annotated[ClientService, Depends(ClientService)],
    _admin: Annotated[str, Depends(admin_auth_guard)],
) -> ClientResponse:
    return await client_service.update_client(client_id, body)
