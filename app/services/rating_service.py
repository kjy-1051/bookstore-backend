# app/services/rating_service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.models.rating import Rating
from app.models.book import Book
from app.schemas.rating import RatingResponse
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode
from app.models.user import User

# ===================== 평점 생성 =====================
def create_rating(db, user_id, book_id, score):
    # 책 존재 여부 확인
    if not db.query(Book.id).filter(Book.id == book_id).first():
        raise CustomException(
            404, ErrorCode.RESOURCE_NOT_FOUND,
            "Book not found", details={"book_id": book_id}
        )

    # 이미 작성했는지 확인
    exists = db.query(Rating).filter_by(user_id=user_id, book_id=book_id).first()
    if exists:
        raise CustomException(
            409, ErrorCode.STATE_CONFLICT,
            "이미 이 책에 대한 평점을 등록했습니다.",
            details={"book_id": book_id}
        )

    # 🔥 score 범위 검증 (스웨거 요구사항)
    if not isinstance(score, int):
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "score", "msg": "must be integer"}]
        )

    if score < 1 or score > 5:
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "score", "msg": "must be between 1~5"}]
        )

    try:
        rating = Rating(user_id=user_id, book_id=book_id, score=score)
        db.add(rating)
        db.commit()
        db.refresh(rating)
        return rating

    except IntegrityError:
        db.rollback()
        raise CustomException(
            500, ErrorCode.INTERNAL_SERVER_ERROR,
            "Rating create failed"
        )
    except Exception:
        db.rollback()
        raise CustomException(
            500, ErrorCode.INTERNAL_SERVER_ERROR,
            "Rating create failed"
        )


# ===================== 평점 수정 =====================
def update_rating(db, user_id, book_id, score):
    # 평점 존재 여부 확인
    rating = db.query(Rating).filter_by(user_id=user_id, book_id=book_id).first()
    if not rating:
        raise CustomException(
            404, ErrorCode.RESOURCE_NOT_FOUND,
            "평점을 찾을 수 없습니다.",
            details={"book_id": book_id}
        )

    # 🔥 score 타입 검증
    if not isinstance(score, int):
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "score", "msg": "must be integer"}]
        )

    # 🔥 score 범위 검증
    if score < 1 or score > 5:
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "score", "msg": "value must be between 1~5"}]
        )

    try:
        rating.score = score
        db.commit()
        db.refresh(rating)
        return rating

    except Exception:
        db.rollback()
        raise CustomException(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR,
            "Rating update failed"
        )



# ===================== 평점 목록 조회 (기존 구조 유지) =====================
def get_book_ratings(
    db: Session, 
    book_id: int, 
    page: int = 1, 
    size: int = 10, 
    sort: str = "id,DESC",
    keyword: str | None = None,
    minScore: int | None = None,
    maxScore: int | None = None
):

    # 🔥 score 타입 검증 + 정수 변환 실패 방지
    # keyword 변환
    if keyword is not None:
        try:
            keyword_int = int(keyword)
        except:
            raise CustomException(
                422,
                ErrorCode.VALIDATION_FAILED,
                "Validation failed",
                details=[{"field": "keyword", "msg": "must be integer"}]
            )
    else:
        keyword_int = None

    # 🔥 sort 형식 검증 ("field,DESC" only)
    try:
        field, direction = sort.split(",")
        direction = direction.upper()
        if direction not in ["ASC", "DESC"]:
            raise ValueError
    except:
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "sort", "msg": "must be in 'field,ASC|DESC' format"}]
        )

    # 실제 컬럼 존재 검증
    if not hasattr(Rating, field):
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "sort", "msg": f"unknown sort field '{field}'"}]
        )

    # minScore / maxScore 타입 검증
    if minScore is not None and not isinstance(minScore, int):
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "minScore", "msg": "must be integer"}]
        )

    if maxScore is not None and not isinstance(maxScore, int):
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "maxScore", "msg": "must be integer"}]
        )
    
        # 🔥 page/size 범위 검증
    if page < 1:
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "page", "msg": "must be >= 1"}]
        )

    if size < 1:
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "size", "msg": "must be >= 1"}]
        )

    try:
        query = db.query(Rating).filter(Rating.book_id == book_id)

        if keyword_int is not None:
            query = query.filter(Rating.score == keyword_int)
        if minScore is not None:
            query = query.filter(Rating.score >= minScore)
        if maxScore is not None:
            query = query.filter(Rating.score <= maxScore)

        # 정렬
        column = getattr(Rating, field)
        query = query.order_by(column.desc() if direction == "DESC" else column.asc())

        total = query.count()
        ratings = query.offset((page - 1) * size).limit(size).all()

        return {
            "content": [RatingResponse.model_validate(r, from_attributes=True) for r in ratings],
            "page": page,
            "size": size,
            "totalElements": total,
            "totalPages": (total + size - 1) // size,
            "sort": sort,
            "keyword": keyword,
            "minScore": minScore,
            "maxScore": maxScore
        }

    except Exception:
        raise CustomException(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR,
            "Rating list fetch failed"
        )



# ===================== 평점 삭제 =====================
def delete_rating(db, user_id, book_id):
    rating = db.query(Rating).filter_by(user_id=user_id, book_id=book_id).first()

    if not rating:
        raise CustomException(
            404, ErrorCode.RESOURCE_NOT_FOUND,
            "Rating not found",
            details={"book_id": book_id}
        )

    try:
        db.delete(rating)
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise CustomException(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR,
            "Rating delete failed"
        )



# ===================== 책 평점 요약 =====================
def get_book_rating_summary(db, book_id: int):
    book_exists = db.query(Book.id).filter(Book.id == book_id).first()
    if not book_exists:
        raise CustomException(
            404, ErrorCode.RESOURCE_NOT_FOUND,
            "Book not found", details={"book_id": book_id}
        )

    result = db.query(
        func.avg(Rating.score).label("avg"),
        func.count(Rating.id).label("count")
    ).filter(Rating.book_id == book_id).first()

    avg = float(result.avg) if result.avg else 0.0
    count = result.count

    return {
        "bookId": book_id,
        "averageRating": round(avg, 2),
        "reviewCount": count
    }

# ===================== 특정 유저의 평점 목록 조회 (Admin) =====================
def get_ratings_by_user(db: Session, user_id: int, page: int = 1, size: int = 10):

    # 🔥 page/size 검증
    if page < 1:
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "page", "msg": "must be >= 1"}]
        )

    if size < 1:
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "size", "msg": "must be >= 1"}]
        )

    try:
        # 🔥 user 존재 여부 확인
        user_exists = db.query(User.id).filter(User.id == user_id).first()
        if not user_exists:
            raise CustomException(
                404,
                ErrorCode.USER_NOT_FOUND,
                "사용자를 찾을 수 없습니다.",
                details={"user_id": user_id}
            )

        query = db.query(Rating).filter(Rating.user_id == user_id)

        total = query.count()
        ratings = (
            query
            .order_by(Rating.id.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return {
            "page": page,
            "size": size,
            "total": total,
            "items": [
                RatingResponse.model_validate(r, from_attributes=True)
                for r in ratings
            ]
        }

    except CustomException:
        raise

    except Exception:
        raise CustomException(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR,
            "평점 조회 실패"
        )
