"""
Tests for the example API.
"""
import pytest
import json
import jwt
from examples.combined_example import app
from apifrom.core.request import Request
from apifrom.core.response import Response

@pytest.fixture
def api():
    """Return the API instance."""
    return app

@pytest.mark.asyncio
async def test_hello_endpoint(api):
    """Test the hello endpoint."""
    # Get the handler for the hello endpoint
    handler = api.router.get_route_handler("/hello/{name}", "GET")
    
    # Create a mock request
    request = Request(
        method="GET",
        path="/hello/World",
        headers={},
        query_params={"greeting": "Hi"},
        body=None,
        path_params={"name": "World"}
    )
    
    # Call the handler
    response = await handler(request)
    
    # Check the response
    assert response.status_code == 200
    assert json.loads(response.body) == {"message": "Hi, World!"}

@pytest.mark.asyncio
async def test_create_user_endpoint(api):
    """Test the create_user endpoint."""
    # Get the handler for the create_user endpoint
    handler = api.router.get_route_handler("/users", "POST")
    
    # Create a mock request
    request = Request(
        method="POST",
        path="/users",
        headers={"Content-Type": "application/json"},
        query_params={},
        body=json.dumps({
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "tags": ["user", "customer"]
        }).encode("utf-8"),
        path_params={}
    )
    
    # Call the handler
    response = await handler(request)
    
    # Check the response
    assert response.status_code == 200
    assert json.loads(response.body) == {
        "name": "John Doe",
        "email": "john@example.com",
        "id": 123,
        "age": 30,
        "tags": ["user", "customer"]
    }

@pytest.mark.asyncio
async def test_secured_endpoint(api):
    """Test the secured endpoint."""
    # Get the handler for the secured endpoint
    handler = api.router.get_route_handler("/secured", "GET")
    
    # Create a JWT token
    token = jwt.encode(
        {"sub": "test-user"},
        "your-secret-key",
        algorithm="HS256"
    )
    
    # Create a mock request
    request = Request(
        method="GET",
        path="/secured",
        headers={"Authorization": f"Bearer {token}"},
        query_params={},
        body=None,
        path_params={}
    )
    
    # Call the handler
    response = await handler(request)
    
    # Check the response
    assert response.status_code == 200
    assert json.loads(response.body) == {
        "user": "test-user",
        "authenticated": True
    }

@pytest.mark.asyncio
async def test_api_key_secured_endpoint(api):
    """Test the API key secured endpoint."""
    # Get the handler for the API key secured endpoint
    handler = api.router.get_route_handler("/api-key-secured", "GET")
    
    # Create a mock request
    request = Request(
        method="GET",
        path="/api-key-secured",
        headers={"X-API-Key": "test-key"},
        query_params={},
        body=None,
        path_params={}
    )
    
    # Call the handler
    response = await handler(request)
    
    # Check the response
    assert response.status_code == 200
    assert json.loads(response.body) == {
        "api_key": "test-key",
        "authenticated": True
    } 