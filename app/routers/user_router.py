# app/routers/user_router.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, admin_required
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import create_user, get_user, get_users, update_user, delete_user

# 추가 🔥
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode

router = APIRouter(tags=["Users"])


# =========================================================
# 📌 회원가입 (공개)
# =========================================================
@router.post("/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201:{
            "description":"회원가입 성공",
            "content":{"application/json":{"example":{
                "id": 36,
                "email": "user100@test.com",
                "name": "홍길똥",
                "phone": "010-1234-5678",
                "address": "서울시 성북구",
                "role": "USER",
                "status": "ACTIVE"
        }}}
        },
        400:{"description":"잘못된 입력값","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T17:00:00Z","path":"/users",
            "status":400,"code":"BAD_REQUEST",
            "message":"필수 필드 누락","details":{"email":"required"} 
        }}}},
        409:{
            "description":"중복 이메일",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T17:00:00Z","path":"/users",
                "status":409,"code":"DUPLICATE_RESOURCE",
                "message":"이미 존재하는 이메일입니다.","details":{"email":"user@test.com"}
            }}}
        },
        422:{"description":"Validation 실패","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T17:00:30Z","path":"/users",
            "status":422,"code":"VALIDATION_FAILED",
            "message":"Validation failed","details":[{"field":"email","msg":"invalid email"}]
        }}}},
        500:{"description":"서버 오류","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T17:00:50Z","path":"/users",
            "status":500,"code":"INTERNAL_SERVER_ERROR",
            "message":"회원 생성 중 오류","details":None
        }}}}
    }
)
def register_user(user_data:UserCreate, db:Session=Depends(get_db)):
    try:
        return create_user(db, user_data)
    except Exception: # 실제로는 IntegrityError 발생
        raise CustomException(
            status=409,
            code=ErrorCode.DUPLICATE_RESOURCE,
            message="이미 존재하는 이메일입니다.",
            details={"email":user_data.email}
        )


# =========================================================
# 📌 전체 조회 (관리자)
# =========================================================
@router.get("/",
    response_model=list[UserResponse],
    dependencies=[Depends(admin_required)],
    responses={
        200:{
            "description":"전체 회원 조회 성공",
            "content":{"application/json":{"example":[
                {"id":1,"email":"admin@test.com","role":"ADMIN"},
                {"id":2,"email":"user@test.com","role":"USER"},
            ]}}
        },
        401:{"description":"인증 필요","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T17:10:00Z","path":"/users",
            "status":401,"code":"UNAUTHORIZED",
            "message":"로그인이 필요합니다."
        }}}},
        403:{
            "description":"관리자 권한 필요",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T17:10:00Z","path":"/users",
                "status":403,"code":"FORBIDDEN",
                "message":"ADMIN 계정만 조회 가능"
            }}}
        },
        500:{"description":"서버 오류","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T17:11:00Z","path":"/users",
            "status":500,"code":"INTERNAL_SERVER_ERROR",
            "message":"전체 회원 조회 실패"
        }}}}
    },
    openapi_extra={"security":[{"BearerAuth":[]}]}
)
def list_users(db:Session=Depends(get_db)):
    return get_users(db)


# =========================================================
# 📌 내 정보 조회
# =========================================================
@router.get("/me",
    response_model=UserResponse,
    dependencies=[Depends(get_current_user)],
    responses={
        200:{
            "description":"조회 성공",
            "content":{"application/json":{"example":{
                "id":5,"email":"me@test.com","name":"내 계정","role":"USER"
            }}}
        },
        401:{"description":"인증 필요","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T17:20:00Z","path":"/users/me",
            "status":401,"code":"UNAUTHORIZED",
            "message":"로그인이 필요합니다."
        }}}},
        404:{
            "description":"내 계정 없음(삭제/비활성화)",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T17:20:00Z","path":"/users/me",
                "status":404,"code":"USER_NOT_FOUND",
                "message":"유저를 찾을 수 없습니다."
            }}}
        },
        500:{"description":"서버 오류","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T17:20:20Z","path":"/users/me",
            "status":500,"code":"INTERNAL_SERVER_ERROR",
            "message":"유저 조회 중 오류"
        }}}}
    },
    openapi_extra={"security":[{"BearerAuth":[]}]}
)
def get_me(user=Depends(get_current_user), db:Session=Depends(get_db)):
    result = get_user(db, user["id"])
    if not result:
        raise CustomException(
            status=404,
            code=ErrorCode.USER_NOT_FOUND,
            message="유저를 찾을 수 없습니다.",
            details={"user_id":user["id"]}
        )
    return result


# =========================================================
# 📌 내 정보 수정
# =========================================================
@router.patch("/me",
    response_model=UserResponse,
    dependencies=[Depends(get_current_user)],
    responses={
        200:{
            "description":"정보 수정 성공",
            "content":{"application/json":{"example":{
                "id":5,"email":"me@test.com","name":"닉네임 변경","role":"USER"
            }}}
        },
        400:{"description":"잘못된 입력","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T17:30:00Z","path":"/users/me",
            "status":400,"code":"BAD_REQUEST",
            "message":"email 형식이 잘못되었습니다.","details":{"email":"invalid"}
        }}}},
        404:{
            "description":"계정 없음",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T17:30:00Z","path":"/users/me",
                "status":404,"code":"USER_NOT_FOUND",
                "message":"User not found","details":{"user_id":5}
            }}}
        },
        422:{"description":"Validation 실패","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T17:30:10Z","path":"/users/me",
            "status":422,"code":"VALIDATION_FAILED",
            "message":"Validation failed","details":[{"field":"name","msg":"min length 2"}]
        }}}},
        500:{"description":"서버 오류","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T17:30:40Z","path":"/users/me",
            "status":500,"code":"INTERNAL_SERVER_ERROR",
            "message":"내 정보 수정 실패"
        }}}}
    },
    openapi_extra={"security":[{"BearerAuth":[]}]}
)
def update_me(data:UserUpdate, user=Depends(get_current_user), db:Session=Depends(get_db)):
    updated = update_user(db, user["id"], data)
    if not updated:
        raise CustomException(
            status=404,
            code=ErrorCode.USER_NOT_FOUND,
            message="User not found",
            details={"user_id":user["id"]}
        )
    return updated


# =========================================================
# 📌 회원 탈퇴
# =========================================================
@router.delete("/me",
    dependencies=[Depends(get_current_user)],
    responses={
        200:{
            "description":"회원 탈퇴 성공",
            "content":{"application/json":{"example":{"message":"User deleted"}}}
        },
        404:{
            "description":"이미 없는 계정",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T17:40:00Z","path":"/users/me",
                "status":404,"code":"USER_NOT_FOUND",
                "message":"User not found","details":{"user_id":5}
            }}}
        },
        500:{"description":"서버 오류","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T17:40:50Z","path":"/users/me",
            "status":500,"code":"INTERNAL_SERVER_ERROR",
            "message":"회원 삭제 실패"
        }}}}
    },
    openapi_extra={"security":[{"BearerAuth":[]}]}
)
def delete_me(user=Depends(get_current_user), db:Session=Depends(get_db)):
    ok = delete_user(db, user["id"])
    if not ok:
        raise CustomException(
            status=404,
            code=ErrorCode.USER_NOT_FOUND,
            message="User not found",
            details={"user_id":user["id"]}
        )
    return {"message":"User deleted"}
