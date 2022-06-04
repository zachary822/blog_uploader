import json
import logging
import os
import subprocess
from datetime import datetime
from functools import partial, reduce
from typing import Callable, Optional, Union

import orjson
import pendulum
from pandocfilters import stringify, walk
from pendulum.tz.timezone import Timezone

from blog_uploader.bionic.public import Bionic
from blog_uploader.embedders import Embedder
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
        stderr=subprocess.PIPE,
    ) as p:
        output, error = p.communicate()
        if p.returncode != 0:
            raise PostException(error)
        return orjson.loads(output)


def process_doc(file: Union[str, os.PathLike[str]]) -> tuple[dict, str, dict]:
    doc = markdown_to_ast(file)
    meta = doc["meta"]

    title_block = doc["blocks"].pop(0)

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
        stderr=subprocess.PIPE,
        encoding="utf8",
    ) as p:
        output, error = p.communicate(json.dumps(doc))

        if p.returncode != 0:
            raise PostException(error)

    return output


def get_mtime(
    file: Union[str, os.PathLike[str]], *, tz: Timezone = LOCAL_TZ
) -> datetime:
    s = os.stat(file)
    return pendulum.from_timestamp(s.st_mtime, tz=tz)


def markdown_to_doc(
    file: Union[str, os.PathLike[str]],
    *,
    timezone: Timezone = LOCAL_TZ,
    pandoc_filters: Optional[list[Callable]] = None
) -> Post:
    meta, title, doc = process_doc(file)

    try:
        metadata = Metadata(id=stringify(meta["id"]))
    except KeyError as e:
        raise PostException("no id") from e

    if pandoc_filters is not None:
        doc = reduce(partial(walk, format="", meta=meta), pandoc_filters, doc)

    mtime = get_mtime(file, tz=timezone)
    body = doc_to_markdown(doc)

    return Post(
        title=title,
        created=mtime,
        body=body,
        _id=metadata.id,
    )
