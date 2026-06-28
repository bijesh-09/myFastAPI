from app.database import Base #note this app is the ./app/ dir as a package due to __init__.py
from sqlalchemy import Column, Integer, String, Boolean

# NOTE THIS FILE USES SQLALCHEMY ORM OF VERSION 1.4.23

class Post(Base): #every orm models will be extended from Base class. also each models represent db tables
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean, default=True, nullable=False)
    