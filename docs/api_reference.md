# 📚 API Reference for APIFromAnything

<div align="center">
  <img src="https://img.shields.io/badge/APIFromAnything-API%20Reference-blue?style=for-the-badge&logo=python" alt="APIFromAnything API Reference" />
  <br/>
  <strong>Comprehensive reference documentation for all modules, classes, and functions</strong>
</div>

This document provides a comprehensive reference for the APIFromAnything library's classes, methods, and functions. Use this as your go-to resource when building applications with APIFromAnything.

## 🧩 Core Module

The core module contains the fundamental components for creating and running APIs.

### API Class

The `API` class is the main entry point for creating an API. It handles routing, middleware, and serves as the central configuration point for your application.

```python
from apifrom import API

app = API(
    title="My API",
    description="API description",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url="/redoc",
    debug=True
)
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | `str` | `"APIFromAnything"` | The title of the API, displayed in documentation |
| `description` | `str` | `None` | A detailed description of the API's purpose and functionality |
| `version` | `str` | `"1.0.0"` | The semantic version of the API (e.g., "1.2.3") |
| `docs_url` | `str` | `"/docs"` | The URL path for the Swagger UI documentation |
| `openapi_url` | `str` | `"/openapi.json"` | The URL path for the OpenAPI schema JSON |
| `redoc_url` | `str` | `"/redoc"` | The URL path for the ReDoc documentation |
| `debug` | `bool` | `False` | Enable debug mode for detailed error messages and logging |

#### Methods

##### `add_middleware`

Add a middleware component to the API. Middleware components are executed in the order they are added.

```python
from apifrom.middleware import CORSMiddleware

app.add_middleware(CORSMiddleware(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"]
))
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `middleware` | `Middleware` | The middleware instance to add to the request/response processing pipeline |

##### `run`

Start the API server.

```python
app.run(host="0.0.0.0", port=8000, workers=4)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | `str` | `"127.0.0.1"` | The host address to bind the server to |
| `port` | `int` | `8000` | The port number to listen on |
| `workers` | `int` | `1` | Number of worker processes (for production use) |
| `ssl_certfile` | `str` | `None` | Path to SSL certificate file for HTTPS |
| `ssl_keyfile` | `str` | `None` | Path to SSL key file for HTTPS |

##### `register_plugin`

Register a plugin with the API.

```python
from apifrom.plugins import LoggingPlugin

logger_plugin = LoggingPlugin()
app.register_plugin(logger_plugin)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `plugin` | `Plugin` | The plugin instance to register |

##### `mount`

Mount another API or WSGI/ASGI application at a specific path.

```python
app.mount(path="/subapi", app=subapp)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` | The path to mount the application at |
| `app` | `Union[API, Any]` | The application to mount |

##### `include_router`

Include a router in the API.

```python
app.include_router(router)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `router` | `Router` | The router to include |
| `prefix` | `str` | The prefix to add to all routes in the router |
| `tags` | `List[str]` | The tags to add to all routes in the router |

### api Decorator

The `api` decorator is used to define API endpoints.

```python
from apifrom import api

@api(
    route="/users/{user_id}",
    method="GET",
    tags=["users"],
    summary="Get a user",
    description="Get a user by ID",
    response_model=dict,
    status_code=200,
    deprecated=False,
    include_in_schema=True
)
def get_user(user_id: int) -> dict:
    return {"id": user_id, "name": "John Doe"}
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `route` | `str` | `None` | The URL path for the endpoint |
| `method` | `str` | `"GET"` | The HTTP method for the endpoint |
| `tags` | `List[str]` | `[]` | Tags for documentation |
| `summary` | `str` | `None` | Summary for documentation |
| `description` | `str` | `None` | Description for documentation |
| `response_model` | `Type` | `None` | Expected response model |
| `status_code` | `int` | `200` | HTTP status code |
| `deprecated` | `bool` | `False` | Mark as deprecated |
| `include_in_schema` | `bool` | `True` | Include in OpenAPI schema |
| `responses` | `Dict[int, Dict]` | `{}` | Additional responses |
| `response_description` | `str` | `"Successful Response"` | Description of the response |

### Request Class

The `Request` class represents an HTTP request.

