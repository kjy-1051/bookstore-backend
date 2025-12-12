from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# 로그인 응답 형식
class TokenResponseModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str   # ⭐ 추가


# 리프레시 API 입력 형식
class TokenRefreshRequest(BaseModel):
    refresh_token: str
