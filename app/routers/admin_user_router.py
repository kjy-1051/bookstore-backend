# app/routers/admin_user_router.py
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import admin_required
from app.schemas.user import UserResponse
from app.services.user_service import (
    get_user,
    get_users_admin,
    update_user_status,
    update_user_role,
    get_comments_by_user
)
from app.services.rating_service import get_ratings_by_user
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode

router = APIRouter(
    prefix="/admin/users",
    tags=["Admin-Users"]
)

# =========================================================
# 📌 관리자용 전체 유저 목록 조회
# =========================================================
@router.get("/",
    dependencies=[Depends(admin_required)],
    responses={
        200:{
            "description":"유저 목록 조회 성공",
            "content":{
                "application/json":{
                    "example":{
                        "page":1,
                        "size":20,
                        "total":242,
                        "items":[
                            {"id":1,"email":"a@test.com","name":"Alice","role":"USER"},
                            {"id":2,"email":"b@test.com","name":"Bob","role":"ADMIN"}
                        ]
                    }
                }
            }
        },
        400:{"description":"잘못된 Query 파라미터","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T12:10:15Z",
            "path":"/admin/users",
            "status":400,
            "code":"INVALID_QUERY_PARAM",
            "message":"올바르지 않은 정렬 형식입니다. 예) id,ASC",
            "details":{"sort":"wrong-format"}
        }}}},
        401:{
            "description":"로그인 필요(관리자)",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T12:10:00Z",
                "path":"/admin/users",
                "status":401,
                "code":"UNAUTHORIZED",
                "message":"로그인이 필요합니다."
            }}}
        },
        403:{
            "description":"권한 부족",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T12:10:30Z",
                "path":"/admin/users",
                "status":403,
                "code":"FORBIDDEN",
                "message":"관리자 권한이 필요합니다."
            }}}
        },
        422:{"description":"Validation 실패","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T12:10:40Z",
            "path":"/admin/users",
            "status":422,
            "code":"VALIDATION_FAILED",
            "message":"Validation failed",
            "details":[{"field":"page","msg":"must be integer"}]
        }}}},
        500:{"description":"서버 오류","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T12:11:00Z",
            "path":"/admin/users",
            "status":500,
            "code":"INTERNAL_SERVER_ERROR",
            "message":"유저 목록 조회 실패"
        }}}}
    },
    openapi_extra={"security":[{"BearerAuth": []}]}
)
def list_users_admin(
    page:int=1,
    size:int=20,
    sort:str="id,ASC",
    role:str|None=None,
    keyword:str|None=None,
    db:Session=Depends(get_db)
):
    return get_users_admin(db, page, size, sort, role, keyword)



# =========================================================
# 📌 관리자용 특정 유저 조회
# =========================================================
@router.get("/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(admin_required)],
    responses={
        200:{
            "description":"조회 성공",
            "content":{"application/json":{"example":{
                "id":10,"email":"test@test.com","name":"철수","role":"USER","status":"ACTIVE"
            }}}
        },
        401:{"description":"인증 필요","content":{"application/json":{"example":{
            "timestamp":"2025-12-10T11:56:00Z",
            "path":"/admin/users/1",
            "status":401,
            "code":"UNAUTHORIZED",
            "message":"로그인이 필요합니다."
        }}}},
        403:{
            "description":"유저 없음",
            "content":{"application/json":{"example":{
                "timestamp": "2025-12-10T11:56:18.952456+00:00",
                "path": "/admin/users/1",
                "status": 403,
                "code": "FORBIDDEN",
                "message": "관리자 전용 API 입니다.",
                "details": {"role: user"}
            }}}
        },
        404:{
            "description":"유저 없음",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T13:00:00Z",
                "path":"/admin/users/999",
                "status":404,
                "code":"USER_NOT_FOUND",
                "message":"존재하지 않는 사용자입니다.",
                "details":{"user_id":999}
            }}}
        },
        422:{"description":"유효성 실패","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T13:01:00Z",
            "path":"/admin/users/asdf",
            "status":422,
            "code":"VALIDATION_FAILED",
            "message":"Validation failed"
        }}}},
        500:{"description":"DB 오류","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T13:02:00Z",
            "path":"/admin/users/10",
            "status":500,
            "code":"DATABASE_ERROR",
            "message":"유저 조회 중 오류"
        }}}}
    },
    openapi_extra={"security":[{"BearerAuth": []}]}
)
def get_user_detail(user_id: str, db: Session = Depends(get_db), request: Request = None):

    # 1) user_id 검증 (422 커스텀)
    try:
        uid = int(user_id)
    except ValueError:
        raise CustomException(
            status=422,
            code=ErrorCode.VALIDATION_FAILED,
            message="Validation failed",
            details=[{"field": "user_id", "msg": "must be integer"}]
        )

    # 2) DB 조회
    user = get_user(db, uid)
    if not user:
        raise CustomException(
            status=404,
            code=ErrorCode.USER_NOT_FOUND,
            message="존재하지 않는 사용자입니다.",
            details={"user_id": uid}
        )

    return user



