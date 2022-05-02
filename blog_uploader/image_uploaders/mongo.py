from abc import ABC
from pathlib import Path, PosixPath

from bson.codec_options import TypeEncoder, TypeRegistry


class PathEncoder(TypeEncoder, ABC):
    def transform_python(self, value: Path) -> str:
        return str(value)


class PosixPathEncoder(PathEncoder):
    python_type = PosixPath


type_registry = TypeRegistry([PosixPathEncoder()])
