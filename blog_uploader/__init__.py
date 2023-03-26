import json
import logging
import subprocess
from datetime import datetime
from functools import partial, reduce
from pathlib import Path
from typing import Any, Callable, Optional

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


def markdown_to_ast(file: Path) -> dict:
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


def parse_token(obj: dict):
    match obj:
        case {"t": "MetaInlines" | "MetaBlocks", "c": meta_inlines}:
            return stringify(meta_inlines)
        case {"t": "MetaMap", "c": meta_map}:
            return {key: parse_token(value) for key, value in meta_map.items()}
        case {"t": "MetaList", "c": meta_list}:
            return list(map(parse_token, meta_list))
        case {"t": "MetaString", "c": ""}:
            return None
        case _:
            return obj


def parse_meta(meta: dict):
    return {key: parse_token(value) for key, value in meta.items()}


def process_doc(file: Path) -> tuple[dict, str, dict]:
    doc = markdown_to_ast(file)
    meta = doc["meta"]

    title_block = doc["blocks"].pop(0)

    match title_block:
        case {"t": "Header", "c": [1, _, _]}:
            title = stringify(title_block)
        case _:
            raise PostException("No title")

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


def get_mtime(file: Path, *, tz: Timezone = LOCAL_TZ) -> datetime:
    s = file.stat()
    return pendulum.from_timestamp(s.st_mtime, tz=tz)


def markdown_to_doc(
    file: Path,
    *,
    timezone: Timezone = LOCAL_TZ,
    pandoc_filters: Optional[list[Callable]] = None,
) -> Post:
    meta, title, doc = process_doc(file)

    try:
        metadata = Metadata(**parse_meta(meta))
    except KeyError as e:
        raise PostException("no id") from e

    if pandoc_filters is not None:
        doc = reduce(partial(walk, format="", meta=meta), pandoc_filters, doc)

    file_stat = file.stat()
    body = doc_to_markdown(doc)

    return Post(
        title=title,
        created=pendulum.from_timestamp(file_stat.st_birthtime, tz=timezone),
        updated=pendulum.from_timestamp(file_stat.st_mtime, tz=timezone),
        body=body,
        **metadata.dict(),
    )
