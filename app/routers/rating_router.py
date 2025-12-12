# app/routers/rating_router.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.rating import RatingCreate, RatingResponse
from app.services.rating_service import (
    create_rating,
    update_rating,
    get_book_ratings,
    delete_rating,
    get_book_rating_summary,
)
from app.core.database import get_db
from app.core.security import get_current_user

from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode

router = APIRouter(tags=["Ratings"])

# ===================== 1. 평점 등록 =====================
@router.post(
    "/{book_id}",
    response_model=RatingResponse,
    dependencies=[Depends(get_current_user)],
    openapi_extra={"security":[{"BearerAuth": []}]},
    summary="도서 평점 신규 등록 (1회만 가능)",
    status_code=201,
    responses={
        201: {
            "description": "평점 등록 성공",
            "content": {"application/json": {"example":
                {"id": 12, "book_id": 3, "user_id": 5, "score": 5}
            }},
        },
        401:{
        "description":"로그인 필요",
        "content":{"application/json":{"example":{
            "timestamp":"2025-02-01T10:00:00Z","path":"/ratings/3",
            "status":401,"code":"UNAUTHORIZED",
            "message":"로그인이 필요합니다."
        }}}
        },
        409:{
            "description":"이미 평점을 등록함 (STATE_CONFLICT)",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T10:10:10Z","path":"/ratings/3",
                "status":409,"code":"STATE_CONFLICT",
                "message":"이미 이 책에 평점을 등록했습니다.",
                "details":{"book_id":3}
            }}}
        },
        422:{
            "description":"Validation 실패",
            "content":{"application/json":{"example":{
                "timestamp": "2025-12-11T11:58:07.577564+00:00",
                "path": "/ratings/2",
                "status": 422,
                "code": "VALIDATION_FAILED",
                "message": "Validation failed",
                "details": [
                    {
                        "field": "score",
                        "msg": "must be between 1~5"
                    }
                ]
            }}}
        },
        500:{
            "description":"서버 오류",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T10:11:00Z","path":"/ratings/3",
                "status":500,"code":"INTERNAL_SERVER_ERROR",
                "message":"Rating create failed",
                "details":None
            }}}
        }
    }
)
def create_rating_api(book_id:int, data:RatingCreate, user=Depends(get_current_user), db:Session=Depends(get_db)):
    return create_rating(db, user["id"], book_id, data.score)


# ===================== 2. 평점 수정 =====================
@router.patch(
    "/{book_id}",
    response_model=RatingResponse,
    dependencies=[Depends(get_current_user)],
    openapi_extra={"security":[{"BearerAuth": []}]},
    summary="기존 평점 수정",
    responses={
        200: {"description":"수정 성공","content":{"application/json":{"example":{
            "id":12,"book_id":3,"user_id":5,"score":4
        }}}},
        401:{
        "description":"로그인 필요",
        "content":{"application/json":{"example":{
            "timestamp":"2025-02-01T11:15:00Z","path":"/ratings/3",
            "status":401,"code":"UNAUTHORIZED",
            "message":"인증이 필요합니다."
        }}}
        },
        404:{
            "description":"평점 없음",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T11:20:00Z","path":"/ratings/3",
                "status":404,"code":"RESOURCE_NOT_FOUND",
                "message":"평점을 찾을 수 없습니다.",
                "details":{"book_id":3}
            }}}
        },
        422:{
            "description":"Validation 실패",
            "content":{"application/json":{"example":{
            "timestamp": "2025-12-11T12:03:38.031639+00:00",
            "path": "/ratings/1",
            "status": 422,
            "code": "VALIDATION_FAILED",
            "message": "Validation failed",
            "details": [
                {
                    "field": "score",
                    "msg": "value must be between 1~5"
                }
            ]
        }}}
        },
        500:{
            "description":"서버 오류",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T11:22:00Z","path":"/ratings/3",
                "status":500,"code":"INTERNAL_SERVER_ERROR",
                "message":"Rating update failed"
            }}}
        }
    }
)
def update_rating_api(book_id:int, data:RatingCreate, user=Depends(get_current_user), db:Session=Depends(get_db)):
    return update_rating(db, user["id"], book_id, data.score)


