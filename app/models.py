from app.database import Base #note this app is the ./app/ dir as a package due to __init__.py
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Identity, ForeignKey
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship

# NOTE THIS FILE USES SQLALCHEMY ORM OF VERSION 1.4.23

class Post(Base): #every orm models will be extended from Base class. also each models represent db tables
    __tablename__ = "posts"

    id = Column(Integer, Identity(always=True), primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)    
    published = Column(Boolean, server_default=text("TRUE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")) 
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    #note use "users.id" instead of "User.id" because the table name is users and not User
    owner = relationship("User")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, Identity(always=True), primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))