```python
from apifrom.core.request import Request

@api(route="/echo", method="POST")
def echo(request: Request) -> dict:
    body = request.json()
    headers = request.headers
    query_params = request.query_params
    path_params = request.path_params
    return {"body": body}
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `method` | `str` | The HTTP method |
| `url` | `URL` | The URL object |
| `headers` | `Headers` | The request headers |
| `query_params` | `QueryParams` | The query parameters |
| `path_params` | `PathParams` | The path parameters |
| `cookies` | `Cookies` | The cookies |
| `client` | `Address` | The client address |
| `state` | `State` | The request state |

#### Methods

##### `json`

Parse the request body as JSON.

```python
body = request.json()
```

##### `form`

Parse the request body as form data.

```python
form_data = request.form()
```

##### `body`

Get the raw request body.

```python
raw_body = request.body()
```

### Response Class

The `Response` class represents an HTTP response.

```python
from apifrom.core.response import Response

@api(route="/custom-response", method="GET")
def custom_response() -> Response:
    return Response(
        content={"message": "Hello, world!"},
        status_code=200,
        headers={"X-Custom-Header": "Value"}
    )
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `Any` | `None` | The response content |
| `status_code` | `int` | `200` | The HTTP status code |
| `headers` | `Dict[str, str]` | `None` | The response headers |
| `media_type` | `str` | `None` | The media type |
| `background` | `BackgroundTask` | `None` | A background task to run after sending the response |

## Middleware Module

### Middleware Base Class

The `Middleware` class is the base class for all middleware components.

```python
from apifrom.middleware import Middleware
from apifrom.core.request import Request
from apifrom.core.response import Response
from typing import Callable, Awaitable

class CustomMiddleware(Middleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Process the request
        print(f"Request: {request.method} {request.url.path}")
        
        # Call the next middleware or endpoint
        response = await call_next(request)
        
        # Process the response
        print(f"Response: {response.status_code}")
        return response
```

#### Methods

##### `dispatch`

Process the request and response.

```python
async def dispatch(
    self,
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    # Implementation
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `request` | `Request` | The request object |
| `call_next` | `Callable[[Request], Awaitable[Response]]` | The next middleware in the stack |

### Built-in Middleware Components

#### CacheMiddleware

```python
from apifrom.middleware import CacheMiddleware

