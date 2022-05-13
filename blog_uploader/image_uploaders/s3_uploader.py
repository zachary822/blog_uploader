import base64
import hashlib
import os
from functools import partial
from pathlib import Path
from typing import BinaryIO, Union
from urllib.parse import quote

import boto3

from blog_uploader.image_uploaders import ImageUploader
from blog_uploader.image_uploaders.exceptions import ChecksumMismatch

__all__ = ["S3Uploader"]


class S3Uploader(ImageUploader):
    def __init__(
        self, aws_access_key_id: str, aws_secret_access_key: str, s3_bucket: str
    ):
        self.client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        self.s3_bucket = s3_bucket

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def sha256(file: BinaryIO) -> bytes:
        t = file.tell()
        m = hashlib.sha256()
        for chunk in iter(partial(file.read, 1024), b""):
            m.update(chunk)
        file.seek(t)
        return m.digest()

    def upload(self, file: BinaryIO) -> str:
        key = Path(file.name).name
        checksum = self.sha256(file)

        try:
            resp = self.client.get_object_attributes(
                Bucket=self.s3_bucket, Key=key, ObjectAttributes=["Checksum"]
            )
            if checksum != base64.b64decode(resp["Checksum"]["ChecksumSHA256"]):
                raise ChecksumMismatch
        except (self.client.exceptions.NoSuchKey, ChecksumMismatch, KeyError):
            self.client.put_object(
                Bucket=self.s3_bucket,
                Body=file,
                Key=key,
                ChecksumAlgorithm="SHA256",
                ChecksumSHA256=base64.b64encode(checksum).decode(),
            )

        return f"https://s3.amazonaws.com/{quote(self.s3_bucket)}/{quote(key)}"

    def remove(self, path: Union[str, Path, os.PathLike], *args, **kwargs) -> None:
        p = Path(path)
        self.client.delete_object(Key=p.name, Bucket=self.s3_bucket)
