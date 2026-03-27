import http
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status

from api.core.security import auth_guard
from api.schemas import (
    TaskCallback,
    TaskDataFailed,
    TaskDataPending,
    TaskDataProgress,
    TaskDataSuccess,
    TaskErrorResponse,
    TaskRequest,
    TaskResponse,
)
from api.schemas.enum import ErrorEnum, TaskStatus
from api.schemas.errors import TaskNotFound
from api.services import TaskService

router = APIRouter(tags=["Tasks"])
callback_router = APIRouter()


@callback_router.post(path="{$callback.url}")
def receive_callback(body: TaskCallback) -> None:
    """Exemple d'endpoint pour recevoir le callback d'une tâche asynchrone."""


@router.post(
    path="/services/{service}/tasks",
    status_code=status.HTTP_201_CREATED,
    callbacks=callback_router.routes,
    responses={
        404: {
            "model": TaskErrorResponse,
            "description": ErrorEnum.SERVICE_NOT_FOUND.value,
        },
        500: {
            "model": TaskErrorResponse,
            "description": http.HTTPStatus.INTERNAL_SERVER_ERROR.value,
        },
    },
    summary="Créer une tâche asynchrone",
    description="""
Crée une tâche asynchrone pour un service donné.

- **service** : nom du service à appeler (doit être dans la liste autorisée)
- **body** : paramètres à transmettre au service cible (dépend du service)
- **callback** : URL à appeler une fois la tâche terminée (optionnel)
""",
)
async def create_task(
    service: Annotated[
        str,
        Path(
            default=...,
            description="Nom du service pour lequel créer la tâche. Doit être dans la liste des services autorisés.",
        ),
    ],
    task: Annotated[
        TaskRequest,
        Body(
            default=...,
            description=(
                "Représente la tâche à créer. Inclut le nom du service, les paramètres, et éventuellement un callback."
            ),
        ),
    ],
    task_service: Annotated[TaskService, Depends(TaskService)],
    client_id: Annotated[str, Depends(auth_guard)],
) -> TaskResponse:
    """Crée une tâche pour le service demandé."""
    task_data: TaskDataPending = await task_service.submit_task(task=task, service=service, client_id=client_id)
    return TaskResponse(status=TaskStatus.SUCCESS, data=task_data)


@router.get(
    path="/services/{service}/tasks/{task_id}",
    responses={
        404: {
            "model": TaskErrorResponse,
            "description": ErrorEnum.TASK_NOT_FOUND.value,
        },
        500: {
            "model": TaskErrorResponse,
            "description": http.HTTPStatus.INTERNAL_SERVER_ERROR.value,
        },
    },
    summary="Récupérer le statut d'une tâche",
    description="""
Permet de récupérer le statut d'une tâche asynchrone via son identifiant.

- **task_id** : identifiant unique de la tâche à interroger
""",
)
async def get_task(
    service: Annotated[
        str,
        Path(
            default=...,
            description=(
                "Nom du service pour lequel récupérer la tâche doit être dans la liste des services autorisés."
            ),
        ),
    ],
    task_id: Annotated[
        str,
        Path(default=..., description="Identifiant unique de la tâche à récupérer."),
    ],
    task_service: Annotated[TaskService, Depends(TaskService)],
    client_id: Annotated[str, Depends(auth_guard)],
) -> TaskResponse:
    """Récupère le statut d'une tâche via son identifiant.
    - **task_id** : identifiant unique de la tâche.
    """
    task_info: (
        TaskDataPending | TaskDataProgress | TaskDataFailed | TaskDataSuccess | TaskErrorResponse | None
    ) = await task_service.poll_task(task_id=task_id, service=service, client_id=client_id)
    if not task_info:
        raise TaskNotFound
    return TaskResponse(status=TaskStatus.SUCCESS, data=task_info)
