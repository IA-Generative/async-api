from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuthorizationRequest(BaseModel):
    service: str = Field(description="Nom du service autorisé (ou 'all' pour tous)")
    quotas: int | None = Field(default=None, description="Quota de tâches concurrentes pour ce service")


class ClientCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_id": "my_client",
                "name": "My Client",
                "client_secret": "my_secret",
                "is_active": True,
                "authorizations": [
                    {"service": "my_service", "quotas": 100},
                ],
            },
        },
    )

    client_id: str = Field(description="Identifiant unique du client")
    name: str = Field(description="Nom du client")
    client_secret: str | None = Field(default=None, description="Secret du client (optionnel)")
    is_active: bool = Field(default=True, description="Client actif ou non")
    authorizations: list[AuthorizationRequest] = Field(
        default_factory=list, description="Liste des autorisations par service",
    )


class ClientUpdateRequest(BaseModel):
    client_secret: str | None = Field(default=None, description="Nouveau secret du client")
    is_active: bool | None = Field(default=None, description="Activer ou désactiver le client")
    authorizations: list[AuthorizationRequest] | None = Field(
        default=None, description="Nouvelle liste des autorisations (remplace l'existante)",
    )


class AuthorizationResponse(BaseModel):
    service: str
    quotas: int | None = None


class ClientResponse(BaseModel):
    client_id: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    authorizations: list[AuthorizationResponse]
