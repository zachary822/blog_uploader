import os
from base64 import b64encode
from pathlib import Path
from typing import BinaryIO, Optional, Union

import requests
from bson.objectid import ObjectId

from blog_uploader.image_uploaders import ImageUploader
from blog_uploader.image_uploaders.schemas import ImgbbResponse


class ImgbbUploader(requests.Session, ImageUploader):
    def __init__(self, imgbb_api_key: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._api_key = imgbb_api_key

    def upload(self, file: BinaryIO) -> str:
        resp = self.post(
            "https://api.imgbb.com/1/upload",
            params={"key": self._api_key},
            data={"image": b64encode(file.read()).decode()},
        )
        resp_model = ImgbbResponse.parse_raw(resp.content)
        return resp_model.data.url
