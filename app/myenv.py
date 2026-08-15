from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent  # basedir will be my_fast_api/app


class Settings(BaseSettings):
    database_password: str
    database_username: str = "postgres"
    database_host: str = "localhost"
    database_name: str = "fastapi"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    #this is depricated
    class Config:
        env_file = BASE_DIR/".env"

    # model_config = SettingsConfigDict(env_file=BASE_DIR/".env", extra="ignore")

settings = Settings()