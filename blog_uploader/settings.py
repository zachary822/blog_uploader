from typing import Optional

from pydantic import AnyUrl, BaseSettings


class MongoDsn(AnyUrl):
    allowed_schemes = {"mongodb", "mongodb+srv"}


class Settings(BaseSettings):
    mongodb_uri: MongoDsn
    imgur_client_id: Optional[str]
    imgbb_api_key: Optional[str]
    aws_access_key_id: Optional[str]
    aws_secret_access_key: Optional[str]
    s3_bucket: Optional[str]

    class Config:
        env_file = ".env"


settings = Settings()
