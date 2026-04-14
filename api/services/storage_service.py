import uuid
from pathlib import PurePosixPath
from typing import IO, Annotated

from fastapi import Depends

from api.clients.s3_client import S3Client
from api.core.config import settings
from api.core.logger import logger


class StorageService:
    def __init__(
        self,
        s3_client: Annotated[S3Client, Depends(S3Client)],
    ) -> None:
        self.s3_client: S3Client = s3_client

    @staticmethod
    def generate_file_id(client_id: str, filename: str) -> str:
        """Generate file_id in format: {client_id}/{uuid}/{filename}"""
        safe_filename = PurePosixPath(filename).name
        return f"{client_id}/{uuid.uuid4()!s}/{safe_filename}"

    def upload_file(self, client_id: str, filename: str, file_obj: IO[bytes]) -> str:
        """Upload a file and return the file_id (S3 key)."""
        file_id = self.generate_file_id(client_id=client_id, filename=filename)
        self.s3_client.upload_fileobj(
            bucket_name=settings.S3_BUCKET_NAME,
            file_key=file_id,
            file_obj=file_obj,
        )
        logger.info(f"File uploaded: {file_id}")
        return file_id
