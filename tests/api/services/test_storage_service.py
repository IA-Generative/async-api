from io import BytesIO
from unittest.mock import Mock

import pytest

from api.services.storage_service import StorageService


@pytest.fixture
def storage_service() -> StorageService:
    s3_client_mock = Mock()
    s3_client_mock.upload_fileobj.return_value = None
    return StorageService(s3_client=s3_client_mock)


class TestGenerateFileId:
    def test_format(self) -> None:
        file_id = StorageService.generate_file_id(client_id="astree", filename="facture.pdf")
        parts = file_id.split("/")
        assert len(parts) == 3
        assert parts[0] == "astree"
        assert len(parts[1]) == 36  # UUID with hyphens
        assert parts[2] == "facture.pdf"

    def test_unique_ids(self) -> None:
        id1 = StorageService.generate_file_id(client_id="client", filename="file.txt")
        id2 = StorageService.generate_file_id(client_id="client", filename="file.txt")
        assert id1 != id2

    def test_preserves_filename(self) -> None:
        file_id = StorageService.generate_file_id(client_id="c", filename="my doc (1).pdf")
        assert file_id.endswith("/my doc (1).pdf")

    def test_sanitizes_path_traversal(self) -> None:
        file_id = StorageService.generate_file_id(client_id="c", filename="../../etc/passwd")
        assert file_id.endswith("/passwd")
        assert ".." not in file_id


class TestUploadFile:
    def test_upload_returns_file_id(self, storage_service: StorageService) -> None:
        file_obj = BytesIO(b"fake content")
        file_id = storage_service.upload_file(
            client_id="astree",
            filename="facture.pdf",
            file_obj=file_obj,
        )
        assert file_id.startswith("astree/")
        assert file_id.endswith("/facture.pdf")
        storage_service.s3_client.upload_fileobj.assert_called_once()

    def test_upload_calls_s3_with_correct_params(self, storage_service: StorageService) -> None:
        file_obj = BytesIO(b"data")
        file_id = storage_service.upload_file(
            client_id="test",
            filename="doc.pdf",
            file_obj=file_obj,
        )
        call_kwargs = storage_service.s3_client.upload_fileobj.call_args
        assert call_kwargs.kwargs["file_key"] == file_id
        assert call_kwargs.kwargs["file_obj"] is file_obj
