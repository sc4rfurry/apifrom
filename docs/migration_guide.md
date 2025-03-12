# Migration Guide: Upgrading to APIFromAnything 1.0.0

This guide will help you migrate your application from APIFromAnything 0.1.0 to 1.0.0. Version 1.0.0 includes significant improvements, including full async/await support, enhanced security features, and improved performance.

## Overview of Changes

### Major Changes

- **Full Async Support**: All components now support async/await syntax
- **Improved Middleware System**: Enhanced middleware architecture with better async support
- **Enhanced Security Features**: Improved security middleware and decorators
- **Performance Optimizations**: Better caching, connection pooling, and request coalescing
- **Comprehensive Documentation**: Detailed documentation for all features
- **Improved Testing Framework**: Better support for testing async functions

### Breaking Changes

1. **Middleware Interface**: The middleware interface has changed to better support async functions
2. **Security Decorators**: Security decorators now handle async functions differently
3. **Error Handling**: Error handling has been improved and may require changes to your code
4. **Configuration Options**: Some configuration options have been renamed or changed
5. **Testing Utilities**: Testing utilities have been updated to support async functions

## Step-by-Step Migration Guide

### 1. Update Your Dependencies

Update your `requirements.txt` file to use the latest version:

```diff
- apifrom==0.1.0
+ apifrom==1.0.0
```

Or install the latest version directly:

```bash
pip install --upgrade apifrom
```

### 2. Update Middleware Implementation

If you've created custom middleware, you'll need to update it to use the new async interface:

```diff
from apifrom.middleware import Middleware
from apifrom.core.request import Request
from apifrom.core.response import Response

class CustomMiddleware(Middleware):
-    def dispatch(self, request, call_next):
+    async def dispatch(self, request, call_next):
        # Process request
        print(f"Request: {request.method} {request.url.path}")
        
-        response = call_next(request)
+        response = await call_next(request)
        
        # Process response
        print(f"Response: {response.status_code}")
        
        return response
```

### 3. Update API Endpoints for Async Support

If you want to take advantage of async support, update your API endpoints:

```diff
from apifrom import API, api

app = API()

@api(route="/users", method="GET")
- def get_users():
+ async def get_users():
    # Your code here
    return {"users": [...]}
```

### 4. Update Database Operations

If you're using database operations, update them to use async libraries:

```diff
- import sqlite3
+ import aiosqlite

@api(route="/users", method="GET")
- def get_users():
+ async def get_users():
-    conn = sqlite3.connect("database.db")
-    cursor = conn.cursor()
-    cursor.execute("SELECT * FROM users")
-    users = cursor.fetchall()
-    conn.close()
+    async with aiosqlite.connect("database.db") as db:
+        async with db.execute("SELECT * FROM users") as cursor:
+            users = await cursor.fetchall()
    
    return {"users": users}
```

### 5. Update HTTP Client Code

If you're making HTTP requests, update them to use async HTTP clients:

```diff
- import requests
+ import aiohttp

@api(route="/proxy", method="GET")
- def proxy(url: str):
+ async def proxy(url: str):
-    response = requests.get(url)
-    data = response.json()
+    async with aiohttp.ClientSession() as session:
+        async with session.get(url) as response:
+            data = await response.json()
    
    return {"data": data}
```

### 6. Update Security Decorators

If you're using security decorators, update them to handle async functions:

```diff
from apifrom import API, api
from apifrom.security import jwt_required

app = API()

@api(route="/protected", method="GET")
@jwt_required(secret="your-secret-key")
- def protected_endpoint(request):
+ async def protected_endpoint(request):
    user_id = request.state.jwt_payload.get("sub")
    return {"message": f"Hello, user {user_id}!"}
```

### 7. Update Error Handling

If you're using custom error handling, update it to handle async functions:

```diff
from apifrom import API, api
from apifrom.middleware import ErrorHandlingMiddleware
from apifrom.exceptions import BadRequestError

app = API()

app.add_middleware(
    ErrorHandlingMiddleware(
        debug=True,
-        on_error=lambda request, exc, traceback: print(f"Error: {exc}")
+        on_error=async_error_handler
    )
)

+ async def async_error_handler(request, exc, traceback):
+    print(f"Error: {exc}")
+    # You can now perform async operations here
+    return {"error": str(exc)}, 500

@api(route="/users/{user_id}", method="GET")
- def get_user(user_id: int):
+ async def get_user(user_id: int):
    if user_id <= 0:
        raise BadRequestError(message="User ID must be positive")
    
    # Your code here
    return {"id": user_id, "name": "John Doe"}
```

### 8. Update Testing Code

If you're using the testing utilities, update them to support async functions:

