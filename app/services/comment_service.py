from sqlalchemy.orm import Session
from app.models.comment import Comment
from app.models.book import Book
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode


# ==========================
# 📌 댓글 생성
# ==========================
def create_comment(db: Session, user_id: int, data: CommentCreate):
    # 🔥 책 존재 여부 확인
    book_exists = db.query(Book.id).filter(Book.id == data.book_id).first()
    if not book_exists:
        raise CustomException(
            404, ErrorCode.RESOURCE_NOT_FOUND,
            "Book not found",
            details={"book_id": data.book_id}
        )

    comment = Comment(
        book_id=data.book_id,
        user_id=user_id,
        content=data.content
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


# ==========================
# 📌 댓글 수정 (작성자만)
# ==========================
def update_comment(db: Session, comment_id: int, user_id: int, data: CommentUpdate):
    comment = db.query(Comment).filter_by(id=comment_id).first()

    if not comment:
        raise CustomException(
            404, ErrorCode.RESOURCE_NOT_FOUND,
            "Comment not found",
            details={"comment_id": comment_id}
        )

    if comment.user_id != user_id:
        raise CustomException(
            403, ErrorCode.FORBIDDEN,
            "수정 권한 없음",
            details={"comment_id": comment_id}
        )

    # PATCH body가 {} 이면 content=None → 변경 없이 성공 처리
    if data.content is None:
        return comment

    # 빈 문자열 → 422 VALIDATION_FAILED
    if isinstance(data.content, str) and len(data.content.strip()) == 0:
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "content", "msg": "최소 1자 이상 입력해야 합니다."}]
        )

    # 정상 업데이트
    comment.content = data.content

    db.commit()
    db.refresh(comment)
    return comment


# ==========================
# 📌 댓글 삭제
# ==========================
def delete_comment(db: Session, comment_id: int, user_id: int):
    comment = db.query(Comment).filter_by(id=comment_id).first()

    if not comment:
        raise CustomException(
            404, ErrorCode.RESOURCE_NOT_FOUND,
            "Comment not found",
            details={"comment_id": comment_id}
        )

    if comment.user_id != user_id:
        raise CustomException(
            403, ErrorCode.FORBIDDEN,
            "삭제 권한 없음",
            details={"comment_id": comment_id}
        )

    db.delete(comment)
    db.commit()
    return True


# ==========================
# 📌 특정 도서 댓글 전체 조회
# ==========================
def get_comments_by_book(db: Session, book_id: int):
    return db.query(Comment).filter(Comment.book_id == book_id).all()


# ==========================
# 📌 댓글 페이징 (rating과 동일 구조)
# ==========================
def get_comments_paginated(
    db: Session,
    book_id: int,
    page: int = 1,
    size: int = 10,
    sort: str = "id,DESC",
    keyword: str | None = None
):
    # 정렬
    field, direction = sort.split(",")
    column = getattr(Comment, field)

    query = db.query(Comment).filter(Comment.book_id == book_id)

    # 검색
    if keyword:
        query = query.filter(Comment.content.like(f"%{keyword}%"))

    # 정렬 적용
    query = query.order_by(column.desc() if direction.upper() == "DESC" else column.asc())

    total = query.count()
    comments = query.offset((page - 1) * size).limit(size).all()

    return {
        "content": [
            CommentResponse.model_validate(c, from_attributes=True)
            for c in comments
        ],
        "page": page,
        "size": size,
        "totalElements": total,
        "totalPages": (total + size - 1) // size,
        "sort": sort,
        "keyword": keyword,
    }
