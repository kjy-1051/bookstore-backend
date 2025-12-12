# app/routers/book_router.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.book import BookResponse
from app.services.book_service import (
    get_books_paginated,
    get_book_by_id,
    filter_by_price,
    get_latest_books,
    search_books,
    get_top_rated_books,
    get_top_commented_books,
    get_random_books,
)

# 🔥 추가: 커스텀 예외
from app.exceptions.custom_exception import CustomException
from app.exceptions.error_codes import ErrorCode

router = APIRouter(tags=["Books"])


# =========================================================
# 📌 최신 도서 목록
# =========================================================
@router.get(
    "/latest",
    response_model=List[BookResponse],
    summary="최신 등록 도서",
    responses={
        200: {
            "description": "최신 도서 조회 성공",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 30,
                            "title": "Modern C++",
                            "price": 27000,
                            "authors": ["Scott Meyers"],
                            "categories": ["C++"],
                            "summary": "현대 C++ 기법 정리",
                        }
                    ]
                }
            },
        },
        500: {
            "description": "서버 내부 오류",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-02-02T11:30:00Z",
                        "path": "/books/latest",
                        "status": 500,
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "최신 도서 조회 중 오류가 발생했습니다."
                    }
                }
            },
        },
    },
)
def get_latest(db: Session = Depends(get_db)):
    return [BookResponse(**b) for b in get_latest_books(db)]

# =========================================================
# 📌 전체 책 조회 (페이지네이션)
# =========================================================
@router.get(
    "/",
    summary="책 전체 조회",
    description="Pagination + Sort 지원",
    responses={
        200: {
            "description": "검색 성공",
            "content": {
                "application/json": {
                    "example": {
                        "content": [
                            {
                                "id": 37,
                                "isbn": "978-1-267-85901-3",
                                "title": "Voluptatem exercitationem dolor.",
                                "price": 39394,
                                "publisher": "(유) 중앙푸른은행",
                                "summary": "Nostrum necessitatibus placeat nihil architecto totam.",
                                "publicationDate": "2025-03-23",
                                "authors": ["백재현","이지우","윤진호"],
                                "categories": ["철학"]
                            }
                        ],
                        "page": 1,
                        "size": 10,
                        "totalElements": 1,
                        "totalPages": 1,
                        "sort": "id,ASC"
                    }
                }
            },
        },
        400:{
            "description":"잘못된 Query 값",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T12:00:00Z","path":"/books",
                "status":400,"code":"INVALID_QUERY_PARAM",
                "message":"size는 1~50 사이여야 합니다.","details":{"size":0}
            }}}
        },
        422:{
            "description":"Validation 실패",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-01T12:00:40Z","path":"/books",
                "status":422,"code":"UNPROCESSABLE_ENTITY",
                "message":"Validation failed",
                "details":[{"field":"page","msg":"must be integer"}]
            }}}
        },
        500: {
            "description": "서버 내부 오류",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-02-01T12:00:00Z",
                        "path": "/books",
                        "status": 500,
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "책 목록을 불러오는 중 오류가 발생했습니다.",
                        "details": None,
                    }
                }
            },
        },
    },
)
def list_books(
    page: int = Query(1),
    size: int = Query(10),
    sort: str = "id,ASC",
    db: Session = Depends(get_db),
):
    # 🔥 페이지 0 또는 음수 요청 → CustomException
    if page < 1:
        raise CustomException(
            status=400,
            code=ErrorCode.INVALID_QUERY_PARAM,
            message="page는 1 이상이어야 합니다.",
            details={"page": page}
        )

    # 🔥 size 1 미만 → CustomException (Postman 테스트용 PERFECT)
    # 🔥 size 최소·최대 모두 제한
    if size < 1 or size > 50:
        raise CustomException(
            status=400,
            code=ErrorCode.INVALID_QUERY_PARAM,
            message="size는 1~50 사이여야 합니다.",
            details={"size": size}
        )
    return get_books_paginated(db, page, size, sort)


