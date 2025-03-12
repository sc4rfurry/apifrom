# Examples for APIFromAnything

This document provides a collection of examples demonstrating how to use the APIFromAnything library for various use cases.

## Basic Examples

### Simple API

Create a basic API with a few endpoints:

```python
from apifrom import API, api
from typing import List, Dict, Optional

# Create an API instance
app = API(
    title="User API",
    description="A simple user API",
    version="1.0.0"
)

# In-memory database
users_db = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
]

@api(route="/users", method="GET")
def get_users() -> List[Dict]:
    """Get all users."""
    return users_db

@api(route="/users/{user_id}", method="GET")
def get_user(user_id: int) -> Dict:
    """Get a user by ID."""
    for user in users_db:
        if user["id"] == user_id:
            return user
    return {"error": "User not found"}

@api(route="/users", method="POST")
def create_user(name: str, email: str) -> Dict:
    """Create a new user."""
    user_id = max(user["id"] for user in users_db) + 1
    new_user = {"id": user_id, "name": name, "email": email}
    users_db.append(new_user)
    return new_user

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Type Validation

Use Pydantic models for input validation:

```python
from apifrom import API, api
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

# Create an API instance
app = API(
    title="User API with Validation",
    description="A user API with input validation",
    version="1.0.0"
)

# Define Pydantic models
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    age: int = Field(..., ge=18, le=120)
    tags: List[str] = []

class User(UserCreate):
    id: int

# In-memory database
users_db = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30, "tags": ["admin"]},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 25, "tags": ["user"]},
]

@api(route="/users", method="GET")
def get_users() -> List[User]:
    """Get all users."""
    return [User(**user) for user in users_db]

@api(route="/users/{user_id}", method="GET")
def get_user(user_id: int) -> User:
    """Get a user by ID."""
    for user in users_db:
        if user["id"] == user_id:
            return User(**user)
    raise ValueError(f"User with ID {user_id} not found")

@api(route="/users", method="POST")
def create_user(user: UserCreate) -> User:
    """Create a new user."""
    user_id = max(user["id"] for user in users_db) + 1
    new_user = User(id=user_id, **user.dict())
    users_db.append(new_user.dict())
    return new_user

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Asynchronous API

Create an API with asynchronous endpoints:

```python
import asyncio
from apifrom import API, api
from typing import List, Dict

# Create an API instance
app = API(
    title="Async API",
    description="An asynchronous API example",
    version="1.0.0"
)

# Simulated database
tasks_db = [
    {"id": 1, "title": "Task 1", "completed": False},
    {"id": 2, "title": "Task 2", "completed": True},
]

@api(route="/tasks", method="GET")
async def get_tasks() -> List[Dict]:
    """Get all tasks asynchronously."""
    # Simulate async database query
    await asyncio.sleep(0.1)
    return tasks_db

@api(route="/tasks/{task_id}", method="GET")
async def get_task(task_id: int) -> Dict:
    """Get a task by ID asynchronously."""
    # Simulate async database query
    await asyncio.sleep(0.05)
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    return {"error": "Task not found"}

@api(route="/tasks", method="POST")
async def create_task(title: str) -> Dict:
    """Create a new task asynchronously."""
    # Simulate async database insert
    await asyncio.sleep(0.1)
    task_id = max(task["id"] for task in tasks_db) + 1
    new_task = {"id": task_id, "title": title, "completed": False}
    tasks_db.append(new_task)
    return new_task

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## Middleware Examples

### Logging Middleware

Create a custom logging middleware:

```python
from apifrom import API, api
from apifrom.middleware import Middleware
from apifrom.core.request import Request
from apifrom.core.response import Response
from typing import Callable, Awaitable
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api")

