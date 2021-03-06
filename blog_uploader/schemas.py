from datetime import datetime
from enum import Enum
from typing import Callable, Iterable, Optional, Union

from bson.objectid import ObjectId as _ObjectId
from pydantic import AnyHttpUrl, BaseModel, Field, FilePath


class ObjectId(_ObjectId):
    @classmethod
    def __get_validators__(
        cls,
    ) -> Iterable[Callable[[Union[str, bytes, "ObjectId"]], "ObjectId"]]:
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, bytes, "ObjectId"]) -> "ObjectId":
        return cls(v)


class MongoModel(BaseModel):
    id: ObjectId = Field(alias="_id", default_factory=ObjectId)

    class Config:
        allow_population_by_field_name = False


class Post(MongoModel):
    title: str
    created: datetime
    body: str
    published: bool = False


class Image(MongoModel):
    path: FilePath
    url: AnyHttpUrl
    delete_key: str
    post_id: Optional[ObjectId]


class Metadata(BaseModel):
    id: ObjectId


class Action(str, Enum):
    create = "create"
    upload = "upload"
    publish = "publish"
    delete = "delete"

    def __str__(self) -> str:
        return self.value
