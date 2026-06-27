# Response is for manipulating res from server side
from fastapi import FastAPI, Response, status, HTTPException
from fastapi.params import Body
from pydantic import BaseModel
from typing import Optional
# for generating random id for new post, cuz normally its handled by db, but for now we dont have db
from random import randrange
# for loading env variables from .env file
from pydantic_settings import BaseSettings
import psycopg2  # PostgreSQL adapter for Python
# to get the result of the query in dict format rather than tuple format
from psycopg2.extras import RealDictCursor
from pathlib import Path  # for getting the abs path
import time  # for adding delay in db connection retry


app = FastAPI()


# setting up env variables using pydantic's BaseSettings class
BASE_DIR = Path(__file__).resolve().parent  # basedir will be my_fast_api/app


class Settings(BaseSettings):
    # Pydantic will automatically look for an env var named DATABASE_PASSWORD in .env
    database_password: str
    database_username: str = "postgres"  # default fallback value

    class Config:
        # ABSOLUTE PATH to the .env file cuz running uvicorn daemon from different path in terminal will cause issue
        env_file = BASE_DIR/".env"


# create an instance of the Settings class to access the env variables
settings = Settings()
db_pass = settings.database_password
db_user = settings.database_username

while True:
    try:
        # the host part is always the the ip addr of where the db is hosted
        # realdictcursor helps to give the values along with their coln names, which psycopg2 provides only values but not coln names by default
        conn = psycopg2.connect(host='localhost', database='fastapi',
                                user=db_user, password=db_pass, cursor_factory=RealDictCursor)
        # cursor is like a pointer to the db, which helps us to execute queries and fetch results from the db
        cursor = conn.cursor()
        print("Database connection was successful")
        break  # on successful connection, otherwise keep trying to connect to the db in case of failure, so that the app does not crash
    except Exception as e:
        print(f"Database connection failed, error: {e}")
        time.sleep(5)  # wait for 5 seconds before retrying

# api dev starting:


class Post(BaseModel):
    title: str
    content: str
    published: bool = True  # default value
    # rating: Optional[int] = None #import Optional from "typing" module


my_posts = [{"title": "title of post 1", "content": "content of post 1", "id": 1}, {"title":
                                                                                    "favorite foods", "content": "i like pizza", "id": 2}]


def find_post(id):
    for p in my_posts:
        if p["id"] == id:
            return p


def find_index_post(id):
    # enumerate() returns both index and value of the iterable,
    for i, p in enumerate(my_posts):
        # What enumerate(my_posts) looks like under the hood:
        # [
        #     (0, {"title": "Post 1"}),
        #     (1, {"title": "Post 2"})
        # ]
        if p["id"] == id:
            return i


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/posts")
def get_posts():
    # the my_posts array is auto serialized into json format by fastapi
    return {"data": my_posts}
# though dict may seem like json obj, but its actually complex python obj, so serializing dict into json string is required via json.dumps() which is auto handled by fastapi

# using Body param from fastapi
# @app.post("/createposts")
# def create_post(payload: dict = Body(...)): #make sure to import Body from fastapi.params
#     # the "..." is a marker telling FastAPI: "The user cannot leave this body blank. If they send a request without a body, block it and return a 422 Unprocessable Entity error."
#     print(payload)
#     return {"new_post": f"Title: {payload['title']}, Content: {payload['description']}"}
# payload in postman:
# {
#     "title": "Top beaches in Florida",
#     "description": "check out these awesome beaches"
# }

# using pydantic's base model to validate the request body


# provide 201 for creation, good practice
@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(payload: Post):  # now payload is an instance of the Post class
    post_dict = payload.model_dump()  # to convert the payload to a dictionary
    post_dict["id"] = randrange(0, 1000000)  # generate random id for new post
    my_posts.append(post_dict)
    return {"data": post_dict}
# paylod's structure: title str, content str, published bool, rating Optional[int]

# VVI NOTE: order of api routes matters (fastapi has top down apprach),
# if this /posts/latest fn defn was below the /posts/{id} then the fastapi would take "latest" as path parameter
# rather than actual route making id: int validation wrong, so the /posts/latest route should be defined before the /posts/{id} route


@app.get("/posts/latest")
def get_latest_post():
    post = my_posts[len(my_posts) - 1]
    return {"latest_post": post}

# getting single post

# @app.get("/posts/{id}") #the id is the path parameter
# def get_post(id): #fastapi auto extracts the path param and pass it to fn's arg
#     # print(type(id)) -> <class 'str'> ,note the path parameter is always recieved as a string, so convert it into int before comparing with the id in my_posts
#     post = find_post(int(id))
#     return {"post_detail": post}

# better way of getting single post:


@app.get("/posts/{id}")
# here the pydantic model enforces, converts and validates the id type, so we dont have to worry about path params validation
def get_post(id: int, res: Response):
    post = find_post(id)
    if not post:
        # res.status_code = status.HTTP_404_NOT_FOUND #aka literally int 404, "status" is imported from fastapi
        # return {"message": f"post with id: {id} was not found"}
        # OR
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} was not found")
    else:
        return {"post_detail": post}

# @app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT) #204 is for successful deletion, good practice
# def delete_post(id: int):
#     post = find_post(id)
#     if not post:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} could not be deleted since its not found")
#     else:
#         print( my_posts)
#         my_posts.remove(post)
#         print(my_posts)
#         # return {"message": f"post with id: {id} has been deleted"} cuz the 204 mandates res body to be empty, and makes the body empty forcefully even if we have returned some body
#         return

# another method of deleting


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int):
    index = find_index_post(id)
    if index == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} could not be deleted since its not found")
    else:
        # pop removes the element and returns it back to us
        my_posts.pop(index)
        return


@app.put("/posts/{id}")
def update_post(id: int, post: Post):
    index = find_index_post(id)
    if index == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} could not be updated since its not found")
    else:
        post_dict = post.model_dump()
        # cuz Post instance of pydantic model does not have id field, so we need to add it manually to make it compatible with our my_posts
        post_dict["id"] = id
        print(my_posts[index])
        my_posts[index] = post_dict
        print(my_posts[index])
        return {"message": f"post with id: {id} has been updated"}
