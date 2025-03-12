# Testing Your APIs

This guide covers best practices and techniques for testing APIs built with APIFromAnything.

## Overview

Testing is a crucial part of API development. It helps ensure that your API works as expected, handles errors gracefully, and maintains backward compatibility. APIFromAnything provides tools and utilities to make testing your APIs easier and more effective.

## Types of Tests

When testing APIs, it's important to consider different types of tests:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test how components work together
3. **Functional Tests**: Test the API from the user's perspective
4. **Performance Tests**: Test the API's performance under load
5. **Security Tests**: Test the API's security features

## Test Client

APIFromAnything provides a `TestClient` class that allows you to make requests to your API without running a server.

```python
from apifrom import API, api
from apifrom.testing import TestClient

# Create an API
app = API()

@api(route="/hello/{name}", method="GET")
def hello(name: str):
    return {"message": f"Hello, {name}!"}

# Create a test client
client = TestClient(app)

# Make a request
response = client.get("/hello/World")

# Assert the response
assert response.status_code == 200
assert response.json() == {"message": "Hello, World!"}
```

## Unit Testing

Unit tests focus on testing individual components in isolation. For example, you might test a single API endpoint or a utility function.

```python
import pytest
from apifrom import API, api
from apifrom.testing import TestClient

# Create an API
app = API()

@api(route="/add", method="POST")
def add(a: int, b: int):
    return {"result": a + b}

# Create a test client
client = TestClient(app)

def test_add():
    response = client.post("/add", json={"a": 2, "b": 3})
    assert response.status_code == 200
    assert response.json() == {"result": 5}

def test_add_invalid_input():
    response = client.post("/add", json={"a": "not a number", "b": 3})
    assert response.status_code == 422  # Validation error
```

## Integration Testing

Integration tests focus on testing how components work together. For example, you might test how your API interacts with a database or an external service.

```python
import pytest
from apifrom import API, api
from apifrom.testing import TestClient
from myapp.database import get_db, User

# Create an API
app = API()

@api(route="/users", method="POST")
def create_user(name: str, email: str):
    db = get_db()
    user = User(name=name, email=email)
    db.add(user)
    db.commit()
    return {"id": user.id, "name": user.name, "email": user.email}

@api(route="/users/{user_id}", method="GET")
def get_user(user_id: int):
    db = get_db()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}, 404
    return {"id": user.id, "name": user.name, "email": user.email}

# Create a test client
client = TestClient(app)

def test_create_and_get_user():
    # Create a user
    create_response = client.post(
        "/users",
        json={"name": "John Doe", "email": "john@example.com"}
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]
    
    # Get the user
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 200
    assert get_response.json() == {
        "id": user_id,
        "name": "John Doe",
        "email": "john@example.com"
    }
```

## Functional Testing

Functional tests focus on testing the API from the user's perspective. They test the API as a whole, including routing, middleware, and error handling.

```python
import pytest
from apifrom import API, api
from apifrom.testing import TestClient
from apifrom.middleware import ErrorHandlingMiddleware

# Create an API
app = API()

# Add error handling middleware
app.add_middleware(ErrorHandlingMiddleware())

@api(route="/users", method="GET")
def get_users():
    return [
        {"id": 1, "name": "John Doe"},
        {"id": 2, "name": "Jane Doe"}
    ]

@api(route="/users/{user_id}", method="GET")
def get_user(user_id: int):
    if user_id == 1:
        return {"id": 1, "name": "John Doe"}
    elif user_id == 2:
        return {"id": 2, "name": "Jane Doe"}
    else:
        return {"error": "User not found"}, 404

# Create a test client
client = TestClient(app)

def test_get_users():
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_user():
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "John Doe"}

def test_get_user_not_found():
    response = client.get("/users/999")
    assert response.status_code == 404
    assert "error" in response.json()
```

## Performance Testing

Performance tests focus on testing the API's performance under load. They help identify bottlenecks and ensure that the API can handle the expected traffic.

