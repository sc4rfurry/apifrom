# APIFromAnything Test Suite

This directory contains the test suite for the APIFromAnything library. The tests are organized into several categories:

- **Unit Tests**: Tests for individual components in isolation
- **Integration Tests**: Tests for components working together
- **Performance Tests**: Tests for performance optimization features
- **Security Tests**: Tests for security features

## Helper Modules

The test suite includes several helper modules to make testing easier:

### `test_server_helper.py`

This module provides a refactored `TestServer` class that uses factory methods instead of constructors to avoid pytest collection issues. Use this for synchronous tests.

```python
from tests.test_server_helper import TestServer

# Create a test server
server = TestServer.create(api_instance, host="127.0.0.1", port=8888)

# Use the server in a context manager
with server:
    # Make requests to the server
    response = requests.get("http://127.0.0.1:8888/hello")
```

### `async_test_server_helper.py`

This module provides an async-compatible `AsyncTestServer` class for testing async APIs.

```python
import pytest
from tests.async_test_server_helper import AsyncTestServer

@pytest.mark.asyncio
async def test_async_api():
    # Create an async test server
    server = AsyncTestServer.create(api_instance, host="127.0.0.1", port=8888)
    
    # Use the server in an async context manager
    async with server:
        # Make requests to the server
        response = await server.request("GET", "/hello")
```

### `middleware_test_helper.py`

This module provides utilities for testing middleware components with proper async support.

```python
import pytest
from tests.middleware_test_helper import MockRequest, MockResponse, AsyncMiddlewareTester

@pytest.mark.asyncio
async def test_middleware():
    # Create a middleware component
    middleware = MyMiddleware()
    
    # Create a mock request
    request = MockRequest(method="GET", path="/hello")
    
    # Test the middleware
    processed_request = await AsyncMiddlewareTester.test_process_request(middleware, request)
    
    # Test a middleware chain
    middleware_list = [MyMiddleware(), AnotherMiddleware()]
    processed_request = await AsyncMiddlewareTester.test_middleware_chain(middleware_list, request)
```

### `security_test_helper.py`

This module provides utilities for testing security components with proper async support.

```python
import pytest
from tests.security_test_helper import SecurityTestHelper

@pytest.mark.asyncio
async def test_jwt_auth():
    # Create a JWT-protected handler
    @jwt_required(secret="test-secret")
    async def handler(request):
        return {"message": "Hello, world!"}
    
    # Test the handler with JWT authentication
    response = await SecurityTestHelper.test_jwt_auth(handler)
    
    # Test with a custom payload
    payload = {"sub": "test-user", "role": "admin"}
    response = await SecurityTestHelper.test_jwt_auth(handler, payload=payload)
```

## Running Tests

To run the tests, use pytest:

```bash
# Run all tests
python -m pytest

# Run a specific test file
python -m pytest tests/test_core.py

# Run a specific test
python -m pytest tests/test_core.py::test_api_creation

# Run tests with coverage
python -m pytest --cov=apifrom
```

## Writing Tests

When writing tests, follow these guidelines:

1. Use the helper modules to simplify testing
2. Use factory methods instead of constructors for test classes
3. Use async/await for async functions
4. Use pytest fixtures for common setup
5. Use pytest marks to categorize tests
6. Use pytest parametrize for testing multiple cases

### Example

```python
import pytest
from tests.middleware_test_helper import MockRequest, AsyncMiddlewareTester

@pytest.mark.asyncio
async def test_my_middleware():
    # Create a middleware component
    middleware = MyMiddleware()
    
    # Create a mock request
    request = MockRequest(method="GET", path="/hello")
    
    # Test the middleware
    processed_request = await AsyncMiddlewareTester.test_process_request(middleware, request)
    
    # Assert the expected behavior
    assert processed_request.headers["X-My-Header"] == "My Value"
```

## Test Structure

### Unit Tests

Unit tests focus on testing individual components in isolation. They are located in the `tests/unit` directory.

### Integration Tests

Integration tests verify that different components work together correctly. They are located in the `tests/integration` directory.

### Performance Tests

Performance tests evaluate the library's behavior under various load conditions. They are located in the `tests/performance` directory.

### Security Tests

Security tests verify that the library's security features work correctly and that it's not vulnerable to common attacks. They are located in the `tests/security` directory.

## Continuous Integration

Tests are automatically run on GitHub Actions for each pull request and push to the main branch. The workflow is defined in `.github/workflows/tests.yml`. 