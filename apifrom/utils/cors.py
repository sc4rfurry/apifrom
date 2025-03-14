from typing import Dict, List, Optional, Set, Union, Any


def validate_origin(
    origin: str, 
    allowed_origins: Optional[Union[List[str], str]] = None
) -> bool:
    """
    Validate if the given origin is allowed based on the allowed_origins configuration.
    
    Args:
        origin: The origin to validate
        allowed_origins: List of allowed origins or '*' for all origins
        
    Returns:
        True if the origin is allowed, False otherwise
    """
    if allowed_origins is None:
        return False
        
    if allowed_origins == "*":
        return True
        
    if isinstance(allowed_origins, str):
        return origin == allowed_origins
        
    return origin in allowed_origins


def get_cors_headers(
    origin: str,
    allow_origins: Optional[Union[List[str], str]] = None,
    allow_methods: Optional[List[str]] = None,
    allow_headers: Optional[List[str]] = None,
    allow_credentials: bool = False,
    expose_headers: Optional[List[str]] = None,
    max_age: int = 600
) -> Dict[str, str]:
    """
    Generate CORS headers based on the provided configuration.
    
    Args:
        origin: The request origin
        allow_origins: List of allowed origins or '*' for all origins
        allow_methods: List of allowed HTTP methods
        allow_headers: List of allowed HTTP headers
        allow_credentials: Whether to allow credentials
        expose_headers: List of headers to expose to the client
        max_age: Max age for preflight requests caching
        
    Returns:
        Dictionary with CORS headers
    """
    headers: Dict[str, str] = {}
    
    # Handle Access-Control-Allow-Origin
    if validate_origin(origin, allow_origins):
        headers["Access-Control-Allow-Origin"] = origin
    elif allow_origins == "*":
        headers["Access-Control-Allow-Origin"] = "*"
        
    # Handle Access-Control-Allow-Methods
    if allow_methods:
        headers["Access-Control-Allow-Methods"] = ", ".join(allow_methods)
        
    # Handle Access-Control-Allow-Headers
    if allow_headers:
        headers["Access-Control-Allow-Headers"] = ", ".join(allow_headers)
        
    # Handle Access-Control-Allow-Credentials
    if allow_credentials:
        headers["Access-Control-Allow-Credentials"] = "true"
        
    # Handle Access-Control-Expose-Headers
    if expose_headers:
        headers["Access-Control-Expose-Headers"] = ", ".join(expose_headers)
        
    # Handle Access-Control-Max-Age
    headers["Access-Control-Max-Age"] = str(max_age)
    
    return headers


def is_cors_preflight_request(method: str, headers: Dict[str, Any]) -> bool:
    """
    Check if a request is a CORS preflight request.
    
    Args:
        method: The HTTP method
        headers: The request headers
        
    Returns:
        True if the request is a CORS preflight request, False otherwise
    """
    return (
        method == "OPTIONS" and
        "origin" in headers and
        "access-control-request-method" in headers
    )


def handle_cors_preflight(
    origin: str,
    request_method: str,
    request_headers: Optional[str] = None,
    allow_origins: Optional[Union[List[str], str]] = None,
    allow_methods: Optional[List[str]] = None,
    allow_headers: Optional[List[str]] = None,
    allow_credentials: bool = False,
    max_age: int = 600
) -> Dict[str, str]:
    """
    Handle a CORS preflight request and generate appropriate headers.
    
    Args:
        origin: The request origin
        request_method: The requested method
        request_headers: The requested headers
        allow_origins: List of allowed origins or '*' for all origins
        allow_methods: List of allowed HTTP methods
        allow_headers: List of allowed HTTP headers
        allow_credentials: Whether to allow credentials
        max_age: Max age for preflight requests caching
        
    Returns:
        Dictionary with CORS headers for the preflight response
    """
    headers = get_cors_headers(
        origin=origin,
        allow_origins=allow_origins,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        allow_credentials=allow_credentials,
        max_age=max_age
    )
    
    # Validate the requested method
    if allow_methods and request_method and request_method not in allow_methods:
        # Method not allowed, don't add the requested method to the response
        return headers
        
    # Validate the requested headers
    if request_headers and allow_headers:
        requested = [h.strip().lower() for h in request_headers.split(",")]
        allowed = [h.lower() for h in allow_headers]
        
        # Check if all requested headers are allowed
        for header in requested:
            if header and header not in allowed:
                # Header not allowed, don't add the requested headers to the response
                return headers
                
    return headers

