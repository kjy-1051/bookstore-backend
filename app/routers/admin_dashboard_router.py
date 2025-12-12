# app/routers/admin_dashboard_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import admin_required
from app.services.admin_service import get_admin_dashboard_stats

from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode

router = APIRouter(prefix="/admin/dashboard", tags=["Admin-Dashboard"])


# =========================================================
# 📌 관리자 통계 조회
# =========================================================
@router.get("/stats",
    dependencies=[Depends(admin_required)],
    responses={
        200:{
            "description":"관리자 대시보드 통계 조회 성공",
            "content":{
                "application/json":{
                    "example":{
                        "isSuccess":True,
                        "message":"관리자 통계를 조회했습니다.",
                        "payload":{
                            "books":180,
                            "users":240,
                            "comments":420,
                            "ratings":350
                        }
                    }
                }
            }
        },
        400:{
            "description":"잘못된 요청",
            "content":{"application/json":{"example":{
                "timestamp":"2025-01-10T12:00:00Z",
                "path":"/admin/dashboard/stats",
                "status":400,
                "code":"BAD_REQUEST",
                "message":"요청 형식이 올바르지 않습니다.",
                "details":{"query":"invalid format"}
            }}}
        },
        401:{
            "description":"로그인 필요",
            "content":{
                "application/json":{
                    "example":{
                        "timestamp":"2025-01-10T12:00:00Z",
                        "path":"/admin/dashboard/stats",
                        "status":401,
                        "code":"UNAUTHORIZED",
                        "message":"인증이 필요합니다.",
                        "details":None
                    }
                }
            }
        },
        403:{
            "description":"ADMIN 권한 필요",
            "content":{
                "application/json":{
                    "example":{
                        "timestamp":"2025-01-10T12:00:03Z",
                        "path":"/admin/dashboard/stats",
                        "status":403,
                        "code":"FORBIDDEN",
                        "message":"관리자 권한이 필요합니다.",
                        "details":None
                    }
                }
            }
        },
        404:{
            "description":"조회할 통계 데이터 없음",
            "content":{"application/json":{"example":{
                "timestamp":"2025-01-10T12:00:04Z",
                "path":"/admin/dashboard/stats",
                "status":404,
                "code":"RESOURCE_NOT_FOUND",
                "message":"대시보드 데이터가 존재하지 않습니다.",
                "details":None
            }}}
        },
        422:{
            "description":"유효성 검증 실패",
            "content":{"application/json":{"example":{
                "timestamp":"2025-01-10T12:00:04Z",
                "path":"/admin/dashboard/stats",
                "status":422,
                "code":"VALIDATION_FAILED",
                "message":"Validation failed",
                "details":[{"field":"page","msg":"must be integer"}]
            }}}
        },
        500:{
            "description":"서버 내부 오류",
            "content":{
                "application/json":{
                    "example":{
                        "timestamp":"2025-01-10T12:00:05Z",
                        "path":"/admin/dashboard/stats",
                        "status":500,
                        "code":"INTERNAL_SERVER_ERROR",
                        "message":"대시보드 데이터 조회 실패",
                        "details":None
                    }
                }
            }
        }
    },
    openapi_extra={"security":[{"BearerAuth": []}]}
)
def admin_stats(db: Session = Depends(get_db)):
    data = get_admin_dashboard_stats(db)
    return {
        "isSuccess": True,
        "message": "관리자 통계를 조회했습니다.",
        "payload": data
    }

