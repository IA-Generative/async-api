from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db_session
from api.core.logger import logger
from api.schemas import HealthResponse, ReadyComponent, ReadyResponse
from api.schemas.enum import ReadyStatus
from api.schemas.errors import DependenciesNotReady
from api.services.queue_service import QueueSender

router = APIRouter()


@router.get(path="/health", summary="Vérifie la santé de l'API")
def health() -> HealthResponse:
    return HealthResponse(status=ReadyStatus.OK)


@router.get(
    path="/ready",
    summary="Vérifie si les dépendances sont prêtes",
)
async def ready(
    db: Annotated[AsyncSession, Depends(dependency=get_db_session)],
    queue_sender: Annotated[QueueSender, Depends(dependency=QueueSender)],
) -> ReadyResponse:
    components: dict[str, ReadyComponent] = {}

    try:
        await db.execute(text("SELECT 1"))
        db_status = ReadyStatus.OK
        db_details = None
    except Exception as error:
        logger.error(f"Database connection error: {error}")
        db_status = ReadyStatus.ERROR
        db_details = str(error)
    components["database"] = ReadyComponent(status=db_status, details=db_details)

    try:
        await queue_sender.ping()
        broker_status = ReadyStatus.OK
        broker_details = None
    except Exception as error:
        logger.error(f"Broker connection error: {error}")
        broker_status = ReadyStatus.ERROR
        broker_details = str(error)
    components["broker"] = ReadyComponent(status=broker_status, details=broker_details)

    global_status: ReadyStatus = (
        ReadyStatus.OK
        if all(component.status == ReadyStatus.OK for component in components.values())
        else ReadyStatus.ERROR
    )

    # Si les dépendances ne sont pas prêtes, lever une exception
    if global_status == ReadyStatus.ERROR:
        raise DependenciesNotReady(components=components, details="One or more dependencies are not ready")

    return ReadyResponse(status=global_status, components=components)