# =========================================================
# 📌 통합 검색 (keyword + category)
# =========================================================
@router.get(
    "/search",
    summary="책 검색 조회",
    description="검색 가능 키워드: 제목, 저자, 요약, 카테고리, ISBN",
    responses={
        200: {
            "description": "검색 결과",
            "content": {
                "application/json": {
                    "example": {
                        "content": [
                            {
                            "id": 37,
                            "isbn": "978-1-267-85901-3",
                            "title": "Voluptatem exercitationem dolor.",
                            "price": 39394,
                            "publisher": "(유) 중앙푸른은행",
                            "summary": "Nostrum necessitatibus placeat nihil architecto totam.",
                            "publicationDate": "2025-03-23",
                            "authors": [
                                "백재현",
                                "이지우",
                                "윤진호"
                            ],
                            "categories": [
                                "철학"
                            ]
                            }
                        ],
                        "page": 1,
                        "size": 3,
                        "totalElements": 1,
                        "totalPages": 1,
                        "sort": "id,ASC",
                        "keyword": "백재현",
                        "category": "철학"
                        }
                }
            },
        },
        400: {
            "description": "잘못된 검색 요청",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-02-02T12:00:00Z",
                        "path": "/books/search",
                        "status": 400,
                        "code": "INVALID_QUERY_PARAM",
                        "message": "page는 1 이상이어야 합니다.",
                        "details": {"page": 0}
                    }
                }
            },
        },
        422:{
        "description":"Validation 실패 (Query 검증)",
        "content":{"application/json":{"example":{
            "timestamp":"2025-02-02T12:00:00Z",
            "path":"/books/search",
            "status":422,
            "code":"VALIDATION_FAILED",
            "message":"Validation failed",
            "details":[
                {"field": "size", "msg": "must be <= 50"}
            ]
        }}}
        },
        500: {
            "description": "서버 오류",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-02-02T12:00:10Z",
                        "path": "/books/search",
                        "status": 500,
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "검색 처리 중 오류가 발생했습니다."
                    }
                }
            },
        },
    },
)
def search_books_api(
    keyword: str | None = None,
    category: str | None = None,
    page: int = 1,
    size: int = 10,
    sort: str = "id,ASC",
    db: Session = Depends(get_db),
):
    """
    통합 검색 API
    - keyword: 제목/요약/저자 포함검색
    - category: 카테고리 필터링
    - page/size: 페이지네이션
    - sort=필드,정렬방향 (예: price,DESC)
    """
    if page < 1:
        raise CustomException(
            status=400,
            code=ErrorCode.INVALID_QUERY_PARAM,
            message="page는 1 이상이어야 합니다.",
            details={"page": page}
        )

    if size < 1 or size > 50:
        raise CustomException(
            status=400,
            code=ErrorCode.INVALID_QUERY_PARAM,
            message="size는 1~50 사이여야 합니다.",
            details={"size": size}
        )

    return search_books(db, keyword, category, page, size, sort)


# =========================================================
# 📌 가격 필터
# =========================================================
@router.get(
    "/filter/price",
    summary="가격 필터 조회",
    responses={
        200: {
            "description": "가격 필터 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "content": [
                            {
                                "id": 12,
                                "title": "Clean Code",
                                "price": 18000,
                                "authors": ["Robert C. Martin"],
                                "categories": ["Programming"],
                                "summary": "좋은 코드 작성 원칙을 설명합니다."
                            }
                        ],
                        "page": 1,
                        "size": 10,
                        "totalElements": 1,
                        "totalPages": 1,
                        "sort": "price,ASC",
                        "min_price": 10000,
                        "max_price": 20000
                    }
                }
            },
        },
        400: {
            "description": "잘못된 가격 범위 (INVALID_QUERY_PARAM)",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-02-01T12:00:00Z",
                        "path": "/books/filter/price",
                        "status": 400,
                        "code": "INVALID_QUERY_PARAM",
                        "message": "min_price must be <= max_price",
                        "details": {
                            "min_price": 1000,
                            "max_price": 100
                        }
                    }
                }
            },
        },
        422: {
            "description":"Validation 실패",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-02T12:00:30Z",
                "path":"/books/filter/price",
                "status":422,
                "code":"VALIDATION_FAILED",
                "message":"Validation failed",
                "details": {
                    "min_price": "Input should be a valid integer",
                    "max_price": "Input should be a valid integer"
                }
            }}}
        },
        500: {
            "description": "서버 내부 오류",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-02-01T12:30:00Z",
                        "path": "/books/filter/price",
                        "status": 500,
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "서버 처리 중 오류가 발생했습니다."
                    }
                }
            },
        },
    },
)
def filter_books_by_price(
    min_price: str | None = None,
    max_price: str | None = None,
    page: str = "1",
    size: str = "10",
    sort: str = "price,ASC",
    db: Session = Depends(get_db)
):
    # ---------- 1) page / size 변환 ----------
    try:
        page_int = int(page)
        size_int = int(size)
    except ValueError:
        raise CustomException(
            status=422,
            code=ErrorCode.UNPROCESSABLE_ENTITY,
            message="Validation failed",
            details={"page/size": "must be integer"}
        )

    if page_int < 1 or size_int < 1 or size_int > 50:
        raise CustomException(
            status=400,
            code=ErrorCode.INVALID_QUERY_PARAM,
            message="Invalid pagination value",
            details={"page": page_int, "size": size_int}
        )

    # ---------- 2) price 변환 ----------
    try:
        min_val = int(min_price) if min_price is not None else None
        max_val = int(max_price) if max_price is not None else None
    except ValueError:
        raise CustomException(
            status=422,
            code=ErrorCode.UNPROCESSABLE_ENTITY,
            message="Validation failed",
            details={"min_price/max_price": "must be integer"}
        )

    # ---------- 3) 논리 오류 ----------
    if min_val is not None and max_val is not None and min_val > max_val:
        raise CustomException(
            status=400,
            code=ErrorCode.INVALID_QUERY_PARAM,
            message="min_price must be <= max_price",
            details={"min_price": min_val, "max_price": max_val}
        )

    return filter_by_price(db, min_val, max_val, page_int, size_int, sort)

