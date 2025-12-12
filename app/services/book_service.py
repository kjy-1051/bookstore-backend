from sqlalchemy.orm import Session
from sqlalchemy.sql import func
#from fastapi import HTTPException
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode

from app.models.book import Book
from app.models.rating import Rating
from app.models.comment import Comment
from app.schemas.book import BookCreate, BookUpdate
from sqlalchemy import asc, desc, or_
import random


def serialize_book(book):
    return {
        "id": book.id,
        "isbn": book.isbn,
        "title": book.title,
        "price": book.price,
        "publisher": book.publisher,
        "summary": book.summary,
        "publicationDate": book.publication_date,
        "authors": book.authors.split(",") if book.authors else [],
        "categories": book.categories.split(",") if book.categories else []
    }

def search_books(db, keyword=None, category=None, page:int=1, size:int=10, sort:str="id,ASC"):
    try:
        field, order = sort.split(",")
        column = getattr(Book, field, None)

        if column is None:
            raise CustomException(
                400,
                ErrorCode.INVALID_QUERY_PARAM,
                "Invalid sort field",
                details={"sort": sort}
            )

        order_by = desc(column) if order.upper()=="DESC" else asc(column)

        query = db.query(Book)

        if keyword:
            query = query.filter(
                or_(
                    Book.title.like(f"%{keyword}%"),
                    Book.summary.like(f"%{keyword}%"),
                    Book.authors.like(f"%{keyword}%"),
                    Book.categories.like(f"%{keyword}%"),
                    Book.isbn.like(f"%{keyword}%")
                )
            )

        if category:
            query = query.filter(Book.categories.like(f"%{category}%"))

        total = query.count()
        books = query.order_by(order_by).offset((page-1)*size).limit(size).all()

        return {
            "content": [serialize_book(b) for b in books],
            "page": page,
            "size": size,
            "totalElements": total,
            "totalPages": (total + size - 1) // size,
            "sort": sort,
            "keyword": keyword,
            "category": category
        }

    except CustomException:
        raise
    except Exception:
        raise CustomException(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR,
            "검색 처리 중 오류가 발생했습니다."
        )


# Create
def create_book(db: Session, book_data: BookCreate):
    exists = db.query(Book).filter(Book.isbn == book_data.isbn).first()
    if exists:
        raise CustomException(
            status=409,
            code=ErrorCode.DUPLICATE_RESOURCE,
            message="이미 등록된 ISBN 입니다.",
            details={"isbn": book_data.isbn}
        )

    authors = ",".join(book_data.authors) if book_data.authors else None
    categories = ",".join(book_data.categories) if book_data.categories else None

    book = Book(
        title=book_data.title,
        isbn=book_data.isbn,
        price=book_data.price,
        publisher=book_data.publisher,
        summary=book_data.summary,
        publication_date=book_data.publicationDate,
        authors=authors,
        categories=categories
    )

    db.add(book)
    db.commit()
    db.refresh(book)
    return serialize_book(book)


# Read All
def get_books_paginated(db, page:int=1, size:int=10, sort:str="id,ASC"):
    try:
        field, order = sort.split(",")
        column = getattr(Book, field, None)

        if column is None:
            raise CustomException(
                400,
                ErrorCode.INVALID_QUERY_PARAM,
                "Invalid sort field",
                details={"sort": sort}
            )

        order_by = desc(column) if order.upper()=="DESC" else asc(column)

        total = db.query(Book).count()
        books = (
            db.query(Book)
            .order_by(order_by)
            .offset((page-1)*size)
            .limit(size)
            .all()
        )

        return {
            "content": [serialize_book(b) for b in books],
            "page": page,
            "size": size,
            "totalElements": total,
            "totalPages": (total + size - 1) // size,
            "sort": sort
        }

    except CustomException:
        raise
    except Exception:
        raise CustomException(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR,
            "책 목록 조회 중 오류가 발생했습니다."
        )


