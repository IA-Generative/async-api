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

        # TODO: ticket 5 — upload résultat dans S3 + pre-signed URL
        return {
            "warnings": result.warnings,
        }

    def _download_template(self, task_id: str, file_id: str) -> bytes:
        logger.info(f"Task {task_id}: downloading template {file_id}")
        content = self.s3_client.download(file_id)
        logger.info(f"Task {task_id}: template downloaded ({len(content)} bytes)")
        return content