# Create a custom logging middleware
class LoggingMiddleware(Middleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Measure response time
        start_time = time.time()
        
        # Process the request through the next middleware or endpoint
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log response
        logger.info(f"Response: {response.status_code} ({response_time:.3f}s)")
        
        return response

# Create an API instance
app = API(
    title="API with Logging",
    description="An API with custom logging middleware",
    version="1.0.0"
)

# Add the logging middleware
app.add_middleware(LoggingMiddleware())

@api(route="/hello/{name}", method="GET")
def hello(name: str) -> dict:
    """Say hello to someone."""
    return {"message": f"Hello, {name}!"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Multiple Middleware

Use multiple middleware components:

```python
from apifrom import API, api
from apifrom.middleware import (
    CORSMiddleware,
    CacheMiddleware,
    RateLimitMiddleware,
    ErrorHandlingMiddleware
)

# Create an API instance
app = API(
    title="API with Multiple Middleware",
    description="An API with multiple middleware components",
    version="1.0.0"
)

# Add middleware components
app.add_middleware(
    CORSMiddleware(
        allow_origins=["https://example.com"],
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
        allow_credentials=True
    )
)
app.add_middleware(
    CacheMiddleware(
        ttl=60,  # Cache for 60 seconds
        storage="memory"
    )
)
app.add_middleware(
    RateLimitMiddleware(
        limit=100,  # 100 requests per minute
        window=60
    )
)
app.add_middleware(
    ErrorHandlingMiddleware(
        debug=True,
        include_traceback=True,
        log_exceptions=True
    )
)

@api(route="/hello/{name}", method="GET")
def hello(name: str) -> dict:
    """Say hello to someone."""
    return {"message": f"Hello, {name}!"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## Security Examples

### JWT Authentication

Secure an API with JWT authentication:

```python
from apifrom import API, api
from apifrom.security import jwt_required, create_jwt_token
import os

# Create an API instance
app = API(
    title="JWT Secured API",
    description="An API secured with JWT authentication",
    version="1.0.0"
)

# JWT configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"

@api(route="/login", method="POST")
def login(username: str, password: str) -> dict:
    """Login and get a JWT token."""
    # In a real application, you would validate the credentials against a database
    if username == "admin" and password == "password":
        # Create a JWT token
        token = create_jwt_token(
            payload={"sub": username, "role": "admin"},
            secret=JWT_SECRET,
            algorithm=JWT_ALGORITHM,
            expires_delta=3600  # 1 hour
        )
        return {"access_token": token, "token_type": "bearer"}
    return {"error": "Invalid credentials"}

@api(route="/protected", method="GET")
@jwt_required(secret=JWT_SECRET, algorithm=JWT_ALGORITHM)
def protected_endpoint(request) -> dict:
    """A protected endpoint that requires JWT authentication."""
    # Access JWT payload
    jwt_payload = request.state.jwt_payload
    username = jwt_payload.get("sub")
    role = jwt_payload.get("role")
    
    return {
        "message": f"Hello, {username}!",
        "role": role
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### API Key Authentication

Secure an API with API key authentication:

```python
from apifrom import API, api
from apifrom.security import api_key_required

# Create an API instance
app = API(
    title="API Key Secured API",
    description="An API secured with API key authentication",
    version="1.0.0"
)

# API key configuration
API_KEYS = {
    "api-key-1": ["read"],
    "api-key-2": ["read", "write"],
}

@api(route="/read", method="GET")
@api_key_required(api_keys=API_KEYS, scopes=["read"])
def read_endpoint(request) -> dict:
    """A protected endpoint that requires read access."""
    # Access API key
    api_key = request.state.api_key
    
    return {
        "message": "Read access granted",
        "api_key": api_key
    }

@api(route="/write", method="POST")
@api_key_required(api_keys=API_KEYS, scopes=["write"])
def write_endpoint(request, data: str) -> dict:
    """A protected endpoint that requires write access."""
    # Access API key
    api_key = request.state.api_key
    
    return {
        "message": "Write access granted",
        "api_key": api_key,
        "data": data
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Multiple Authentication Methods

Secure an API with multiple authentication methods:

```python
from apifrom import API, api
from apifrom.security import (
    multi_auth_required,
    jwt_required,
    api_key_required,
    basic_auth_required
)

# Create an API instance
app = API(
    title="Multi-Auth API",
    description="An API with multiple authentication methods",
    version="1.0.0"
)

# Authentication configurations
JWT_CONFIG = {"secret": "your-secret-key", "algorithm": "HS256"}
API_KEY_CONFIG = {"api_keys": {"api-key-1": ["read"]}}
BASIC_AUTH_CONFIG = {"credentials": {"user1": "password1"}}

@api(route="/multi-auth", method="GET")
@multi_auth_required(
    auth_methods=[
        jwt_required(**JWT_CONFIG),
        api_key_required(**API_KEY_CONFIG),
        basic_auth_required(**BASIC_AUTH_CONFIG),
    ],
    require_all=False  # Any method can pass
)
def multi_auth_endpoint(request) -> dict:
    """An endpoint that accepts multiple authentication methods."""
    # Check which authentication method passed
    if hasattr(request.state, "jwt_payload"):
        user_id = request.state.jwt_payload.get("sub")
        return {"message": f"Hello, JWT user {user_id}!"}
    elif hasattr(request.state, "api_key"):
        api_key = request.state.api_key
        return {"message": f"Hello, API key {api_key}!"}
    elif hasattr(request.state, "username"):
        username = request.state.username
        return {"message": f"Hello, Basic Auth user {username}!"}
    
    return {"message": "Hello, authenticated user!"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## Performance Examples

### Caching

Improve performance with caching:

```python
from apifrom import API, api
from apifrom.performance import cache
import time

# Create an API instance
app = API(
    title="Cached API",
    description="An API with caching",
    version="1.0.0"
)

@api(route="/expensive", method="GET")
@cache(ttl=60)  # Cache for 60 seconds
def expensive_operation() -> dict:
    """An expensive operation that benefits from caching."""
    # Simulate an expensive operation
    time.sleep(2)
    return {
        "result": "expensive computation",
        "timestamp": time.time()
    }

@api(route="/user/{user_id}", method="GET")
@cache(
    ttl=300,  # Cache for 5 minutes
    key_prefix="user",  # Cache key prefix
    vary_by_query_params=["version"]  # Vary cache by version query parameter
)
def get_user(user_id: int, version: str = "v1") -> dict:
    """Get a user by ID with caching."""
    # Simulate a database query
    time.sleep(1)
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "version": version,
        "timestamp": time.time()
    }

@api(route="/user/{user_id}", method="PUT")
def update_user(user_id: int, name: str) -> dict:
    """Update a user and invalidate cache."""
    # Update user in database
    
    # Invalidate cache
    from apifrom.performance import invalidate_cache
    invalidate_cache(f"user:user:{user_id}")
    
    return {"id": user_id, "name": name}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Request Coalescing

Optimize high-traffic endpoints with request coalescing:

```python
from apifrom import API, api
from apifrom.performance import coalesce_requests
import asyncio
import time

# Create an API instance
app = API(
    title="Coalesced API",
    description="An API with request coalescing",
    version="1.0.0"
)

@api(route="/popular-data", method="GET")
@coalesce_requests(ttl=30, max_wait_time=0.05)
async def get_popular_data() -> dict:
    """
    A popular endpoint that might receive many identical requests under load.
    With request coalescing, only one database query will be executed
    even if 100 users request this data at the same time.
    """
    # Simulate an expensive database query
    await asyncio.sleep(2)
    return {
        "data": "expensive computation result",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Batch Processing

Optimize bulk operations with batch processing:

```python
from apifrom import API, api
from apifrom.performance import batch_process
import asyncio
from typing import List, Dict

# Create an API instance
app = API(
    title="Batch Processing API",
    description="An API with batch processing",
    version="1.0.0"
)

@api(route="/users", method="POST")
@batch_process(max_batch_size=100, max_wait_time=0.1)
async def create_users(user_data_batch: List[Dict]) -> List[Dict]:
    """
    Create multiple users in a batch.
    This endpoint will collect individual user creation requests and
    process them in batches of up to 100 users or after 0.1 seconds.
    """
    # Simulate a bulk insert operation
    await asyncio.sleep(1)
    
    # Process each user in the batch
    results = []
    for i, user_data in enumerate(user_data_batch):
        results.append({
            "id": i + 1,
            "name": user_data.get("name"),
            "email": user_data.get("email")
        })
    
    return results

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Web Decorator

Use the Web decorator for easy optimization:

```python
from apifrom import API, api
from apifrom.performance import Web
import time

# Create an API instance
app = API(
    title="Optimized API",
    description="An API with the Web decorator for optimization",
    version="1.0.0"
)

@api(route="/products", method="GET")
@Web.optimize(
    cache_ttl=30,  # Cache for 30 seconds
    profile=True,  # Enable profiling
    connection_pool=True,  # Enable connection pooling
    request_coalescing=True,  # Enable request coalescing
    batch_processing=True,  # Enable batch processing
    batch_size=100  # Set batch size
)
def get_products() -> dict:
    """Get all products with automatic optimization."""
    # Simulate an expensive operation
    time.sleep(1)
    
    return {
        "products": [
            {"id": 1, "name": "Product 1", "price": 10.99},
            {"id": 2, "name": "Product 2", "price": 19.99},
            {"id": 3, "name": "Product 3", "price": 5.99}
        ],
        "timestamp": time.time()
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## Monitoring Examples

### Metrics Collection

Collect and expose metrics:

```python
from apifrom import API, api
from apifrom.monitoring import MetricsCollector, MetricsMiddleware, PrometheusExporter

# Create an API instance
app = API(
    title="Monitored API",
    description="An API with metrics collection",
    version="1.0.0"
)

# Create a metrics collector
metrics = MetricsCollector()

# Register the metrics middleware
app.add_middleware(
    MetricsMiddleware(
        collector=metrics,
        prefix="api",
        include_paths=True,
        include_methods=True,
        include_status_codes=True
    )
)

# Create a Prometheus exporter
prometheus_exporter = PrometheusExporter(collector=metrics)

# Define a metrics endpoint
@api(route="/metrics", method="GET")
def metrics():
    """Return Prometheus metrics."""
    return prometheus_exporter.export()

# Define a custom counter
requests_counter = metrics.create_counter(
    name="custom_requests_total",
    description="Total number of custom requests",
    labels=["endpoint"]
)

@api(route="/hello/{name}", method="GET")
def hello(name: str) -> dict:
    """Say hello to someone."""
    # Increment the custom counter
    requests_counter.inc(labels={"endpoint": "hello"})
    
    return {"message": f"Hello, {name}!"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## Serverless Examples

### AWS Lambda

Deploy an API to AWS Lambda:

```python
from apifrom import API, api
from apifrom.adapters import LambdaAdapter

# Create an API instance
app = API(
    title="Serverless API",
    description="An API deployed to AWS Lambda",
    version="1.0.0"
)

@api(route="/hello/{name}", method="GET")
def hello(name: str) -> dict:
    """Say hello to someone."""
    return {"message": f"Hello, {name}!"}

# Create a Lambda handler
lambda_adapter = LambdaAdapter(app)

def handler(event, context):
    """AWS Lambda handler function."""
    return lambda_adapter.handle(event, context)
```

### Vercel

Deploy an API to Vercel:

```python
from apifrom import API, api
from apifrom.adapters import VercelAdapter

# Create an API instance
app = API(
    title="Vercel API",
    description="An API deployed to Vercel",
    version="1.0.0"
)

@api(route="/api/hello", method="GET")
def hello(name: str = "World") -> dict:
    """Say hello to someone."""
    return {"message": f"Hello, {name}!"}

# Create a Vercel handler
vercel_adapter = VercelAdapter(app)

def handler(req):
    """Vercel handler function."""
    return vercel_adapter.handle(req)
```

## Advanced Examples

### Error Handling

Implement custom error handling:

```python
from apifrom import API, api
from apifrom.exceptions import BadRequestError, NotFoundError, ForbiddenError
from apifrom.middleware import ErrorHandlingMiddleware

# Create an API instance
app = API(
    title="Error Handling API",
    description="An API with custom error handling",
    version="1.0.0"
)

# Add error handling middleware
app.add_middleware(
    ErrorHandlingMiddleware(
        debug=True,
        include_traceback=True,
        log_exceptions=True
    )
)

@api(route="/users/{user_id}", method="GET")
def get_user(user_id: int) -> dict:
    """Get a user by ID with error handling."""
    if user_id <= 0:
        raise BadRequestError(
            message="User ID must be positive",
            details={"user_id": user_id}
        )
    
    # Simulate a database query
    if user_id > 100:
        raise NotFoundError(
            message=f"User with ID {user_id} not found",
            details={"user_id": user_id}
        )
    
    return {"id": user_id, "name": f"User {user_id}"}

@api(route="/admin", method="GET")
def admin_endpoint(role: str = "user") -> dict:
    """An admin endpoint that requires admin role."""
    if role != "admin":
        raise ForbiddenError(
            message="Admin role required",
            details={"role": role}
        )
    
    return {"message": "Welcome, admin!"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Database Integration

Integrate with a database:

```python
from apifrom import API, api
from apifrom.database import Database
from pydantic import BaseModel
from typing import List, Optional

# Create an API instance
app = API(
    title="Database API",
    description="An API with database integration",
    version="1.0.0"
)

# Create a database connection
db = Database("sqlite:///app.db")

# Define Pydantic models
class UserCreate(BaseModel):
    name: str
    email: str
    age: int

class User(UserCreate):
    id: int

# Create tables
db.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    age INTEGER NOT NULL
)
""")

@api(route="/users", method="GET")
def get_users() -> List[User]:
    """Get all users from the database."""
    users = db.query("SELECT * FROM users")
    return [User(**user) for user in users]

@api(route="/users/{user_id}", method="GET")
def get_user(user_id: int) -> User:
    """Get a user by ID from the database."""
    user = db.query_one("SELECT * FROM users WHERE id = ?", [user_id])
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    return User(**user)

@api(route="/users", method="POST")
def create_user(user: UserCreate) -> User:
    """Create a new user in the database."""
    user_id = db.execute(
        "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
        [user.name, user.email, user.age]
    )
    return User(id=user_id, **user.dict())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### File Upload

Handle file uploads:

```python
from apifrom import API, api
from apifrom.core.request import Request
from apifrom.core.response import Response
import os
import uuid

# Create an API instance
app = API(
    title="File Upload API",
    description="An API that handles file uploads",
    version="1.0.0"
)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

@api(route="/upload", method="POST")
async def upload_file(request: Request) -> dict:
    """Upload a file."""
    # Parse the multipart form data
    form_data = await request.form()
    
    # Get the file from the form data
    file = form_data.get("file")
    if not file:
        return {"error": "No file provided"}
    
    # Generate a unique filename
    filename = f"{uuid.uuid4()}_{file.filename}"
    
    # Save the file
    with open(os.path.join("uploads", filename), "wb") as f:
        f.write(await file.read())
    
    return {
        "message": "File uploaded successfully",
        "filename": filename,
        "content_type": file.content_type,
        "size": file.size
    }

@api(route="/files/{filename}", method="GET")
def get_file(filename: str) -> Response:
    """Get a file by filename."""
    file_path = os.path.join("uploads", filename)
    
    if not os.path.exists(file_path):
        return Response(
            content={"error": "File not found"},
            status_code=404
        )
    
    # Determine content type
    content_type = "application/octet-stream"
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        content_type = "image/jpeg"
    elif filename.endswith(".png"):
        content_type = "image/png"
    elif filename.endswith(".pdf"):
        content_type = "application/pdf"
    
    # Read the file
    with open(file_path, "rb") as f:
        content = f.read()
    
    return Response(
        content=content,
        status_code=200,
        headers={"Content-Type": content_type}
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### WebSocket Support

Implement WebSocket support:

```python
from apifrom import API, api
from apifrom.websockets import WebSocket, WebSocketRoute
import asyncio
import json

# Create an API instance
app = API(
    title="WebSocket API",
    description="An API with WebSocket support",
    version="1.0.0"
)

# Create a WebSocket route
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint."""
    # Accept the connection
    await websocket.accept()
    
    try:
        # Send a welcome message
        await websocket.send_text("Welcome to the WebSocket server!")
        
        # Handle messages
        while True:
            # Receive a message
            data = await websocket.receive_text()
            
            # Parse the message
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text("Invalid JSON")
                continue
            
            # Echo the message
            await websocket.send_json({
                "type": "echo",
                "data": message
            })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Close the connection
        await websocket.close()

# Create a regular API endpoint
@api(route="/send-to-websocket", method="POST")
async def send_to_websocket(message: str) -> dict:
    """Send a message to all connected WebSocket clients."""
    # Get all connected WebSocket clients
    clients = app.websocket_clients
    
    # Send the message to all clients
    for client in clients:
        await client.send_text(message)
    
    return {
        "message": "Message sent to all WebSocket clients",
        "client_count": len(clients)
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## <div align="center">🔌 Plugin System Examples</div>

<div align="center">
  <img src="https://img.shields.io/badge/APIFromAnything-Plugin%20Examples-blue?style=for-the-badge" alt="Plugin Examples" />
  <br/>
  <strong>Extend and customize your API with powerful plugins</strong>
</div>

<p align="center">
  <a href="#basic-plugin-example">Basic Plugin</a> •
  <a href="#advanced-plugin-example">Advanced Plugin</a> •
  <a href="#plugin-with-dependencies">Dependencies</a> •
  <a href="#using-hooks">Hooks</a> •
  <a href="#event-handling-plugin">Events</a>
</p>

---

### Basic Plugin Example

This example demonstrates how to create and use a simple timing plugin that measures request execution time:

```python
import time
from typing import Optional

from apifrom import API, api, Plugin
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.plugins.base import PluginMetadata, PluginConfig

class TimingPlugin(Plugin):
    """
    Plugin for measuring request execution time.
    """
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="timing",
            version="1.0.0",
            description="Measures request execution time",
            author="Your Name",
            tags=["utility", "performance"]
        )
    
    def get_config(self) -> PluginConfig:
        return PluginConfig(
            defaults={
                "add_header": True,
                "log_timing": True
            }
        )
    
    async def pre_request(self, request: Request) -> Request:
        # Store the start time
        request.state.timing_start_time = time.time()
        return request
    
    async def post_response(self, response: Response, request: Request) -> Response:
        # Calculate the execution time
        start_time = getattr(request.state, "timing_start_time", None)
        if start_time:
            execution_time = time.time() - start_time
            
            # Add timing header to the response
            if self.config.get("add_header"):
                response.headers["X-Execution-Time"] = f"{execution_time:.4f}s"
            
            # Log the timing information
            if self.config.get("log_timing"):
                self.logger.info(f"Request to {request.path} took {execution_time:.4f} seconds")
        
        return response

# Create an API instance
app = API(title="Timing Plugin Example")

# Register the timing plugin
timing_plugin = TimingPlugin()
app.plugin_manager.register(timing_plugin)

# Define an API endpoint
@api(route="/test")
def test_endpoint():
    """Test endpoint that simulates a delay."""
    time.sleep(0.5)
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

<div align="center">
  <table>
    <tr>
      <th>Key Features</th>
      <th>Description</th>
    </tr>
    <tr>
      <td>⏱️ Request Timing</td>
      <td>Measures the execution time of each request</td>
    </tr>
    <tr>
      <td>📊 Response Headers</td>
      <td>Adds an X-Execution-Time header to responses</td>
    </tr>
    <tr>
      <td>📝 Logging</td>
      <td>Logs timing information for each request</td>
    </tr>
    <tr>
      <td>⚙️ Configuration</td>
      <td>Configurable behavior through plugin configuration</td>
    </tr>
  </table>
</div>

### Advanced Plugin Example

This example demonstrates a more advanced plugin that implements JWT authentication:

```python
import jwt
from typing import Optional, Dict, Any

from apifrom import API, api, Plugin
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.plugins.base import PluginMetadata, PluginConfig
from apifrom.exceptions import UnauthorizedError

class AuthPlugin(Plugin):
    """
    Plugin for JWT authentication.
    """
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="auth",
            version="1.0.0",
            description="JWT authentication plugin",
            author="Your Name",
            tags=["security", "authentication"]
        )
    
    def get_config(self) -> PluginConfig:
        return PluginConfig(
            defaults={
                "secret_key": "your-secret-key",
                "algorithm": "HS256",
                "token_prefix": "Bearer",
                "exclude_paths": ["/login", "/public"]
            },
            schema={
                "type": "object",
                "properties": {
                    "secret_key": {"type": "string"},
                    "algorithm": {"type": "string"},
                    "token_prefix": {"type": "string"},
                    "exclude_paths": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["secret_key"]
            }
        )
    
    async def pre_request(self, request: Request) -> Request:
        # Skip authentication for excluded paths
        if any(request.path.startswith(path) for path in self.config.get("exclude_paths", [])):
            return request
        
        # Get the authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise UnauthorizedError("Missing Authorization header")
        
        # Extract the token
        token_prefix = self.config.get("token_prefix")
        if token_prefix and auth_header.startswith(token_prefix):
            token = auth_header[len(token_prefix):].strip()
        else:
            token = auth_header
        
        # Verify the token
        try:
            payload = jwt.decode(
                token,
                self.config.get("secret_key"),
                algorithms=[self.config.get("algorithm")]
            )
            
            # Store the payload in the request state
            request.state.user = payload
            
        except jwt.PyJWTError as e:
            raise UnauthorizedError(f"Invalid token: {str(e)}")
        
        return request

# Create an API instance
app = API(title="Auth Plugin Example")

# Register the auth plugin
auth_plugin = AuthPlugin()
app.plugin_manager.register(auth_plugin)

# Define a protected endpoint
@api(route="/protected")
def protected_endpoint(request: Request):
    """Protected endpoint that requires authentication."""
    return {
        "message": "You are authenticated!",
        "user": request.state.user
    }

# Define a public endpoint
@api(route="/public")
def public_endpoint():
    """Public endpoint that doesn't require authentication."""
    return {"message": "This is a public endpoint"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Plugin with Dependencies

This example demonstrates a plugin that depends on another plugin:

```python
import time
from typing import Optional, List, Dict

from apifrom import API, api, Plugin
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.plugins.base import PluginMetadata, PluginConfig, PluginEvent

class MetricsPlugin(Plugin):
    """
    Plugin for collecting API metrics.
    Depends on the TimingPlugin to get request execution times.
    """
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="metrics",
            version="1.0.0",
            description="Collects API metrics",
            author="Your Name",
            dependencies=["timing"],  # This plugin depends on the timing plugin
            tags=["utility", "monitoring"]
        )
    
    def get_config(self) -> PluginConfig:
        return PluginConfig(
            defaults={
                "collect_request_metrics": True,
                "collect_response_metrics": True,
                "collect_error_metrics": True,
                "max_response_times": 1000
            }
        )
    
    def initialize(self, api: API) -> None:
        super().initialize(api)
        
        # Get the timing plugin
        self.timing_plugin = api.plugin_manager.get_plugin("timing")
        
        # Initialize metrics
        self.request_count = 0
        self.response_count = 0
        self.error_count = 0
        self.response_times: List[float] = []
        self.status_codes: Dict[int, int] = {}
        
        # Register for events
        api.plugin_manager.register_event_listener(self, PluginEvent.SERVER_STARTING)
    
    async def pre_request(self, request: Request) -> Request:
        if self.config.get("collect_request_metrics"):
            self.request_count += 1
            self.logger.debug(f"Request count: {self.request_count}")
        
        return request
    
    async def post_response(self, response: Response, request: Request) -> Response:
        if self.config.get("collect_response_metrics"):
            self.response_count += 1
            
            # Update status code counts
            status_code = response.status_code
            self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
            
            # Get the execution time from the timing plugin
            start_time = getattr(request.state, "timing_start_time", None)
            if start_time:
                execution_time = time.time() - start_time
                self.response_times.append(execution_time)
                
                # Limit the number of stored response times
                max_times = self.config.get("max_response_times")
                if len(self.response_times) > max_times:
                    self.response_times = self.response_times[-max_times:]
        
        return response
    
    async def on_error(self, error: Exception, request: Request) -> Optional[Response]:
        if self.config.get("collect_error_metrics"):
            self.error_count += 1
            self.logger.debug(f"Error count: {self.error_count}")
        
        return None
    
    async def on_event(self, event: PluginEvent, **kwargs) -> None:
        if event == PluginEvent.SERVER_STARTING:
            self.logger.info("Server is starting, resetting metrics")
            self.request_count = 0
            self.response_count = 0
            self.error_count = 0
            self.response_times = []
            self.status_codes = {}
    
    def get_metrics(self) -> Dict:
        """Get the collected metrics."""
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            "request_count": self.request_count,
            "response_count": self.response_count,
            "error_count": self.error_count,
            "error_rate": (self.error_count / self.request_count) if self.request_count > 0 else 0,
            "average_response_time": avg_response_time,
            "status_codes": self.status_codes
        }

# Create an API instance
app = API(title="Metrics Plugin Example")

# Register the timing plugin first (dependency)
app.plugin_manager.register(TimingPlugin())

# Register the metrics plugin
metrics_plugin = MetricsPlugin()
app.plugin_manager.register(metrics_plugin)

# Define an endpoint that returns metrics
@api(route="/metrics")
def metrics_endpoint():
    """Return metrics collected by the metrics plugin."""
    return app.plugin_manager.get_plugin("metrics").get_metrics()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Using Hooks

This example demonstrates how to use the hook system:

```python
import uuid
from typing import Dict, Any

from apifrom import API, api, Plugin
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.plugins.base import PluginMetadata, PluginHook

class TransformationPlugin(Plugin):
    """
    Plugin for transforming requests and responses using hooks.
    """
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="transformation",
            version="1.0.0",
            description="Transforms requests and responses",
            author="Your Name",
            tags=["utility"]
        )
    
    def initialize(self, api: API) -> None:
        super().initialize(api)
        
        # Register hooks
        self.request_transformation_hook = api.plugin_manager.register_hook(
            "request_transformation",
            "Transform the request before it is processed by the API"
        )
        
        self.response_transformation_hook = api.plugin_manager.register_hook(
            "response_transformation",
            "Transform the response before it is sent to the client"
        )
        
        # Register callbacks for the hooks
        self.register_hook(
            self.request_transformation_hook,
            self.add_request_id,
            priority=75  # Higher priority callbacks are executed first
        )
        
        self.register_hook(
            self.response_transformation_hook,
            self.add_response_id,
            priority=75
        )
    
    def add_request_id(self, request: Request) -> Request:
        """Add a request ID to the request."""
        request.state.request_id = str(uuid.uuid4())
        return request
    
    def add_response_id(self, response: Response, request: Request) -> Response:
        """Add the request ID to the response headers."""
        if hasattr(request.state, "request_id"):
            response.headers["X-Request-ID"] = request.state.request_id
        return response
    
    async def pre_request(self, request: Request) -> Request:
        # Call the request transformation hook
        results = await self.request_transformation_hook(request)
        # The last result is the final transformed request
        return results[-1] if results else request
    
    async def post_response(self, response: Response, request: Request) -> Response:
        # Call the response transformation hook
        results = await self.response_transformation_hook(response, request)
        # The last result is the final transformed response
        return results[-1] if results else response
    
    def shutdown(self) -> None:
        # Unregister the callbacks when the plugin is shut down
        self.unregister_hook(self.request_transformation_hook, self.add_request_id)
        self.unregister_hook(self.response_transformation_hook, self.add_response_id)

# Create an API instance
app = API(title="Hook Example")

# Register the transformation plugin
app.plugin_manager.register(TransformationPlugin())

# Define an API endpoint
@api(route="/test")
def test_endpoint():
    """Test endpoint."""
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Event Handling Plugin

This example demonstrates how to handle events in a plugin:

```python
import time
from typing import Dict, List, Any

from apifrom import API, api, Plugin
from apifrom.plugins.base import PluginMetadata, PluginEvent

class EventLoggerPlugin(Plugin):
    """
    Plugin for logging events.
    """
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="event-logger",
            version="1.0.0",
            description="Logs events emitted by the plugin system",
            author="Your Name",
            tags=["utility", "logging"]
        )
    
    def initialize(self, api: API) -> None:
        super().initialize(api)
        
        # Initialize event log
        self.event_log: List[Dict[str, Any]] = []
        
        # Register for all events
        for event in PluginEvent:
            api.plugin_manager.register_event_listener(self, event)
    
    async def on_event(self, event: PluginEvent, **kwargs) -> None:
        """Handle events emitted by the plugin system."""
        # Log the event
        event_data = {
            "event": event.value,
            "timestamp": time.time(),
            "data": {k: str(v) for k, v in kwargs.items() if k != "request" and k != "response"}
        }
        
        self.event_log.append(event_data)
        self.logger.info(f"Event: {event.value}")
        
        # Keep only the last 100 events
        if len(self.event_log) > 100:
            self.event_log = self.event_log[-100:]
    
    def get_event_log(self) -> List[Dict[str, Any]]:
        """Get the event log."""
        return self.event_log

# Create an API instance
app = API(title="Event Logger Example")

# Register the event logger plugin
event_logger = EventLoggerPlugin()
app.plugin_manager.register(event_logger)

# Define an endpoint that returns the event log
@api(route="/events")
def events_endpoint():
    """Return the event log."""
    return app.plugin_manager.get_plugin("event-logger").get_event_log()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

<div align="center">
  <p>
    <a href="plugins.md">
      <img src="https://img.shields.io/badge/Learn%20More%20About%20Plugins-blue?style=for-the-badge" alt="Learn More About Plugins" />
    </a>
  </p>
</div>

These examples demonstrate the various features and capabilities of the APIFromAnything library. You can use them as a starting point for your own API projects. 