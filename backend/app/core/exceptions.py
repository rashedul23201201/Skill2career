import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception with standardized code and status."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details


class BadRequestException(AppException):
    def __init__(self, message: str, error_code: str = "BAD_REQUEST", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST, error_code=error_code, details=details)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Could not validate credentials", error_code: str = "UNAUTHORIZED", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED, error_code=error_code, details=details)


class ForbiddenException(AppException):
    def __init__(self, message: str = "You do not have permission to perform this action", error_code: str = "FORBIDDEN", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN, error_code=error_code, details=details)


class NotFoundException(AppException):
    def __init__(self, message: str, error_code: str = "NOT_FOUND", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND, error_code=error_code, details=details)


class ConflictException(AppException):
    def __init__(self, message: str, error_code: str = "RESOURCE_CONFLICT", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT, error_code=error_code, details=details)


class TooManyRequestsException(AppException):
    def __init__(self, message: str = "Too many failed attempts. Please try again later.", error_code: str = "TOO_MANY_REQUESTS", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_429_TOO_MANY_REQUESTS, error_code=error_code, details=details)



def register_exception_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers for standard JSON error formatting."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        content: Dict[str, Any] = {
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
        }
        if exc.details is not None:
            content["details"] = exc.details
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "Invalid input")
            errors.append(f"{loc}: {msg}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Validation error: " + "; ".join(errors),
                "error_code": "VALIDATION_ERROR",
                "details": jsonable_encoder(exc.errors()),
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception occurred on %s %s: %s", request.method, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An unexpected internal server error occurred. Please try again later.",
                "error_code": "INTERNAL_SERVER_ERROR",
            },
        )
