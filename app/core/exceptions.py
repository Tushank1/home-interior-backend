from fastapi import HTTPException, Request,status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging


logger = logging.getLogger(__name__)


class CustomException(Exception):
    """Base custom exception."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(CustomException):
    """Authentication related errors."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(CustomException):
    """Authorization related errors."""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)
    

class ValidationError(CustomException):
    """Validation related errors."""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class NotFoundError(CustomException):
    """Resource not found errors."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ConflictError(CustomException):
    """Resource conflict errors."""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status.HTTP_409_CONFLICT)


async def custom_exception_handler(request: Request, exc: CustomException):
    """Handle custom exceptions."""
    logger.error(f"Custom exception: {exc.message}, Status: {exc.status_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "type": type(exc).__name__,
                "status_code": exc.status_code
            }
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP exception: {exc.detail}, Status: {exc.status_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "HTTPException",
                "status_code": exc.status_code
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions."""
    logger.error(f"Validation exception: {str(exc.errors())}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "message": "Validation failed",
                "type": "ValidationError",
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "details": str(exc.errors())
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "Internal server error",
                "type": "InternalServerError",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
        }
    )