# =========================================================
# 📌 상태 변경 ACTIVE / INACTIVE
# =========================================================
@router.patch("/{user_id}/status",
    dependencies=[Depends(admin_required)],
    responses={
        200:{
            "description":"상태 변경 성공",
            "content":{"application/json":{"example":{
                "message":"User status updated","user_id":10,"status":"INACTIVE"
            }}}
        },
        400:{
            "description":"잘못된 상태 값",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T13:30:00Z",
                "path":"/admin/users/10/status",
                "status":400,
                "code":"BAD_REQUEST",
                "message":"status는 ACTIVE 또는 INACTIVE만 가능합니다.",
                "details":{"input":"DELETED"}
            }}}
        },
        401:{"description":"인증 필요","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T13:30:10Z",
            "path":"/admin/users/10/status",
            "status":401,
            "code":"UNAUTHORIZED",
            "message":"로그인이 필요합니다."
        }}}},
        403:{"description":"권한 부족","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T13:30:20Z",
            "path":"/admin/users/10/status",
            "status":403,
            "code":"FORBIDDEN",
            "message":"관리자 권한이 필요합니다."
        }}}},
        404:{"description":"유저 없음","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T13:30:40Z",
            "path":"/admin/users/999/status",
            "status":404,
            "code":"USER_NOT_FOUND",
            "message":"해당 사용자가 존재하지 않습니다.",
            "details":{"user_id":999}
        }}}},
        422:{"description":"Validation 실패","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T13:31:00Z",
            "path":"/admin/users/10/status",
            "status":422,
            "code":"VALIDATION_FAILED",
            "message":"Validation failed"
        }}}},
        500:{"description":"서버 오류","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T13:32:00Z",
            "path":"/admin/users/10/status",
            "status":500,
            "code":"INTERNAL_SERVER_ERROR",
            "message":"유저 상태 변경 실패"
        }}}}
    },
    openapi_extra={"security":[{"BearerAuth": []}]}
)
def change_user_status(
    user_id:int,
    status:str=Query(...,description="ACTIVE or INACTIVE"),
    db:Session=Depends(get_db)
):
    if status not in ["ACTIVE","INACTIVE"]:
        raise CustomException(
            status=400,
            code=ErrorCode.BAD_REQUEST,
            message="status는 ACTIVE 또는 INACTIVE만 가능합니다.",
            details={"input":status}
        )
    return update_user_status(db, user_id, status)



# =========================================================
# 📌 권한 변경 USER/ADMIN
# =========================================================
@router.patch("/{user_id}/role",
    dependencies=[Depends(admin_required)],
    responses={
        200:{
            "description":"권한 변경 성공",
            "content":{"application/json":{"example":{
                "message":"User role updated","user_id":5,"role":"ADMIN"
            }}}
        },
        400:{
            "description":"잘못된 role 값",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T14:00:00Z",
                "path":"/admin/users/5/role",
                "status":400,
                "code":"BAD_REQUEST",
                "message":"role은 USER 또는 ADMIN만 가능합니다.",
                "details":{"input":"OWNER"}
            }}}
        },
        401:{"description":"인증 필요","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T14:00:20Z",
            "path":"/admin/users/5/role",
            "status":401,
            "code":"UNAUTHORIZED",
            "message":"로그인이 필요합니다."
        }}}},
        403:{"description":"권한 부족","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T14:00:30Z",
            "path":"/admin/users/5/role",
            "status":403,
            "code":"FORBIDDEN",
            "message":"관리자 권한이 필요합니다."
        }}}},
        404:{"description":"유저 없음","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T14:00:45Z",
            "path":"/admin/users/999/role",
            "status":404,
            "code":"USER_NOT_FOUND",
            "message":"사용자를 찾을 수 없습니다."
        }}}},
        422:{"description":"Validation 실패","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T14:01:00Z",
            "path":"/admin/users/5/role",
            "status":422,
            "code":"VALIDATION_FAILED",
            "message":"Validation failed"
        }}}},
        500:{"description":"서버 오류","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T14:01:30Z",
            "path":"/admin/users/5/role",
            "status":500,
            "code":"INTERNAL_SERVER_ERROR",
            "message":"권한 변경 처리 중 오류"
        }}}}
    },
    openapi_extra={"security":[{"BearerAuth": []}]}
)
def change_user_role(
    user_id:int,
    role:str=Query(...,description="USER or ADMIN"),
    db:Session=Depends(get_db)
):
    if role not in ["USER","ADMIN"]:
        raise CustomException(
            status=400,
            code=ErrorCode.BAD_REQUEST,
            message="role은 USER 또는 ADMIN만 가능합니다.",
            details={"input":role}
        )
    return update_user_role(db, user_id, role)



