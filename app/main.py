# Response is for manipulating res from server side
from fastapi import FastAPI

#setting up orm
from app import models #note this app is the ./app/ dir as a package due to __init__.py, not the instance of FastAPI() file in it. so we can import models.py from it
from app.database import engine
from app.routers import post, user, auth, vote

#creates all the tables in the db if they dont exist already, note all the tables we defined in models.py belongs to metadata of Base class
try:
    models.Base.metadata.create_all(bind=engine)
    print("Tables creation  for models that didn't existed was successful")
except Exception as e:
    print(f"Tables creation failed, error: {e}")

#instantiating FastAPI class, this is the main instance of the app
app = FastAPI()

# api dev starting: 

@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(vote.router)