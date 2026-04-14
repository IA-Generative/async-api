from typing import Annotated

from fastapi import APIRouter, Depends

from api.schemas import ServiceInfo
from api.services import ServiceService

router = APIRouter()


@router.get(
    path="/services",
    summary="Lister les services disponibles",
    description="Retourne la liste des services disponibles pour la création de tâches.",
)
def get_services(
    service_service: Annotated[ServiceService, Depends(ServiceService)],
) -> list[ServiceInfo]:
    """Retourne la liste des services disponibles avec leur json_schema."""
    return service_service.list_all()
