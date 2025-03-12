"""
API decorator for APIFromAnything.

This module defines the main API decorator that can be used to expose Python
functions as API endpoints.
"""

import asyncio
import functools
import inspect
import json
import logging
import typing as t
from http import HTTPStatus

from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse

from apifrom.core.request import Request
from apifrom.core.response import JSONResponse, ErrorResponse, Response
from apifrom.utils.serialization import (
    serialize_response,
    deserialize_params,
)
from apifrom.utils.type_utils import get_type_hints_with_extras

logger = logging.getLogger(__name__)


def api(
    route: str = None,
    method: str = "GET",
    name: str = None,
    description: str = None,
    tags: t.List[str] = None,
    response_model: t.Type = None,
    status_code: int = 200,
    deprecated: bool = False,
    include_in_schema: bool = True,
    **kwargs
):
    """
    Decorator to expose a Python function as an API endpoint.
    
    Args:
        route: The route for the endpoint. If None, derived from function name.
        method: The HTTP method for the endpoint.
        name: The name for the endpoint. If None, derived from function name.
        description: The description for the endpoint.
        tags: Tags for the endpoint.
        response_model: The response model for the endpoint.
        status_code: The default status code for successful responses.
        deprecated: Whether the endpoint is deprecated.
        include_in_schema: Whether to include the endpoint in the API schema.
        **kwargs: Additional arguments to pass to the router.
        
    Returns:
        A decorator function.
    """
    def decorator(func: t.Callable) -> t.Callable:
        """
        Decorator function.
        
        Args:
            func: The function to decorate.
            
        Returns:
            The decorated function.
        """
        # Get function signature and type hints
        sig = inspect.signature(func)
        type_hints = get_type_hints_with_extras(func)
        
        # Store API metadata on the function
        func.__api__ = {
            "route": route,
            "method": method,
            "name": name or func.__name__,
            "description": description or func.__doc__,
            "tags": tags or [],
            "response_model": response_model or type_hints.get("return"),
            "status_code": status_code,
            "deprecated": deprecated,
            "include_in_schema": include_in_schema,
            "signature": sig,
            "type_hints": type_hints,
            **kwargs
        }
        
        @functools.wraps(func)
        async def wrapper(request: StarletteRequest) -> StarletteResponse:
            """
            Wrapper function for the API endpoint.
            
            This function handles the HTTP request, extracts parameters,
            calls the original function, and returns the response.
            
            Args:
                request: The HTTP request.
                
            Returns:
                The HTTP response.
            """
            # Create our Request object
            if isinstance(request, Request):
                api_request = request
            else:
                api_request = Request(request)
            
            try:
                # Extract parameters from request
                params = {}
                
                # Extract path parameters
                if hasattr(request, "path_params"):
                    params.update(request.path_params)
                    logger.debug(f"Path parameters: {request.path_params}")
                
                # Extract query parameters
                params.update(api_request.query_params)
                logger.debug(f"Query parameters: {api_request.query_params}")
                
                # Extract body parameters for non-GET requests
                if request.method != "GET":
                    # Make header lookup case-insensitive by converting to lowercase
                    headers_lower = {k.lower(): v for k, v in request.headers.items()}
                    content_type = headers_lower.get("content-type", "")
                    logger.debug(f"Content type: {content_type}")
                    
                    if "application/json" in content_type:
                        # JSON body
                        try:
                            body_params = await api_request.json()
                            logger.debug(f"JSON body: {body_params}")
                            if isinstance(body_params, dict):
                                params.update(body_params)
                        except Exception as e:
                            logger.error(f"Failed to parse JSON body: {e}")
                    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                        # Form data
                        try:
                            form_params = await api_request.form()
                            logger.debug(f"Form data: {form_params}")
                            params.update(form_params)
                        except Exception as e:
                            logger.error(f"Failed to parse form data: {e}")
                
                logger.debug(f"Final parameters: {params}")
                
                # Deserialize parameters
                try:
                    kwargs = deserialize_params(params, sig, type_hints)
                except ValueError as e:
                    # Parameter validation error
                    logger.error(f"Parameter validation error: {e}")
                    response = ErrorResponse(
                        message=str(e),
                        status_code=HTTPStatus.BAD_REQUEST,
                        error_code="PARAMETER_VALIDATION_ERROR"
                    )
                    return response.to_starlette_response()
                
                # Check if the function expects a request parameter
                if "request" in sig.parameters:
                    kwargs["request"] = api_request
                
                # Call the function
                if inspect.iscoroutinefunction(func):
                    # Async function
                    result = await func(**kwargs)
                else:
                    # Sync function
                    result = await asyncio.to_thread(func, **kwargs)
                
                # If the result is already a Response object, return it
                if isinstance(result, Response):
                    return result.to_starlette_response()
                
                # Serialize response
                serialized_result = serialize_response(result)
                
                # Create response
                response = JSONResponse(
                    content=serialized_result,
                    status_code=status_code
                )
                
                return response.to_starlette_response()
            
            except Exception as e:
                # Unexpected error
                logger.exception(f"Unexpected error in endpoint {func.__name__}: {e}")
                response = ErrorResponse(
                    message="Internal server error",
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    error_code="INTERNAL_SERVER_ERROR",
                    details={"error": str(e)}
                )
                return response.to_starlette_response()
        
        # Store the original function on the wrapper
        wrapper.__original_func__ = func
        
        # Register the endpoint with the API instance
        from apifrom import API
        
        # Get the current API instance
        api_instance = API._get_current_instance()
        
        if api_instance:
            api_instance.register_endpoint(
                wrapper,
                route=route,
                method=method,
                name=name,
                **kwargs
            )
        
        return wrapper
    
    return decorator 