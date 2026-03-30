import logging
from typing import BinaryIO

import boto3
from botocore.config import Config

from api.core.config import settings


class S3Client:
    def __init__(self) -> None:
        self.client = self._get_client()

    def _get_client(self) -> "boto3.client":
        return boto3.client(
            service_name="s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION_NAME,
            verify=False,
            config=Config(
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    def get_presigned_download_url(self, bucket: str, key: str, expires_in_seconds: int = 3600) -> str:
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in_seconds,
        )

    def upload_file(self, bucket_name: str, file_key: str, file_path: str) -> None:
        self.client.upload_file(Filename=file_path, Bucket=bucket_name, Key=file_key)
        logging.info("Uploaded file to bucket: %s/%s", bucket_name, file_key)

    def upload_fileobj(self, bucket_name: str, file_key: str, file_obj: BinaryIO) -> None:
        self.client.upload_fileobj(Fileobj=file_obj, Bucket=bucket_name, Key=file_key)
        logging.info("Uploaded file object to bucket: %s/%s", bucket_name, file_key)

    def list_files(self, bucket_name: str, prefix: str) -> list[str]:
        response = self.client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        return [obj["Key"] for obj in response.get("Contents", [])]

    def delete_file(self, bucket_name: str, file_key: str) -> None:
        self.client.delete_object(Bucket=bucket_name, Key=file_key)
        logging.info("Deleted file from bucket: %s/%s", bucket_name, file_key)

    def download(self, bucket_name: str, file_key: str) -> bytes:
        response = self.client.get_object(Bucket=bucket_name, Key=file_key)
        content: bytes = response["Body"].read()
        return content
