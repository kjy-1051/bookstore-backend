# app/exceptions/handler.py
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime, timezone

from .custom_exception import CustomException
from .error_response import ErrorResponse
from .error_codes import ErrorCode
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

async def custom_exception_handler(request: Request, exc: CustomException):

    logger.error(
        f"CustomException | {exc.code} | {exc.message} | path={request.url.path}",
        exc_info=True
    )

    return JSONResponse(
        status_code=exc.status,
        content=ErrorResponse(
            timestamp=datetime.now(timezone.utc).isoformat(),
            path=request.url.path,
            status=exc.status,
            code=exc.code,
            message=exc.message,
            details=exc.details
        ).model_dump()
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):

    logger.error(
        f"HTTPException | status={exc.status_code} | path={request.url.path}",
        exc_info=True
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            timestamp=datetime.now(timezone.utc).isoformat(),
            path=request.url.path,
            status=exc.status_code,
            code=ErrorCode.UNKNOWN_ERROR,
            message=str(exc.detail)
        ).model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):

    logger.error(
        f"ValidationError | path={request.url.path}",
        exc_info=True
    )

    error_dict = {}
    for e in exc.errors():
        field = ".".join(str(x) for x in e.get("loc", []) if x != "query")
        msg = e.get("msg")
        error_dict[field] = msg

    return JSONResponse(
        status_code=422,
        content={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
            "status": 422,
            "code": ErrorCode.UNPROCESSABLE_ENTITY,
            "message": "Validation failed",
            "details": error_dict
        }
    )

