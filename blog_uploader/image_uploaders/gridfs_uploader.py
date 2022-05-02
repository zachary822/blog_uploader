import mimetypes
import shutil
from typing import BinaryIO
from pathlib import Path
from functools import partial

import gridfs
from pymongo.database import Database

from blog_uploader.image_uploaders import ImageUploader
from hashlib import md5


class GridFsUploader(ImageUploader):
    URL = "https://api.thoughtbank.app/images/{object_id}/"

    def __init__(self, db: Database, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
        self.fs = gridfs.GridFS(self.db)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def upload(self, file: BinaryIO) -> str:
        mime_type, _ = mimetypes.guess_type(file.name)
        filename = Path(file.name).name

        h = md5()
        loc = file.tell()
        for chunk in iter(partial(file.read, 1024), b""):
            h.update(chunk)
        md5_hash = h.hexdigest()
        file.seek(loc)

        f = self.fs.find_one({"metadata.md5": md5_hash})

        if f is not None:
            return self.URL.format(object_id=f._id)

        with self.fs.new_file(
            content_type=mime_type, filename=filename, metadata={"md5": md5_hash}
        ) as g:
            shutil.copyfileobj(file, g)
            return self.URL.format(object_id=g._id)
