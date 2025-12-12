from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from app.services.comment_service import (
    create_comment,
    get_comments_by_book,
    update_comment,
    delete_comment,
    get_comments_paginated,
)

from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode

router = APIRouter(
    prefix="/comments",
    tags=["Comments"]
)


# =========================================================
# 📌 1. 댓글 생성
# =========================================================
@router.post(
    "/",
    response_model=CommentResponse,
    dependencies=[Depends(get_current_user)],
    status_code=201,
    openapi_extra={"security":[{"BearerAuth": []}]},
    responses={
        201: {
            "description": "댓글 작성 성공",
            "content": {"application/json": {"example": {
                "id": 15,
                "book_id": 3,
                "user_id": 5,
                "content": "재밌는 책!",
                "created_at": "2025-02-01T10:00:00Z"
            }}}
        },
        400: {
            "description": "잘못된 입력값",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T10:00:10Z",
                "path": "/comments",
                "status": 400,
                "code": "BAD_REQUEST",
                "message": "Invalid request body",
                "details": [{"field": "content", "msg": "최소 1자 이상 입력"}]
            }}}
        },
        401: {
            "description": "로그인 필요",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T10:00:00Z",
                "path": "/comments",
                "status": 401,
                "code": "UNAUTHORIZED",
                "message": "로그인이 필요합니다."
            }}}
        },
        404: {
            "description": "존재하지 않는 책",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T10:00:30Z",
                "path": "/comments",
                "status": 404,
                "code": "RESOURCE_NOT_FOUND",
                "message": "Book not found",
                "details": {"book_id": 999}
            }}}
        },
        422: {
            "description": "Validation 실패",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T10:00:15Z",
                "path": "/comments",
                "status": 422,
                "code": "VALIDATION_ERROR",
                "message": "입력값 검증 실패",
                "details": [{"field": "content", "msg": "최소 1자 이상 입력"}]
            }}}
        },
        500: {
            "description": "서버 오류",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T10:00:40Z",
                "path": "/comments",
                "status": 500,
                "code": "INTERNAL_SERVER_ERROR",
                "message": "댓글 생성 중 오류"
            }}}
        }
    }
)
def add_comment(
    data: CommentCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return create_comment(db, user["id"], data)



# =========================================================
# 📌 2. 댓글 페이징 조회 (book_id 기반)
# =========================================================
@router.get(
    "/",
    response_model=dict,
    responses={
        200: {
            "description": "댓글 목록 조회 성공",
            "content": {"application/json": {"example": {
                "content": [
                    {
                        "id": 1,
                        "book_id": 1,
                        "user_id": 2,
                        "content": "도움이 되는 책입니다.",
                        "created_at": "2025-02-01T12:10:00Z"
                    }
                ],
                "page": 1,
                "size": 10,
                "totalElements": 23,
                "totalPages": 3,
                "sort": "id,DESC",
                "keyword": None
            }}}
        },
        422: {
            "description": "Query validation 실패",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T12:10:30Z",
                "path": "/comments",
                "status": 422,
                "code": "VALIDATION_FAILED",
                "message": "Validation failed",
                "details": [{"field": "page", "msg": "must be integer"}]
            }}}
        },
        500: {
            "description": "서버 오류",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T12:11:00Z",
                "path": "/comments",
                "status": 500,
                "code": "INTERNAL_SERVER_ERROR",
                "message": "댓글 조회 실패"
            }}}
        }
    }
)
def list_comments(
    book_id: int,
    page: int = 1,
    size: int = 10,
    sort: str = "id,DESC",
    keyword: str | None = None,
    db: Session = Depends(get_db)
):
    return get_comments_paginated(db, book_id, page, size, sort, keyword)



