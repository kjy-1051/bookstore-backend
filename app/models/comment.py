# app/models/comment.py
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # 관계 설정 (역참조)
    user = relationship("User", backref="comments")
    book = relationship("Book", backref="comments")
