from pydantic import BaseModel, EmailStr
from datetime import datetime

class PostBase(BaseModel):
    title: str
    content: str
    published: bool = True 

#for sending req body from browser to fastapi server
#here these title content and published will be send to db that appends that along with other attributes like id, createdat
class PostCreate(PostBase):
    pass

class PostUpdate(PostBase): # we can add additional things if we want
    pass

#for sending res body from fastapi server to browser
# since we dont want to send id and createdat to browser, we will create this class that has only title, content and published
class PostRespond(PostBase): 
    created_at: datetime

class UserBase(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr 
    created_at: datetime

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
