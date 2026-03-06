from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.response.response import handle_error


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles validation exceptions raised during request processing.

    This function is triggered when a request validation error occurs (e.g., when input data does not match the expected model schema).
    It formats the errors and returns a standardized error response.

    Args:
        request (Request): The incoming request that caused the validation error.
        exc (RequestValidationError): The exception raised due to validation failure.

    Returns:
        JSONResponse: A standardized response with error details including a list of formatted validation errors.

    Example:
        validation_exception_handler(request, exc)
        # Returns a JSON response with validation error details.
    """
    errors = exc.errors()
    formatted_errors = [
        {"field": error["loc"][-1], "error": error["msg"]} for error in errors
    ]

    return handle_error(
        HTTP_422_UNPROCESSABLE_ENTITY, "Validation error", formatted_errors
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handles HTTP exceptions raised during request processing.

    This function is triggered when an HTTP exception is raised (e.g., a client error like 404 or 403).
    It returns a standardized error response based on the exception status code and message.

    Args:
        request (Request): The incoming request that caused the HTTP exception.
        exc (HTTPException): The HTTP exception raised during the request.

    Returns:
        JSONResponse: A standardized response with the exception's status code and message.

    Example:
        http_exception_handler(request, exc)
        # Returns a JSON response with HTTP error details.
    """
    return handle_error(
        status_code=exc.status_code,
        message=exc.detail,
    )

async def http_exception_internal_server_handler(request: Request, exc: Exception):
    """
    Handles internal server errors (HTTP 500) raised during request processing.

    This function is triggered when an unhandled exception or error occurs on the server side.
    It returns a standardized error response indicating an internal server error.

    Args:
        request (Request): The incoming request that caused the internal server error.
        exc (Exception): The exception that caused the internal server error.

    Returns:
        JSONResponse: A standardized response with HTTP 500 status code and a message indicating internal server error.

    Example:
        http_exception_internal_server_handler(request, exc)
        # Returns a JSON response with the internal server error message.
    """
    return handle_error(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        message="Internal Server Error",
        data=str(exc),
    )


class WebSocketException(Exception):
    def __init__(self, detail: str, code: int = status.WS_1003_UNSUPPORTED_DATA):

        self.detail = detail
        self.code = code
        super().__init__(detail)
