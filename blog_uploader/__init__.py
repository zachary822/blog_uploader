import logging
import os
import subprocess
from datetime import datetime
from functools import singledispatch
from pathlib import Path
from typing import Optional, Union

import lxml.etree as etree
import pendulum
import yaml
from lxml.html import fragments_fromstring
from pendulum.tz.timezone import Timezone

from blog_uploader.exceptions import PostException
from blog_uploader.image_uploaders import ImageUploader
from blog_uploader.schemas import Metadata, Post

logger = logging.getLogger(__name__)

LOCAL_TZ = pendulum.timezone("America/New_York")


def markdown_to_fragments(file: Union[str, os.PathLike[str]]) -> list[etree.Element]:
    with subprocess.Popen(
        ["pandoc", "--no-highlight", "-f", "gfm", "-t", "html-auto_identifiers"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        encoding="utf8",
    ) as p, open(file, "r") as f:
        output, error = p.communicate(f.read())

    return fragments_fromstring(output)


def process_fragments(
    file: Union[str, os.PathLike[str]]
) -> tuple[Metadata, etree.Element, list[etree.Element]]:
    fragments = markdown_to_fragments(file)

    if fragments[0].tag is etree.Comment:
        _metadata, title, *fragments = fragments
        metadata = Metadata(**(yaml.load(_metadata.text, Loader=yaml.SafeLoader) or {}))
    else:
        raise PostException("No id")

    if title.tag != "h1":
        raise PostException("No title")

    return metadata, title, fragments


@singledispatch
def serialize_element(ele):
    return etree.tounicode(ele)


@serialize_element.register
def _(ele: str):
    return ele


def fragments_to_markdown(fragments: list[etree.Element]) -> str:
    body = "".join(map(serialize_element, fragments))

    with subprocess.Popen(
        ["pandoc", "-f", "html+raw_html", "-t", "gfm"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        encoding="utf8",
    ) as p:
        output, error = p.communicate(body)

    return output


def get_mtime(
    file: Union[str, os.PathLike[str]], *, tz: Timezone = LOCAL_TZ
) -> datetime:
    s = os.stat(file)
    return pendulum.from_timestamp(s.st_mtime, tz=tz)


def markdown_to_doc(
    file: Union[str, os.PathLike[str]],
    *,
    image_uploader: Optional[ImageUploader] = None,
    timezone: Timezone = LOCAL_TZ
) -> Post:
    metadata, title, fragments = process_fragments(file)

    md_path = Path(file)

    if image_uploader is not None:
        for img in title.xpath("//img"):
            with open(md_path.parent / img.attrib["src"], "rb") as f:
                img.attrib["src"] = image_uploader.upload(f)

    mtime = get_mtime(file, tz=timezone)
    body = fragments_to_markdown(fragments)

    return Post(title=title.text_content(), created=mtime, body=body, _id=metadata.id)
