# Core Concepts

This document explains the fundamental concepts and components of the APIFromAnything library.

## API Class

The `API` class is the main entry point for creating an API. It serves as a container for your API endpoints and provides methods for configuring and running your API.

```python
from apifrom import API

app = API(
    title="My API",
    description="A powerful API built with APIFromAnything",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url="/redoc",
    debug=True
)
```

### Key Properties

- **title**: The name of your API, displayed in the documentation
- **description**: A detailed description of your API
- **version**: The version of your API
- **docs_url**: The URL path for the Swagger UI documentation
- **openapi_url**: The URL path for the OpenAPI schema
- **redoc_url**: The URL path for the ReDoc documentation
- **debug**: Enable debug mode for detailed error messages

### Key Methods

- **run()**: Start the API server
- **add_middleware()**: Add a middleware component to the API
- **mount()**: Mount a sub-application at a specific path
- **include_router()**: Include a router in the API

## API Decorator

The `@api` decorator is used to transform a Python function into an API endpoint. It handles routing, request parsing, validation, and response serialization.

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
    # Function implementation
    return {"id": user_id, "name": "John Doe"}
```

### Key Parameters

- **route**: The URL path for the endpoint, can include path parameters
- **method**: The HTTP method (GET, POST, PUT, DELETE, etc.)
- **tags**: Tags for organizing endpoints in the documentation
- **summary**: A brief summary of the endpoint
- **description**: A detailed description of the endpoint
- **response_model**: The expected response model
- **status_code**: The HTTP status code for successful responses
- **deprecated**: Mark the endpoint as deprecated
- **include_in_schema**: Include the endpoint in the OpenAPI schema

## Request and Response

APIFromAnything provides `Request` and `Response` classes for handling HTTP requests and responses.

### Request

The `Request` class represents an HTTP request and provides methods for accessing request data.

```python
from apifrom.core.request import Request

@api(route="/echo", method="POST")
def echo(request: Request) -> dict:
    # Access request data
    body = request.json()
    headers = request.headers
    query_params = request.query_params
    path_params = request.path_params
    cookies = request.cookies
    client_ip = request.client.host
    
    return {
        "body": body,
        "headers": dict(headers),
        "query_params": dict(query_params),
        "path_params": dict(path_params),
        "cookies": dict(cookies),
        "client_ip": client_ip
    }
```

### Response

The `Response` class represents an HTTP response and allows you to customize the response.

```python
from apifrom.core.response import Response

@api(route="/custom-response", method="GET")
def custom_response() -> Response:
    return Response(
        content={"message": "Hello, World!"},
        status_code=200,
        headers={"X-Custom-Header": "Value"},
        media_type="application/json"
    )
```

## Router

The `Router` class allows you to organize your API endpoints into groups.

```python
from apifrom import API, Router, api

app = API()

# Create a router for user-related endpoints
user_router = Router(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "User not found"}}
)

# Add endpoints to the router
@user_router.api(route="/{user_id}", method="GET")
def get_user(user_id: int) -> dict:
    return {"id": user_id, "name": "John Doe"}

@user_router.api(route="/", method="POST")
def create_user(name: str, email: str) -> dict:
    return {"id": 123, "name": name, "email": email}

# Include the router in the API
app.include_router(user_router)
```

## Middleware

Middleware components process requests and responses before and after they reach your API endpoints. They can be used for authentication, logging, error handling, and more.

```python
from apifrom import API
from apifrom.middleware import Middleware
from apifrom.core.request import Request
from apifrom.core.response import Response
from typing import Callable, Awaitable

# Create a custom middleware
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

# Add the middleware to the API
app = API()
app.add_middleware(LoggingMiddleware())
```

## Type Validation

APIFromAnything uses Python type hints and Pydantic models for request validation.

### Basic Type Validation

```python
@api(route="/users", method="POST")
def create_user(
    name: str,
    email: str,
    age: int,
    is_active: bool = True
) -> dict:
    return {
        "name": name,
        "email": email,
        "age": age,
        "is_active": is_active
    }
```

### Advanced Type Validation with Pydantic

```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class User(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    age: int = Field(..., ge=18, le=120)
    role: UserRole = UserRole.USER
    tags: List[str] = []
    address: Optional[Address] = None

@api(route="/users", method="POST")
def create_user(user: User) -> dict:
    return user.dict()
```

## Asynchronous Support

APIFromAnything supports both synchronous and asynchronous functions.

```python
import asyncio
from apifrom import API, api

app = API()

@api(route="/sync", method="GET")
def sync_endpoint() -> dict:
    # Synchronous function
    return {"message": "Sync endpoint"}

@api(route="/async", method="GET")
async def async_endpoint() -> dict:
    # Asynchronous function
    await asyncio.sleep(0.1)
    return {"message": "Async endpoint"}
```

## Plugin System

The plugin system allows you to extend and customize the functionality of your API.

```python
from apifrom import API, Plugin
from apifrom.plugins.base import PluginMetadata

# Create a custom plugin
class TimingPlugin(Plugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="timing",
            version="1.0.0",
            description="Measures request execution time"
        )
    
    async def pre_request(self, request):
        request.state.start_time = time.time()
        return request
    
    async def post_response(self, response, request):
        duration = time.time() - request.state.start_time
        response.headers["X-Execution-Time"] = f"{duration:.4f}s"
        return response

# Register the plugin
app = API()
app.plugin_manager.register(TimingPlugin())
```

## Serverless Adapters

APIFromAnything includes adapters for popular serverless platforms.

```python
from apifrom import API, api
from apifrom.adapters import LambdaAdapter

# Create an API
app = API(title="Serverless API")

@api(route="/hello/{name}", method="GET")
def hello(name: str):
    return {"message": f"Hello, {name}!"}

# Create a Lambda handler
lambda_adapter = LambdaAdapter(app)

def handler(event, context):
    return lambda_adapter.handle(event, context)
```

## OpenAPI Documentation

APIFromAnything automatically generates OpenAPI documentation for your API.

```python
from apifrom import API, api

app = API(
    title="My API",
    description="API description",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    openapi_url="/openapi.json",  # OpenAPI schema
    redoc_url="/redoc"  # ReDoc
)

@api(
    route="/users/{user_id}",
    method="GET",
    tags=["users"],
    summary="Get a user",
    description="Get a user by ID",
    response_model=dict,
    status_code=200
)
def get_user(user_id: int) -> dict:
    """
    Get a user by ID.
    
    Args:
        user_id: The ID of the user to retrieve
        
    Returns:
        User information
    """
    return {"id": user_id, "name": "John Doe"}
```

Visit `http://localhost:8000/docs` to see the Swagger UI documentation, `http://localhost:8000/redoc` for ReDoc, or `http://localhost:8000/openapi.json` for the raw OpenAPI schema. 