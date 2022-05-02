from typing import BinaryIO

import requests
from bson.objectid import ObjectId

from blog_uploader.image_uploaders import ImageUploader
from blog_uploader.image_uploaders.schemas import ImgurBasicResponse


class ImgurUploader(requests.Session, ImageUploader):
    def __init__(self, imgur_client_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers["Authorization"] = f"Client-ID {imgur_client_id}"

    def upload(self, file: BinaryIO, *args, **kwargs) -> str:
        resp = self.post(
            "https://api.imgur.com/3/upload",
            files={"image": file},
        )
        resp_model = ImgurBasicResponse.parse_raw(resp.content)

        return resp_model.data.link
