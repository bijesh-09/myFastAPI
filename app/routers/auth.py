from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.pydantic_schemas import UserLogin
from app import models, utils, oauth2, pydantic_schemas

router = APIRouter(tags=['auth'])

@router.post("/login", response_model=pydantic_schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with email: {user_credentials.username} not found")

    # Verify the password
    if not utils.verify_pwd(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    else:
        access_token = oauth2.create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}