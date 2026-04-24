from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from starlette.datastructures import UploadFile

from api.core.config import settings
from api.core.logger import logger
from api.core.security import auth_guard
from api.schemas.errors import ERROR, ErrorResponse, StorageUploadError
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
    responses={
        400: {
            "description": "Champ 'file' manquant dans le form-data",
        },
        401: ERROR.AUTH,
        500: {
            "model": ErrorResponse,
            "description": "Échec de l'upload du fichier dans le stockage S3",
        },
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "file": {
                                "type": "string",
                                "format": "binary",
                                "description": "Fichier binaire à stocker",
                            },
                        },
                        "required": ["file"],
                    },
                },
            },
            "required": True,
        },
    },
)
async def upload_file(
    request: Request,
    storage_service: Annotated[StorageService, Depends(StorageService)],
    client_id: Annotated[str, Depends(auth_guard)],
) -> StorageUploadResponse:
    """Upload un fichier dans le stockage S3 et retourne un file_id unique.

    Parse manuellement le form avec une limite `max_part_size` configurable
    pour contourner la limite par defaut de Starlette (1 MB depuis 0.45+).
    """
    max_part_size = settings.API_UPLOAD_MAX_SIZE_MB * 1024 * 1024
    form = await request.form(max_part_size=max_part_size)
    file = form.get("file")

    if not isinstance(file, UploadFile):
        raise HTTPException(status_code=400, detail="Missing 'file' field in form data")

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
