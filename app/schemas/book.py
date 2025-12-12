# app/schemas/book.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class BookCreate(BaseModel):
    isbn: str
    title: str
    price: int
    publisher: Optional[str] = None
    summary: Optional[str] = None
    publicationDate: Optional[date] = None
    authors: Optional[List[str]] = None
    categories: Optional[List[str]] = None

class BookUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[int] = None
    publisher: Optional[str] = None
    summary: Optional[str] = None
    publicationDate: Optional[date] = None
    authors: Optional[List[str]] = None
    categories: Optional[List[str]] = None

class BookResponse(BaseModel):
    id: int
    isbn: str
    title: str
    price: int
    publisher: Optional[str]
    summary: Optional[str]
    publicationDate: Optional[date] = None    # default 없으면 밸리데이션 발생
    authors: Optional[List[str]] = []         # default 추가
    categories: Optional[List[str]] = []

    model_config = {
        "from_attributes": True
    }
