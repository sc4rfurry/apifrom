# Troubleshooting

This guide covers common issues you might encounter when using APIFromAnything and how to resolve them.

## Installation Issues

### Package Not Found

**Issue**: `pip install apifrom` fails with "Package not found" error.

**Solution**: 

1. Make sure you're using the correct package name:

   ```bash
   pip install apifrom
   ```

2. Check your internet connection and try again.

3. If you're behind a proxy, configure pip to use it:

   ```bash
   pip install --proxy http://user:password@proxyserver:port apifrom
   ```

### Dependency Conflicts

**Issue**: Installation fails due to dependency conflicts.

**Solution**:

1. Create a new virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install APIFromAnything in the virtual environment:

   ```bash
   pip install apifrom
   ```

3. If you still encounter conflicts, try installing with the `--no-dependencies` flag and then install dependencies manually:

   ```bash
   pip install --no-dependencies apifrom
   pip install -r requirements.txt
   ```

## Runtime Issues

### Import Errors

**Issue**: `ImportError: No module named 'apifrom'` when trying to import the library.

**Solution**:

1. Make sure the package is installed:

   ```bash
   pip list | grep apifrom
   ```

2. If it's not installed, install it:

   ```bash
   pip install apifrom
   ```

3. If it's installed but still not found, check your Python path:

   ```python
   import sys
   print(sys.path)
   ```

4. Make sure you're using the correct Python interpreter (the one where you installed the package).

### API Not Starting

**Issue**: The API server doesn't start or crashes immediately.

**Solution**:

1. Check for port conflicts:

   ```bash
   # On Linux/macOS
   lsof -i :8000
   
   # On Windows
   netstat -ano | findstr :8000
   ```

2. If the port is in use, choose a different port:

   ```python
   app.run(host="0.0.0.0", port=8001)
   ```

3. Check for syntax errors in your code.

4. Enable debug mode to get more detailed error messages:

   ```python
   app = API(debug=True)
   ```

### Route Not Found

**Issue**: Requests to your API endpoints return 404 Not Found.

**Solution**:

1. Make sure the route path is correct:

   ```python
   @api(route="/users/{user_id}", method="GET")
   def get_user(user_id: int):
       # ...
   ```

2. Check if the HTTP method is correct:

   ```python
   @api(route="/users", method="POST")  # Only responds to POST requests
   def create_user(name: str, email: str):
       # ...
   ```

3. Make sure the API instance is correctly configured:

   ```python
   app = API()
   
   @api(route="/users", method="GET")
   def get_users():
       # ...
   
   # Make sure to run the API instance
   if __name__ == "__main__":
       app.run()
   ```

4. If you're using a router, make sure it's included in the API:

   ```python
   user_router = Router(prefix="/users")
   
   @user_router.api(route="/{user_id}", method="GET")
   def get_user(user_id: int):
       # ...
   
   app.include_router(user_router)
   ```

### Validation Errors

**Issue**: Requests fail with 422 Unprocessable Entity errors.

**Solution**:

1. Check the request payload against the function parameters:

   ```python
   @api(route="/users", method="POST")
   def create_user(name: str, email: str, age: int):
       # ...
   ```

   The request payload should be:

   ```json
   {
       "name": "John Doe",
       "email": "john@example.com",
       "age": 30
   }
   ```

2. Make sure the types match:

   ```python
   # age must be an integer, not a string
   {
       "name": "John Doe",
       "email": "john@example.com",
       "age": "30"  # This will fail validation
   }
   ```

3. If you're using Pydantic models, check the model constraints:

   ```python
   from pydantic import BaseModel, Field, EmailStr
   
   class User(BaseModel):
       name: str = Field(..., min_length=2, max_length=50)
       email: EmailStr
       age: int = Field(..., ge=18, le=120)
   
   @api(route="/users", method="POST")
   def create_user(user: User):
       # ...
   ```

   The request payload must satisfy all constraints.

### Authentication Errors

**Issue**: Requests to protected endpoints fail with 401 Unauthorized.

**Solution**:

1. Make sure you're including the correct authentication headers:

   ```bash
   # JWT authentication
   curl -H "Authorization: Bearer your-token" http://localhost:8000/protected
   
   # API key authentication
   curl -H "X-API-Key: your-api-key" http://localhost:8000/protected
   
   # Basic authentication
   curl -u username:password http://localhost:8000/protected
   ```

