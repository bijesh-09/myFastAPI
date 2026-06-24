from fastapi import FastAPI, Response, status, HTTPException #Response is for manipulating res from server side
from fastapi.params import Body
from pydantic import BaseModel
from typing import Optional
from random import randrange #for generating random id for new post, cuz normally its handled by db, but for now we dont have db

app = FastAPI()

class Post(BaseModel):
    title: str
    content: str
    published: bool = True #default value
    rating: Optional[int] = None #import Optional from "typing" module

my_posts = [{"title": "title of post 1", "content": "content of post 1", "id": 1}, {"title":
"favorite foods", "content": "i like pizza", "id": 2}]

def find_post(id):
    for p in my_posts:
        if p["id"] == id:
            return p

def find_index_post(id):
    for i,p in enumerate(my_posts): #enumerate() returns both index and value of the iterable, 
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
    return {"data": my_posts} #the my_posts array is auto serialized into json format by fastapi
# though dict may seem like json obj, but its actually complex python obj, so serializing dict into json string is required via json.dumps() which is auto handled by fastapi

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

@app.post("/posts", status_code=status.HTTP_201_CREATED) #provide 201 for creation, good practice
def create_post(payload: Post): #now payload is an instance of the Post class
    post_dict = payload.model_dump() #to convert the payload to a dictionary
    post_dict["id"] = randrange(0, 1000000) #generate random id for new post
    my_posts.append(post_dict) 
    return {"data": post_dict}
# paylod's structure: title str, content str, published bool, rating Optional[int]

#VVI NOTE: order of api routes matters (fastapi has top down apprach),
#if this /posts/latest fn defn was below the /posts/{id} then the fastapi would take "latest" as path parameter
#rather than actual route making id: int validation wrong, so the /posts/latest route should be defined before the /posts/{id} route
@app.get("/posts/latest")
def get_latest_post():
    post = my_posts[len(my_posts) - 1]
    return {"latest_post": post}

#getting single post

# @app.get("/posts/{id}") #the id is the path parameter
# def get_post(id): #fastapi auto extracts the path param and pass it to fn's arg
#     # print(type(id)) -> <class 'str'> ,note the path parameter is always recieved as a string, so convert it into int before comparing with the id in my_posts
#     post = find_post(int(id))
#     return {"post_detail": post}

# better way of getting single post:
@app.get("/posts/{id}") 
def get_post(id: int, res: Response): #here the pydantic model enforces, converts and validates the id type, so we dont have to worry about path params validation
    post = find_post(id)
    if not post:
        # res.status_code = status.HTTP_404_NOT_FOUND #aka literally int 404, "status" is imported from fastapi
        # return {"message": f"post with id: {id} was not found"}
        # OR
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")
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

#another method of deleting
@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT) 
def delete_post(id: int):
    index = find_index_post(id)
    if index == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} could not be deleted since its not found")
    else:
        my_posts.pop(index) #pop removes the element and returns it back to us
        return

@app.put("/posts/{id}")
def update_post(id: int, post: Post):
    index = find_index_post(id)
    if index == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} could not be updated since its not found")
    else:
        post_dict = post.model_dump()
        post_dict["id"] = id #cuz Post instance of pydantic model does not have id field, so we need to add it manually to make it compatible with our my_posts 
        print(my_posts[index])
        my_posts[index] = post_dict
        print(my_posts[index])
        return {"message": f"post with id: {id} has been updated"}