import base64
import hashlib
import os
from functools import partial
from pathlib import Path
from typing import BinaryIO, Union
from urllib.parse import quote

import boto3

from blog_uploader.image_uploaders import ImageUploader


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
    def md5(file: BinaryIO) -> str:
        m = hashlib.md5()
        for chunk in iter(partial(file.read, 1024), b""):
            m.update(chunk)
        file.seek(0)
        return base64.b64encode(m.digest()).decode()

    def upload(self, file: BinaryIO, *args, **kwargs) -> str:
        key = Path(file.name).name
        self.client.put_object(
            Bucket=self.s3_bucket, Body=file, Key=key, ContentMD5=self.md5(file)
        )
        return f"https://s3.amazonaws.com/{quote(self.s3_bucket)}/{quote(key)}"

    def remove(self, path: Union[str, Path, os.PathLike], *args, **kwargs) -> None:
        p = Path(path)
        self.client.delete_object(Key=p.name, Bucket=self.s3_bucket)