2. Check if the token or credentials are valid:

   ```python
   # JWT authentication
   @api(route="/protected", method="GET")
   @jwt_required(secret="your-secret-key", algorithm="HS256")
   def protected(request):
       # ...
   
   # API key authentication
   @api(route="/protected", method="GET")
   @api_key_required(api_keys={"your-api-key": ["read"]})
   def protected(request):
       # ...
   
   # Basic authentication
   @api(route="/protected", method="GET")
   @basic_auth_required(credentials={"username": "password"})
   def protected(request):
       # ...
   ```

3. If you're using JWT, check if the token is expired:

   ```python
   import jwt
   from datetime import datetime, timedelta
   
   # Create a token that expires in 1 hour
   payload = {
       "sub": "user123",
       "exp": datetime.utcnow() + timedelta(hours=1)
   }
   token = jwt.encode(payload, "your-secret-key", algorithm="HS256")
   ```

### CORS Errors

**Issue**: Browser requests fail with CORS errors.

**Solution**:

1. Add CORS middleware to your API:

   ```python
   from apifrom import API
   from apifrom.middleware import CORSMiddleware
   
   app = API()
   
   app.add_middleware(
       CORSMiddleware(
           allow_origins=["http://localhost:3000"],  # Frontend origin
           allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
           allow_headers=["Content-Type", "Authorization"],
           allow_credentials=True
       )
   )
   ```

2. Make sure the origin of the request is in the `allow_origins` list.

3. If you need to allow all origins, use `["*"]`:

   ```python
   app.add_middleware(
       CORSMiddleware(
           allow_origins=["*"],  # Allow all origins
           # ...
       )
   )
   ```

### Performance Issues

**Issue**: API endpoints are slow to respond.

**Solution**:

1. Use the profiling middleware to identify bottlenecks:

   ```python
   from apifrom import API
   from apifrom.middleware import ProfileMiddleware
   
   app = API()
   
   app.add_middleware(ProfileMiddleware())
   ```

2. Use caching for expensive operations:

   ```python
   from apifrom import API
   from apifrom.middleware import CacheMiddleware
   
   app = API()
   
   app.add_middleware(CacheMiddleware(ttl=60))  # Cache for 60 seconds
   ```

3. Use asynchronous functions for I/O-bound operations:

   ```python
   @api(route="/users", method="GET")
   async def get_users():
       # Asynchronous database query
       users = await db.fetch_all("SELECT * FROM users")
       return users
   ```

4. Use connection pooling for database connections:

   ```python
   from apifrom.performance import ConnectionPool
   
   # Create a connection pool
   pool = ConnectionPool(
       "postgresql://user:password@localhost/db",
       min_size=5,
       max_size=20
   )
   
   @api(route="/users", method="GET")
   async def get_users():
       async with pool.acquire() as conn:
           users = await conn.fetch("SELECT * FROM users")
           return users
   ```

5. Use batch processing for multiple similar operations:

   ```python
   from apifrom.performance import batch_process
   
   @api(route="/users", method="POST")
   @batch_process(max_batch_size=100, max_wait_time=0.1)
   async def create_users(user_data_batch):
       # Bulk insert all users in the batch
       return await db.bulk_insert_users(user_data_batch)
   ```

## Deployment Issues

### Serverless Deployment Issues

**Issue**: API doesn't work when deployed to a serverless platform.

**Solution**:

1. Make sure you're using the correct adapter:

   ```python
   # AWS Lambda
   from apifrom.adapters import LambdaAdapter
   
   lambda_adapter = LambdaAdapter(app)
   
   def handler(event, context):
       return lambda_adapter.handle(event, context)
   
   # Google Cloud Functions
   from apifrom.adapters import CloudFunctionAdapter
   
   cloud_function_adapter = CloudFunctionAdapter(app)
   
   def handler(request):
       return cloud_function_adapter.handle(request)
   
   # Azure Functions
   from apifrom.adapters import AzureFunctionAdapter
   
   azure_function_adapter = AzureFunctionAdapter(app)
   
   def main(req):
       return azure_function_adapter.handle(req)
   
   # Vercel
   from apifrom.adapters import VercelAdapter
   
   vercel_adapter = VercelAdapter(app)
   
   def handler(req):
       return vercel_adapter.handle(req)
   
   # Netlify
   from apifrom.adapters import NetlifyAdapter
   
   netlify_adapter = NetlifyAdapter(app)
   
   def handler(event, context):
       return netlify_adapter.handle(event, context)
   ```

