from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Float
from sqlalchemy.sql import func
from app.core.database import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(30), unique=True, nullable=False, index=True)   # 검색 최적화
    title = Column(String(255), nullable=False, index=True)
    price = Column(Integer, nullable=False)

    publisher = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)

    publication_date = Column(Date, nullable=True)

    # 현재는 문자열(Text) 기반 but 후기/카테고리 기능 확장 대비 분리 가능
    authors = Column(Text, nullable=True)
    categories = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())   # Date→DateTime
    updated_at = Column(DateTime, onupdate=func.now())