```python
import pytest
import time
from apifrom import API, api
from apifrom.testing import TestClient

# Create an API
app = API()

@api(route="/fast", method="GET")
def fast():
    return {"message": "Fast response"}

@api(route="/slow", method="GET")
def slow():
    time.sleep(0.1)  # Simulate a slow operation
    return {"message": "Slow response"}

# Create a test client
client = TestClient(app)

def test_fast_endpoint_performance():
    start_time = time.time()
    response = client.get("/fast")
    end_time = time.time()
    
    assert response.status_code == 200
    assert end_time - start_time < 0.01  # Response time should be less than 10ms

def test_slow_endpoint_performance():
    start_time = time.time()
    response = client.get("/slow")
    end_time = time.time()
    
    assert response.status_code == 200
    assert end_time - start_time >= 0.1  # Response time should be at least 100ms
```

## Security Testing

Security tests focus on testing the API's security features. They help identify vulnerabilities and ensure that the API is secure.

```python
import pytest
import jwt
from apifrom import API, api
from apifrom.testing import TestClient
from apifrom.security import jwt_required

# Create an API
app = API()

# JWT configuration
JWT_SECRET = "your-secret-key"
JWT_ALGORITHM = "HS256"

@api(route="/public", method="GET")
def public():
    return {"message": "Public endpoint"}

@api(route="/protected", method="GET")
@jwt_required(secret=JWT_SECRET, algorithm=JWT_ALGORITHM)
def protected(request):
    return {"message": "Protected endpoint", "user": request.state.jwt_payload.get("sub")}

# Create a test client
client = TestClient(app)

def test_public_endpoint():
    response = client.get("/public")
    assert response.status_code == 200
    assert response.json() == {"message": "Public endpoint"}

def test_protected_endpoint_without_token():
    response = client.get("/protected")
    assert response.status_code == 401  # Unauthorized

def test_protected_endpoint_with_invalid_token():
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401  # Unauthorized

def test_protected_endpoint_with_valid_token():
    # Create a valid token
    payload = {"sub": "user123"}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/protected", headers=headers)
    
    assert response.status_code == 200
    assert response.json() == {"message": "Protected endpoint", "user": "user123"}
```

## Mocking

Mocking is a technique used in testing to replace real objects with mock objects. It's useful for isolating the code being tested and for simulating different scenarios.

```python
import pytest
from unittest.mock import patch, MagicMock
from apifrom import API, api
from apifrom.testing import TestClient

# Create an API
app = API()

# External service
class WeatherService:
    def get_temperature(self, city):
        # In a real application, this would make an HTTP request
        # to an external weather service
        pass

weather_service = WeatherService()

@api(route="/weather/{city}", method="GET")
def get_weather(city: str):
    temperature = weather_service.get_temperature(city)
    return {"city": city, "temperature": temperature}

# Create a test client
client = TestClient(app)

def test_get_weather():
    # Mock the get_temperature method
    with patch.object(weather_service, "get_temperature", return_value=25):
        response = client.get("/weather/London")
        
        assert response.status_code == 200
        assert response.json() == {"city": "London", "temperature": 25}
```

## Fixtures

Fixtures are a way to provide data or objects to tests. They help reduce duplication and make tests more maintainable.

```python
import pytest
from apifrom import API, api
from apifrom.testing import TestClient

# Create an API
app = API()

@api(route="/users/{user_id}", method="GET")
def get_user(user_id: int):
    # In a real application, this would query a database
    users = {
        1: {"id": 1, "name": "John Doe"},
        2: {"id": 2, "name": "Jane Doe"}
    }
    
    if user_id in users:
        return users[user_id]
    else:
        return {"error": "User not found"}, 404

# Create a test client
client = TestClient(app)

@pytest.fixture
def user_id():
    return 1

@pytest.fixture
def non_existent_user_id():
    return 999

def test_get_user(user_id):
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "John Doe"}

def test_get_user_not_found(non_existent_user_id):
    response = client.get(f"/users/{non_existent_user_id}")
    assert response.status_code == 404
    assert "error" in response.json()
```

## Parameterized Tests

