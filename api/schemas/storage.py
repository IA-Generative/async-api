from pydantic import BaseModel, Field


class StorageUploadResponse(BaseModel):
    file_id: str = Field(
        ...,
        description="Identifiant unique du fichier stocké (format: client_id/uuid/filename)",
        examples=["astree/a1b2c3d4-e5f6-7890-abcd-ef1234567890/facture.pdf"],
    )
