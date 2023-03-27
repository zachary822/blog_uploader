from importlib import resources

import yaml
from jinja2 import Template

from blog_uploader.schemas import Metadata, ObjectId

__all__ = ["create_post"]


def object_id_representer(dumper: yaml.Dumper, data: ObjectId) -> yaml.Node:
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


yaml.add_representer(ObjectId, object_id_representer)


TEMPLATE_PATH = resources.files("blog_uploader") / "blog.md.jinja"


def create_post(title: str) -> str:
    with resources.as_file(TEMPLATE_PATH) as p, p.open("r") as f:
        template = Template(f.read())
    metadata = Metadata(id=ObjectId())

    return template.render(metadata=yaml.dump(metadata.dict()), title=title)
