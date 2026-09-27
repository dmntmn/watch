"""S3-compatible object storage for attachments (MinIO locally)."""
import io
from typing import BinaryIO

from aiobotocore.session import AioSession

from src.config import get_settings
from src.logging_config import get_logger

logger = get_logger(__name__)

settings = get_settings()


class ObjectStorage:
    def __init__(self) -> None:
        self._session = AioSession()

    async def _client(self):
        return self._session.create_client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            use_ssl=settings.s3_use_ssl,
        )

    async def ensure_bucket(self) -> None:
        async with await self._client() as client:
            try:
                await client.head_bucket(Bucket=settings.s3_bucket)
            except Exception:  # noqa: BLE001
                await client.create_bucket(Bucket=settings.s3_bucket)
                logger.info("S3 bucket created: %s", settings.s3_bucket)

    async def upload(self, key: str, body: bytes, content_type: str | None = None) -> None:
        async with await self._client() as client:
            await client.put_object(
                Bucket=settings.s3_bucket,
                Key=key,
                Body=body,
                ContentType=content_type or "application/octet-stream",
            )

    async def download(self, key: str) -> BinaryIO:
        async with await self._client() as client:
            response = await client.get_object(Bucket=settings.s3_bucket, Key=key)
            data = await response["Body"].read()
        return io.BytesIO(data)

    async def delete(self, key: str) -> None:
        async with await self._client() as client:
            await client.delete_object(Bucket=settings.s3_bucket, Key=key)


storage = ObjectStorage()