# =========================================================
# 📌 평균 평점 높은 책 TOP N
# =========================================================
@router.get(
    "/popular/ratings",
    summary="평점 상위 도서 조회",
    responses={
        200: {
            "description": "평점 상위 도서 목록",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 24,
                            "title": "Neque.",
                            "avg_score": 5,
                            "rating_count": 1
                        },
                        {
                            "id": 3,
                            "title": "Vel assumenda tempore.",
                            "avg_score": 4.5,
                            "rating_count": 2
                        }
                    ]
                }
            },
        },
        400: {
            "description": "잘못된 가격 범위 (INVALID_QUERY_PARAM)",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-12-11T10:54:01.994295+00:00",
                        "path": "/books/popular/ratings",
                        "status": 400,
                        "code": "INVALID_QUERY_PARAM",
                        "message": "limit must be >= 1",
                        "details": {
                            "limit": 0
                        }
                    }
                }
            },
        },
        422: {
            "description": "Validation 실패",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-12-11T10:42:25.912840+00:00",
                        "path": "/books/popular/ratings",
                        "status": 422,
                        "code": "UNPROCESSABLE_ENTITY",
                        "message": "Validation failed",
                        "details": {
                            "limit": "must be integer"
                        }
                    }
                }
            }
        },
        500: {
            "description": "서버 오류",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-02-01T16:00:00Z",
                        "path": "/books/popular/ratings",
                        "status": 500,
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "상위 평점 도서 조회 중 오류 발생"
                    }
                }
            }
        }
    },
)

def popular_books_by_rating(limit: str = "10", db: Session = Depends(get_db)):
    try:
        limit_int = int(limit)
    except ValueError:
        raise CustomException(
            422,
            ErrorCode.UNPROCESSABLE_ENTITY,
            "Validation failed",
            details={"limit": "must be integer"}
        )

    if limit_int < 1:
        raise CustomException(
            400,
            ErrorCode.INVALID_QUERY_PARAM,
            "limit must be >= 1",
            details={"limit": limit_int}
        )

    return get_top_rated_books(db, limit_int)


# =========================================================
# 📌 댓글 많은 책 TOP N
# =========================================================
@router.get(
    "/popular/comments",
    summary="댓글 많은 도서 조회",
    responses={
        200: {
            "description": "댓글 수 상위 도서 목록",
            "content": {
                "application/json": {
                    "example": [
                        {"book_id": 1, "title": "CSAPP", "comment_count": 123},
                        {"book_id": 5, "title": "Clean Code", "comment_count": 98},
                    ]
                }
            },
        },
        400: {
            "description": "잘못된 가격 범위 (INVALID_QUERY_PARAM)",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-12-11T10:52:52.112507+00:00",
                        "path": "/books/popular/comments",
                        "status": 400,
                        "code": "INVALID_QUERY_PARAM",
                        "message": "limit must be >= 1",
                        "details": {
                            "limit": 0
                        }
                    }
                }
            },
        },
        422: {
            "description": "Validation 실패",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-12-11T10:44:34.457546+00:00",
                        "path": "/books/popular/comments",
                        "status": 422,
                        "code": "UNPROCESSABLE_ENTITY",
                        "message": "Validation failed",
                        "details": {
                            "limit": "must be integer"
                        }
                    }
                }
            }
        },
        500: {
            "description": "서버 오류",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp":"2025-02-01T16:10:00Z",
                        "path":"/books/popular/comments",
                        "status":500,
                        "code":"INTERNAL_SERVER_ERROR",
                        "message":"댓글 상위 도서 조회 중 오류 발생"
                    }
                }
            }
        }
    },
)