```diff
- from apifrom.testing import TestClient, MiddlewareTester
+ from apifrom.testing import TestClient, AsyncMiddlewareTester
import pytest

- def test_api():
+ @pytest.mark.asyncio
+ async def test_api():
    client = TestClient(app)
    
-    response = client.get("/users")
+    response = await client.get("/users")
    
    assert response.status_code == 200
    assert "users" in response.json()

- def test_middleware():
+ @pytest.mark.asyncio
+ async def test_middleware():
-    tester = MiddlewareTester(CustomMiddleware())
+    tester = AsyncMiddlewareTester(CustomMiddleware())
    
    request = Request(method="GET", url="/test")
    mock_response = Response(content={"message": "Test"}, status_code=200)
    
-    response = tester.test_dispatch(request=request, mock_response=mock_response)
+    response = await tester.test_dispatch(request=request, mock_response=mock_response)
    
    assert response.status_code == 200
```

### 9. Update Configuration Options

Some configuration options have been renamed or changed:

```diff
app = API(
    title="My API",
    version="1.0.0",
-    enable_docs=True,
+    docs_url="/docs",
-    enable_openapi=True,
+    openapi_url="/openapi.json",
-    debug_mode=True,
+    debug=True,
)
```

### 10. Update Performance Optimization Code

If you're using performance optimization features, update them to support async functions:

```diff
from apifrom import API, api
from apifrom.performance import cache, coalesce_requests, batch_process

app = API()

@api(route="/expensive-operation", method="GET")
@cache(ttl=60)
- def expensive_operation():
+ async def expensive_operation():
    # Your code here
    return {"result": "expensive computation"}

@api(route="/popular-data", method="GET")
@coalesce_requests(ttl=30, max_wait_time=0.05)
- def get_popular_data():
+ async def get_popular_data():
    # Your code here
    return {"data": "popular data"}

@api(route="/users", method="POST")
@batch_process(max_batch_size=100, max_wait_time=0.1)
- def create_users(user_data_batch):
+ async def create_users(user_data_batch):
    # Your code here
    return {"status": "success"}
```

## Common Migration Issues and Solutions

### Issue 1: Coroutine Was Never Awaited Warning

**Problem**: You see a warning like `RuntimeWarning: coroutine 'function_name' was never awaited`

**Solution**: Ensure you're properly awaiting all async functions:

```python
# Incorrect
@api(route="/users", method="GET")
async def get_users():
    result = fetch_users()  # Missing await
    return result

# Correct
@api(route="/users", method="GET")
async def get_users():
    result = await fetch_users()  # Properly awaited
    return result
```

### Issue 2: Event Loop Already Running Error

**Problem**: You get an error like `RuntimeError: This event loop is already running`

**Solution**: Use `asyncio.create_task()` instead of `asyncio.run()` when inside an async function:

```python
# Incorrect - inside an async function
async def outer_function():
    # This will fail with "event loop already running"
    result = asyncio.run(inner_function())
    return result

# Correct - inside an async function
async def outer_function():
    # Create a task instead
    task = asyncio.create_task(inner_function())
    result = await task
    return result
```

### Issue 3: Middleware Not Handling Async Functions

**Problem**: Your middleware is not properly handling async functions

**Solution**: Ensure your middleware is using `await` when calling the next middleware or endpoint:

```python
# Incorrect middleware
class IncorrectMiddleware(Middleware):
    def dispatch(self, request, call_next):
        # Missing await
        response = call_next(request)
        return response

# Correct middleware
class CorrectMiddleware(Middleware):
    async def dispatch(self, request, call_next):
        # Properly awaited
        response = await call_next(request)
        return response
```

### Issue 4: Testing Async Functions

**Problem**: You're having trouble testing async functions

**Solution**: Use `pytest.mark.asyncio` to test async functions:

```python
import pytest

# Mark the test as async
@pytest.mark.asyncio
async def test_async_function():
    # Test async function
    result = await async_function()
    assert result == "expected result"
```

### Issue 5: Mixing Sync and Async Code

**Problem**: You're trying to call an async function from a synchronous function

**Solution**: Use `asyncio.run()` to call async functions from synchronous code:

```python
import asyncio

# Synchronous function calling an async function
def sync_function():
    # Use asyncio.run() to call async functions from sync code
    result = asyncio.run(async_function())
    return result

async def async_function():
    await asyncio.sleep(1)
    return "result"
```

## Conclusion

Migrating to APIFromAnything 1.0.0 requires some changes to your code, but the benefits of full async support, improved security, and better performance are worth the effort. If you encounter any issues during migration, please refer to the [troubleshooting guide](troubleshooting.md) or open an issue on the [GitHub repository](https://github.com/sc4rfurry/apifrom/issues).

For more information about the new features in version 1.0.0, see the [changelog](https://github.com/sc4rfurry/apifrom/blob/main/CHANGELOG.md). 