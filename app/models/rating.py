from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    score = Column(Integer, nullable=False)  # 1~5

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='unique_user_book_rating'),
    )
