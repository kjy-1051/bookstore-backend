# app/services/user_service.py
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User
from app.models.comment import Comment

from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.comment import CommentResponse

from passlib.context import CryptContext

# Custom 에러
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =========================================================
# 📌 비밀번호 해시
# =========================================================
def hash_password(password: str):
    return pwd_context.hash(password)


# =========================================================
# 📌 회원가입
# =========================================================
def create_user(db: Session, user_data: UserCreate):
    try:
        hashed_pw = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_pw,
            name=user_data.name,
            phone=user_data.phone,
            address=user_data.address,
            role="USER",
            status="ACTIVE"
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    except:
        db.rollback()
        raise CustomException(
            status=409,
            code=ErrorCode.DUPLICATE_RESOURCE,
            message="이미 존재하는 이메일입니다.",
            details={"email": user_data.email}
        )


# =========================================================
# 📌 유저 정보 조회
# =========================================================
def get_user(db: Session, user_id: int):
    try:
        return db.query(User).filter(User.id == user_id).first()
    except:
        raise CustomException(
            status=500,
            code=ErrorCode.DATABASE_ERROR,
            message="유저 조회 중 오류"
        )


# =========================================================
# 📌 전체 유저 조회 (ADMIN only)
# =========================================================
def get_users(db: Session):
    try:
        return db.query(User).all()
    except:
        raise CustomException(
            status=500,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="전체 회원 조회 실패"
        )


# =========================================================
# 📌 내 정보 수정
# =========================================================
def update_user(db: Session, user_id: int, data: UserUpdate):
    try:
        user = get_user(db, user_id)
        if not user:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user

    except CustomException:
        raise

    except Exception:
        db.rollback()
        raise CustomException(
            status=500,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="유저 수정 중 오류"
        )


# =========================================================
# 📌 회원 삭제 (탈퇴)
# =========================================================
def delete_user(db: Session, user_id: int):
    try:
        user = get_user(db, user_id)
        if not user:
            return False

        db.delete(user)
        db.commit()
        return True

    except CustomException:
        raise

    except Exception:
        db.rollback()
        raise CustomException(
            status=500,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="유저 삭제 실패"
        )


# =========================================================
# 📌 관리자용 목록 조회 (page/size/sort/검색)
# =========================================================
def get_users_admin(db: Session, page=1, size=20, sort="id,ASC", role=None, keyword=None):

    # page/size 범위
    if page < 1:
        raise CustomException(
            422, ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "page", "msg": "must be >= 1"}]
        )
    if size < 1:
        raise CustomException(
            422, ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "size", "msg": "must be >= 1"}]
        )

    # sort 형식 검증
    try:
        field, direction = sort.split(",")
        column = getattr(User, field)
    except:
        raise CustomException(
            400,
            ErrorCode.INVALID_QUERY_PARAM,
            "올바르지 않은 정렬 형식입니다. 예) id,ASC",
            details={"sort": sort}
        )

    try:
        query = db.query(User)

        # 검색 필터
        if role:
            query = query.filter(User.role == role.upper())
        if keyword:
            query = query.filter(
                or_(User.name.like(f"%{keyword}%"), User.email.like(f"%{keyword}%"))
            )

        # 정렬 적용
        query = query.order_by(column.desc() if direction.upper() == "DESC" else column.asc())

        total = query.count()
        users = query.offset((page - 1) * size).limit(size).all()

        return {
            "items": [UserResponse.model_validate(u, from_attributes=True) for u in users],
            "page": page,
            "size": size,
            "total": total,
            "sort": sort
        }

    except:
        raise CustomException(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR,
            "유저 목록 조회 실패"
        )


# =========================================================
# 📌 관리자용 유저 상태 변경
# =========================================================
def update_user_status(db: Session, user_id: int, status: str):

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise CustomException(
                404,
                ErrorCode.USER_NOT_FOUND,
                "해당 사용자가 존재하지 않습니다.",
                details={"user_id": user_id}
            )

        status = status.upper()
        if status not in ["ACTIVE", "INACTIVE"]:
            raise CustomException(
                400,
                ErrorCode.BAD_REQUEST,
                "status는 ACTIVE 또는 INACTIVE만 가능합니다.",
                details={"input": status}
            )

        user.status = status
        db.commit()
        db.refresh(user)

        return {
            "message": "User status updated",
            "user_id": user_id,
            "status": status
        }

    except CustomException:
        raise

    except:
        db.rollback()
        raise CustomException(
            500, ErrorCode.INTERNAL_SERVER_ERROR,
            "유저 상태 변경 실패"
        )


# =========================================================
# 📌 관리자용 유저 권한 변경
# =========================================================
def update_user_role(db: Session, user_id: int, role: str):

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise CustomException(
                404,
                ErrorCode.USER_NOT_FOUND,
                "사용자를 찾을 수 없습니다.",
                details={"user_id": user_id}
            )

        role = role.upper()
        if role not in ["USER", "ADMIN"]:
            raise CustomException(
                400,
                ErrorCode.BAD_REQUEST,
                "role은 USER 또는 ADMIN만 가능합니다.",
                details={"input": role}
            )

        user.role = role
        db.commit()
        db.refresh(user)

        return {
            "message": "User role updated",
            "user_id": user_id,
            "role": role
        }

    except CustomException:
        raise

    except:
        db.rollback()
        raise CustomException(
            500, ErrorCode.INTERNAL_SERVER_ERROR,
            "권한 변경 처리 중 오류"
        )


# =========================================================
# 📌 관리자용 유저 댓글 조회
# =========================================================
def get_comments_by_user(db: Session, user_id: int, page=1, size=10):

    # page/size 검증
    if page < 1 or size < 1:
        raise CustomException(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Validation failed",
            details=[{"field": "page/size", "msg": "must be >= 1"}]
        )

    try:
        query = db.query(Comment).filter(Comment.user_id == user_id)

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
            "totalPages": (total + size - 1) // size
        }
    except:
        raise CustomException(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR,
            "댓글 조회 실패"
        )
