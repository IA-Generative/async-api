from typing import Annotated

from fastapi import APIRouter, Depends
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from starlette.responses import Response

from api.services.metrics_service import MetricsService

router = APIRouter()


@router.get(
    path="/metrics",
)
async def metrics(
    prom_service: Annotated[MetricsService, Depends(MetricsService)],
) -> Response:
    await prom_service.update_custom_metrics()
    return Response(content=generate_latest(registry=REGISTRY), media_type=CONTENT_TYPE_LATEST)
