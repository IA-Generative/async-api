from pathlib import PurePosixPath
from typing import Any

from loguru import logger

from mic_worker.typed import AsyncProgressProtocol, AsyncTaskInterface, IncomingMessage
from src.renderers import get_renderer
from src.s3_client import S3Client


class GenerationRenderTask(AsyncTaskInterface):
    def __init__(self, s3_client: S3Client) -> None:
        self.s3_client = s3_client

    async def execute(
        self,
        incoming_message: IncomingMessage,
        progress: AsyncProgressProtocol,
    ) -> Any:  # noqa: ANN401
        task_id = incoming_message.task_id
        body: dict[str, Any] = incoming_message.body
        file_id: str = body["file_id"]
        data: dict[str, str] = body["data"]

        template_content = self._download_template(task_id, file_id)
        await progress(progress=0.3, payload=None)

        renderer = get_renderer(file_id)
        result = renderer.render(template_content, data)
        await progress(progress=0.7, payload=None)

        output_file_id = self._build_output_file_id(task_id, file_id)
        self._upload_result(task_id, output_file_id, result.content)
        download_url = self.s3_client.get_presigned_download_url(output_file_id)
        await progress(progress=1.0, payload=None)

        return {
            "output_file_id": output_file_id,
            "download_url": download_url,
            "warnings": result.warnings,
        }

    def _download_template(self, task_id: str, file_id: str) -> bytes:
        logger.info(f"Task {task_id}: downloading template {file_id}")
        content = self.s3_client.download(file_id)
        logger.info(f"Task {task_id}: template downloaded ({len(content)} bytes)")
        return content

    def _build_output_file_id(self, task_id: str, source_file_id: str) -> str:
        """Build the S3 key for the rendered file.

        Example: "client1/abc123/facture.odt" → "client1/abc123/<task_id>/rendered_facture.odt"
        """
        path = PurePosixPath(source_file_id)
        return str(path.parent / task_id / f"rendered_{path.name}")

    def _upload_result(self, task_id: str, output_file_id: str, content: bytes) -> None:
        logger.info(f"Task {task_id}: uploading result to {output_file_id}")
        self.s3_client.upload(output_file_id, content)
        logger.info(f"Task {task_id}: result uploaded ({len(content)} bytes)")
