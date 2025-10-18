from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskCallback(BaseModel):
    task_id: str = Field(default=..., description="Identifiant unique de la tâche")
    status: str = Field(default=..., description="Statut de la tâche (success, failure, etc.)")
    submission_date: datetime | None = Field(default=None, description="Date de soumission de la tâche")
    start_date: datetime | None = Field(default=None, description="Date de début de la tâche")
    end_date: datetime | None = Field(default=None, description="Date de fin de la tâche")
    progress: float | None = Field(
        default=None,
        examples=[0.1, 1.0],
        description="Progression de la tâche en pourcentage",
    )
    response: Any = Field(default=None, description="Réponse du service cible")
