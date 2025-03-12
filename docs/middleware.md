# Middleware System in APIFromAnything

This guide covers the middleware system in APIFromAnything, which allows you to process requests and responses in a flexible and modular way.

## Introduction to Middleware

Middleware components are functions or classes that have access to the request and response objects in your API's request-response cycle. They can:

- Execute code before or after the request is processed
- Modify the request or response objects
- End the request-response cycle early
- Call the next middleware in the stack

Middleware is executed in the order it is added to the API, forming a "middleware stack".

## Adding Middleware to Your API

```python
from apifrom import API
from apifrom.middleware import CacheMiddleware, RateLimitMiddleware, CORSMiddleware

# Create an API instance
app = API(
    title="Middleware Example",
    description="An example of using middleware",
    version="1.0.0"
)

# Add middleware to the API
app.add_middleware(CacheMiddleware(ttl=60))  # Cache responses for 60 seconds
app.add_middleware(RateLimitMiddleware(limit=100, window=60))  # 100 requests per minute
app.add_middleware(CORSMiddleware(allow_origins=["https://example.com"]))  # CORS support
```

## Built-in Middleware Components

APIFromAnything includes several built-in middleware components:

### CacheMiddleware

Caches API responses with configurable TTL:

```python
from apifrom import API
from apifrom.middleware import CacheMiddleware

app = API()

# Add cache middleware
app.add_middleware(
    CacheMiddleware(
        ttl=60,  # Cache TTL in seconds
        max_size=1000,  # Maximum number of cached responses
        key_builder=None,  # Custom function to build cache keys
        storage="memory",  # Storage backend (memory, redis)
        redis_url=None,  # Redis URL (if using redis storage)
        include_query_params=True,  # Include query parameters in cache key
        include_headers=False,  # Include headers in cache key
        cache_control=True,  # Add Cache-Control headers to responses
    )
)
```

### RateLimitMiddleware

Limits the number of requests a client can make:

```python
from apifrom import API
from apifrom.middleware import RateLimitMiddleware

app = API()

# Add rate limit middleware
app.add_middleware(
    RateLimitMiddleware(
        limit=100,  # Maximum requests
        window=60,  # Time window in seconds
        key_func=lambda request: request.client.host,  # Function to extract the client key
        storage="memory",  # Storage backend (memory, redis)
        redis_url=None,  # Redis URL (if using redis storage)
        headers=True,  # Add rate limit headers to responses
    )
)
```

### CORSMiddleware

Handles Cross-Origin Resource Sharing (CORS) headers:

```python
from apifrom import API
from apifrom.middleware import CORSMiddleware

app = API()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware(
        allow_origins=["https://example.com", "https://app.example.com"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Custom-Header"],
        allow_credentials=True,
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
)
```

### SecurityHeadersMiddleware

Adds security headers to responses:

```python
from apifrom import API
from apifrom.middleware import SecurityHeadersMiddleware

app = API()

# Add security headers middleware
app.add_middleware(
    SecurityHeadersMiddleware(
        # Content Security Policy
        csp={
            "default-src": ["'self'"],
            "script-src": ["'self'", "https://cdn.example.com"],
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:"],
            "font-src": ["'self'", "https://fonts.googleapis.com"],
            "connect-src": ["'self'", "https://api.example.com"],
            "object-src": ["'none'"],
            "frame-ancestors": ["'none'"],
            "upgrade-insecure-requests": True,
            "block-all-mixed-content": True,
        },
        # HTTP Strict Transport Security
        hsts={
            "max-age": 31536000,  # 1 year
            "includeSubDomains": True,
            "preload": True,
        },
        # X-Content-Type-Options
        x_content_type_options="nosniff",
        # X-Frame-Options
        x_frame_options="DENY",
        # X-XSS-Protection
        x_xss_protection="1; mode=block",
        # Referrer-Policy
        referrer_policy="strict-origin-when-cross-origin",
        # Permissions-Policy
        permissions_policy={
            "geolocation": ["self"],
            "microphone": [],
            "camera": [],
            "payment": [],
        },
    )
)
```

### CSRFMiddleware

Protects against Cross-Site Request Forgery attacks:

```python
from apifrom import API
from apifrom.middleware import CSRFMiddleware

app = API()

# Add CSRF middleware
app.add_middleware(
    CSRFMiddleware(
        secret="your-csrf-secret",
        cookie_name="csrf_token",
        header_name="X-CSRF-Token",
        secure=True,  # Only send cookie over HTTPS
        samesite="strict",  # Cookie same-site policy
        methods=["POST", "PUT", "DELETE", "PATCH"],  # Methods to protect
    )
)
```

