from fastapi import Depends
from datetime import datetime, timedelta, timezone
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.core.database import get_db
from app.models.user import User
from app.core.config import settings

# 추가
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.JWT_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

from fastapi import Request

class CustomHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request):
        try:
            return await super().__call__(request)
        except Exception:
            raise CustomException(
                status=401,
                code=ErrorCode.UNAUTHORIZED,
                message="로그인이 필요합니다."
            )

# ---------------------- Password ----------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# ---------------------- Token ----------------------
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------- Bearer for swagger ----------------------
bearer_scheme = CustomHTTPBearer()


# ---------------------- Current user ----------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role_from_token = payload.get("role")

        if not user_id:
            raise CustomException(status=401, code=ErrorCode.UNAUTHORIZED,
                                  message="Invalid token payload")

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise CustomException(status=404, code=ErrorCode.RESOURCE_NOT_FOUND,
                                  message="User not found")

        if user.status != "ACTIVE":
            raise CustomException(status=403, code=ErrorCode.FORBIDDEN,
                                  message="User inactive")

        # 🟩 Debug
        #print("\n===== AUTH DEBUG =====")
        #print("TOKEN ROLE:", role_from_token)
        #print("DB ROLE:", user.role)
        #print("=====================\n")

        return {"id": user.id, "role": user.role}  # Enum 그대로 반환

    except ExpiredSignatureError:
        raise CustomException(status=401, code=ErrorCode.UNAUTHORIZED,
                              message="Token expired")

    except JWTError:
        raise CustomException(status=401, code=ErrorCode.UNAUTHORIZED,
                              message="Token invalid")


def admin_required(user = Depends(get_current_user)):
    role = user["role"].value if hasattr(user["role"], "value") else user["role"]
    print("ADMIN CHECK ROLE =", role)

    if role != "ADMIN":
        raise CustomException(status=403, code=ErrorCode.FORBIDDEN,
                              message="관리자 전용 API 입니다.")
    return user

