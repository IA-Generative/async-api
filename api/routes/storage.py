from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from api.core.logger import logger
from api.core.security import auth_guard
from api.schemas.errors import StorageUploadError
from api.schemas.storage import StorageUploadResponse
from api.services.storage_service import StorageService

router = APIRouter(tags=["Storage"])


@router.post(
    path="/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Stocker un fichier",
    description="""
Permet de stocker un fichier binaire dans le stockage S3.

- Le fichier est envoyé en multipart/form-data
- Le fichier est automatiquement supprimé après 24h
- Retourne un identifiant unique (file_id) au format `{client_id}/{uuid}/{filename}`
""",
)
def upload_file(
    file: Annotated[UploadFile, File(description="Fichier binaire à stocker")],
    storage_service: Annotated[StorageService, Depends(StorageService)],
    client_id: Annotated[str, Depends(auth_guard)],
) -> StorageUploadResponse:
    """Upload un fichier dans le stockage S3 et retourne un file_id unique."""
    try:
        file_id = storage_service.upload_file(
            client_id=client_id,
            filename=file.filename or "unnamed",
            file_obj=file.file,
        )
    except Exception as e:
        logger.exception(f"Upload failed for client_id={client_id} filename={file.filename}")
        raise StorageUploadError(details=str(e)) from e
    return StorageUploadResponse(file_id=file_id)
