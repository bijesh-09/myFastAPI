
#NOTE: EVERY FILES IN CURR DIR WHERE CONFTEST.PY LIES OR NESTED SUB DIRS OF CURR DIR WILL HAVE ACCESS TO FIXTURES DEFINED HERE

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import text
from app.myenv import settings
from app.models import Base
from app.database import get_db
from app.main import app
from app import pydantic_schemas
from app.oauth2 import create_access_token, verify_access_token
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException, status
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


# ----------------------------------------------------------Single user test-----------------------------------------------------
#making test_login_user is now independent of test_create_user
@pytest.fixture
def single_user_fixture(client):
    user_data = {"email": "hello@gmail.com", "password": "hello"}
    res = client.post("/users", json=user_data)
    print(res.json(), res.status_code)
    new_user = res.json()
    new_user['password'] = user_data['password'] #adding password to new_user json so that test_login_user can get access to the password
    assert res.status_code == 201
    return new_user

@pytest.fixture
def token(single_user_fixture):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                              detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    
    token = create_access_token(data={"sub": str(single_user_fixture['id'])})
    verify_access_token(token=token, credentials_exception=credentials_exception)
    return token

@pytest.fixture
def authenticated_client(token, client):
    client.headers = {
        **client.headers, #unpacking all the client(i.e. a req)'s headers
        "Authorization": f"Bearer {token}" #updating the Authorization header with token
    }
    return client

# --------------------------------------------------------------------------------------------------------------------------------------


# -------------------------------------------------------Multi user test-------------------------------------------------------------------

@pytest.fixture
def set_of_users_fixture(client):
    user_data = [
        {"email": "hi@gmail.com", "password": "hi"},
        {"email": "bro@gmail.com", "password": "bro"},
        {"email": "pro@gmail.com", "password": "pro"}
    ]
    created_user = []
    for user in user_data:
        res = client.post("/users", json=user)
        print(res.json(), res.status_code)
        pydantic_schemas.UserCreate(**res.json())
        new_user = res.json()
        # new_user['password'] = user_data['password'] we dont need password since we are using token to verify auth session here
        assert res.status_code == 201
        created_user.append(new_user)
    return created_user

def make_headers(user_id):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                                  detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
        
    token = create_access_token(data={"sub": str(user_id)})
    verify_access_token(token=token, credentials_exception=credentials_exception)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers():
    return make_headers

@pytest.fixture
def create_posts_fixture(set_of_users_fixture, client):
    posts_data = [
        {
            "title": "hi post 1",
            "content": "hi post content",
            "owner_id": set_of_users_fixture[0]['id']
        },
        {
            "title": "hi post 2",
            "content": "hi post content 2",
            "owner_id": set_of_users_fixture[0]['id']
        },
        {
            "title": "bro post",
            "content": "bro post content",
            "owner_id": set_of_users_fixture[1]['id']
        },
        {
            "title": "pro post",
            "content": "pro post content 2",
            "owner_id": set_of_users_fixture[2]['id']
        }
    ]

    posts = []

    for p in posts_data:
        res = client.post("/posts", json={"title": p['title'], "content": p['content']}
                          , headers=make_headers(p['owner_id']))
        print(res.json())
        pydantic_schemas.PostRespond(**res.json())
        post = res.json()
        posts.append(post)

    return posts