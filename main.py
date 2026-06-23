from fastapi import FastAPI
from fastapi.params import Body

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/posts")
def get_posts():
    return {"data": "This is a list of posts"}

@app.post("/createposts")
def create_post(payload: dict = Body(...)): #make sure to import Body from fastapi.params
    # the "..." is a marker telling FastAPI: "The user cannot leave this body blank. If they send a request without a body, block it and return a 422 Unprocessable Entity error."
    print(payload)
    return {"new_post": f"Title: {payload['title']}, Content: {payload['description']}"}
# payload in postman:
# {
#     "title": "Top beaches in Florida",
#     "description": "check out these awesome beaches"
# }