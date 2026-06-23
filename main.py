from fastapi import FastAPI
from fastapi.params import Body
from pydantic import BaseModel
from typing import Optional

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/posts")
def get_posts():
    return {"data": "This is a list of posts"}

#using Body param from fastapi
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

#using pydantic's base model to validate the request body
class Post(BaseModel):
    title: str
    content: str
    published: bool = True #default value
    rating: Optional[int] = None #import Optional from "typing" module

@app.post("/createposts")
def create_post(payload: Post): #now payload is an instance of the Post class
    print(payload)
    print(payload.model_dump()) #to convert the payload to a dictionary
    return {"data": f"{payload}"}
# paylod's structure: title str, content str, published bool, rating Optional[int]