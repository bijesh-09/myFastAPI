from fastapi import status, HTTPException, Depends, APIRouter
from app import pydantic_schemas, models
from app.database import get_db
from app.utils import hash_pwd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=pydantic_schemas.UserCreate)
def create_user(user_payload: pydantic_schemas.UserBase, db: Session = Depends(get_db)):

    # Hash the password before storing it in the database
    user_payload.password = hash_pwd(user_payload.password)

    new_user = models.User(**user_payload.model_dump())
    db.add(new_user)
    try:
        db.flush()
        db.commit()
        db.refresh(new_user)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User with this email: {user_payload.email} already exists.")
    return new_user

@router.get("/{id}", status_code=status.HTTP_200_OK, response_model=pydantic_schemas.UserGet)
def get_user(id: int, db:Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"user with id: {id} was not found")
    else:
        return user