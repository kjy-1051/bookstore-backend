from sqlalchemy.orm import Session
from app.models.user import User
from app.models.book import Book
from app.models.comment import Comment
from app.models.rating import Rating
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode

def get_admin_dashboard_stats(db: Session):
    try:
        book_count = db.query(Book).count()
        user_count = db.query(User).count()
        comment_count = db.query(Comment).count()
        rating_count = db.query(Rating).count()

        # 🔥 스웨거 정의에 맞춘 “데이터 없음 → 404”
        if book_count == 0 and user_count == 0 and comment_count == 0 and rating_count == 0:
            raise CustomException(
                status=404,
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="대시보드 데이터가 존재하지 않습니다.",
                details=None
            )

        return {
            "books": book_count,
            "users": user_count,
            "comments": comment_count,
            "ratings": rating_count
        }

    except CustomException:
        raise
    except Exception as e:
        raise CustomException(
            status=500,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="대시보드 데이터 조회 실패",
            details=str(e)
        )
