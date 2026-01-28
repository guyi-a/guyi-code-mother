import logging
from typing import Any
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings

logger = logging.getLogger(__name__)


class CustomException(Exception):
    """自定义异常基类"""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(CustomException):
    """资源未找到异常"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class BadRequestException(CustomException):
    """错误请求异常"""
    def __init__(self, message: str = "Bad request"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class UnauthorizedException(CustomException):
    """未授权异常"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(CustomException):
    """禁止访问异常"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


async def custom_exception_handler(request: Request, exc: CustomException) -> JSONResponse:
    """自定义异常处理器"""
    logger.error(f"CustomException: {exc.message} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "status_code": exc.status_code,
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """HTTP 异常处理器"""
    logger.warning(f"HTTPException: {exc.detail} - Path: {request.url.path} - Status: {exc.status_code}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """请求验证异常处理器"""
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Validation error")
        error_messages.append(f"{field}: {message}")
    
    error_detail = "; ".join(error_messages)
    logger.warning(f"ValidationError: {error_detail} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation error",
            "details": errors,
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        }
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """数据库异常处理器"""
    error_message = "Database error occurred"
    
    if settings.DEBUG:
        error_message = str(exc)
    
    logger.error(f"DatabaseError: {str(exc)} - Path: {request.url.path}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": error_message,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    error_message = "Internal server error"
    
    if settings.DEBUG:
        error_message = str(exc)
    
    logger.error(f"UnhandledException: {str(exc)} - Path: {request.url.path}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": error_message,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
    )


def setup_exception_handlers(app):
    """设置全局异常处理器"""
    # 自定义异常
    app.add_exception_handler(CustomException, custom_exception_handler)
    
    # HTTP 异常
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # 验证异常
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # 数据库异常
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    
    # 通用异常（放在最后，作为兜底）
    app.add_exception_handler(Exception, general_exception_handler)

