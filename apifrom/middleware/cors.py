"""
CORS (Cross-Origin Resource Sharing) middleware for APIFromAnything.

This module provides middleware for handling CORS headers to allow controlled
cross-origin requests to the API.
"""

from typing import Callable, Dict, List, Optional, Set, Union

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware.base import BaseMiddleware


class CORSMiddleware(BaseMiddleware):
    """
    Middleware for handling Cross-Origin Resource Sharing (CORS).
    
    This middleware adds appropriate CORS headers to responses to allow
    controlled cross-origin requests to the API.
    """
    
    def __init__(
        self,
        allow_origins: Optional[Union[List[str], str]] = None,
        allow_methods: Optional[List[str]] = None,
        allow_headers: Optional[List[str]] = None,
        allow_credentials: bool = False,
        expose_headers: Optional[List[str]] = None,
        max_age: int = 600,
        preflight_continue: bool = False,
        options_success_status: int = 204,
    ):
        """
        Initialize the CORS middleware.
        
        Args:
            allow_origins: List of origins that are allowed to make cross-origin requests,
                or "*" to allow any origin
            allow_methods: List of HTTP methods that are allowed for cross-origin requests
            allow_headers: List of HTTP headers that can be used in cross-origin requests
            allow_credentials: Whether cookies and credentials can be included in cross-origin requests
            expose_headers: List of HTTP headers that can be exposed to the browser
            max_age: How long the results of a preflight request can be cached (in seconds)
            preflight_continue: Whether to continue processing after a preflight request
            options_success_status: Status code to use for successful OPTIONS requests
        """
        super().__init__()
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.allow_headers = allow_headers or ["Content-Type", "Authorization"]
        self.allow_credentials = allow_credentials
        self.expose_headers = expose_headers or []
        self.max_age = max_age
        self.preflight_continue = preflight_continue
        self.options_success_status = options_success_status
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """
        Check if an origin is allowed.
        
        Args:
            origin: The origin to check
            
        Returns:
            True if the origin is allowed, False otherwise
        """
        if "*" in self.allow_origins:
            return True
        
        return origin in self.allow_origins
    
    def _add_cors_headers(self, request: Request, response: Response) -> None:
        """
        Add CORS headers to a response.
        
        Args:
            request: The request
            response: The response to add headers to
        """
        origin = request.headers.get("Origin")
        
        # If there's no Origin header, this isn't a CORS request
        if not origin:
            return
        
        # Check if the origin is allowed
        if not self._is_origin_allowed(origin):
            return
        
        # Add Access-Control-Allow-Origin header
        if "*" in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        else:
            response.headers["Access-Control-Allow-Origin"] = origin
        
        # Add Access-Control-Allow-Credentials header if needed
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        # Add Access-Control-Expose-Headers header if needed
        if self.expose_headers:
            response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
    
    def _handle_preflight(self, request: Request) -> Optional[Response]:
        """
        Handle a CORS preflight request.
        
        Args:
            request: The preflight request
            
        Returns:
            A response for the preflight request, or None to continue processing
        """
        origin = request.headers.get("Origin")
        
        # If there's no Origin header, this isn't a CORS request
        if not origin:
            return None
        
        # Check if the origin is allowed
        if not self._is_origin_allowed(origin):
            return None
        
        # Create a response for the preflight request
        response = Response(status_code=self.options_success_status)
        
        # Add Access-Control-Allow-Origin header
        if "*" in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        else:
            response.headers["Access-Control-Allow-Origin"] = origin
        
        # Add Access-Control-Allow-Methods header
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        
        # Add Access-Control-Allow-Headers header
        requested_headers = request.headers.get("Access-Control-Request-Headers")
        if requested_headers:
            response.headers["Access-Control-Allow-Headers"] = requested_headers
        elif self.allow_headers:
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        
        # Add Access-Control-Allow-Credentials header if needed
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        # Add Access-Control-Max-Age header
        if self.max_age:
            response.headers["Access-Control-Max-Age"] = str(self.max_age)
        
        return response
    
    async def process_request(self, request: Request) -> Request:
        """
        Process a request through the CORS middleware.
        
        Args:
            request: The request to process
            
        Returns:
            The processed request
        """
        # Handle preflight requests (OPTIONS)
        if request.method == "OPTIONS":
            preflight_response = self._handle_preflight(request)
            if preflight_response and not self.preflight_continue:
                # Store the preflight response in the request state
                request.state.preflight_response = preflight_response
        
        return request
    
    async def process_response(self, response: Response) -> Response:
        """
        Process a response through the CORS middleware.
        
        Args:
            response: The response to process
            
        Returns:
            The processed response
        """
        # If we have a preflight response in the request state, return it
        if hasattr(response.request.state, 'preflight_response'):
            return response.request.state.preflight_response
        
        # Add CORS headers to the response
        self._add_cors_headers(response.request, response)
        
        return response 