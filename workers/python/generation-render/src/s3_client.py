from io import BytesIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from loguru import logger


class S3Client:
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region_name: str,
        bucket_name: str,
    ) -> None:
        self.bucket_name = bucket_name
        self.client = boto3.client(
            service_name="s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
            verify=False,
            config=Config(
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    def download(self, file_id: str) -> bytes:
        """Download a file from S3 by its file_id (key).

        Raises:
            FileNotFoundError: if the file does not exist in S3.
        """
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=file_id)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                msg = f"File related to {file_id} does not exist"
                logger.error(msg)
                raise FileNotFoundError(msg) from e
            raise
        content: bytes = response["Body"].read()
        logger.info(f"Downloaded {file_id} ({len(content)} bytes)")
        return content

    def upload(self, file_id: str, content: bytes) -> None:
        """Upload file content to S3."""
        self.client.upload_fileobj(
            Fileobj=BytesIO(content),
            Bucket=self.bucket_name,
            Key=file_id,
        )
        logger.info(f"Uploaded {file_id} ({len(content)} bytes)")

    def get_presigned_download_url(self, file_id: str, expires_in: int = 86400) -> str:
        """Generate a pre-signed URL to download a file (default: 24h)."""
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.bucket_name, "Key": file_id},
            ExpiresIn=expires_in,
        )
