"""
Error handling middleware for APIFromAnything.

This module provides middleware for catching and formatting exceptions 
in a consistent way for API responses.
"""

import sys
import traceback
import logging
import json
from typing import Dict, Any, Optional, Callable, Awaitable, Type, List, Union
import inspect

from apifrom.middleware.base import Middleware
from apifrom.core.request import Request
from apifrom.core.response import Response

# Set up logging
logger = logging.getLogger("apifrom.middleware.error_handling")


class APIError(Exception):
    """Base class for API errors that can be safely exposed to clients."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 400, 
        error_code: str = "bad_request",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an API error.
        
        Args:
            message: The error message
            status_code: The HTTP status code
            error_code: An application-specific error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class BadRequestError(APIError):
    """Error for invalid client requests."""
    
    def __init__(
        self, 
        message: str = "Bad request", 
        error_code: str = "bad_request",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code,
            details=details
        )


class UnauthorizedError(APIError):
    """Error for unauthorized requests."""
    
    def __init__(
        self, 
        message: str = "Unauthorized", 
        error_code: str = "unauthorized",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code=error_code,
            details=details
        )


class ForbiddenError(APIError):
    """Error for forbidden requests."""
    
    def __init__(
        self, 
        message: str = "Forbidden", 
        error_code: str = "forbidden",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code=error_code,
            details=details
        )


class NotFoundError(APIError):
    """Error for resources that don't exist."""
    
    def __init__(
        self, 
        message: str = "Not found", 
        error_code: str = "not_found",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=404,
            error_code=error_code,
            details=details
        )


class MethodNotAllowedError(APIError):
    """Error for disallowed HTTP methods."""
    
    def __init__(
        self, 
        message: str = "Method not allowed", 
        error_code: str = "method_not_allowed",
        details: Optional[Dict[str, Any]] = None,
        allowed_methods: Optional[List[str]] = None
    ):
        details = details or {}
        if allowed_methods:
            details["allowed_methods"] = allowed_methods
        
        super().__init__(
            message=message,
            status_code=405,
            error_code=error_code,
            details=details
        )


class ConflictError(APIError):
    """Error for resource conflicts."""
    
    def __init__(
        self, 
        message: str = "Conflict", 
        error_code: str = "conflict",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=409,
            error_code=error_code,
            details=details
        )


