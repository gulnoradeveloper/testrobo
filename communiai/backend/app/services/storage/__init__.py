"""Private file storage. Local filesystem for development, S3-compatible object storage for production.

Only metadata and the storage key are kept in the database. Files are never served by public URL.
"""
import os
import uuid
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


class Storage(Protocol):
    def save(self, data: bytes, suffix: str) -> str: ...
    def read(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


class LocalStorage:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = (self.root / key).resolve()
        if self.root not in p.parents:
            raise ValueError("invalid storage key")
        return p

    def save(self, data: bytes, suffix: str) -> str:
        key = f"{uuid.uuid4().hex[:2]}/{uuid.uuid4().hex}{suffix}"
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(data)
        os.chmod(p, 0o600)
        return key

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            # Overwrite before unlinking (best effort secure delete on local disks).
            size = p.stat().st_size
            with open(p, "r+b") as fh:
                fh.write(b"\0" * size)
                fh.flush()
                os.fsync(fh.fileno())
            p.unlink()


class S3Storage:
    def __init__(self):
        import boto3
        s = get_settings()
        self.bucket = s.STORAGE_BUCKET
        self.client = boto3.client(
            "s3", endpoint_url=s.S3_ENDPOINT_URL or None, region_name=s.S3_REGION,
            aws_access_key_id=s.S3_ACCESS_KEY_ID or None, aws_secret_access_key=s.S3_SECRET_ACCESS_KEY or None,
        )

    def save(self, data: bytes, suffix: str) -> str:
        key = f"projects/{uuid.uuid4().hex}{suffix}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ServerSideEncryption="AES256")
        return key

    def read(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        s = get_settings()
        _storage = S3Storage() if s.FILE_STORAGE_BACKEND == "s3" else LocalStorage(s.LOCAL_STORAGE_DIR)
    return _storage
