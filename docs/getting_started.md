# Getting Started with APIFromAnything

This guide will help you get started with APIFromAnything, a powerful Python library for creating APIs from any Python function. Version 1.0.0 is now production-ready with full async support and many other improvements.

## Installation

### Basic Installation

```bash
pip install apifrom
```

### Installation with Optional Dependencies

```bash
# With database support (SQLAlchemy, PostgreSQL, MySQL, SQLite)
pip install "apifrom[database]"

# With caching support (Redis)
pip install "apifrom[cache]"

# With monitoring support (Prometheus)
pip install "apifrom[monitoring]"

# With development tools
pip install "apifrom[dev]"

# With all optional dependencies
pip install "apifrom[all]"
```

## Quick Start

### Creating Your First API

Create a file named `app.py`:

```python
from apifrom import API, api

# Create an API instance
app = API(
    title="My First API",
    description="A simple API created with APIFromAnything",
    version="1.0.0"
)

# Define an API endpoint
@api(route="/hello/{name}", method="GET")
def hello(name: str, greeting: str = "Hello") -> dict:
    """Say hello to someone."""
    return {"message": f"{greeting}, {name}!"}

# Run the API server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

Run your API:

```bash
python app.py
```

Visit `http://localhost:8000/hello/world` in your browser or use curl:

```bash
curl http://localhost:8000/hello/world
```

You should see:

```json
{"message": "Hello, world!"}
```

### Creating an Async API

APIFromAnything has full support for async/await. Here's how to create an async API:

```python
from apifrom import API, api
import asyncio

app = API(
    title="Async API Example",
    description="An async API created with APIFromAnything",
    version="1.0.0"
)

@api(route="/async-hello/{name}", method="GET")
async def async_hello(name: str, greeting: str = "Hello") -> dict:
    """Say hello to someone asynchronously."""
    # Simulate an async operation
    await asyncio.sleep(1)
    return {"message": f"{greeting}, {name}!", "async": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Testing Your API

Test the API using curl:

```bash
curl "http://localhost:8000/hello/World?greeting=Hi"
# {"message": "Hi, World!"}
```

Or visit the automatic Swagger documentation at `http://localhost:8000/docs`.

## Core Concepts

### API Instance

The `API` class is the main entry point for creating an API:

```python
from apifrom import API

app = API(
    title="My API",
    description="API description",
    version="1.0.0",
    docs_url="/docs",  # URL for Swagger documentation
    openapi_url="/openapi.json",  # URL for OpenAPI schema
    redoc_url="/redoc",  # URL for ReDoc documentation
    debug=True  # Enable debug mode
)
```

### API Decorator

The `@api` decorator is used to define API endpoints:

```python
from apifrom import api

@api(
    route="/users/{user_id}",  # URL path with path parameters
    method="GET",  # HTTP method (GET, POST, PUT, DELETE, etc.)
    tags=["users"],  # Tags for documentation
    summary="Get a user",  # Summary for documentation
    description="Get a user by ID",  # Description for documentation
    response_model=dict,  # Expected response model
    status_code=200,  # HTTP status code
    deprecated=False,  # Mark as deprecated
    include_in_schema=True  # Include in OpenAPI schema
)
def get_user(user_id: int) -> dict:
    # Function implementation
    return {"id": user_id, "name": "John Doe"}
```

### Request and Response

APIFromAnything automatically handles request parsing and response serialization:

```python
from apifrom import API, api
from apifrom.core.request import Request
from apifrom.core.response import Response

app = API()

@api(route="/echo", method="POST")
def echo(request: Request) -> Response:
    """Echo the request body."""
    # Access request data
    body = request.json()
    headers = request.headers
    query_params = request.query_params
    path_params = request.path_params
    
    # Create a custom response
    return Response(
        content=body,
        status_code=200,
        headers={"X-Custom-Header": "Value"}
    )
```

### Path Parameters

Path parameters are defined in the route path and automatically parsed:

```python
@api(route="/users/{user_id}/posts/{post_id}", method="GET")
def get_user_post(user_id: int, post_id: int) -> dict:
    """Get a post by a specific user."""
    return {"user_id": user_id, "post_id": post_id}
```

### Query Parameters

Query parameters are automatically parsed from the URL:

```python
@api(route="/search", method="GET")
def search(query: str, page: int = 1, limit: int = 10) -> dict:
    """Search for items."""
    return {
        "query": query,
        "page": page,
        "limit": limit,
        "results": []
    }
```

### Request Body

Request body is automatically parsed based on the function parameters:

```python
from typing import List, Dict, Optional

@api(route="/users", method="POST")
def create_user(
    name: str,
    email: str,
    age: int,
    tags: List[str] = [],
    metadata: Dict[str, str] = {},
    address: Optional[str] = None
) -> dict:
    """Create a new user."""
    return {
        "id": 123,
        "name": name,
        "email": email,
        "age": age,
        "tags": tags,
        "metadata": metadata,
        "address": address
    }
```

### Type Validation

APIFromAnything automatically validates input types:

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
    """Create a new user."""
    return user.dict()
```

### Plugin System

The plugin system allows you to extend and customize the functionality of your API:

```python
from apifrom import API
from apifrom.plugins import LoggingPlugin

# Create an API instance
app = API(title="My API")

# Create and register a logging plugin
logging_plugin = LoggingPlugin(
    log_request_body=True,
    log_response_body=True
)
app.plugin_manager.register(logging_plugin)
```

Plugins can:
- Process requests before they are handled by the API
- Process responses before they are sent to the client
- Handle errors that occur during request processing
- React to events emitted by the API
- Register callbacks for specific hooks

For more information about the plugin system, see the [Plugin System Documentation](plugins.md).

## Middleware

Middleware allows you to process requests and responses:

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

# Create an API instance
app = API()

# Add middleware to the API
app.add_middleware(LoggingMiddleware())
```

## Error Handling

APIFromAnything provides comprehensive error handling:

```python
from apifrom import API, api
from apifrom.middleware import ErrorHandlingMiddleware
from apifrom.exceptions import BadRequestError, NotFoundError

# Create an API instance
app = API()

# Add error handling middleware
app.add_middleware(
    ErrorHandlingMiddleware(
        debug=True,  # Include debug information in development
        include_traceback=True,  # Include tracebacks in error responses
        log_exceptions=True  # Log exceptions to the console
    )
)

@api(route="/users/{user_id}", method="GET")
def get_user(user_id: int):
    if user_id <= 0:
        raise BadRequestError(message="User ID must be positive")
    
    user = find_user(user_id)
    if not user:
        raise NotFoundError(
            message=f"User with ID {user_id} not found",
            details={"user_id": user_id}
        )
    
    return user
```

## Next Steps

Now that you've learned the basics of APIFromAnything, you can explore more advanced features:

- [Security and Authentication](security.md)
- [Advanced Caching](advanced_caching.md)
- [Middleware System](middleware.md)
- [Performance Optimization](performance.md)
- [Deployment Guide](deployment.md)
- [API Reference](api_reference.md)

For more examples, check the `/examples` directory in the repository. 