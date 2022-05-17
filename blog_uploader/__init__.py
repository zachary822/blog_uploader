import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

import pendulum
from pandocfilters import Image, stringify, walk
from pendulum.tz.timezone import Timezone

from blog_uploader.embedders import codepen_iframe, replit_iframe, youtube_iframe
from blog_uploader.exceptions import PostException
from blog_uploader.image_uploaders import ImageUploader
from blog_uploader.schemas import Metadata, Post

logger = logging.getLogger(__name__)

LOCAL_TZ = pendulum.timezone("America/New_York")


def markdown_to_ast(file: Union[str, os.PathLike[str]]) -> dict:
    with open(file, "rb") as f, subprocess.Popen(
        [
            "pandoc",
            "--no-highlight",
            "-f",
            "gfm",
            "-t",
            "json",
        ],
        stdin=f,
        stdout=subprocess.PIPE,
    ) as p:
        output, error = p.communicate()
        return json.loads(output)


def process_doc(file: Union[str, os.PathLike[str]]) -> tuple[dict, str, dict]:
    doc = markdown_to_ast(file)
    meta = doc["meta"]

    title_block = doc["blocks"][0]

    if title_block["t"] != "Header" and title_block["c"][0] != 1:
        raise PostException("No title")

    title = stringify(title_block)

    return meta, title, doc


def doc_to_markdown(doc: dict) -> str:
    with subprocess.Popen(
        [
            "pandoc",
            "-f",
            "json",
            "-t",
            "gfm",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        encoding="utf8",
    ) as p:
        output, error = p.communicate(json.dumps(doc))

    return output


def get_mtime(
    file: Union[str, os.PathLike[str]], *, tz: Timezone = LOCAL_TZ
) -> datetime:
    s = os.stat(file)
    return pendulum.from_timestamp(s.st_mtime, tz=tz)


def embed(key, value, format, meta):
    if key == "Link":
        parse_result = urlparse(value[2][0])
        match parse_result.netloc:
            case "www.youtube.com":
                return youtube_iframe(parse_result)
            case "replit.com":
                return replit_iframe(parse_result)
            case "codepen.io":
                return codepen_iframe(parse_result)
            case _:
                return None


def markdown_to_doc(
    file: Union[str, os.PathLike[str]],
    *,
    image_uploader: Optional[ImageUploader] = None,
    timezone: Timezone = LOCAL_TZ,
) -> Post:
    meta, title, doc = process_doc(file)

    try:
        metadata = Metadata(id=stringify(meta["id"]))
    except KeyError as e:
        raise

    md_path = Path(file)

    if image_uploader is not None:

        def _uploader(key, value, format, meta):
            if key == "Image":
                with open(md_path.parent / value[2][0], "rb") as f:
                    url = image_uploader.upload(f)

                return Image(*value[:2], [url, ""])

        doc = walk(doc, _uploader, "", meta)

    doc = walk(doc, embed, "", meta)

    mtime = get_mtime(file, tz=timezone)
    body = doc_to_markdown(doc)

    return Post(
        title=title,
        created=mtime,
        body=body,
        _id=metadata.id,
    )
