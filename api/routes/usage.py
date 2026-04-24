import http
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from api.core.security import admin_auth_guard
from api.schemas.errors import ErrorResponse
from api.schemas.usage import ClientUsageResponse
from api.services.usage_service import UsageService

router = APIRouter(tags=["Usage"])


@router.get(
    path="/usage/{client_id}",
    summary="Usage par client et par service",
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Authentification administrateur requise ou invalide",
        },
        422: {
            "description": "Erreur de validation des paramètres de la requête (days hors intervalle)",
        },
        500: {
            "model": ErrorResponse,
            "description": http.HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
        },
    },
)
async def get_client_usage(
    client_id: Annotated[str, Path(description="Identifiant du client")],
    usage_service: Annotated[UsageService, Depends(UsageService)],
    _admin: Annotated[str, Depends(admin_auth_guard)],
    days: Annotated[int, Query(description="Nombre de jours à observer", ge=1, le=365)] = 30,
) -> ClientUsageResponse:
    return await usage_service.get_client_usage(client_id=client_id, days=days)
