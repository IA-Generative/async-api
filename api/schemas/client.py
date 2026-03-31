from datetime import datetime

from pydantic import BaseModel, Field


class AuthorizationRequest(BaseModel):
    service: str = Field(description="Nom du service autorisé (ou 'all' pour tous)")
    quotas: int | None = Field(default=None, description="Quota de tâches concurrentes pour ce service")


class ClientCreateRequest(BaseModel):
    client_id: str = Field(description="Identifiant unique du client")
    name: str = Field(description="Nom du client")
    client_secret: str | None = Field(default=None, description="Secret du client (optionnel)")
    is_active: bool = Field(default=True, description="Client actif ou non")
    authorizations: list[AuthorizationRequest] = Field(default=[], description="Liste des autorisations par service")


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
