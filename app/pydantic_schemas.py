from pydantic import BaseModel, EmailStr, StringConstraints
from datetime import datetime
from typing import Literal, Annotated

class PostBase(BaseModel):
    id: int | None = None
    title: str
    content: str
    published: bool

#for sending req body from browser to fastapi server
#here these title content and published will be send to db that appends that along with other attributes like id, createdat
NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
class PostCreate(BaseModel):
    title: NonEmptyStr
    content: NonEmptyStr
    published: bool = True

class PostUpdate(BaseModel): # we can add additional things if we want
    title: NonEmptyStr
    content: NonEmptyStr
    published: bool = True

class UserCreate(BaseModel):
    id: int
    email: EmailStr 
    created_at: datetime

#for sending res body from fastapi server to browser
# since we dont want to send id and createdat to browser, we will create this class that has only title, content and published
class PostRespond(PostBase): 
    created_at: datetime
    owner_id: int
    owner: UserCreate

class PostWithVotes(BaseModel):
    Post: PostRespond
    votes: int


class UserBase(BaseModel):
    email: EmailStr
    password: str


class UserGet(UserCreate):
    id: int

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: str | None = None

class Vote(BaseModel):
    post_id: int
    dir: Literal[0, 1]  # making values strictly 0 or 1