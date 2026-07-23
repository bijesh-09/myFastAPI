from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# NOTE THIS FILE USES SQLALCHEMY ORM OF VERSION 1.4.23

BASE_DIR = Path(__file__).resolve().parent  # basedir will be my_fast_api/app


class Settings(BaseSettings):
    database_password: str
    database_username: str = "postgres"
    database_host: str = "localhost"
    database_name: str = "fastapi"

    #this is depricated
    class Config:
        env_file = BASE_DIR/".env"

    # model_config = SettingsConfigDict(env_file=BASE_DIR/".env", extra="ignore")

settings = Settings()
db_pass = settings.database_password
db_user = settings.database_username
db_host = settings.database_host
db_name = settings.database_name

# SQLALCHEMY_DATABASE_URL = f"postgresql://<username>:<password>@<ip_addr> OR <hostname>/<database_name>"
SQLALCHEMY_DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"

# engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True) # doing echo true is for debugging purpose, it will print all the sql statements in the console

# #do this specifically for sqlite db, cuz it cant handle concurrency
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=={"check_same_thread": False})

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL) 
    print("Database connection was successful")
except Exception as e:
    print(f"Database connection failed, error: {e}")

try:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("Sessionmaker creation was successful")
except Exception as e:
    print(f"Sessionmaker creation failed, error: {e}")
    

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
