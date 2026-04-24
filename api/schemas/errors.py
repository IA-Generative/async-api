import http
from typing import TypedDict

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api.core.logger import logger
from api.schemas import ReadyComponent, TaskErrorResponse
from api.schemas.enum import ErrorEnum, ReadyStatus
from api.schemas.status import ReadyResponse


class ErrorDetail(BaseModel):
    number: int = Field(default=..., description="Code d'erreur unique")
    description: str = Field(default=..., description="Description de l'erreur")
    details: str | None = Field(default=None, description="Détails optionnels")


class ErrorResponse(BaseModel):
    status: str = Field(default="error", description="Statut de la réponse (toujours 'error')")
    error: ErrorDetail = Field(default=..., description="Détails de l'erreur")


class AppException(Exception):
    status_code: int = 500
    number: int = 500000
    description: str = ""

    def __init__(self, details: str | None = None) -> None:
        self.details: str | None = details
        logger.error(
            f"Internal server error: {self.number} - {self.description} | Details: {self.details}",
        )

    def to_response(self) -> JSONResponse:
        error = ErrorDetail(
            number=self.number,
            description=self.description,
            details=self.details,
        )
        response = ErrorResponse(error=error)
        return JSONResponse(
            status_code=self.status_code,
            content=response.model_dump(exclude_none=True),
        )


class ServiceNotFound(AppException):
    status_code = 404
    number = 404001
    description = "Service not found"


class TaskNotFound(AppException):
    status_code = 404
    number = 404002
    description = "Task not found"


class Forbidden(AppException):
    status_code = 403
    number = 403001
    description = "Forbidden"


class TooManyRequests(AppException):
    status_code = 429
    number = 429001
    description = "Too many service requests"


class TooManyClientsRequests(AppException):
    status_code = 429
    number = 429002
    description = "Too many service requests for the clientId."


class Unauthorized(AppException):
    status_code = 401
    number = 401001
    description = "Authentication required"


class InternalServerError(AppException):
    status_code = 500
    number = 500000
    description = "Internal server error"


class NotImplemented(AppException):
    status_code = 501
    number = 501001
    description = "Not implemented"


class ReadyResponseError(AppException):
    def __init__(self, status: str, components: dict[str, ReadyComponent], details: str | None = None) -> None:
        super().__init__(details=details)
        self.status: str = status
        self.components: dict[str, ReadyComponent] = components


class DependenciesNotReady(AppException):
    status_code = 503
    number = 503001
    description = "Service dependencies are not ready"

    def __init__(self, components: dict[str, ReadyComponent], details: str | None = None) -> None:
        super().__init__(details=details)
        self.components: dict[str, ReadyComponent] = components

    def to_response(self) -> JSONResponse:
        ready_response = ReadyResponse(
            status=ReadyStatus.ERROR,
            components=self.components,
        )

        return JSONResponse(
            status_code=self.status_code,
            content=ready_response.model_dump(),
        )


class BodyValidationError(AppException):
    status_code = 400
    number = 400001
    description = "Body validation error"


class ClientAlreadyExists(AppException):
    status_code = 409
    number = 409001
    description = "Client already exists"


class ClientNotFound(AppException):
    status_code = 404
    number = 404003
    description = "Client not found"


class StorageUploadError(AppException):
    status_code = 500
    number = 500002
    description = "File upload failed"


class OpenAPIErrorResponse(TypedDict, total=False):
    """Shape d'une entrée de `responses={}` pour la documentation OpenAPI."""

    model: type[BaseModel]
    description: str


class ERROR:
    """Réponses d'erreur OpenAPI réutilisables (modèle `ErrorResponse`)."""

    ADMIN_AUTH: OpenAPIErrorResponse = {
        "model": ErrorResponse,
        "description": "Authentification administrateur requise ou invalide",
    }
    AUTH: OpenAPIErrorResponse = {
        "model": ErrorResponse,
        "description": http.HTTPStatus.UNAUTHORIZED.phrase,
    }
    CLIENT_NOT_FOUND: OpenAPIErrorResponse = {
        "model": ErrorResponse,
        "description": "Client introuvable",
    }
    BODY_VALIDATION: OpenAPIErrorResponse = {
        "description": "Erreur de validation du corps de la requête",
    }
    INTERNAL: OpenAPIErrorResponse = {
        "model": ErrorResponse,
        "description": http.HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
    }


class TASK_ERROR:
    """Réponses d'erreur OpenAPI réutilisables pour les routes de tâches (modèle `TaskErrorResponse`)."""

    AUTH: OpenAPIErrorResponse = {
        "model": TaskErrorResponse,
        "description": http.HTTPStatus.UNAUTHORIZED.phrase,
    }
    FORBIDDEN: OpenAPIErrorResponse = {
        "model": TaskErrorResponse,
        "description": "Client non autorisé à utiliser ce service",
    }
    SERVICE_NOT_FOUND: OpenAPIErrorResponse = {
        "model": TaskErrorResponse,
        "description": ErrorEnum.SERVICE_NOT_FOUND.value,
    }
    INTERNAL: OpenAPIErrorResponse = {
        "model": TaskErrorResponse,
        "description": http.HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
    }
