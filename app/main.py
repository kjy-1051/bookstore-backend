from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import time
from datetime import datetime, timezone

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from contextlib import asynccontextmanager
from app.core.database import get_engine, Base

from app.routers.user_router import router as user_router
from app.routers.auth_router import router as auth_router
from app.routers.book_router import router as book_router
from app.routers.admin_book_router import router as admin_book_router
from app.routers.comment_router import router as comment_router
from app.routers.rating_router import router as rating_router
from app.routers.admin_user_router import router as admin_user_router
from app.routers.admin_dashboard_router import router as admin_dashboard_router

from app.models.rating import Rating   # 추가하지 않으면 테이블 생성 안 됨
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

from contextlib import asynccontextmanager
from app.core.database import get_engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("✅ DB tables ensured")
    yield


app = FastAPI(
    title="Bookstore API",
    description="A simple FastAPI Bookstore service",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan
)

app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")

        # 1MB 제한 (과제용으로 충분)
        if content_length and int(content_length) > 1_000_000:
            raise HTTPException(
                status_code=413,
                detail="Payload too large"
            )

        return await call_next(request)
    
app.add_middleware(MaxBodySizeMiddleware)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    print(
        f"{request.method} "
        f"{request.url.path} "
        f"{response.status_code} "
        f"{duration:.3f}s"
    )
    return response

BUILD_TIME = datetime.now(timezone.utc)

@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "build_time": BUILD_TIME.isoformat(),
        "server_time": datetime.now(timezone.utc).isoformat()
    }

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Bookstore API",
        version="1.0",
        description="Swagger Auth Setup",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    app.openapi_schema = openapi_schema
    return openapi_schema

app.openapi = custom_openapi

# Routers (항상 custom_openapi 정의 다음에)
app.include_router(auth_router, prefix="/auth")
app.include_router(user_router, prefix="/users")
app.include_router(book_router, prefix="/books")
app.include_router(admin_book_router)
app.include_router(comment_router)
app.include_router(rating_router, prefix="/ratings")
app.include_router(admin_user_router)
app.include_router(admin_dashboard_router)


from app.exceptions.handler import (
    custom_exception_handler,
    validation_exception_handler,
    http_exception_handler,
)
from app.exceptions.custom_exception import CustomException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app.add_exception_handler(CustomException, custom_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