2. Check the route paths:

   ```python
   # AWS Lambda with API Gateway
   @api(route="/hello/{name}", method="GET")
   def hello(name: str):
       # ...
   
   # Vercel
   @api(route="/api/hello", method="GET")
   def hello(name: str = "World"):
       # ...
   
   # Netlify
   @api(route="/.netlify/functions/hello", method="GET")
   def hello(name: str = "World"):
       # ...
   ```

3. Check the deployment configuration:

   ```python
   # AWS Lambda
   lambda_adapter = LambdaAdapter(
       app,
       strip_stage_path=True,  # Strip the stage path from the request path
       enable_binary_response=True,  # Enable binary responses
   )
   
   # Vercel
   vercel_adapter = VercelAdapter(
       app,
       enable_binary_response=True,  # Enable binary responses
   )
   
   # Netlify
   netlify_adapter = NetlifyAdapter(
       app,
       strip_function_path=True,  # Strip the function path from the request path
       enable_binary_response=True,  # Enable binary responses
   )
   ```

### Docker Deployment Issues

**Issue**: API doesn't work when deployed with Docker.

**Solution**:

1. Make sure the Dockerfile is correct:

   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 8000
   
   CMD ["python", "app.py"]
   ```

2. Make sure the API is listening on the correct host and port:

   ```python
   if __name__ == "__main__":
       app.run(host="0.0.0.0", port=8000)
   ```

3. Make sure the container is exposing the correct port:

   ```bash
   docker run -p 8000:8000 myapi
   ```

## Plugin Issues

### Plugin Not Loading

**Issue**: Plugin is not being loaded or executed.

**Solution**:

1. Make sure the plugin is registered:

   ```python
   from apifrom import API
   from apifrom.plugins import LoggingPlugin
   
   app = API()
   
   # Create and register a logging plugin
   logging_plugin = LoggingPlugin(
       log_request_body=True,
       log_response_body=True
   )
   app.plugin_manager.register(logging_plugin)
   ```

2. Check if the plugin is activated:

   ```python
   # Activate the plugin
   app.plugin_manager.activate(logging_plugin)
   ```

3. Make sure the plugin is implementing the correct hooks:

   ```python
   from apifrom import Plugin
   from apifrom.plugins.base import PluginMetadata
   
   class MyPlugin(Plugin):
       def get_metadata(self) -> PluginMetadata:
           return PluginMetadata(
               name="my-plugin",
               version="1.0.0",
               description="My custom plugin"
           )
       
       async def pre_request(self, request):
           # This hook is called before the request is processed
           return request
       
       async def post_response(self, response, request):
           # This hook is called after the response is generated
           return response
   ```

### Plugin Errors

**Issue**: Plugin is causing errors or exceptions.

**Solution**:

1. Enable debug mode to get more detailed error messages:

   ```python
   app = API(debug=True)
   ```

2. Add error handling to the plugin:

   ```python
   async def pre_request(self, request):
       try:
           # Plugin logic
           return request
       except Exception as e:
           self.logger.error(f"Error in pre_request: {e}")
           return request
   ```

3. Use the plugin's logger for debugging:

   ```python
   def initialize(self, api):
       super().initialize(api)
       self.logger.debug("Plugin initialized")
   ```

## Middleware Issues

### Middleware Not Executing

**Issue**: Middleware is not being executed.

**Solution**:

1. Make sure the middleware is added to the API:

   ```python
   from apifrom import API
   from apifrom.middleware import LoggingMiddleware
   
   app = API()
   
   app.add_middleware(LoggingMiddleware())
   ```

2. Check the order of middleware:

   ```python
   # Middleware is executed in the order it's added
   app.add_middleware(FirstMiddleware())
   app.add_middleware(SecondMiddleware())
   app.add_middleware(ThirdMiddleware())
   ```

3. Make sure the middleware is implementing the correct methods:

   ```python
   from apifrom.middleware import Middleware
   
   class MyMiddleware(Middleware):
       async def dispatch(self, request, call_next):
           # Pre-processing
           print(f"Request: {request.method} {request.url.path}")
           
           # Process the request through the next middleware or endpoint
           response = await call_next(request)
           
           # Post-processing
           print(f"Response: {response.status_code}")
           return response
   ```

### Middleware Errors

**Issue**: Middleware is causing errors or exceptions.

**Solution**:

1. Enable debug mode to get more detailed error messages:

   ```python
   app = API(debug=True)
   ```

2. Add error handling to the middleware:

   ```python
   async def dispatch(self, request, call_next):
       try:
           # Pre-processing
           print(f"Request: {request.method} {request.url.path}")
           
           # Process the request through the next middleware or endpoint
           response = await call_next(request)
           
           # Post-processing
           print(f"Response: {response.status_code}")
           return response
       except Exception as e:
           print(f"Error in middleware: {e}")
           raise
   ```

## Documentation Issues

### Swagger UI Not Working

**Issue**: Swagger UI is not available or not showing all endpoints.

**Solution**:

1. Make sure the Swagger UI is enabled:

   ```python
   app = API(
       title="My API",
       description="API description",
       version="1.0.0",
       docs_url="/docs",  # Swagger UI URL
       openapi_url="/openapi.json",  # OpenAPI schema URL
       redoc_url="/redoc"  # ReDoc URL
   )
   ```

2. Make sure endpoints are included in the schema:

   ```python
   @api(
       route="/users/{user_id}",
       method="GET",
       tags=["users"],
       summary="Get a user",
       description="Get a user by ID",
       response_model=dict,
       status_code=200,
       deprecated=False,
       include_in_schema=True  # Include in OpenAPI schema
   )
   def get_user(user_id: int):
       # ...
   ```

3. Check if the endpoint has proper documentation:

   ```python
   @api(route="/users/{user_id}", method="GET")
   def get_user(user_id: int):
       """
       Get a user by ID.
       
       Args:
           user_id: The ID of the user to retrieve
           
       Returns:
           User information
       """
       # ...
   ```

## Logging Issues

### Logs Not Appearing

**Issue**: Logs are not being displayed or written to file.

**Solution**:

1. Configure logging:

   ```python
   import logging
   
   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
       handlers=[
           logging.StreamHandler(),  # Log to console
           logging.FileHandler("api.log")  # Log to file
       ]
   )
   
   # Get a logger
   logger = logging.getLogger(__name__)
   
   # Use the logger
   logger.info("API starting")
   logger.warning("Something might be wrong")
   logger.error("Something went wrong")
   ```

2. Make sure the log level is appropriate:

   ```python
   # Debug logs will only appear if the log level is DEBUG or lower
   logging.basicConfig(level=logging.DEBUG)
   
   logger.debug("This is a debug message")
   ```

3. If you're using a logging plugin, make sure it's configured correctly:

   ```python
   from apifrom.plugins import LoggingPlugin
   
   logging_plugin = LoggingPlugin(
       log_level="INFO",
       log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
       log_to_console=True,
       log_to_file=True,
       log_file="api.log",
       log_request_body=True,
       log_response_body=True
   )
   app.plugin_manager.register(logging_plugin)
   ```

## Troubleshooting Async/Await Issues

Asynchronous programming with `async`/`await` can introduce unique challenges. Here are solutions to common issues:

### Coroutine Was Never Awaited Warning

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

### Mixing Sync and Async Code

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

### Event Loop Already Running Error

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

### Blocking the Event Loop

**Problem**: Your async API is not handling requests concurrently because of blocking operations

**Solution**: Ensure you're using async versions of libraries and avoid blocking operations:

```python
# Incorrect - blocks the event loop
@api(route="/users", method="GET")
async def get_users():
    # time.sleep() blocks the entire event loop
    time.sleep(1)
    return {"users": [...]}