# Read One
def get_book_by_id(db: Session, book_id: int):
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return None
        return serialize_book(book)

    except Exception:
        raise CustomException(
            status=500,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="도서 조회 중 오류가 발생했습니다.",
            details=None
        )



# Update
def update_book(db: Session, book_id: int, data: BookUpdate):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise CustomException(
            status=404,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Book not found",
            details={"book_id": book_id}
        )

    update_data = data.model_dump(exclude_unset=True)

    if "authors" in update_data:
        update_data["authors"] = ",".join(update_data["authors"]) if update_data["authors"] else None
    if "categories" in update_data:
        update_data["categories"] = ",".join(update_data["categories"]) if update_data["categories"] else None

    for field, value in update_data.items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)
    return serialize_book(book)



# Delete
def delete_book(db: Session, book_id: int):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise CustomException(
            status=404,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Book not found",
            details={"book_id": book_id}
        )

    db.delete(book)
    db.commit()
    return True


#평균 평점 높은 책  TOP N 조회
def get_top_rated_books(db: Session, limit: int = 10):
    try:
        result = (
            db.query(
                Book.id,
                Book.title,
                func.avg(Rating.score).label("avg_score"),
                func.count(Rating.id).label("rating_count")
            )
            .join(Rating, Rating.book_id == Book.id)
            .group_by(Book.id)
            .order_by(func.avg(Rating.score).desc(), func.count(Rating.id).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": r.id,
                "title": r.title,
                "avg_score": float(r.avg_score),
                "rating_count": r.rating_count
            }
            for r in result
        ]

    except Exception:
        raise CustomException(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR,
            "상위 평점 도서 조회 중 오류 발생"
        )


# 댓글 많은 책 TOP N 조회
def get_top_commented_books(db: Session, limit: int = 10):
    try:
        result = (
            db.query(
                Book.id,
                Book.title,
                func.count(Comment.id).label("comment_count")
            )
            .join(Comment, Comment.book_id == Book.id)
            .group_by(Book.id)
            .order_by(func.count(Comment.id).desc())
            .limit(limit)
            .all()
        )

        return [
            {"id": r.id, "title": r.title, "comment_count": r.comment_count}
            for r in result
        ]

    except Exception:
        raise CustomException(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR,
            "댓글 상위 도서 조회 중 오류 발생"
        )


def filter_by_price(db, min_price=None, max_price=None, page:int=1, size:int=10, sort:str="price,ASC"):
    try:
        query = db.query(Book)

        if min_price is not None:
            query = query.filter(Book.price >= min_price)
        if max_price is not None:
            query = query.filter(Book.price <= max_price)

        field, direction = sort.split(",")
        column = getattr(Book, field, None)

        if column is None:
            raise CustomException(
                400,
                ErrorCode.INVALID_QUERY_PARAM,
                "Invalid sort field",
                details={"sort": sort}
            )

        order_by = desc(column) if direction.upper()=="DESC" else asc(column)

        total = query.count()
        books = query.order_by(order_by).offset((page-1)*size).limit(size).all()

        return {
            "content": [serialize_book(b) for b in books],
            "page": page,
            "size": size,
            "totalElements": total,
            "totalPages": (total + size - 1) // size,
            "sort": sort,
            "min_price": min_price,
            "max_price": max_price,
        }

    except CustomException:
        raise
    except Exception:
        raise CustomException(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR,
            "가격 필터 처리 중 오류 발생"
        )


def get_latest_books(db):
    try:
        books = db.query(Book).order_by(desc(Book.publication_date)).all()
        return [serialize_book(b) for b in books]
    except Exception:
        raise CustomException(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR,
            "최신 도서 조회 중 오류 발생"
        )


def get_random_books(db:Session, limit:int=5):
    try:
        books = db.query(Book).all()
        random.shuffle(books)
        return [serialize_book(b) for b in books[:limit]]
    except Exception:
        raise CustomException(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR,
            "랜덤 도서 추천 중 오류 발생"
        )