# =========================================================
# 📌 3. 특정 도서 댓글 전체 조회 (공개)
# =========================================================
@router.get(
    "/book/{book_id}",
    response_model=List[CommentResponse],
    responses={
        200: {
            "description": "도서 댓글 전체 조회 성공",
            "content": {"application/json": {"example": [
                {
                    "id": 10,
                    "book_id": 5,
                    "user_id": 3,
                    "content": "유익한 내용",
                    "created_at": "2025-02-01T13:00:00Z"
                },
                {
                    "id": 11,
                    "book_id": 5,
                    "user_id": 2,
                    "content": "추천합니다",
                    "created_at": "2025-02-01T13:02:00Z"
                }
            ]}}
        },
        404: {
            "description": "책 없음",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T13:02:30Z",
                "path": "/comments/book/999",
                "status": 404,
                "code": "RESOURCE_NOT_FOUND",
                "message": "Book not found",
                "details": {"book_id": 999}
            }}}
        }
    }
)
def list_comments_public(
    book_id: int,
    db: Session = Depends(get_db)
):
    return get_comments_by_book(db, book_id)



# =========================================================
# 📌 4. 댓글 수정
# =========================================================
@router.patch(
    "/{comment_id}",
    response_model=CommentResponse,
    dependencies=[Depends(get_current_user)],
    openapi_extra={"security":[{"BearerAuth": []}]},
    responses={
        200: {
            "description": "댓글 수정 성공",
            "content": {"application/json": {"example": {
                "id": 11,
                "book_id": 3,
                "user_id": 5,
                "content": "수정한 댓글입니다.",
                "created_at": "2025-02-01T13:20:00Z"
            }}}
        },
        401: {
            "description": "로그인 필요",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T13:15:00Z",
                "path": "/comments/11",
                "status": 401,
                "code": "UNAUTHORIZED",
                "message": "로그인이 필요합니다."
            }}}
        },
        403: {
            "description": "권한 없음",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T13:16:00Z",
                "path": "/comments/11",
                "status": 403,
                "code": "FORBIDDEN",
                "message": "수정 권한 없음",
                "details": {"comment_id": 11}
            }}}
        },
        404: {
            "description": "댓글 없음",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T13:17:00Z",
                "path": "/comments/11",
                "status": 404,
                "code": "RESOURCE_NOT_FOUND",
                "message": "Comment not found",
                "details": {"comment_id": 11}
            }}}
        },
        422: {
            "description": "Validation 실패",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T13:18:00Z",
                "path": "/comments/11",
                "status": 422,
                "code": "VALIDATION_ERROR",
                "message": "댓글 내용 형식 오류",
                "details": [{"field": "content", "msg": "최소 1자 이상 입력해야 합니다."}]
            }}}
        }
    }
)
def edit_comment(
    comment_id: int,
    data: CommentUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return update_comment(db, comment_id, user["id"], data)



# =========================================================
# 📌 5. 댓글 삭제
# =========================================================
@router.delete(
    "/{comment_id}",
    dependencies=[Depends(get_current_user)],
    openapi_extra={"security":[{"BearerAuth": []}]},
    responses={
        200: {
            "description": "댓글 삭제 성공",
            "content": {"application/json": {"example": {
                "message": "deleted"
            }}}
        },
        401: {
            "description": "로그인 필요",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T13:40:00Z",
                "path": "/comments/10",
                "status": 401,
                "code": "UNAUTHORIZED",
                "message": "로그인이 필요합니다."
            }}}
        },
        403: {
            "description": "삭제 권한 없음",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T13:41:00Z",
                "path": "/comments/10",
                "status": 403,
                "code": "FORBIDDEN",
                "message": "삭제 권한 없음",
                "details": {"comment_id": 10}
            }}}
        },
        404: {
            "description": "댓글 없음",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T13:42:00Z",
                "path": "/comments/10",
                "status": 404,
                "code": "RESOURCE_NOT_FOUND",
                "message": "Comment not found",
                "details": {"comment_id": 10}
            }}}
        },
        500: {
            "description": "서버 오류",
            "content": {"application/json": {"example": {
                "timestamp": "2025-02-01T13:43:00Z",
                "path": "/comments/10",
                "status": 500,
                "code": "INTERNAL_SERVER_ERROR",
                "message": "댓글 삭제 실패"
            }}}
        }
    }
)
def remove_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    delete_comment(db, comment_id, user["id"])
    return {"message": "deleted"}