# Correct - non-blocking
@api(route="/users", method="GET")
async def get_users():
    # asyncio.sleep() allows other tasks to run
    await asyncio.sleep(1)
    return {"users": [...]}
```

### Database Operations Blocking the Event Loop

**Problem**: Database operations are blocking the event loop

**Solution**: Use async database libraries like `asyncpg` for PostgreSQL or `motor` for MongoDB:

```python
# Incorrect - blocks the event loop
@api(route="/users", method="GET")
async def get_users():
    # This blocks the event loop
    users = db_connection.execute("SELECT * FROM users")
    return {"users": users}

# Correct - non-blocking with asyncpg
@api(route="/users", method="GET")
async def get_users():
    async with db_pool.acquire() as connection:
        # This is non-blocking
        users = await connection.fetch("SELECT * FROM users")
        return {"users": users}
```

### HTTP Requests Blocking the Event Loop

**Problem**: HTTP requests are blocking the event loop

**Solution**: Use async HTTP libraries like `aiohttp` or `httpx`:

```python
# Incorrect - blocks the event loop
import requests

@api(route="/proxy", method="GET")
async def proxy(url: str):
    # This blocks the event loop
    response = requests.get(url)
    return {"data": response.json()}

# Correct - non-blocking with aiohttp
import aiohttp

