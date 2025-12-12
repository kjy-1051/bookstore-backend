# app/services/auth_service.py
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.models.user import User
from app.core.redis import r
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.config import settings

from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode


# =========================================================
# 📌 로그인
# =========================================================
def login_user(db: Session, email: str, password: str):
    try:
        user = db.query(User).filter(User.email == email).first()

        if not user or not verify_password(password, user.hashed_password):
            raise CustomException(
                status=401,
                code=ErrorCode.UNAUTHORIZED,
                message="이메일 또는 비밀번호가 올바르지 않습니다."
            )

        if user.status != "ACTIVE":
            raise CustomException(
                status=403,
                code=ErrorCode.FORBIDDEN,
                message="비활성화되었거나 차단된 계정입니다."
            )

        access = create_access_token({"sub": str(user.id), "role": user.role})
        refresh = create_refresh_token({"sub": str(user.id), "role": user.role})

        r.set(f"user:{user.id}:refresh", refresh, ex=60*60*24*7)

        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "role": user.role
        }

    except CustomException:
        raise
    except Exception:
        raise CustomException(
            status=500,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="로그인 처리 중 오류"
        )



# =========================================================
# 📌 토큰 재발급
# =========================================================
def refresh_access_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        role = payload.get("role")

        if not user_id:
            raise CustomException(
                status=401,
                code=ErrorCode.UNAUTHORIZED,
                message="올바르지 않은 Refresh Token 입니다."
            )

        stored = r.get(f"user:{user_id}:refresh")

        if not stored or stored != refresh_token:
            raise CustomException(
                status=401,
                code=ErrorCode.TOKEN_EXPIRED,
                message="Refresh Token expired or invalid"
            )

        new_access = create_access_token({"sub": str(user_id), "role": role})
        new_refresh = create_refresh_token({"sub": str(user_id), "role": role})

        r.set(f"user:{user_id}:refresh", new_refresh, ex=60*60*24*7)

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "role": role
        }

    except JWTError:
        raise CustomException(
            status=401,
            code=ErrorCode.TOKEN_EXPIRED,
            message="Refresh Token expired or invalid"
        )


# =========================================================
# 📌 로그아웃
# =========================================================
def logout_user(user_id: int):
    deleted = r.delete(f"user:{user_id}:refresh")

    return {
        "message": "Logged out successfully" if deleted else "Already logged out or token not found"
    }
