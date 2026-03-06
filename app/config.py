from typing import Union, List
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic.functional_validators import field_validator


# @lru_cache()
def get_settings():
    return Settings()


class Settings(BaseSettings):
    query_max_limit_by_http: int = 1000
    request_timeout: int = 300
    api_host: str = Field(default="http://localhost", description="API outbound", env="API_HOST")
    api_port: int = Field(default=9000, env="API_PORT")
    env: str = Field(default="local", description="environment name")
    allow_origins: Union[str, List] = Field(default=["*"])
    allow_methods: Union[str, List] = Field(default=["*"])
    allow_headers: Union[str, List] = Field(default=["*"])
    allow_credentials: bool = True

    sqlalchemy_pool_recycle: int = Field(default=600)
    common_db_name: str = Field("common", env='COMMON_DB_NAME')

    # MySQL DB info
    mysql_url_format: str = Field(
        '{driver}://{user}:{password}@{host}:{port}/{database}?charset={charset}',
        env='MYSQL_URL_FORMAT'
    )
    mysql_driver: str = Field("mysql", env='MYSQL_DRIVER')
    mysql_user: str = Field("", env='MYSQL_USER')
    mysql_password: str = Field("", env='MYSQL_PASSWORD')
    mysql_host: str = Field("", env='MYSQL_HOST')
    mysql_port: int = Field(3306, env='MYSQL_PORT')
    mysql_database: str = Field("", env='MYSQL_DATABASE')
    mysql_charset: str = Field("utf8", env='MYSQL_CHARSET')

    # DB connection pool settings
    db_pool_size: int = Field(40, env='DB_POOL_SIZE')        # Persistent connections
    db_max_overflow: int = Field(10, env='DB_MAX_OVERFLOW')  # Extra temporary connections
    db_pool_timeout: int = Field(10, env='DB_POOL_TIMEOUT')  # Wait time (seconds) for a connection

    aws_secret_access_key: str = Field("", env="AWS_SECRET_ACCESS_KEY")
    aws_access_key_id: str = Field("", env="AWS_ACCESS_KEY_ID")
    default_region: str = Field("", env="DEFAULT_REGION")
    upload_bucket: str = Field(0, env='UPLOAD_BUCKET')

    class Config:
        # Load .env file
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator(
        "allow_origins",
        "allow_methods",
        "allow_headers",
        mode="before",
    )
    @classmethod
    def split_comma_string(cls, val):
        if isinstance(val, str):
            return [item.strip() for item in val.split(",")]
        return val
    

settings = Settings()
