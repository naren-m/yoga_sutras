from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

def pk():
    """Define a simple integer primary key."""
    return Column(Integer, primary_key=True, autoincrement=True)

def foreign_key(field: str, nullable=False):
    """Define a simple foreign key."""
    return Column(Integer, ForeignKey(field), nullable=nullable, index=True)