@api(route="/proxy", method="GET")
async def proxy(url: str):
    async with aiohttp.ClientSession() as session:
        # This is non-blocking
        async with session.get(url) as response:
            data = await response.json()
            return {"data": data}
```

### Middleware Not Handling Async Functions

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

### Testing Async Functions

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

### Handling Exceptions in Async Code

**Problem**: Exceptions in async code are not being caught properly

**Solution**: Use try/except blocks inside async functions and ensure you're awaiting the function:

```python
# Incorrect - exception not caught
@api(route="/users", method="GET")
async def get_users():
    # If this raises an exception, it won't be caught properly
    users = fetch_users()
    return {"users": users}

# Correct - exception properly caught
@api(route="/users", method="GET")
async def get_users():
    try:
        # Properly awaited
        users = await fetch_users()
        return {"users": users}
    except Exception as e:
        # Handle the exception
        return {"error": str(e)}, 500
```

### Async Context Managers

**Problem**: You're having issues with async context managers

**Solution**: Use `async with` for async context managers:

```python
# Incorrect - not using async with
@api(route="/users", method="GET")
async def get_users():
    # This will fail
    with db_pool.acquire() as connection:
        users = await connection.fetch("SELECT * FROM users")
        return {"users": users}

# Correct - using async with
@api(route="/users", method="GET")
async def get_users():
    # This works correctly
    async with db_pool.acquire() as connection:
        users = await connection.fetch("SELECT * FROM users")
        return {"users": users}
```

### Async Iterators

**Problem**: You're having issues with async iterators

**Solution**: Use `async for` for async iterators:

```python
# Incorrect - not using async for
@api(route="/stream", method="GET")
async def stream_data():
    results = []
    # This will fail
    for item in async_generator():
        results.append(item)
    return {"results": results}

# Correct - using async for
@api(route="/stream", method="GET")
async def stream_data():
    results = []
    # This works correctly
    async for item in async_generator():
        results.append(item)
    return {"results": results}
```

### Timeouts in Async Code

**Problem**: Async operations are taking too long and you want to add timeouts

**Solution**: Use `asyncio.wait_for()` to add timeouts to async operations:

```python
import asyncio

@api(route="/users", method="GET")
async def get_users():
    try:
        # Add a timeout of 5 seconds
        users = await asyncio.wait_for(fetch_users(), timeout=5.0)
        return {"users": users}
    except asyncio.TimeoutError:
        # Handle timeout
        return {"error": "Request timed out"}, 504
```

### Cancelling Async Tasks

**Problem**: You need to cancel async tasks

**Solution**: Use `asyncio.create_task()` and `task.cancel()`:

```python
import asyncio

@api(route="/long-operation", method="POST")
async def long_operation():
    # Create a task
    task = asyncio.create_task(expensive_operation())
    
    # Set up a cancellation after 10 seconds
    async def cancel_after(seconds):
        await asyncio.sleep(seconds)
        task.cancel()
    
    asyncio.create_task(cancel_after(10))
    
    try:
        result = await task
        return {"result": result}
    except asyncio.CancelledError:
        return {"status": "cancelled"}, 408
```

By understanding these common async/await issues and their solutions, you'll be able to build more robust and efficient async APIs with APIFromAnything.

## Conclusion

This troubleshooting guide covers common issues you might encounter when using APIFromAnything. If you're still experiencing issues, please check the [GitHub repository](https://github.com/apifrom/apifrom/issues) for known issues or to report a new one. 