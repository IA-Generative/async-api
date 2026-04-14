from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from api.core.security import admin_auth_guard
from api.schemas.usage import ClientUsageResponse
from api.services.usage_service import UsageService

router = APIRouter(tags=["Usage"])


@router.get(
    path="/usage/{client_id}",
    summary="Usage par client et par service",
)
async def get_client_usage(
    client_id: Annotated[str, Path(description="Identifiant du client")],
    usage_service: Annotated[UsageService, Depends(UsageService)],
    _admin: Annotated[str, Depends(admin_auth_guard)],
    days: Annotated[int, Query(description="Nombre de jours à observer", ge=1, le=365)] = 30,
) -> ClientUsageResponse:
    return await usage_service.get_client_usage(client_id=client_id, days=days)
