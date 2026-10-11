from app import pydantic_schemas
from app.myenv import settings
import pytest
from jose import jwt

#no need to import cuz conftest.py is available
# from tests.dummy_db import client, session # need to import session fixture as well cuz client fixture depends upon it

def test_root(client):
    res = client.get("/")
    print(res.json().get('message'), res.status_code)
    assert res.json().get('message') == 'Hello World'
    assert res.status_code == 200

def test_create_user(client):
    res = client.post("/users", json={"email": "hello@gmail.com", "password": "hello"})
    print(res.json(), res.status_code)
    new_user = pydantic_schemas.UserCreate(**res.json()) #unpack the json to assign it to class vars of UserCreate class
    assert res.json().get('email') == 'hello@gmail.com'
    assert res.status_code == 201

# #NOTE: here test_login_user is now dependent upon another test i.e. test_create_user, which is a bad practice cuz every tests should run independently
# # if the fixture's scope isnt set to module then test_login_user cant find the username in db cuz tables will be destroyed and recreated when fixture runs
# def test_login_user(client):
#     # the body should be of 'form-data' type which is 'data' here, also OAuth2PasswordRequestForm strictly looks for 'usernme' and 'password' keys in payload
#     res = client.post("/login", data={"username": "hello@gmail.com", "password": "hello"})
#     print(res.json(), res.status_code)
#     pydantic_schemas.Token(**res.json()) #for pydantic validation of response model
#     assert res.status_code == 200

#depends upon test_user fixture in conftest.py
def test_login_user(client, test_user):
    # the body should be of 'form-data' type which is 'data' here, also OAuth2PasswordRequestForm strictly looks for 'usernme' and 'password' keys in payload
    res = client.post("/login", data={"username": test_user['email'], "password": test_user['password']})
    print(res.json(), res.status_code)
    
    #for pydantic validation of response model
    login_res = pydantic_schemas.Token(**res.json()) 

    #verifying token 
    payload = jwt.decode(login_res.access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    id = int(payload.get("sub")) #res returns id as str , for eg id 1 as '1'

    assert id == test_user['id']
    assert login_res.token_type == "bearer"
    assert res.status_code == 200

@pytest.mark.parametrize("email, password, status_code", [
    ("wrong@gmail.com", "wrongPassword", 404),
    ("hello@gmail.com", "wrongPassword", 401),
    (None, "wrongPassword", 422) #this will be pydantic validation error
])
def test_incorrect_login(test_user, client, email, password, status_code):
    res = client.post("/login", data={"username": email, "password": password})
    print(res.json(), res.status_code)

    assert res.status_code == status_code