# ===================== 3. 평점 목록 조회 =====================
@router.get(
    "/",
    summary="도서 평점 목록 조회",
    response_model=dict,
    responses={
        200: {
            "description": "조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "content": [
                            {
                                "id": 1,
                                "user_id": 2,
                                "book_id": 1,
                                "score": 5
                            }
                        ],
                        "page": 1,
                        "size": 10,
                        "totalElements": 3,
                        "totalPages": 1,
                        "sort": "id,DESC",
                        "keyword": None,
                        "minScore": None,
                        "maxScore": None
                    }
                }
            }
        },
        422:{
            "description":"Validation 실패",
            "content":{"application/json":{"example":{
                "timestamp": "2025-12-11T12:09:38.308298+00:00",
                "path": "/ratings/",
                "status": 422,
                "code": "VALIDATION_FAILED",
                "message": "Validation failed",
                "details": [
                    {
                        "field": "size",
                        "msg": "must be >= 1"
                    }
                ]
            }}}
        },
        500:{
            "description":"서버 오류",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T12:00:30Z","path":"/ratings",
                "status":500,"code":"INTERNAL_SERVER_ERROR",
                "message":"Rating list fetch failed"
            }}}
        }
    }
)
def list_ratings(
    book_id:int,
    page:int=1,
    size:int=10,
    sort:str="id,DESC",
    keyword:str|None=None,
    minScore:int|None=None,
    maxScore:int|None=None,
    db:Session=Depends(get_db)
):
    return get_book_ratings(db, book_id, page, size, sort, keyword, minScore, maxScore)


# ===================== 4. 평점 삭제 =====================
@router.delete(
    "/{book_id}",
    summary="평점 삭제 (본인만)",
    dependencies=[Depends(get_current_user)],
    openapi_extra={"security":[{"BearerAuth": []}]},
    responses={
        200: {"description":"삭제 성공","content":{"application/json":{"example":{
            "message":"Rating deleted"
        }}}},
        401:{
        "description":"로그인 필요",
        "content":{"application/json":{"example":{
            "timestamp":"2025-02-01T17:00:00Z","path":"/ratings/3",
            "status":401,"code":"UNAUTHORIZED",
            "message":"로그인이 필요합니다."
        }}}
        },
        404:{
            "description":"평점 없음",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T17:00:00Z","path":"/ratings/3",
                "status":404,"code":"RESOURCE_NOT_FOUND",
                "message":"Rating not found",
                "details":{"book_id":3}
            }}}
        },
        500:{
            "description":"서버 오류",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T17:01:00Z","path":"/ratings/3",
                "status":500,"code":"INTERNAL_SERVER_ERROR",
                "message":"Rating delete failed"
            }}}
        }
    }
)
def remove_rating(book_id:int, user=Depends(get_current_user), db:Session=Depends(get_db)):
    delete_rating(db, user["id"], book_id)   # ← 성공/실패 예외 둘 다 service가 처리
    return {"message":"Rating deleted"}


# ===================== 5. 평점 요약 =====================
@router.get(
    "/summary/{book_id}",
    summary="해당 도서 평점 요약 (평균, 개수)",
    responses={
        200: {
        "description": "조회 성공",
        "content": {
            "application/json": {
                "example": {
                    "bookId": 3,
                    "averageRating": 4.6,
                    "reviewCount": 32
                }
            }
        }
    },
    404: {
        "description": "도서 없음",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-02-01T16:30:00Z",
                    "path": "/ratings/summary/999",
                    "status": 404,
                    "code": "RESOURCE_NOT_FOUND",
                    "message": "Book not found",
                    "details": {"book_id": 999}
                }
            }
        }
    },
    500: {
        "description": "서버 오류",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-02-01T16:31:00Z",
                    "path": "/ratings/summary/3",
                    "status": 500,
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Rating summary fetch failed"
                }
            }
        }
    }
    }
)
def rating_summary(book_id:int, db:Session=Depends(get_db)):
    return get_book_rating_summary(db, book_id)