### XSSProtectionMiddleware

Protects against Cross-Site Scripting attacks:

```python
from apifrom import API
from apifrom.middleware import XSSProtectionMiddleware

app = API()

# Add XSS protection middleware
app.add_middleware(
    XSSProtectionMiddleware(
        sanitize_html=True,  # Sanitize HTML in responses
        sanitize_json=True,  # Sanitize JSON in responses
        sanitize_headers=True,  # Sanitize headers in responses
    )
)
```

### ErrorHandlingMiddleware

Catches and formats exceptions:

```python
from apifrom import API
from apifrom.middleware import ErrorHandlingMiddleware

app = API()

# Add error handling middleware
app.add_middleware(
    ErrorHandlingMiddleware(
        debug=True,  # Include debug information in development
        include_traceback=True,  # Include tracebacks in error responses
        log_exceptions=True,  # Log exceptions to the console
    )
)
```

### LoggingMiddleware

Logs requests and responses:

```python
from apifrom import API
from apifrom.middleware import LoggingMiddleware

app = API()

# Add logging middleware
app.add_middleware(
    LoggingMiddleware(
        level="INFO",  # Logging level
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
        log_request_headers=True,  # Log request headers
        log_request_body=False,  # Log request body
        log_response_headers=True,  # Log response headers
        log_response_body=False,  # Log response body
    )
)
```

### CompressionMiddleware

Compresses responses:

```python
from apifrom import API
from apifrom.middleware import CompressionMiddleware

app = API()

# Add compression middleware
app.add_middleware(
    CompressionMiddleware(
        minimum_size=1000,  # Minimum response size to compress
        level=9,  # Compression level (1-9)
        algorithms=["gzip", "deflate", "br"],  # Supported compression algorithms
    )
)
```

### AuthenticationMiddleware

Handles authentication:

```python
from apifrom import API
from apifrom.middleware import AuthenticationMiddleware
from apifrom.security import JWTAuthenticator, APIKeyAuthenticator

app = API()

# Add authentication middleware
app.add_middleware(
    AuthenticationMiddleware(
        authenticators=[
            JWTAuthenticator(
                secret="your-secret-key",
                algorithm="HS256",
            ),
            APIKeyAuthenticator(
                api_keys={"api-key-1": ["read"]},
            ),
        ],
        require_auth=False,  # If True, all routes require authentication
    )
)
```

## Creating Custom Middleware

You can create your own middleware by extending the `Middleware` class:

```python
from apifrom.middleware import Middleware
from apifrom.core.request import Request
from apifrom.core.response import Response
from typing import Callable, Awaitable

class LoggingMiddleware(Middleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        print(f"Request: {request.method} {request.url.path}")

        # Process the request through the next middleware or endpoint
        response = await call_next(request)

        print(f"Response: {response.status_code}")
        return response

# Add the custom middleware to the API
app.add_middleware(LoggingMiddleware())
```

### Middleware with Configuration

You can create middleware with configuration options:

```python
from apifrom.middleware import Middleware
from apifrom.core.request import Request
from apifrom.core.response import Response
from typing import Callable, Awaitable, List, Optional

class CustomHeadersMiddleware(Middleware):
    def __init__(
        self,
        headers: dict,
        override: bool = False,
        exclude_paths: Optional[List[str]] = None
    ):
        self.headers = headers
        self.override = override
        self.exclude_paths = exclude_paths or []

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Process the request through the next middleware or endpoint
        response = await call_next(request)

        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return response

        # Add custom headers to the response
        for name, value in self.headers.items():
            if self.override or name not in response.headers:
                response.headers[name] = value

        return response

# Add the custom middleware to the API
app.add_middleware(
    CustomHeadersMiddleware(
        headers={"X-Custom-Header": "Value"},
        override=True,
        exclude_paths=["/health", "/metrics"]
    )
)
```

### Middleware with Early Response

You can create middleware that returns a response early:

```python
from apifrom.middleware import Middleware
from apifrom.core.request import Request
from apifrom.core.response import Response
from typing import Callable, Awaitable, List

class MaintenanceModeMiddleware(Middleware):
    def __init__(
        self,
        enabled: bool = False,
        message: str = "The service is under maintenance",
        status_code: int = 503,
        exclude_paths: List[str] = None
    ):
        self.enabled = enabled
        self.message = message
        self.status_code = status_code
        self.exclude_paths = exclude_paths or []

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Return early if maintenance mode is enabled
        if self.enabled:
            return Response(
                content={"message": self.message},
                status_code=self.status_code,
                headers={"Retry-After": "3600"}
            )

        # Process the request through the next middleware or endpoint
        return await call_next(request)

# Add the custom middleware to the API
app.add_middleware(
    MaintenanceModeMiddleware(
        enabled=True,
        message="We are performing scheduled maintenance. Please try again later.",
        exclude_paths=["/health", "/status"]
    )
)
```

## Middleware Execution Order

Middleware is executed in the order it is added to the API:

```python
from apifrom import API
from apifrom.middleware import (
    LoggingMiddleware,
    CORSMiddleware,
    SecurityHeadersMiddleware,
    CompressionMiddleware,
    CacheMiddleware,
    RateLimitMiddleware,
    ErrorHandlingMiddleware
)

app = API()

# Add middleware in the desired order
app.add_middleware(LoggingMiddleware())  # 1. Log the request
app.add_middleware(CORSMiddleware())  # 2. Handle CORS
app.add_middleware(SecurityHeadersMiddleware())  # 3. Add security headers
app.add_middleware(CompressionMiddleware())  # 4. Compress the response
app.add_middleware(CacheMiddleware())  # 5. Cache the response
app.add_middleware(RateLimitMiddleware())  # 6. Rate limit the request
app.add_middleware(ErrorHandlingMiddleware())  # 7. Handle errors
```

The middleware stack is executed in the following order:

1. The request flows through the middleware stack from top to bottom.
2. The endpoint handler is called.
3. The response flows through the middleware stack from bottom to top.

## Middleware Best Practices

### 1. Keep Middleware Focused

Each middleware should have a single responsibility:

```python
# Good: Focused middleware
app.add_middleware(LoggingMiddleware())
app.add_middleware(CORSMiddleware())
app.add_middleware(CacheMiddleware())

# Bad: Middleware with multiple responsibilities
class DoEverythingMiddleware(Middleware):
    async def dispatch(self, request, call_next):
        # Log the request
        # Handle CORS
        # Cache the response
        # ...
```

### 2. Order Middleware Correctly

The order of middleware matters:

```python
# Good: Error handling middleware is added last
app.add_middleware(LoggingMiddleware())
app.add_middleware(CORSMiddleware())
app.add_middleware(ErrorHandlingMiddleware())

# Bad: Error handling middleware is added first
app.add_middleware(ErrorHandlingMiddleware())
app.add_middleware(LoggingMiddleware())
app.add_middleware(CORSMiddleware())
```

### 3. Use Middleware for Cross-Cutting Concerns

Use middleware for concerns that apply to multiple endpoints:

```python
# Good: Use middleware for cross-cutting concerns
app.add_middleware(LoggingMiddleware())
app.add_middleware(CORSMiddleware())
app.add_middleware(AuthenticationMiddleware())

# Bad: Implement cross-cutting concerns in each endpoint
@api(route="/users", method="GET")
def get_users(request):
    # Log the request
    # Handle CORS
    # Authenticate the user
    # ...
```

### 4. Make Middleware Configurable

Make middleware configurable to support different use cases:

```python
# Good: Configurable middleware
app.add_middleware(
    CacheMiddleware(
        ttl=60,
        storage="redis",
        redis_url="redis://localhost:6379/0"
    )
)

# Bad: Hardcoded middleware
class HardcodedCacheMiddleware(Middleware):
    async def dispatch(self, request, call_next):
        # Hardcoded TTL, storage, etc.
        # ...
```

### 5. Document Middleware

Document middleware to make it easier to use:

```python
class DocumentedMiddleware(Middleware):
    """
    A middleware that does something useful.

    Args:
        option1: Description of option1
        option2: Description of option2
    """

    def __init__(self, option1, option2):
        self.option1 = option1
        self.option2 = option2

    async def dispatch(self, request, call_next):
        """
        Process the request and response.

        Args:
            request: The request object
            call_next: The next middleware in the stack

        Returns:
            The response object
        """
        # ...
```

## Conclusion

The middleware system in APIFromAnything provides a powerful way to process requests and responses in a flexible and modular way. By using built-in middleware components and creating custom middleware, you can add functionality to your API without modifying your endpoint handlers. 