Parameterized tests allow you to run the same test with different inputs. They help reduce duplication and make tests more comprehensive.

```python
import pytest
from apifrom import API, api
from apifrom.testing import TestClient

# Create an API
app = API()

@api(route="/calculate", method="POST")
def calculate(operation: str, a: int, b: int):
    if operation == "add":
        return {"result": a + b}
    elif operation == "subtract":
        return {"result": a - b}
    elif operation == "multiply":
        return {"result": a * b}
    elif operation == "divide":
        if b == 0:
            return {"error": "Division by zero"}, 400
        return {"result": a / b}
    else:
        return {"error": "Invalid operation"}, 400

# Create a test client
client = TestClient(app)

@pytest.mark.parametrize("operation,a,b,expected_result,expected_status_code", [
    ("add", 2, 3, {"result": 5}, 200),
    ("subtract", 5, 3, {"result": 2}, 200),
    ("multiply", 2, 3, {"result": 6}, 200),
    ("divide", 6, 3, {"result": 2.0}, 200),
    ("divide", 6, 0, {"error": "Division by zero"}, 400),
    ("invalid", 2, 3, {"error": "Invalid operation"}, 400),
])
def test_calculate(operation, a, b, expected_result, expected_status_code):
    response = client.post(
        "/calculate",
        json={"operation": operation, "a": a, "b": b}
    )
    
    assert response.status_code == expected_status_code
    assert response.json() == expected_result
```

## Test Coverage

Test coverage is a measure of how much of your code is covered by tests. It helps identify areas of your code that are not being tested.

```bash
# Install pytest-cov
pip install pytest-cov

# Run tests with coverage
pytest --cov=myapp tests/
```

## Continuous Integration

Continuous Integration (CI) is a practice of automatically running tests whenever code is pushed to a repository. It helps catch issues early and ensures that the codebase is always in a working state.

Here's an example of a GitHub Actions workflow for running tests:

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov
        pip install -e .
    
    - name: Run tests
      run: |
        pytest --cov=myapp tests/
```

## Best Practices

1. **Write tests first**: Follow Test-Driven Development (TDD) principles by writing tests before implementing features
2. **Keep tests simple**: Each test should test one thing and have a clear purpose
3. **Use descriptive test names**: Test names should describe what the test is testing
4. **Use fixtures**: Use fixtures to reduce duplication and make tests more maintainable
5. **Mock external dependencies**: Use mocking to isolate the code being tested
6. **Test edge cases**: Test boundary conditions and error cases
7. **Run tests automatically**: Use CI to run tests automatically
8. **Monitor test coverage**: Use test coverage tools to identify areas of your code that are not being tested

## Testing Async Functions

APIFromAnything version 1.0.0 includes full support for async/await. This section covers how to properly test asynchronous functions and middleware.

### Setting Up Pytest for Async Testing

To test async functions, you'll need to set up pytest with the `pytest-asyncio` plugin:

```bash
pip install pytest pytest-asyncio
```

Create a `conftest.py` file in your tests directory with the following configuration:

```python
# conftest.py
import pytest

# Set the default event loop scope to function
# This ensures each test function gets a fresh event loop
pytest_plugins = ["pytest_asyncio"]
```

### Testing Async API Endpoints

To test async API endpoints, use the `pytest.mark.asyncio` decorator:

```python
import pytest
from apifrom import API, api
from apifrom.testing import TestClient

# Create a test API
app = API()

@api(route="/async-hello/{name}", method="GET")
async def async_hello(name: str):
    return {"message": f"Hello, {name}!"}

# Mark the test as async
@pytest.mark.asyncio
async def test_async_hello():
    # Create a test client
    client = TestClient(app)
    
    # Make a request to the async endpoint
    response = await client.get("/async-hello/World")
    
    # Assert the response
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}
```

### Testing Async Middleware

To test async middleware, use the `AsyncMiddlewareTester` helper class:

```python
import pytest
from apifrom.middleware import Middleware
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.testing import AsyncMiddlewareTester

