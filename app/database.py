from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings
from pathlib import Path

# NOTE THIS FILE USES SQLALCHEMY ORM OF VERSION 1.4.23

BASE_DIR = Path(__file__).resolve().parent  # basedir will be my_fast_api/app
class Settings(BaseSettings):
    database_password: str
    database_username: str = "postgres"  

    class Config:
        env_file = BASE_DIR/".env"

settings = Settings()
db_pass = settings.database_password
db_user = settings.database_username

# SQLALCHEMY_DATABASE_URL = f"postgresql://<username>:<password>@<ip_addr OR hostname>/<database_name>"
SQLALCHEMY_DATABASE_URL = f"postgresql://{db_user}:{db_pass}@localhost/fastapi"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

