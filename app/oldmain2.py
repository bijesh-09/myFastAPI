# Response is for manipulating res from server side
from fastapi import FastAPI, Response, status, HTTPException
from fastapi.params import Body
from pydantic_settings import BaseSettings
import psycopg2 
from psycopg2.extras import RealDictCursor
from pathlib import Path 

#setting up orm
from app import models, pydantic_schemas #note this app is the ./app/ dir as a package due to __init__.py, not the instance of FastAPI() file in it. so we can import models.py from it
from app.database import engine, get_db
from fastapi import Depends
from sqlalchemy.orm import Session

#creates all the tables in the db if they dont exist already, note all the tables we defined in models.py belongs to metadata of Base class
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# dont need this if using orm
# setting up env variables using pydantic's BaseSettings class
BASE_DIR = Path(__file__).resolve().parent  # basedir will be my_fast_api/app
class Settings(BaseSettings):
    database_password: str
    database_username: str = "postgres" 
    database_host: str = "localhost"
    database_name: str = "fastapi" 

    class Config:
        env_file = BASE_DIR/".env"

settings = Settings()
db_pass = settings.database_password
db_user = settings.database_username
db_host = settings.database_host
db_name = settings.database_name


try:
    conn = psycopg2.connect(host=db_host, database=db_name,
                            user=db_user, password=db_pass, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("Database connection was successful")
except Exception as e:
    print(f"Database connection failed, error: {e}")


# api dev starting: 


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/posts", response_model=list[pydantic_schemas.PostRespond]) #our Postrespond class is only for single dict , but we are returning list of dicts
def get_posts():
    cursor.execute(""" SELECT * FROM posts """)
    posts = cursor.fetchall()
    return posts

# provide 201 for creation, good practice
@app.post("/posts", status_code=status.HTTP_201_CREATED, response_model=pydantic_schemas.PostRespond) #response_model is for sending res body to browser
def create_post(payload: pydantic_schemas.PostCreate, db: Session = Depends(get_db)):  # now payload is an instance of the Post class

    # NOTE THE fstring one in below line is technically correct but prone to SQL injection
    # cursor.execute(f"INSERT INTO posts (title, content, published) VALUES ('{post.title}', '{post.content}', {post.published}) RETURNING *") #using '' for post.title and content cuz they can be spaced strings and python expects strings inside ''
    #eg:
    # {
    #     "title": "hacked','',true );DROP TABLE posts; --",
    #     "content": ""
    # }

    #use below line , cuz psycopg2 auto sanitizes the input values and prevents SQL injection 
    # cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING *""", (post.title, post.content, post.published))
    # new_post = cursor.fetchone()
    # conn.commit() #cursor.execute happens in TRANSACTION wrapper, so we need to commit it to make changes in db
    # return {"data": new_post}

    # new_post = models.Post(title=post.title, content=post.content, published=post.published) # this is inefficient in case of high no. of fields in models

    # NOTE the new_post will have only the fields of the Post orm model that is present in payload's body
    new_post = models.Post(**payload.model_dump()) # ** is for unpacking the dict and assigning it to resspective fields
    db.add(new_post)    
    db.flush() #sends query into tx
    db.commit() #sends tx into hardrive
    db.refresh(new_post) #this will update our old instance with only payload's body field into a full instance stored as in db
    return new_post #note here new_post is an orm model instance not a pydantic model, but pydanticv2 is smart and auto converts it into pydantic model dict 



@app.get("/posts/{id}", response_model=pydantic_schemas.PostRespond)
def get_post(id: int, db:Session = Depends(get_db)): 
    # cursor.execute(""" SELECT * FROM posts WHERE id = %s""", (str(id),))
    # post = cursor.fetchone()

    post = db.query(models.Post).filter(models.Post.id == id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} was not found")
    else:
        return post


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db:Session = Depends(get_db)):

    # cursor.execute(""" DELETE FROM posts WHERE id = %s RETURNING *""", (str(id),))
    # deleted_post = cursor.fetchone() #note if there is no RETURNING... in query then DELETE query wont return anything causing internal server error
    # conn.commit() #make sure to commit whenever there are changes to be made in db

    # Method1 query level delete best for bulk querying
    deleted_post_query = db.query(models.Post).filter(models.Post.id == id)

    if deleted_post_query.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} could not be deleted since its not found")
    else:
        deleted_post_query.delete(synchronize_session=False)
        db.commit()
        return #empty since 204 mandates empty res body

    # METHOD2 instance level delete best for single item delete
    # deleted_post = db.query(models.Post).filter(models.Post.id == id).first()

    # if deleted_post is None:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
    #                         detail=f"post with id: {id} could not be deleted since its not found")
    # else:
    #     db.delete(deleted_post)
    #     db.commit()
    #     return #empty since 204 mandates empty res body

@app.put("/posts/{id}", response_model=pydantic_schemas.PostRespond)
def update_post(id: int, payload: pydantic_schemas.PostUpdate, db: Session = Depends(get_db)):
    
    # cursor.execute("""UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING * """,
    #                (post.title, post.content, post.published, str(id)))
    # updated_post = cursor.fetchone()
    # if cursor.rowcount > 1:
    #     print("Whoa! The query tried to update the whole database. Rolling back!")
    #     conn.rollback()
    #     raise HTTPException(status_code=500, detail="Database safety trigger tripped.")

    post_query = db.query(models.Post).filter(models.Post.id == id)

    post = post_query.first()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} could not be updated since its not found")
    else:
        post_query.update(payload.model_dump(), synchronize_session=False)
        db.commit()
        # db.refresh(payload) ts wont work cuz db.refresh only works with orm models not pydantic models
        return post_query.first()