# Define an async middleware
class AsyncLoggingMiddleware(Middleware):
    async def dispatch(self, request, call_next):
        # Log the request
        print(f"Request: {request.method} {request.url.path}")
        
        # Process the request
        response = await call_next(request)
        
        # Log the response
        print(f"Response: {response.status_code}")
        
        return response

# Mark the test as async
@pytest.mark.asyncio
async def test_async_middleware():
    # Create a middleware tester
    tester = AsyncMiddlewareTester(AsyncLoggingMiddleware())
    
    # Create a mock request
    request = Request(method="GET", url="/test")
    
    # Create a mock response
    mock_response = Response(content={"message": "Test"}, status_code=200)
    
    # Test the middleware
    response = await tester.test_dispatch(
        request=request,
        mock_response=mock_response
    )
    
    # Assert the response
    assert response.status_code == 200
    assert response.json() == {"message": "Test"}
```

### Testing Async Database Operations

To test async database operations, use an in-memory database or mock the database:

```python
import pytest
import asyncio
from unittest.mock import AsyncMock

# Mark the test as async
@pytest.mark.asyncio
async def test_async_database_operations():
    # Mock the database connection
    db_connection = AsyncMock()
    db_connection.fetch.return_value = [
        {"id": 1, "name": "User 1"},
        {"id": 2, "name": "User 2"}
    ]
    
    # Test the function that uses the database
    async def get_users():
        return await db_connection.fetch("SELECT * FROM users")
    
    # Call the function
    users = await get_users()
    
    # Assert the result
    assert len(users) == 2
    assert users[0]["name"] == "User 1"
    assert users[1]["name"] == "User 2"
    
    # Verify the mock was called
    db_connection.fetch.assert_called_once_with("SELECT * FROM users")
```

### Testing Async HTTP Requests

To test async HTTP requests, use the `aioresponses` library:

```bash
pip install aioresponses
```

```python
import pytest
import aiohttp
from aioresponses import aioresponses

# Mark the test as async
@pytest.mark.asyncio
async def test_async_http_requests():
    # Create a mock for aiohttp
    with aioresponses() as m:
        # Mock the HTTP response
        m.get(
            "https://api.example.com/users",
            status=200,
            payload={"users": [{"id": 1, "name": "User 1"}]}
        )
        
        # Test the function that makes HTTP requests
        async def fetch_users():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.example.com/users") as response:
                    return await response.json()
        
        # Call the function
        result = await fetch_users()
        
        # Assert the result
        assert result == {"users": [{"id": 1, "name": "User 1"}]}
```

### Testing Async Context Managers

To test async context managers, use the `contextlib.asynccontextmanager` decorator:

```python
import pytest
from contextlib import asynccontextmanager

# Define an async context manager
@asynccontextmanager
async def database_connection():
    # Set up
    connection = {"connected": True}
    try:
        yield connection
    finally:
        # Tear down
        connection["connected"] = False

# Mark the test as async
@pytest.mark.asyncio
async def test_async_context_manager():
    # Use the async context manager
    async with database_connection() as conn:
        # Assert the connection is established
        assert conn["connected"] is True
        
        # Perform operations with the connection
        conn["data"] = "test"
        assert conn["data"] == "test"
    
    # Assert the connection is closed after the context
    assert conn["connected"] is False
```

### Testing Async Iterators

To test async iterators, use the `async for` syntax:

```python
import pytest

# Define an async iterator
async def async_range(count):
    for i in range(count):
        yield i

# Mark the test as async
@pytest.mark.asyncio
async def test_async_iterator():
    # Use the async iterator
    result = []
    async for i in async_range(5):
        result.append(i)
    
    # Assert the result
    assert result == [0, 1, 2, 3, 4]
```

### Testing Timeouts

To test timeouts, use `asyncio.wait_for()` with a small timeout:

```python
import pytest
import asyncio

# Mark the test as async
@pytest.mark.asyncio
async def test_timeout():
    # Define a function that takes too long
    async def long_operation():
        await asyncio.sleep(1)
        return "result"
    
    # Test that it times out
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(long_operation(), timeout=0.1)
```

### Testing Task Cancellation

To test task cancellation, use `asyncio.create_task()` and `task.cancel()`:

```python
import pytest
import asyncio

