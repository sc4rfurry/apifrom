from typing import List, Optional, Union, Dict, Any

from ..core.request import Request
from ..core.response import Response


class CORSMiddleware:
    """
    Middleware for handling Cross-Origin Resource Sharing (CORS).
    
    This middleware adds appropriate CORS headers to responses and handles
    preflight requests with the OPTIONS method.
    """
    
    def __init__(
        self,
        allow_origins: Optional[Union[List[str], str]] = None,
        allow_methods: Optional[List[str]] = None,
        allow_headers: Optional[List[str]] = None,
        allow_credentials: bool = False,
        expose_headers: Optional[List[str]] = None,
        max_age: int = 600
    ):
        """
        Initialize the CORS middleware with the specified configuration.
        
        Args:
            allow_origins: A list of origins that are allowed to make requests,
                or "*" to allow any origin.
            allow_methods: A list of HTTP methods that are allowed.
            allow_headers: A list of HTTP headers that are allowed.
            allow_credentials: Whether to allow credentials (cookies, authorization headers, etc).
            expose_headers: A list of headers that browsers are allowed to access.
            max_age: The maximum time (in seconds) to cache the preflight response.
        """
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.expose_headers = expose_headers or []
        self.max_age = max_age
        
        if isinstance(self.allow_origins, str):
            self.allow_origins = [self.allow_origins]
    
    async def process_request(self, request: Request) -> Optional[Response]:
        """
        Process an incoming request and handle CORS preflight requests.
        
        Args:
            request: The incoming request.
            
        Returns:
            A response for preflight requests, or None to continue processing.
        """
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS" and origin is not None:
            return self._create_preflight_response(request)
        
        return None
    
    def _create_preflight_response(self, request: Request) -> Response:
        """
        Create a response for preflight requests.
        
        Args:
            request: The preflight request.
            
        Returns:
            A response with appropriate CORS headers.
        """
        headers = {
            "Access-Control-Allow-Origin": self._get_allow_origin(request),
            "Access-Control-Allow-Methods": ", ".join(self.allow_methods),
            "Access-Control-Max-Age": str(self.max_age),
        }
        
        if self.allow_headers:
            headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        
        if self.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        
        return Response(status_code=204, headers=headers)
    
    def _get_allow_origin(self, request: Request) -> str:
        """
        Get the appropriate Access-Control-Allow-Origin header value.
        
        Args:
            request: The request to process.
            
        Returns:
            The appropriate origin value.
        """
        origin = request.headers.get("origin")
        
        if not origin:
            return ""
        
        if "*" in self.allow_origins:
            return "*" if not self.allow_credentials else origin
        
        if origin in self.allow_origins:
            return origin
        
        return ""
    
    def process_response(self, request: Request, response: Response) -> Response:
        """
        Process a response by adding appropriate CORS headers.
        
        Args:
            request: The request that led to this response.
            response: The response to process.
            
        Returns:
            The processed response with CORS headers.
        """
        origin = request.headers.get("origin")
        
        if not origin:
            return response
        
        allow_origin = self._get_allow_origin(request)
        if not allow_origin:
            return response
        
        # Set CORS headers
        response.headers["Access-Control-Allow-Origin"] = allow_origin
        
        if self.expose_headers:
            response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response

