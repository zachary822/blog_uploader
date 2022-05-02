import abc
import os
from contextlib import AbstractContextManager
from pathlib import Path
from typing import BinaryIO, Union


class ImageUploader(AbstractContextManager):
    @abc.abstractmethod
    def upload(self, file: BinaryIO) -> str:
        ...

    def remove(self, path: Union[str, Path, os.PathLike], *args, **kwargs) -> None:
        ...
