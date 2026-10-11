
#NOTE: EVERY FILES IN CURR DIR WHERE CONFTEST.PY LIES OR NESTED SUB DIRS OF CURR DIR WILL HAVE ACCESS TO FIXTURES DEFINED HERE

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import text
from app.myenv import settings
from app.models import Base
from app.database import get_db
from app.main import app
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from alembic.config import Config
from alembic import command

# NOTE THIS FILE USES SQLALCHEMY ORM OF VERSION 1.4.23

db_pass = settings.database_password
db_user = settings.database_username
db_host = settings.database_hostname
db_name = settings.database_name

#MAKING DBNAME = fastapi_test in the same postgres instance as of original db
TEST_SQLALCHEMY_DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}_test" 

try:
    engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL) 
    print("SQLAlchemy test_engine initialized successfully.")
except Exception as e:
    print(f"Failed to initialize SQLAlchemy test_engine (check test_database URL format): {e}")

try:
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("TestingSessionLocal factory created successfully.")
except Exception as e:
    print(f"Failed to create TestingSessionLocal factory, error: {e}")

# Test actual network connection and authentication to PostgreSQL
try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    print("Test_Database authentication and connection test succeeded!")
except Exception as e:
    print(f"CRITICAL: Failed to connect or authenticate with PostgreSQL: {e}")

# app = FastAPI() NEVER CREATE NEW INSTANCE, CUZ IT DOESNT VE THE ROUTES WE DEFINED, USE app FROM THE app.main

# @pytest.fixture(scope="module") # the fixture scope is set to module so that it survives until the last test among all tests ends 
@pytest.fixture #but we want tests run independently of each other. default scope is 'function'
def session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

#this session fn can help later on use session object itself to query in test fns, for eg:
# def test_create_user(client, session):
    # session.query(models.Post.....) 

# to use test db url instead of our real db url
alembic_cfg = Config("alembic.ini")
alembic_cfg.attributes["test_url"] = TEST_SQLALCHEMY_DATABASE_URL 

@pytest.fixture
def client(session):
    # METHOD 1: for creating tables in db
    #drop first before instead of dropping after yield cuz tables would be dropped as soon as test finishes and we wont get to check in db
    # Base.metadata.drop_all(bind=engine)
    # Base.metadata.create_all(bind=engine)

    # METHOD 2: for creating tables in db
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")

    def override_get_db():
            yield session
            # Dont do session.close() cuz its closed by the session()'s db.close
            #if session.close() is written here then the session.query(...) if used in testfns can make conn expire before the tx finishes

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

#making test_login_user is now independent of test_create_user
@pytest.fixture
def test_user(client):
    user_data = {"email": "hello@gmail.com", "password": "hello"}
    res = client.post("/users", json=user_data)
    print(res.json(), res.status_code)
    new_user = res.json()
    new_user['password'] = user_data['password'] #adding password to new_user json so that test_login_user can get access to the password
    assert res.status_code == 201
    return new_user
