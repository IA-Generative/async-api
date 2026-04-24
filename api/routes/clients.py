import http
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status

from api.core.security import admin_auth_guard
from api.schemas.client import ClientCreateRequest, ClientResponse, ClientUpdateRequest
from api.schemas.errors import ErrorResponse
from api.services.client_service import ClientService

router = APIRouter(tags=["Clients"])


@router.post(
    path="/clients",
    status_code=status.HTTP_201_CREATED,
    summary="Créer un client",
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Authentification administrateur requise ou invalide",
        },
        409: {
            "model": ErrorResponse,
            "description": "Un client avec ce client_id existe déjà",
        },
        422: {
            "description": "Erreur de validation du corps de la requête",
        },
        500: {
            "model": ErrorResponse,
            "description": http.HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
        },
    },
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
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Authentification administrateur requise ou invalide",
        },
        500: {
            "model": ErrorResponse,
            "description": http.HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
        },
    },
)
async def list_clients(
    client_service: Annotated[ClientService, Depends(ClientService)],
    _admin: Annotated[str, Depends(admin_auth_guard)],
) -> list[ClientResponse]:
    return await client_service.list_clients()


@router.get(
    path="/clients/{client_id}",
    summary="Détail d'un client",
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Authentification administrateur requise ou invalide",
        },
        404: {
            "model": ErrorResponse,
            "description": "Client introuvable",
        },
        500: {
            "model": ErrorResponse,
            "description": http.HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
        },
    },
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
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Authentification administrateur requise ou invalide",
        },
        404: {
            "model": ErrorResponse,
            "description": "Client introuvable",
        },
        422: {
            "description": "Erreur de validation du corps de la requête",
        },
        500: {
            "model": ErrorResponse,
            "description": http.HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
        },
    },
)
async def update_client(
    client_id: Annotated[str, Path(description="Identifiant du client")],
    body: Annotated[ClientUpdateRequest, Body()],
    client_service: Annotated[ClientService, Depends(ClientService)],
    _admin: Annotated[str, Depends(admin_auth_guard)],
) -> ClientResponse:
    return await client_service.update_client(client_id, body)
