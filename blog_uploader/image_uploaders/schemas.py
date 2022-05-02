from pydantic import BaseModel, AnyHttpUrl


class ImgurData(BaseModel):
    link: AnyHttpUrl
    deletehash: str


class ImgurBasicResponse(BaseModel):
    data: ImgurData
    success: bool
    status: int


class ImgbbData(BaseModel):
    id: str
    url: AnyHttpUrl
    delete_url: AnyHttpUrl


class ImgbbResponse(BaseModel):
    data: ImgbbData
    success: bool
    status: int
