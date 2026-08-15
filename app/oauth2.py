from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.pydantic_schemas import TokenData
from app import models
from app.database import get_db
from fastapi import Depends, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.myenv import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def create_access_token(data: dict):
    to_encode = data.copy()

    issued_at = datetime.now()
    expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    to_encode.update({"iat": issued_at})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str, credentials_exception):

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        id: str = payload.get("sub")

        if id is None:
            raise credentials_exception
        else:
            token_data = TokenData(id=id)
            return token_data
    except JWTError as e:
        print(e)
        raise credentials_exception


def get_current_user(token: str = Depends(oauth2_scheme), db:Session = Depends(get_db)):

    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

    token_data_instance = verify_access_token(token=token, credentials_exception=credentials_exception)

    user = db.query(models.User).filter(token_data_instance.id == models.User.id).first()

    return user 
