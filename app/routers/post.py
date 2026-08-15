from fastapi import status, HTTPException, Depends, APIRouter
from app import pydantic_schemas, models
from app import oauth2 
from sqlalchemy.orm import Session
from app.database import get_db
from typing import Optional

router = APIRouter(prefix="/posts", tags=["Posts"])

@router.get("/", response_model=list[pydantic_schemas.PostRespond]) #our Postrespond class is only for single dict , but we are returning list of dicts
def get_posts(db:Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user),
              limit: int = 5, skip: int = 0, search: Optional[str] = ""): #here limit, skip and search are custome made query parameter
    posts = db.query(models.Post).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()
    return posts

# provide 201 for creation, good practice
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=pydantic_schemas.PostRespond) #response_model is for sending res body to browser
def create_post(payload: pydantic_schemas.PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):  # now payload is an instance of the Post class

    # NOTE the new_post will have only the fields of the Post orm is present in payload's body
    new_post = models.Post(owner_id=current_user.id, **payload.model_dump()) # ** is for unpacking the dict and assigning it to resspective fields
    db.add(new_post)    
    db.flush() #sends query into tx
    db.commit() #sends tx into hardrive
    db.refresh(new_post) #this will update our old instance with only payload's body field into a full instance stored as in db
    return new_post #note here new_post is an orm instance not a pydantic, but pydanticv2 is smart and auto converts it into pydantic dict 



@router.get("/{id}", response_model=pydantic_schemas.PostRespond)
def get_post(id: int, db:Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)): 

    post = db.query(models.Post).filter(models.Post.id == id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} was not found")
    else:
        return post


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db:Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    # Method1 query level delete best for bulk querying
    deleted_post_query = db.query(models.Post).filter(models.Post.id == id)

    if deleted_post_query.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} could not be deleted since its not found")

    to_be_deleted_post = deleted_post_query.first()
    if to_be_deleted_post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Not authorized to perform requested action")
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

@router.put("/{id}", response_model=pydantic_schemas.PostRespond)
def update_post(id: int, payload: pydantic_schemas.PostUpdate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    post_query = db.query(models.Post).filter(models.Post.id == id)

    post = post_query.first()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} could not be updated since its not found")

    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Not authorized to perform requested action")
    else:
        post_query.update(payload.model_dump(), synchronize_session=False)
        db.commit()
        # db.refresh(payload) ts wont work cuz db.refresh only works with orm models not pydantic models
        return post_query.first()