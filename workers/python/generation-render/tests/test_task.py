import json
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.s3_client import S3Client
from src.task import GenerationRenderTask

from mic_worker.typed import IncomingMessage

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_template() -> bytes:
    return (FIXTURES_DIR / "test_template.odt").read_bytes()


def _load_data() -> dict:
    return json.loads((FIXTURES_DIR / "test_data.json").read_text())


def _extract_content_xml(odt_bytes: bytes) -> str:
    with zipfile.ZipFile(BytesIO(odt_bytes), "r") as z:
        return z.read("content.xml").decode("utf-8")


def _make_s3_client(template_content: bytes) -> MagicMock:
    mock = MagicMock(spec=S3Client)
    mock.download.return_value = template_content
    mock.get_presigned_download_url.return_value = "https://s3.example.com/rendered.odt"
    return mock


def _make_progress() -> AsyncMock:
    return AsyncMock()


class TestTaskHappyPath:
    @pytest.mark.asyncio
    async def test_returns_output_file_id(self) -> None:
        s3 = _make_s3_client(_load_template())
        task = GenerationRenderTask(s3_client=s3)
        msg = IncomingMessage(task_id="task-123", body={"file_id": "client1/abc/template.odt", "data": _load_data()})

        result = await task.execute(msg, _make_progress())

        assert "output_file_id" in result
        assert "task-123" in result["output_file_id"]
        assert result["output_file_id"].endswith("rendered_template.odt")

    @pytest.mark.asyncio
    async def test_returns_download_url(self) -> None:
        s3 = _make_s3_client(_load_template())
        task = GenerationRenderTask(s3_client=s3)
        msg = IncomingMessage(task_id="task-123", body={"file_id": "client1/abc/template.odt", "data": _load_data()})

        result = await task.execute(msg, _make_progress())

        assert result["download_url"] == "https://s3.example.com/rendered.odt"

    @pytest.mark.asyncio
    async def test_uploads_rendered_content(self) -> None:
        s3 = _make_s3_client(_load_template())
        task = GenerationRenderTask(s3_client=s3)
        msg = IncomingMessage(task_id="task-123", body={"file_id": "client1/abc/template.odt", "data": _load_data()})

        await task.execute(msg, _make_progress())

        s3.upload.assert_called_once()
        uploaded_file_id, uploaded_content = s3.upload.call_args.args
        assert "task-123" in uploaded_file_id
        content_xml = _extract_content_xml(uploaded_content)
        assert "Dupont" in content_xml
        assert "Nice" in content_xml

    @pytest.mark.asyncio
    async def test_no_warnings_with_complete_data(self) -> None:
        s3 = _make_s3_client(_load_template())
        task = GenerationRenderTask(s3_client=s3)
        msg = IncomingMessage(task_id="task-123", body={"file_id": "client1/abc/template.odt", "data": _load_data()})

        result = await task.execute(msg, _make_progress())

        assert result["warnings"] == []

    @pytest.mark.asyncio
    async def test_progress_called_three_times(self) -> None:
        s3 = _make_s3_client(_load_template())
        task = GenerationRenderTask(s3_client=s3)
        msg = IncomingMessage(task_id="task-123", body={"file_id": "client1/abc/template.odt", "data": _load_data()})
        progress = _make_progress()

        await task.execute(msg, progress)

        assert progress.call_count == 3
        progress_values = [call.kwargs["progress"] for call in progress.call_args_list]
        assert progress_values == [0.3, 0.7, 1.0]


class TestTaskMissingKeys:
    @pytest.mark.asyncio
    async def test_returns_warnings_for_missing_keys(self) -> None:
        s3 = _make_s3_client(_load_template())
        task = GenerationRenderTask(s3_client=s3)
        partial_data = {"nom": "Dupont"}
        msg = IncomingMessage(
            task_id="task-123",
            body={"file_id": "client1/abc/template.odt", "data": partial_data},
        )

        result = await task.execute(msg, _make_progress())

        assert any("ville" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_still_uploads_with_missing_keys(self) -> None:
        s3 = _make_s3_client(_load_template())
        task = GenerationRenderTask(s3_client=s3)
        partial_data = {"nom": "Dupont"}
        msg = IncomingMessage(
            task_id="task-123",
            body={"file_id": "client1/abc/template.odt", "data": partial_data},
        )

        await task.execute(msg, _make_progress())

        s3.upload.assert_called_once()


class TestTaskFileNotFound:
    @pytest.mark.asyncio
    async def test_raises_on_missing_file(self) -> None:
        s3 = MagicMock(spec=S3Client)
        s3.download.side_effect = FileNotFoundError("File related to bad/id.odt does not exist")
        task = GenerationRenderTask(s3_client=s3)
        msg = IncomingMessage(task_id="task-123", body={"file_id": "bad/id.odt", "data": {}})

        with pytest.raises(FileNotFoundError, match="does not exist"):
            await task.execute(msg, _make_progress())
