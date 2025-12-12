# app/routers/admin_book_router.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import admin_required
from app.schemas.book import BookCreate, BookUpdate, BookResponse
from app.services.book_service import create_book, update_book, delete_book

from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode

router = APIRouter(
    prefix="/admin/books",
    tags=["Admin-Books"]
)


# =========================================================
# 📌 책 등록 (관리자)
# =========================================================
@router.post("/",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(admin_required)],
    responses={
        201: {
            "description": "도서 등록 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 21,
                        "title": "Clean Architecture",
                        "price": 22000,
                        "authors": ["Robert Martin"],
                        "categories": ["Software"],
                        "summary": "클린 아키텍처 설계 철학 정리"
                    }
                }
            }
        },
        400: {
            "description": "잘못된 요청 (입력 값 검증 실패)",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T10:17:00Z",
                "path": "/admin/books",
                "status": 400,
                "code": "BAD_REQUEST",
                "message": "필수 필드 누락",
                "details": {"title": "required"}
            }}}
        },
        401: {
            "description": "인증 필요(토큰 없음 또는 만료됨)",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp":"2025-02-01T10:18:00Z",
                        "path":"/admin/books",
                        "status":401,
                        "code":"UNAUTHORIZED",
                        "message":"로그인이 필요합니다.",
                        "details": None
                    }
                }
            }
        },
        403:{
            "description":"관리자 권한 없음",
            "content":{
                "application/json":{
                    "example":{
                        "timestamp":"2025-02-01T10:19:00Z",
                        "path":"/admin/books",
                        "status":403,
                        "code":"FORBIDDEN",
                        "message":"관리자 권한이 없습니다.",
                        "details":None
                    }
                }
            }
        },
        409: {
            "description": "중복 도서(DB Unique 충돌)",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-02-01T10:20:00Z",
                        "path": "/admin/books",
                        "status": 409,
                        "code": "DUPLICATE_RESOURCE",
                        "message": "이미 등록된 ISBN입니다.",
                        "details": {"isbn": "9788998139766"}
                    }
                }
            }
        },
        422: {"description": "ValidationError", "content":{"application/json":{"example":{
            "timestamp":"2025-02-01T10:20:30Z",
            "path":"/admin/books",
            "status":422,
            "code":"VALIDATION_FAILED",
            "message":"Validation failed",
            "details":[{"field":"price","msg":"must be positive"}]
        }}}},
        500: {
            "description": "서버 오류",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-02-01T10:21:00Z",
                        "path": "/admin/books",
                        "status": 500,
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "도서 등록 처리 중 오류",
                        "details": None
                    }
                }
            }
        }
    },
    openapi_extra={"security":[{"BearerAuth":[]}]}
)
def create_admin_book(data: BookCreate, db: Session = Depends(get_db)):
    return create_book(db, data)