class UnprocessableEntityError(APIError):
    """Error for validation failures."""
    
    def __init__(
        self, 
        message: str = "Validation error", 
        error_code: str = "validation_error",
        details: Optional[Dict[str, Any]] = None,
        validation_errors: Optional[Dict[str, List[str]]] = None
    ):
        details = details or {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        
        super().__init__(
            message=message,
            status_code=422,
            error_code=error_code,
            details=details
        )


class TooManyRequestsError(APIError):
    """Error for rate limit exceeded."""
    
    def __init__(
        self, 
        message: str = "Too many requests", 
        error_code: str = "rate_limit_exceeded",
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        details = details or {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            status_code=429,
            error_code=error_code,
            details=details
        )


class InternalServerError(APIError):
    """Error for internal server errors."""
    
    def __init__(
        self, 
        message: str = "Internal server error", 
        error_code: str = "internal_error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code=error_code,
            details=details
        )


class ServiceUnavailableError(APIError):
    """Error for unavailable services."""
    
    def __init__(
        self, 
        message: str = "Service unavailable", 
        error_code: str = "service_unavailable",
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        details = details or {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            status_code=503,
            error_code=error_code,
            details=details
        )


# Map exception types to handlers
class ExceptionHandler:
    """Handler for converting exceptions to API responses."""
    
    def __init__(self, exception_class: Type[Exception], status_code: int, error_code: str):
        """
        Initialize an exception handler.
        
        Args:
            exception_class: The exception class to handle
            status_code: The HTTP status code to return
            error_code: The error code to include in the response
        """
        self.exception_class = exception_class
        self.status_code = status_code
        self.error_code = error_code
    
    def __call__(self, exception: Exception) -> Response:
        """
        Convert an exception to a response.
        
        Args:
            exception: The exception to handle
            
        Returns:
            An API response
        """
        # Get the error message
        message = str(exception)
        
        # Create a response
        return Response(
            content={
                "error": {
                    "message": message,
                    "code": self.error_code,
                    "status": self.status_code
                }
            },
            status_code=self.status_code,
            headers={"Content-Type": "application/json"}
        )


class ErrorHandlingMiddleware(Middleware):
    """
    Middleware for handling errors in API requests.
    
    This middleware catches exceptions and returns appropriate error responses.
    """
    
    def __init__(
        self, 
        debug: bool = False,
        include_traceback: bool = False,
        include_exception_class: bool = False,
        log_exceptions: bool = True,
        json_encoder: Optional[Type[json.JSONEncoder]] = None,
        **kwargs
    ):
        """
        Initialize the error handling middleware.
        
        Args:
            debug: Whether to include debug information in error responses
            include_traceback: Whether to include tracebacks in debug mode
            include_exception_class: Whether to include exception class names
            log_exceptions: Whether to log exceptions
            json_encoder: A custom JSON encoder for error responses
            **kwargs: Additional options for the base middleware
        """
        super().__init__(**kwargs)
        self.debug = debug
        self.include_traceback = include_traceback
        self.include_exception_class = include_exception_class
        self.log_exceptions = log_exceptions
        self.json_encoder = json_encoder
        
        # Set up exception handlers
        self.exception_handlers = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self) -> None:
        """Set up default exception handlers."""
        # Register handlers for built-in API errors
        self.add_exception_handler(
            BadRequestError,
            lambda e: self._handle_api_error(e)
        )
        self.add_exception_handler(
            UnauthorizedError,
            lambda e: self._handle_api_error(e)
        )
        self.add_exception_handler(
            ForbiddenError,
            lambda e: self._handle_api_error(e)
        )
        self.add_exception_handler(
            NotFoundError,
            lambda e: self._handle_api_error(e)
        )
        self.add_exception_handler(
            MethodNotAllowedError,
            lambda e: self._handle_api_error(e)
        )
        self.add_exception_handler(
            ConflictError,
            lambda e: self._handle_api_error(e)
        )
        self.add_exception_handler(
            UnprocessableEntityError,
            lambda e: self._handle_api_error(e)
        )
        self.add_exception_handler(
            TooManyRequestsError,
            lambda e: self._handle_api_error(e)
        )
        self.add_exception_handler(
            InternalServerError,
            lambda e: self._handle_api_error(e)
        )
        self.add_exception_handler(
            ServiceUnavailableError,
            lambda e: self._handle_api_error(e)
        )
        
        # Register handlers for common standard exceptions
        self.add_exception_handler(
            ValueError,
            lambda e: self._create_error_response(
                str(e) or "Invalid value", 
                400, 
                "bad_request",
                e
            )
        )
        self.add_exception_handler(
            TypeError,
            lambda e: self._create_error_response(
                str(e) or "Type error", 
                400, 
                "bad_request",
                e
            )
        )
        self.add_exception_handler(
            KeyError,
            lambda e: self._create_error_response(
                f"Missing key: {str(e)}", 
                400, 
                "bad_request",
                e
            )
        )
        self.add_exception_handler(
            IndexError,
            lambda e: self._create_error_response(
                str(e) or "Index error", 
                400, 
                "bad_request",
                e
            )
        )
        self.add_exception_handler(
            AttributeError,
            lambda e: self._create_error_response(
                str(e) or "Attribute error", 
                500, 
                "internal_error",
                e
            )
        )
        self.add_exception_handler(
            NotImplementedError,
            lambda e: self._create_error_response(
                str(e) or "Not implemented", 
                501, 
                "not_implemented",
                e
            )
        )
        self.add_exception_handler(
            PermissionError,
            lambda e: self._create_error_response(
                str(e) or "Permission denied", 
                403, 
                "forbidden",
                e
            )
        )
        
        # Fallback handler for all other exceptions
        self.add_exception_handler(
            Exception,
            lambda e: self._create_error_response(
                "Internal server error", 
                500, 
                "internal_error",
                e
            )
        )
    
    def add_exception_handler(
        self, 
        exception_class: Type[Exception], 
        handler: Callable[[Exception], Response]
    ) -> None:
        """
        Add a custom exception handler.
        
        Args:
            exception_class: The exception class to handle
            handler: A function that converts the exception to a response
        """
        self.exception_handlers[exception_class] = handler
    
    def _handle_api_error(self, exception: APIError) -> Response:
        """
        Handle an API error.
        
        Args:
            exception: The API error
            
        Returns:
            An API response
        """
        return self._create_error_response(
            exception.message,
            exception.status_code,
            exception.error_code,
            exception,
            exception.details
        )
    
    def _create_error_response(
        self, 
        message: str, 
        status_code: int, 
        error_code: str,
        exception: Exception,
        details: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Create an error response.
        
        Args:
            message: The error message
            status_code: The HTTP status code
            error_code: The error code
            exception: The original exception
            details: Additional error details
            
        Returns:
            An API response
        """
        # Prepare the error body
        error = {
            "message": message,
            "code": error_code,
            "status": status_code
        }
        
        # Include details if provided
        if details:
            error["details"] = details
        
        # Include debug information if in debug mode
        if self.debug:
            # Include exception class if configured
            if self.include_exception_class:
                error["exception"] = exception.__class__.__name__
            
            # Include traceback if configured
            if self.include_traceback:
                tb = traceback.format_exception(
                    type(exception), 
                    exception, 
                    exception.__traceback__
                )
                error["traceback"] = "".join(tb)
        
        # Create the response
        return Response(
            content={"error": error},
            status_code=status_code,
            headers={"Content-Type": "application/json"}
        )
    
    def _find_handler(self, exception: Exception) -> Callable[[Exception], Response]:
        """
        Find the appropriate handler for an exception.
        
        Args:
            exception: The exception to handle
            
        Returns:
            A handler function
        """
        # Match the exception class or the closest parent class
        for exception_class in self.exception_handlers:
            if isinstance(exception, exception_class):
                return self.exception_handlers[exception_class]
        
        # Default to the generic exception handler
        return self.exception_handlers[Exception]
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Dispatch a request, catching and handling any exceptions.
        
        Args:
            request: The request to process
            call_next: The next middleware or route handler
            
        Returns:
            The response
        """
        try:
            # Try to process the request normally
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the exception if configured
            if self.log_exceptions:
                logger.exception(f"Error processing request: {request.method} {request.url.path}")
            
            # Find the appropriate handler
            handler = self._find_handler(e)
            
            # Handle the exception
            return handler(e)

    async def process_request(self, request: Request) -> Request:
        """
        Process a request.

        Args:
            request: The request to process

        Returns:
            The processed request
        """
        # This middleware doesn't modify the request, just passes it through
        return request


# Export public symbols
__all__ = [
    "ErrorHandlingMiddleware",
    "APIError",
    "BadRequestError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "MethodNotAllowedError",
    "ConflictError",
    "UnprocessableEntityError",
    "TooManyRequestsError",
    "InternalServerError",
    "ServiceUnavailableError",
    "ExceptionHandler",
] 