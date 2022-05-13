from typing import Optional

from pydantic import AnyUrl, BaseSettings, SecretStr


class MongoDsn(AnyUrl):
    allowed_schemes = {"mongodb", "mongodb+srv"}


class Settings(BaseSettings):
    mongodb_uri: MongoDsn
    imgur_client_id: Optional[str]
    imgbb_api_key: Optional[SecretStr]
    aws_access_key_id: Optional[SecretStr]
    aws_secret_access_key: Optional[SecretStr]
    s3_bucket: Optional[str]

    class Config:
        env_file = ".env"


settings = Settings()