# =========================================================
# 📌 책 수정
# =========================================================
@router.patch("/{book_id}",
    response_model=BookResponse,
    dependencies=[Depends(admin_required)],
    responses={
        200: {
            "description": "수정 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 10,
                        "title": "Refactoring 2nd Edition",
                        "price": 30000,
                        "authors": ["Martin Fowler"],
                        "categories": ["Software"],
                        "summary": "리팩터링 개선판"
                    }
                }
            }
        },
        400: {"description":"잘못된 요청", "content":{"application/json":{"example":{
            "timestamp":"2025-12-09T22:30:00Z",
            "path":"/admin/books/10",
            "status":400,
            "code":"BAD_REQUEST",
            "message":"입력 형식 오류",
            "details":{"price":"must be positive"}
        }}}},
        401:{
            "description":"Unauthorized",
            "content":{
                "application/json":{
                    "example":{
                        "timestamp": "2025-12-09T22:31:42.777527+00:00",
                        "path": "/admin/books/3",
                        "status": 401,
                        "code": "UNAUTHORIZED",
                        "message": "Token expired",
                        "details": None
}
                }
            }
        },
        403:{
            "description":"관리자 아님",
            "content":{
                "application/json":{
                    "example":{
                        "timestamp":"2025-02-01T10:29:00Z",
                        "path":"/admin/books/10",
                        "status":403,
                        "code":"FORBIDDEN",
                        "message":"관리자 권한이 없습니다.",
                        "details":None
                    }
                }
            }
        },
        404: {
            "description": "도서 없음",
            "content": {
                "application/json": {
                    "example":{
                        "timestamp":"2025-02-01T10:30:00Z",
                        "path":"/admin/books/999",
                        "status":404,
                        "code":"RESOURCE_NOT_FOUND",
                        "message":"Book not found",
                        "details":{"book_id":999}
                    }
                }
            }
        },
        422:{"description":"필드 검증 실패","content":{"application/json":{"example":{
            "timestamp":"2025-12-09T22:32:00Z",
            "path":"/admin/books/10",
            "status":422,
            "code":"VALIDATION_FAILED",
            "message":"Validation failed",
            "details":[{"field":"title","msg":"too short"}]
        }}}},
        500:{
            "description":"DB 처리 중 오류",
            "content":{
                "application/json":{
                    "example":{
                        "timestamp":"2025-02-01T10:32:00Z",
                        "path":"/admin/books/10",
                        "status":500,
                        "code":"INTERNAL_SERVER_ERROR",
                        "message":"Book update failed",
                        "details":None
                    }
                }
            }
        }
    },
    openapi_extra={"security":[{"BearerAuth":[]}]}
)
def update_admin_book(book_id:int, data:BookUpdate, db:Session=Depends(get_db)):
    return update_book(db, book_id, data)



# =========================================================
# 📌 책 삭제
# =========================================================
@router.delete("/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(admin_required)],
    responses={
        204: {"description": "삭제 성공 (응답 바디 없음)"},
        400:{"description":"잘못된 요청","content":{"application/json":{"example":{
            "timestamp":"2025-12-09T22:33:00Z",
            "path":"/admin/books/10",
            "status":400,
            "code":"BAD_REQUEST",
            "message":"book_id must be integer",
            "details":{"book_id":"abc"}
        }}}},
        401:{"description":"로그인 필요","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T10:38:00Z",
            "path":"/admin/books/10",
            "status":401,
            "code":"UNAUTHORIZED",
            "message":"로그인이 필요합니다.",
            "details":None
        }}}},
        403:{"description":"관리자 권한 없음","content":{"application/json":{"example":{
            "timestamp":"2025-02-01T10:39:00Z",
            "path":"/admin/books/10",
            "status":403,
            "code":"FORBIDDEN",
            "message":"관리자 권한이 없습니다.",
            "details":None
        }}}},
        404: {
            "description": "도서 없음",
            "content":{
                "application/json":{
                    "example":{
                        "timestamp":"2025-02-01T10:40:00Z",
                        "path":"/admin/books/999",
                        "status":404,
                        "code":"RESOURCE_NOT_FOUND",
                        "message":"Book not found",
                        "details":{"book_id":999}
                    }
                }
            }
        },
        422:{"description":"유효성 검사 실패","content":{"application/json":{"example":{
            "timestamp":"2025-12-09T22:34:00Z",
            "path":"/admin/books/10",
            "status":422,
            "code":"VALIDATION_FAILED",
            "message":"Validation failed",
            "details":[{"field":"id","msg":"must be integer"}]
        }}}},
        500:{
            "description":"서버 오류",
            "content":{
                "application/json":{
                    "example":{
                        "timestamp":"2025-02-01T10:41:00Z",
                        "path":"/admin/books/10",
                        "status":500,
                        "code":"INTERNAL_SERVER_ERROR",
                        "message":"Book deletion failed",
                        "details":None
                    }
                }
            }
        }
    },
    openapi_extra={"security":[{"BearerAuth":[]}]}
)
def delete_admin_book(book_id:int, db:Session=Depends(get_db)):
    delete_book(db, book_id)

