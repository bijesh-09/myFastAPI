# Response is for manipulating res from server side
from fastapi import FastAPI, Response, status, HTTPException
from fastapi.params import Body
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import psycopg2 
from psycopg2.extras import RealDictCursor
from pathlib import Path 

#setting up orm
from app import models #note this app is the ./app/ dir as a package due to __init__.py, not the instance of FastAPI() file in it. so we can import models.py from it
from app.database import engine, get_db
from fastapi import Depends
from sqlalchemy.orm import Session
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


BASE_DIR = Path(__file__).resolve().parent  # basedir will be my_fast_api/app

# setting up env variables using pydantic's BaseSettings class
class Settings(BaseSettings):
    database_password: str
    database_username: str = "postgres"  

    class Config:
        env_file = BASE_DIR/".env"

settings = Settings()
db_pass = settings.database_password
db_user = settings.database_username


try:
    conn = psycopg2.connect(host='localhost', database='fastapi',
                            user=db_user, password=db_pass, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("Database connection was successful")
except Exception as e:
    print(f"Database connection failed, error: {e}")


# api dev starting:
class Post(BaseModel):
    title: str
    content: str
    published: bool = True  


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/posts")
def get_posts():
    cursor.execute(""" SELECT * FROM posts """)
    posts = cursor.fetchall()
    return {"data": posts}

# provide 201 for creation, good practice
@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(post: Post):  # now payload is an instance of the Post class

    # NOTE THE fstring one in below line is technically correct but prone to SQL injection
    # cursor.execute(f"INSERT INTO posts (title, content, published) VALUES ('{post.title}', '{post.content}', {post.published}) RETURNING *") #using '' for post.title and content cuz they can be spaced strings and python expects strings inside ''
    #eg:
    # {
    #     "title": "hacked','',true );DROP TABLE posts; --",
    #     "content": ""
    # }

    #use below line , cuz psycopg2 auto sanitizes the input values and prevents SQL injection 
    cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING *""", (post.title, post.content, post.published))
    new_post = cursor.fetchone()
    conn.commit() #cursor.execute happens in TRANSACTION wrapper, so we need to commit it to make changes in db
    return {"data": new_post}


@app.get("/posts/{id}")
def get_post(id: int): 
    cursor.execute(""" SELECT * FROM posts WHERE id = %s""", (str(id),))
    post = cursor.fetchone()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} was not found")
    else:
        return {"post_detail": post}


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int):

    cursor.execute(""" DELETE FROM posts WHERE id = %s RETURNING *""", (str(id),))
    deleted_post = cursor.fetchone() #note if there is no RETURNING... in query then DELETE query wont return anything causing internal server error
    conn.commit() #make sure to commit whenever there are changes to be made in db

    if deleted_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} could not be deleted since its not found")
    else:
        return #empty since 204 mandates empty res body


@app.put("/posts/{id}")
def update_post(id: int, post: Post):
    
    cursor.execute("""UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING * """,
                   (post.title, post.content, post.published, str(id)))
    updated_post = cursor.fetchone()
    if cursor.rowcount > 1:
        print("Whoa! The query tried to update the whole database. Rolling back!")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Database safety trigger tripped.")
    elif updated_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} could not be updated since its not found")
    else:
        conn.commit()
        return {"message": updated_post}
