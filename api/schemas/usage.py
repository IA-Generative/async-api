from pydantic import BaseModel, Field


class ServiceUsage(BaseModel):
    service: str = Field(description="Nom du service")
    success_count: int = Field(description="Nombre de tâches réussies")
    failure_count: int = Field(description="Nombre de tâches échouées")


class ClientUsageResponse(BaseModel):
    client_id: str = Field(description="Identifiant du client")
    period_days: int = Field(description="Période d'observation en jours")
    services: list[ServiceUsage] = Field(description="Usage par service")
