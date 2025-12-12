from app.exceptions.error_response import ErrorResponse

def default_error_responses():
    return {
        400: {"model": ErrorResponse, "description": "잘못된 요청(형식 오류/누락)"},
        401: {"model": ErrorResponse, "description": "인증 필요"},
        403: {"model": ErrorResponse, "description": "권한 없음"},
        404: {"model": ErrorResponse, "description": "리소스 없음"},
        422: {"model": ErrorResponse, "description": "유효성 검증 실패"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    }