def popular_books_by_comments(limit: str = "10", db: Session = Depends(get_db)):
    try:
        limit_int = int(limit)
    except ValueError:
        raise CustomException(
            422,
            ErrorCode.UNPROCESSABLE_ENTITY,
            "Validation failed",
            details={"limit": "must be integer"}
        )

    if limit_int < 1:
        raise CustomException(
            400,
            ErrorCode.INVALID_QUERY_PARAM,
            "limit must be >= 1",
            details={"limit": limit_int}
        )

    return get_top_commented_books(db, limit_int)


# =========================================================
# 📌 랜덤 추천
# =========================================================
@router.get(
    "/recommend/random",
    summary="랜덤 도서 추천",
    responses={
        200: {
            "description": "랜덤 도서 목록",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 40,
                            "isbn": "978-0-7413-1225-9",
                            "title": "Sunt sed.",
                            "price": 10753,
                            "publisher": "(유) 첨단",
                            "summary": "Velit explicabo possimus voluptates nostrum.",
                            "publicationDate": "2025-07-19",
                            "authors": [
                            "김중수"
                            ],
                            "categories": [
                            "철학",
                            "소설",
                            "자기계발"
                            ]
                        }
                    ]
                }
            },
        },
        400: {
            "description": "잘못된 가격 범위 (INVALID_QUERY_PARAM)",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-12-11T10:47:30.583083+00:00",
                        "path": "/books/recommend/random",
                        "status": 400,
                        "code": "INVALID_QUERY_PARAM",
                        "message": "limit must be >= 1",
                        "details": {
                            "limit": 0
                        }
                    }
                }
            },
        },
        422: {
            "description": "Validation 실패",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-12-11T10:46:37.856298+00:00",
                        "path": "/books/recommend/random",
                        "status": 422,
                        "code": "UNPROCESSABLE_ENTITY",
                        "message": "Validation failed",
                        "details": {
                            "limit": "must be integer"
                        }
                    }
                }
            }
        },
        500: {
            "description": "서버 오류",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-02-02T12:20:00Z",
                        "path": "/books/recommend/random",
                        "status": 500,
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "랜덤 도서 추천 중 오류 발생"
                    }
                }
            }
        }
    },
)

def random_books(limit: str = "5", db: Session = Depends(get_db)):
    try:
        limit_int = int(limit)
    except ValueError:
        raise CustomException(
            422,
            ErrorCode.UNPROCESSABLE_ENTITY,
            "Validation failed",
            details={"limit": "must be integer"}
        )

    if limit_int < 1:
        raise CustomException(
            400,
            ErrorCode.INVALID_QUERY_PARAM,
            "limit must be >= 1",
            details={"limit": limit_int}
        )

    return get_random_books(db, limit_int)

# =========================================================
# 📌 단일 책 조회 (여기만 예외 처리 변경)
# =========================================================
@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="ID로 도서 조회",
    responses={
        200: {
            "description": "도서 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": 10,
                        "title": "Database System Concepts",
                        "price": 25000,
                        "authors": ["Silberschatz"],
                        "categories": ["DB"],
                        "summary": "데이터베이스 기본 개념을 설명하는 책",
                    }
                }
            },
        },
        404: {
            "description": "도서 없음",
            "content": {
                "application/json": {
                    "example": {
                        "timestamp": "2025-02-01T12:10:00Z",
                        "path": "/books/9999",
                        "status": 404,
                        "code": "RESOURCE_NOT_FOUND",
                        "message": "Book not found",
                        "details": {"book_id": 9999},
                    }
                }
            },
        },
        422:{
            "description":"Validation 실패",
            "content":{"application/json":{"example":{
                "timestamp":"2025-02-02T12:01:10Z",
                "path":"/books/abc",
                "status":422,
                "code": "UNPROCESSABLE_ENTITY",
                "message": "Validation failed",
                "details": {
                    "book_id": "must be integer"
                }
                }}}
        },
        500:{"description":"서버 오류"}
    },
)
def get_book(book_id: str, db: Session = Depends(get_db)):
    # 문자열 → int 변환
    try:
        book_id_int = int(book_id)
    except ValueError:
        raise CustomException(
            422,
            ErrorCode.UNPROCESSABLE_ENTITY,
            "Validation failed",
            details={"book_id": "must be integer"}
        )

    book = get_book_by_id(db, book_id_int)
    if not book:
        raise CustomException(
            404,
            ErrorCode.RESOURCE_NOT_FOUND,
            "Book not found",
            details={"book_id": book_id_int}
        )

    return BookResponse(**book)