# =========================================================
# 📌 유저 댓글 조회
# =========================================================
@router.get("/{user_id}/comments",
    dependencies=[Depends(admin_required)],
    responses={
        200:{
            "description":"조회 성공",
            "content":{"application/json":{"example":{
                "page":1,"size":10,"total":14,"items":[{"id":1,"content":"재밌어요"}]
            }}}
        },
        401:{"description":"인증 필요","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T14:30:00Z",
            "path":"/admin/users/1/comments",
            "status":401,
            "code":"UNAUTHORIZED",
            "message":"로그인이 필요합니다."
        }}}},
        403:{"description":"권한 필요","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T14:30:10Z",
            "path":"/admin/users/1/comments",
            "status":403,
            "code":"FORBIDDEN",
            "message":"관리자 권한이 필요합니다."
        }}}},
        404:{
            "description":"유저 없음",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T14:30:00Z",
                "path":"/admin/users/999/comments",
                "status":404,
                "code":"USER_NOT_FOUND",
                "message":"사용자를 찾을 수 없습니다.",
                "details":{"user_id":999}
            }}}
        },
        422:{"description":"Validation 실패","content":{"application/json":{"example":{
            "timestamp": "2025-12-11T13:25:05.881558+00:00",
            "path": "/admin/users/4/comments",
            "status": 422,
            "code": "VALIDATION_FAILED",
            "message": "Validation failed",
            "details": [
                {
                    "field": "page/size",
                    "msg": "must be >= 1"
                }
            ]
        }}}},
        500:{"description":"오류","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T14:31:10Z",
            "path":"/admin/users/10/comments",
            "status":500,
            "code":"INTERNAL_SERVER_ERROR",
            "message":"댓글 조회 실패"
        }}}}
    },
    openapi_extra={"security":[{"BearerAuth": []}]}
)
def admin_get_user_comments(user_id:int, page:int=1, size:int=10, db:Session=Depends(get_db)):
    return get_comments_by_user(db, user_id, page, size)



# =========================================================
# 📌 유저 평점 조회
# =========================================================
@router.get("/{user_id}/ratings",
    dependencies=[Depends(admin_required)],
    responses={
        200:{
            "description":"조회 성공",
            "content":{"application/json":{"example":{
                "page":1,"size":10,"total":5,"items":[{"book_id":3,"score":5}]
            }}}
        },
        401:{"description":"인증 필요","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T14:50:00Z",
            "path":"/admin/users/1/ratings",
            "status":401,
            "code":"UNAUTHORIZED",
            "message":"로그인이 필요합니다."
        }}}},
        403:{"description":"권한 필요","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T14:50:10Z",
            "path":"/admin/users/1/ratings",
            "status":403,
            "code":"FORBIDDEN",
            "message":"관리자 권한이 필요합니다."
        }}}},
        404:{"description":"유저 없음","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T14:50:30Z",
            "path":"/admin/users/999/ratings",
            "status":404,
            "code":"USER_NOT_FOUND",
            "message":"사용자를 찾을 수 없습니다."
        }}}},
        422:{"description":"Validation 실패","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T14:50:45Z",
            "path":"/admin/users/abc/ratings",
            "status":422,
            "code":"VALIDATION_FAILED",
            "message":"Validation failed"
        }}}},
        500:{"description":"오류","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T14:51:00Z",
            "path":"/admin/users/10/ratings",
            "status":500,
            "code":"INTERNAL_SERVER_ERROR",
            "message":"평점 조회 실패"
        }}}}
    },
    openapi_extra={"security":[{"BearerAuth": []}]}
)
def admin_get_user_ratings(user_id:int, page:int=1, size:int=10, db:Session=Depends(get_db)):
    return get_ratings_by_user(db, user_id, page, size)