# Mark the test as async
@pytest.mark.asyncio
async def test_task_cancellation():
    # Define a function that can be cancelled
    async def cancellable_operation():
        try:
            await asyncio.sleep(1)
            return "completed"
        except asyncio.CancelledError:
            return "cancelled"
    
    # Create a task
    task = asyncio.create_task(cancellable_operation())
    
    # Cancel the task
    task.cancel()
    
    # Wait for the task to complete
    result = await task
    
    # Assert the result
    assert result == "cancelled"
```

### Testing Async Error Handling

To test async error handling, use try/except blocks:

```python
import pytest

# Mark the test as async
@pytest.mark.asyncio
async def test_async_error_handling():
    # Define a function that raises an exception
    async def failing_operation():
        raise ValueError("Test error")
    
    # Test error handling
    try:
        await failing_operation()
        # If we get here, the test should fail
        assert False, "Expected an exception but none was raised"
    except ValueError as e:
        # Assert the exception
        assert str(e) == "Test error"
```

### Testing Async API with TestClient

APIFromAnything provides a `TestClient` class for testing APIs:

```python
import pytest
from apifrom import API, api
from apifrom.testing import TestClient

# Create a test API
app = API()

@api(route="/async-users", method="GET")
async def get_users():
    return {"users": [{"id": 1, "name": "User 1"}]}

@api(route="/async-users", method="POST")
async def create_user(name: str):
    return {"id": 2, "name": name}

# Mark the test as async
@pytest.mark.asyncio
async def test_async_api():
    # Create a test client
    client = TestClient(app)
    
    # Test GET request
    get_response = await client.get("/async-users")
    assert get_response.status_code == 200
    assert get_response.json() == {"users": [{"id": 1, "name": "User 1"}]}
    
    # Test POST request
    post_response = await client.post("/async-users", json={"name": "User 2"})
    assert post_response.status_code == 200
    assert post_response.json() == {"id": 2, "name": "User 2"}
```

### Testing Async Middleware with AsyncMiddlewareTester

APIFromAnything provides an `AsyncMiddlewareTester` class for testing middleware:

```python
import pytest
from apifrom.middleware import Middleware
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.testing import AsyncMiddlewareTester

# Define an async middleware
class AsyncAuthMiddleware(Middleware):
    async def dispatch(self, request, call_next):
        # Check for authorization header
        if "Authorization" not in request.headers:
            return Response(
                content={"error": "Unauthorized"},
                status_code=401
            )
        
        # Process the request
        response = await call_next(request)
        
        return response

# Mark the test as async
@pytest.mark.asyncio
async def test_async_auth_middleware():
    # Create a middleware tester
    tester = AsyncMiddlewareTester(AsyncAuthMiddleware())
    
    # Test without authorization header
    request_without_auth = Request(
        method="GET",
        url="/test",
        headers={}
    )
    
    response_without_auth = await tester.test_dispatch(
        request=request_without_auth,
        mock_response=Response(content={"message": "Test"}, status_code=200)
    )
    
    # Assert unauthorized response
    assert response_without_auth.status_code == 401
    assert response_without_auth.json() == {"error": "Unauthorized"}
    
    # Test with authorization header
    request_with_auth = Request(
        method="GET",
        url="/test",
        headers={"Authorization": "Bearer token"}
    )
    
    response_with_auth = await tester.test_dispatch(
        request=request_with_auth,
        mock_response=Response(content={"message": "Test"}, status_code=200)
    )
    
    # Assert authorized response
    assert response_with_auth.status_code == 200
    assert response_with_auth.json() == {"message": "Test"}
```

By following these testing patterns, you can ensure that your async functions and middleware are working correctly and handling errors properly.

## Conclusion

Testing is a crucial part of API development. APIFromAnything provides tools and utilities to make testing your APIs easier and more effective. By following the best practices outlined in this guide, you can ensure that your APIs are reliable, secure, and maintainable. 