app.add_middleware(
    CacheMiddleware(
        ttl=60,
        max_size=1000,
        key_builder=None,
        storage="memory",
        redis_url=None,
        include_query_params=True,
        include_headers=False,
        cache_control=True
    )
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ttl` | `int` | `60` | Cache TTL in seconds |
| `max_size` | `int` | `1000` | Maximum number of cached responses |
| `key_builder` | `Callable` | `None` | Custom function to build cache keys |
| `storage` | `str` | `"memory"` | Storage backend (memory, redis) |
| `redis_url` | `str` | `None` | Redis URL (if using redis storage) |
| `include_query_params` | `bool` | `True` | Include query parameters in cache key |
| `include_headers` | `bool` | `False` | Include headers in cache key |
| `cache_control` | `bool` | `True` | Add Cache-Control headers to responses |

#### RateLimitMiddleware

```python
from apifrom.middleware import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware(
        limit=100,
        window=60,
        key_func=lambda request: request.client.host,
        storage="memory",
        redis_url=None,
        headers=True
    )
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int` | `100` | Maximum requests |
| `window` | `int` | `60` | Time window in seconds |
| `key_func` | `Callable` | `lambda request: request.client.host` | Function to extract the client key |
| `storage` | `str` | `"memory"` | Storage backend (memory, redis) |
| `redis_url` | `str` | `None` | Redis URL (if using redis storage) |
| `headers` | `bool` | `True` | Add rate limit headers to responses |

#### CORSMiddleware

```python
from apifrom.middleware import CORSMiddleware

app.add_middleware(
    CORSMiddleware(
        allow_origins=["https://example.com"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        allow_credentials=True,
        expose_headers=[],
        max_age=600
    )
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `allow_origins` | `List[str]` | `["*"]` | Allowed origins |
| `allow_methods` | `List[str]` | `["GET", "POST", "PUT", "DELETE", "OPTIONS"]` | Allowed methods |
| `allow_headers` | `List[str]` | `["*"]` | Allowed headers |
| `allow_credentials` | `bool` | `False` | Allow credentials |
| `expose_headers` | `List[str]` | `[]` | Headers to expose |
| `max_age` | `int` | `600` | Maximum age of preflight requests |

## Security Module

### JWT Authentication

```python
from apifrom.security import jwt_required

@api(route="/protected", method="GET")
@jwt_required(
    secret="your-secret-key",
    algorithm="HS256",
    token_location="header",
    header_name="Authorization",
    header_type="Bearer",
    verify_exp=True
)
def protected_endpoint(request):
    jwt_payload = request.state.jwt_payload
    return {"user": jwt_payload.get("sub")}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `secret` | `str` | Required | The secret key |
| `algorithm` | `str` | `"HS256"` | The algorithm to use |
| `token_location` | `str` | `"header"` | Where to look for the token (header, query, cookie) |
| `header_name` | `str` | `"Authorization"` | Header name |
| `header_type` | `str` | `"Bearer"` | Header type |
| `verify_exp` | `bool` | `True` | Verify token expiration |
| `verify_aud` | `bool` | `False` | Verify audience |
| `verify_iss` | `bool` | `False` | Verify issuer |
| `verify_sub` | `bool` | `False` | Verify subject |
| `verify_jti` | `bool` | `False` | Verify JWT ID |
| `verify_at_hash` | `bool` | `False` | Verify access token hash |

### API Key Authentication

```python
from apifrom.security import api_key_required

@api(route="/api-key-protected", method="GET")
@api_key_required(
    api_keys={"api-key-1": ["read"]},
    scopes=["read"],
    header_name="X-API-Key",
    query_param_name=None,
    cookie_name=None
)
def api_key_protected_endpoint(request):
    api_key = request.state.api_key
    return {"api_key": api_key}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_keys` | `Dict[str, List[str]]` | Required | API keys and their scopes |
| `scopes` | `List[str]` | `[]` | Required scopes |
| `header_name` | `str` | `"X-API-Key"` | Header name |
| `query_param_name` | `str` | `None` | Query parameter name |
| `cookie_name` | `str` | `None` | Cookie name |

### Basic Authentication

```python
from apifrom.security import basic_auth_required

@api(route="/basic-auth-protected", method="GET")
@basic_auth_required(
    credentials={"user1": "password1"},
    realm="My API"
)
def basic_auth_protected_endpoint(request):
    username = request.state.username
    return {"username": username}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `credentials` | `Dict[str, str]` | Required | Username and password pairs |
| `realm` | `str` | `"APIFromAnything"` | Realm for WWW-Authenticate header |

## Performance Module

### Caching

```python
from apifrom.performance import cache

@api(route="/expensive-operation", method="GET")
@cache(ttl=60)
def expensive_operation():
    # Expensive operation
    return {"result": "expensive computation"}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ttl` | `int` | `60` | Cache TTL in seconds |
| `key_builder` | `Callable` | `None` | Custom function to build cache keys |
| `key_prefix` | `str` | `None` | Prefix for cache keys |
| `storage` | `str` | `"memory"` | Storage backend (memory, redis) |
| `redis_url` | `str` | `None` | Redis URL (if using redis storage) |
| `invalidate_on_update` | `bool` | `False` | Invalidate cache on update |
| `stale_while_revalidate` | `bool` | `False` | Serve stale data while revalidating |
| `stale_ttl` | `int` | `3600` | Stale data TTL in seconds |
| `vary_by_headers` | `List[str]` | `[]` | Vary cache by headers |
| `vary_by_query_params` | `List[str] | `[]` | Vary cache by query parameters |

### Request Coalescing

```python
from apifrom.performance import coalesce_requests

@api(route="/popular-data", method="GET")
@coalesce_requests(ttl=30, max_wait_time=0.05)
async def get_popular_data():
    # Expensive operation
    return {"data": "expensive computation result"}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ttl` | `int` | `30` | Cache TTL in seconds |
| `max_wait_time` | `float` | `0.05` | Maximum wait time in seconds |
| `key_builder` | `Callable` | `lambda request: request.url.path` | Custom key builder |

### Batch Processing

```python
from apifrom.performance import batch_process

@api(route="/users", method="POST")
@batch_process(max_batch_size=100, max_wait_time=0.1)
async def create_users(user_data_batch):
    # Bulk insert all users in the batch
    return db.bulk_insert_users(user_data_batch)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_batch_size` | `int` | `100` | Maximum batch size |
| `max_wait_time` | `float` | `0.1` | Maximum wait time in seconds |
| `key_builder` | `Callable` | `lambda request: request.url.path` | Custom key builder |

### Web Decorator

```python
from apifrom.performance import Web

@api(route="/products", method="GET")
@Web.optimize(
    cache_ttl=30,
    profile=True,
    connection_pool=True,
    request_coalescing=True,
    batch_processing=True,
    batch_size=100
)
def get_products():
    # Your code here (automatically optimized)
    return {"products": [...]}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cache_ttl` | `int` | `60` | Cache TTL in seconds |
| `profile` | `bool` | `False` | Enable profiling |
| `connection_pool` | `bool` | `False` | Enable connection pooling |
| `request_coalescing` | `bool` | `False` | Enable request coalescing |
| `batch_processing` | `bool` | `False` | Enable batch processing |
| `batch_size` | `int` | `100` | Batch size |

## Exceptions Module

### Base Exception Classes

#### APIError

Base class for all API errors.

```python
from apifrom.exceptions import APIError

raise APIError(message="An error occurred", status_code=500, details={"error": "details"})
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | `"An error occurred"` | Error message |
| `status_code` | `int` | `500` | HTTP status code |
| `details` | `Dict` | `None` | Additional error details |

### Common Error Classes

#### BadRequestError

```python
from apifrom.exceptions import BadRequestError

raise BadRequestError(message="Invalid input", details={"field": "name", "error": "Required"})
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | `"Bad request"` | Error message |
| `details` | `Dict` | `None` | Additional error details |

#### NotFoundError

```python
from apifrom.exceptions import NotFoundError

raise NotFoundError(message="User not found", details={"user_id": 123})
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | `"Not found"` | Error message |
| `details` | `Dict` | `None` | Additional error details |

#### UnauthorizedError

```python
from apifrom.exceptions import UnauthorizedError

raise UnauthorizedError(message="Authentication required")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | `"Unauthorized"` | Error message |
| `details` | `Dict` | `None` | Additional error details |

#### ForbiddenError

```python
from apifrom.exceptions import ForbiddenError

raise ForbiddenError(message="Insufficient permissions")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | `"Forbidden"` | Error message |
| `details` | `Dict` | `None` | Additional error details |

## Monitoring Module

### MetricsCollector

```python
from apifrom.monitoring import MetricsCollector

metrics = MetricsCollector()

# Create a counter
counter = metrics.create_counter(
    name="requests_total",
    description="Total number of requests",
    labels=["method", "path"]
)

# Increment the counter
counter.inc(labels={"method": "GET", "path": "/users"})

# Create a gauge
gauge = metrics.create_gauge(
    name="active_requests",
    description="Number of active requests",
    labels=["method"]
)

# Set the gauge value
gauge.set(1, labels={"method": "GET"})

# Create a histogram
histogram = metrics.create_histogram(
    name="request_duration_seconds",
    description="Request duration in seconds",
    labels=["method", "path"],
    buckets=[0.1, 0.5, 1.0, 5.0]
)

# Observe a value
histogram.observe(0.2, labels={"method": "GET", "path": "/users"})
```

### MetricsMiddleware

```python
from apifrom.monitoring import MetricsMiddleware

app.add_middleware(
    MetricsMiddleware(
        collector=metrics,
        prefix="api",
        include_paths=True,
        include_methods=True,
        include_status_codes=True
    )
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `collector` | `MetricsCollector` | Required | The metrics collector |
| `prefix` | `str` | `"api"` | Prefix for metric names |
| `include_paths` | `bool` | `True` | Include paths in labels |
| `include_methods` | `bool` | `True` | Include methods in labels |
| `include_status_codes` | `bool` | `True` | Include status codes in labels |

### PrometheusExporter

```python
from apifrom.monitoring import PrometheusExporter

exporter = PrometheusExporter(collector=metrics)

@api(route="/metrics", method="GET")
def metrics():
    return exporter.export()
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `collector` | `MetricsCollector` | Required | The metrics collector |

## Adapters Module

### LambdaAdapter

```python
from apifrom import API
from apifrom.adapters import LambdaAdapter

app = API()

@app.api(route="/hello/{name}", method="GET")
def hello(name: str):
    return {"message": f"Hello, {name}!"}

lambda_adapter = LambdaAdapter(app)

def handler(event, context):
    return lambda_adapter.handle(event, context)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | `API` | Required | The API instance |

### VercelAdapter

```python
from apifrom import API
from apifrom.adapters import VercelAdapter

app = API()

@app.api(route="/api/hello", method="GET")
def hello(name: str = "World"):
    return {"message": f"Hello, {name}!"}

vercel_adapter = VercelAdapter(app)

def handler(req):
    return vercel_adapter.handle(req)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | `API` | Required | The API instance |

## Utility Functions

### create_jwt_token

```python
from apifrom.security import create_jwt_token

token = create_jwt_token(
    payload={"sub": "user123", "role": "admin"},
    secret="your-secret-key",
    algorithm="HS256",
    expires_delta=3600
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `payload` | `Dict` | Required | The JWT payload |
| `secret` | `str` | Required | The secret key |
| `algorithm` | `str` | `"HS256"` | The algorithm to use |
| `expires_delta` | `int` | `None` | Token expiration in seconds |

### invalidate_cache

```python
from apifrom.performance import invalidate_cache

invalidate_cache("user:123")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | `str` | Required | The cache key to invalidate |
| `storage` | `str` | `"memory"` | Storage backend (memory, redis) |
| `redis_url` | `str` | `None` | Redis URL (if using redis storage) |

### get_performance_metrics

```python
from apifrom.performance import get_performance_metrics

metrics = get_performance_metrics()
```

## Constants

### HTTP Methods

```python
from apifrom.constants import HTTPMethod

HTTPMethod.GET    # "GET"
HTTPMethod.POST   # "POST"
HTTPMethod.PUT    # "PUT"
HTTPMethod.DELETE # "DELETE"
HTTPMethod.PATCH  # "PATCH"
HTTPMethod.HEAD   # "HEAD"
HTTPMethod.OPTIONS # "OPTIONS"
```

### Status Codes

```python
from apifrom.constants import StatusCode

StatusCode.OK                    # 200
StatusCode.CREATED               # 201
StatusCode.ACCEPTED              # 202
StatusCode.NO_CONTENT            # 204
StatusCode.BAD_REQUEST           # 400
StatusCode.UNAUTHORIZED          # 401
StatusCode.FORBIDDEN             # 403
StatusCode.NOT_FOUND             # 404
StatusCode.METHOD_NOT_ALLOWED    # 405
StatusCode.CONFLICT              # 409
StatusCode.GONE                  # 410
StatusCode.UNPROCESSABLE_ENTITY  # 422
StatusCode.TOO_MANY_REQUESTS     # 429
StatusCode.INTERNAL_SERVER_ERROR # 500
StatusCode.NOT_IMPLEMENTED       # 501
StatusCode.BAD_GATEWAY           # 502
StatusCode.SERVICE_UNAVAILABLE   # 503
StatusCode.GATEWAY_TIMEOUT       # 504
```

## Plugin System

The plugin system allows you to extend and customize the functionality of your API.

### Plugin Class

The `Plugin` abstract base class defines the interface that all plugins must implement.

```python
from apifrom.plugins import Plugin
```

#### Methods

##### `get_metadata`

Get the metadata for this plugin.

```python
def get_metadata(self) -> PluginMetadata:
    """
    Get the metadata for this plugin.
    
    Returns:
        The plugin metadata
    """
    pass
```

##### `get_config`

Get the configuration for this plugin.

```python
def get_config(self) -> PluginConfig:
    """
    Get the configuration for this plugin.
    
    Returns:
        The plugin configuration
    """
    return PluginConfig()
```

##### `initialize`

Initialize the plugin.

```python
def initialize(self, api: API) -> None:
    """
    Initialize the plugin.
    
    Args:
        api: The API instance
    """
    self._api = api
    self._state = PluginState.INITIALIZED
```

##### `activate`

Activate the plugin.

```python
def activate(self) -> None:
    """
    Activate the plugin.
    """
    self._state = PluginState.ACTIVE
```

##### `deactivate`

Deactivate the plugin.

```python
def deactivate(self) -> None:
    """
    Deactivate the plugin.
    """
    self._state = PluginState.DISABLED
```

##### `shutdown`

Shutdown the plugin.

```python
def shutdown(self) -> None:
    """
    Shutdown the plugin.
    """
    pass
```

##### `pre_request`

Process a request before it is handled by the API.

```python
async def pre_request(self, request: Request) -> Request:
    """
    Process a request before it is handled by the API.
    
    Args:
        request: The request object
        
    Returns:
        The processed request object
    """
    return request
```

##### `post_response`

Process a response after it is generated by the API.

```python
async def post_response(self, response: Response, request: Request) -> Response:
    """
    Process a response after it is generated by the API.
    
    Args:
        response: The response object
        request: The request object
        
    Returns:
        The processed response object
    """
    return response
```

##### `on_error`

Handle an error that occurred during request processing.

```python
async def on_error(self, error: Exception, request: Request) -> Optional[Response]:
    """
    Handle an error that occurred during request processing.
    
    Args:
        error: The error that occurred
        request: The request object
        
    Returns:
        A response object, or None to let the API handle the error
    """
    return None
```

##### `on_event`

Handle an event emitted by the plugin system.

```python
async def on_event(self, event: PluginEvent, **kwargs) -> None:
    """
    Handle an event emitted by the plugin system.
    
    Args:
        event: The event that occurred
        **kwargs: Additional event data
    """
    pass
```

##### `register_hook`

Register a callback for a hook.

```python
def register_hook(self, hook: PluginHook, callback: Callable, priority: int = PluginPriority.NORMAL.value) -> None:
    """
    Register a callback for a hook.
    
    Args:
        hook: The hook to register for
        callback: The callback function
        priority: The priority of the callback
    """
    hook.register(callback, priority)
```

##### `unregister_hook`

Unregister a callback from a hook.

```python
def unregister_hook(self, hook: PluginHook, callback: Callable) -> None:
    """
    Unregister a callback from a hook.
    
    Args:
        hook: The hook to unregister from
        callback: The callback function
    """
    hook.unregister(callback)
```

### PluginManager Class

The `PluginManager` class manages the registration and execution of plugins.

```python
from apifrom.plugins.base import PluginManager
```

#### Methods

##### `register_plugin`

Register a plugin with the manager.

```python
def register_plugin(self, plugin: Plugin) -> None:
    """
    Register a plugin with the manager.
    
    Args:
        plugin: The plugin to register
        
    Raises:
        PluginDependencyError: If a plugin dependency cannot be satisfied
        PluginConfigurationError: If the plugin configuration is invalid
    """
    pass
```

##### `register`

Register a plugin with the manager (alias for register_plugin).

```python
def register(self, plugin: Plugin) -> None:
    """
    Register a plugin with the manager (alias for register_plugin).
    
    Args:
        plugin: The plugin to register
    """
    self.register_plugin(plugin)
```

##### `unregister_plugin`

Unregister a plugin from the manager.

```python
def unregister_plugin(self, plugin_name: str) -> None:
    """
    Unregister a plugin from the manager.
    
    Args:
        plugin_name: The name of the plugin to unregister
        
    Raises:
        ValueError: If the plugin is not registered
        PluginDependencyError: If other plugins depend on this plugin
    """
    pass
```

##### `unregister`

Unregister a plugin from the manager (alias for unregister_plugin).

```python
def unregister(self, plugin_name: str) -> None:
    """
    Unregister a plugin from the manager (alias for unregister_plugin).
    
    Args:
        plugin_name: The name of the plugin to unregister
    """
    self.unregister_plugin(plugin_name)
```

##### `get_plugin`

Get a plugin by name.

```python
def get_plugin(self, plugin_name: str) -> Plugin:
    """
    Get a plugin by name.
    
    Args:
        plugin_name: The name of the plugin
        
    Returns:
        The plugin instance
        
    Raises:
        ValueError: If the plugin is not registered
    """
    pass
```

##### `get_plugins_by_tag`

Get plugins by tag.

```python
def get_plugins_by_tag(self, tag: str) -> List[Plugin]:
    """
    Get plugins by tag.
    
    Args:
        tag: The tag to filter by
        
    Returns:
        A list of plugins with the specified tag
    """
    pass
```

##### `get_plugins_by_state`

Get plugins by state.

```python
def get_plugins_by_state(self, state: PluginState) -> List[Plugin]:
    """
    Get plugins by state.
    
    Args:
        state: The state to filter by
        
    Returns:
        A list of plugins in the specified state
    """
    pass
```

##### `register_hook`

Register a new hook.

```python
def register_hook(self, name: str, description: str = "") -> PluginHook:
    """
    Register a new hook.
    
    Args:
        name: The name of the hook
        description: A description of the hook
        
    Returns:
        The hook instance
    """
    pass
```

##### `get_hook`

Get a hook by name.

```python
def get_hook(self, name: str) -> Optional[PluginHook]:
    """
    Get a hook by name.
    
    Args:
        name: The name of the hook
        
    Returns:
        The hook instance, or None if not found
    """
    pass
```

### PluginMetadata Class

The `PluginMetadata` class stores metadata about a plugin.

```python
from apifrom.plugins.base import PluginMetadata
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | The name of the plugin |
| `version` | `str` | Required | The version of the plugin |
| `description` | `str` | `""` | A description of the plugin |
| `author` | `str` | `""` | The author of the plugin |
| `website` | `str` | `""` | The website of the plugin |
| `license` | `str` | `""` | The license of the plugin |
| `dependencies` | `List[str]` | `None` | A list of plugin names that this plugin depends on |
| `tags` | `List[str]` | `None` | A list of tags for the plugin |

### PluginConfig Class

The `PluginConfig` class stores configuration options for a plugin.

```python
from apifrom.plugins.base import PluginConfig
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `defaults` | `Dict[str, Any]` | `None` | Default values for configuration options |
| `schema` | `Dict[str, Any]` | `None` | JSON Schema for validating configuration options |

#### Methods

##### `get`

Get a configuration value.

```python
def get(self, key: str, default: Any = None) -> Any:
    """
    Get a configuration value.
    
    Args:
        key: The configuration key
        default: The default value to return if the key is not found
        
    Returns:
        The configuration value
    """
    pass
```

##### `set`

Set a configuration value.

```python
def set(self, key: str, value: Any) -> None:
    """
    Set a configuration value.
    
    Args:
        key: The configuration key
        value: The configuration value
    """
    pass
```

##### `update`

Update multiple configuration values.

```python
def update(self, values: Dict[str, Any]) -> None:
    """
    Update multiple configuration values.
    
    Args:
        values: A dictionary of configuration values to update
    """
    pass
```

##### `validate`

Validate the configuration against the schema.

```python
def validate(self) -> bool:
    """
    Validate the configuration against the schema.
    
    Returns:
        True if the configuration is valid, False otherwise
    """
    pass
```

### PluginHook Class

The `PluginHook` class provides a way for plugins to register callbacks for specific hooks.

```python
from apifrom.plugins.base import PluginHook
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | The name of the hook |
| `description` | `str` | `""` | A description of the hook |

#### Methods

##### `register`

Register a callback for this hook.

```python
def register(self, callback: Callable[..., T], priority: int = PluginPriority.NORMAL.value) -> None:
    """
    Register a callback for this hook.
    
    Args:
        callback: The callback function
        priority: The priority of the callback (higher priority callbacks are executed first)
    """
    pass
```

##### `unregister`

Unregister a callback from this hook.

```python
def unregister(self, callback: Callable[..., T]) -> None:
    """
    Unregister a callback from this hook.
    
    Args:
        callback: The callback function to unregister
    """
    pass
```

### PluginEvent Enum

The `PluginEvent` enum defines events that can be emitted by the plugin system.

```python
from apifrom.plugins.base import PluginEvent
```

#### Values

| Value | Description |
|-------|-------------|
| `PLUGIN_REGISTERED` | A plugin has been registered |
| `PLUGIN_INITIALIZED` | A plugin has been initialized |
| `PLUGIN_ACTIVATED` | A plugin has been activated |
| `PLUGIN_DISABLED` | A plugin has been disabled |
| `PLUGIN_ERROR` | An error occurred in a plugin |
| `SERVER_STARTING` | The server is starting |
| `SERVER_STARTED` | The server has started |
| `SERVER_STOPPING` | The server is stopping |
| `SERVER_STOPPED` | The server has stopped |
| `REQUEST_RECEIVED` | A request has been received |
| `RESPONSE_SENT` | A response has been sent |
| `ERROR_OCCURRED` | An error occurred during request processing |

### PluginState Enum

The `PluginState` enum defines the possible states for plugins.

```python
from apifrom.plugins.base import PluginState
```

#### Values

| Value | Description |
|-------|-------------|
| `REGISTERED` | The plugin is registered but not initialized |
| `INITIALIZED` | The plugin is initialized but not active |
| `ACTIVE` | The plugin is active and processing requests |
| `DISABLED` | The plugin is disabled and not processing requests |
| `ERROR` | The plugin encountered an error |

### PluginPriority Enum

The `PluginPriority` enum defines priority levels for plugins.

```python
from apifrom.plugins.base import PluginPriority
```

#### Values

| Value | Description |
|-------|-------------|
| `HIGHEST` | Highest priority (100) |
| `HIGH` | High priority (75) |
| `NORMAL` | Normal priority (50) |
| `LOW` | Low priority (25) |
| `LOWEST` | Lowest priority (0) |

### Built-in Plugins

#### LoggingPlugin

The `LoggingPlugin` logs requests and responses.

```python
from apifrom.plugins import LoggingPlugin
```

##### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `logger` | `Optional[logging.Logger]` | `None` | The logger to use (defaults to a new logger) |
| `level` | `int` | `logging.INFO` | The logging level |
| `log_request_body` | `bool` | `False` | Whether to log request bodies |
| `log_response_body` | `bool` | `False` | Whether to log response bodies |
| `log_headers` | `bool` | `False` | Whether to log headers |
| `exclude_paths` | `list` | `None` | Paths to exclude from logging |
| `exclude_methods` | `list` | `None` | HTTP methods to exclude from logging |

## 🔄 Async Support

APIFromAnything provides comprehensive support for asynchronous programming using Python's `async`/`await` syntax. This allows you to build high-performance APIs that can handle many concurrent requests efficiently.

### Async API Endpoints

You can define asynchronous API endpoints using the `async def` syntax:

```python
from apifrom import API, api
import asyncio

app = API(title="Async API")

@api(route="/async-hello/{name}", method="GET")
async def async_hello(name: str, delay: float = 1.0) -> dict:
    """Say hello asynchronously after a delay."""
    await asyncio.sleep(delay)  # Non-blocking sleep
    return {"message": f"Hello, {name}!", "delay": delay}

@api(route="/parallel", method="GET")
async def parallel_operations():
    """Execute multiple operations in parallel."""
    # Create tasks for concurrent execution
    task1 = asyncio.create_task(async_operation_1())
    task2 = asyncio.create_task(async_operation_2())
    task3 = asyncio.create_task(async_operation_3())
    
    # Wait for all tasks to complete
    results = await asyncio.gather(task1, task2, task3)
    
    return {
        "operation1": results[0],
        "operation2": results[1],
        "operation3": results[2]
    }

async def async_operation_1():
    await asyncio.sleep(1)
    return "Result 1"

async def async_operation_2():
    await asyncio.sleep(1)
    return "Result 2"

async def async_operation_3():
    await asyncio.sleep(1)
    return "Result 3"
```

### Async Middleware

Middleware components can also be asynchronous:

```python
from apifrom import API
from apifrom.middleware import Middleware
from apifrom.core.request import Request
from apifrom.core.response import Response
from typing import Callable, Awaitable
import time

class AsyncTimingMiddleware(Middleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = time.time()
        
        # Process the request through the next middleware or endpoint
        response = await call_next(request)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Add timing header to response
        response.headers["X-Processing-Time"] = f"{processing_time:.6f} seconds"
        
        return response

# Create an API instance
app = API()

# Add async middleware to the API
app.add_middleware(AsyncTimingMiddleware())
```

### Async Database Operations

When working with databases, you can use async database libraries for non-blocking database operations:

```python
from apifrom import API, api
import asyncpg

app = API(title="Async Database API")

# Database connection pool
db_pool = None

@app.on_startup
async def setup_database():
    global db_pool
    db_pool = await asyncpg.create_pool(
        "postgresql://user:password@localhost/database"
    )

@app.on_shutdown
async def close_database():
    await db_pool.close()

@api(route="/users", method="GET")
async def get_users():
    """Get all users from the database."""
    async with db_pool.acquire() as connection:
        rows = await connection.fetch("SELECT id, name, email FROM users")
        return [dict(row) for row in rows]

@api(route="/users/{user_id}", method="GET")
async def get_user(user_id: int):
    """Get a user by ID."""
    async with db_pool.acquire() as connection:
        row = await connection.fetchrow(
            "SELECT id, name, email FROM users WHERE id = $1",
            user_id
        )
        if not row:
            return {"error": "User not found"}, 404
        return dict(row)

@api(route="/users", method="POST")
async def create_user(name: str, email: str):
    """Create a new user."""
    async with db_pool.acquire() as connection:
        user_id = await connection.fetchval(
            "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id",
            name, email
        )
        return {"id": user_id, "name": name, "email": email}
``` 