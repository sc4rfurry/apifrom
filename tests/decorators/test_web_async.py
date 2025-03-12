"""
Tests for the async functionality of the Web decorator.

This module tests the Web decorator's ability to handle async functions
and properly render HTML responses.
"""
import pytest
import json
import inspect
from unittest.mock import patch, MagicMock

# Import the Web decorator directly
from apifrom.decorators.web import Web
from apifrom.core.response import Response

# Create a mock Request class for testing
class MockRequest:
    def __init__(self, headers=None):
        self.headers = headers or {}

@pytest.mark.asyncio
class TestWebDecoratorAsync:
    """Test the Web decorator with async functions."""
    
    async def test_web_decorator_with_async_function(self):
        """Test that the Web decorator works with async functions."""
        # Create a Web decorator
        web = Web(title="Test API", description="Test Description")
        
        # Create an async function to decorate
        @web
        async def test_function(request):
            return {"message": "Hello, World!"}
        
        # Check that the decorated function is still a coroutine function
        assert inspect.iscoroutinefunction(test_function)
        
        # Create a mock request with Accept: text/html
        request = MockRequest(headers={"accept": "text/html"})
        
        # Call the decorated function
        response = await test_function(request)
        
        # Check that the response is a Response object
        assert isinstance(response, Response)
        
        # Check that the response has the correct content type
        assert response.content_type == "text/html"
        
        # Check that the response contains the title and description
        assert "Test API" in response.content
        assert "Test Description" in response.content
        
        # Check that the response contains the data
        assert "Hello, World!" in response.content
    
    async def test_web_decorator_with_async_function_json_response(self):
        """Test that the Web decorator returns JSON when Accept is not text/html."""
        # Create a Web decorator
        web = Web(title="Test API", description="Test Description")
        
        # Create an async function to decorate
        @web
        async def test_function(request):
            return {"message": "Hello, World!"}
        
        # Create a mock request with Accept: application/json
        request = MockRequest(headers={"accept": "application/json"})
        
        # Call the decorated function
        response = await test_function(request)
        
        # Check that the response is the original data
        assert response == {"message": "Hello, World!"}
    
    async def test_web_decorator_with_async_function_no_request(self):
        """Test that the Web decorator works with async functions that don't take a request."""
        # Create a Web decorator
        web = Web(title="Test API", description="Test Description")
        
        # Create an async function to decorate that doesn't take a request
        @web
        async def test_function():
            return {"message": "Hello, World!"}
        
        # Call the decorated function
        response = await test_function()
        
        # Check that the response is the original data
        assert response == {"message": "Hello, World!"}
    
    async def test_web_decorator_with_async_function_list_data(self):
        """Test that the Web decorator properly renders list data."""
        # Create a Web decorator
        web = Web(title="Test API", description="Test Description")
        
        # Create an async function to decorate
        @web
        async def test_function(request):
            return ["item1", "item2", "item3"]
        
        # Create a mock request with Accept: text/html
        request = MockRequest(headers={"accept": "text/html"})
        
        # Call the decorated function
        response = await test_function(request)
        
        # Check that the response is a Response object
        assert isinstance(response, Response)
        
        # Check that the response has the correct content type
        assert response.content_type == "text/html"
        
        # Check that the response contains the list items
        assert "item1" in response.content
        assert "item2" in response.content
        assert "item3" in response.content
    
    async def test_web_decorator_with_async_function_list_of_dicts(self):
        """Test that the Web decorator properly renders a list of dictionaries."""
        # Create a Web decorator
        web = Web(title="Test API", description="Test Description")
        
        # Create an async function to decorate
        @web
        async def test_function(request):
            return [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Charlie"}
            ]
        
        # Create a mock request with Accept: text/html
        request = MockRequest(headers={"accept": "text/html"})
        
        # Call the decorated function
        response = await test_function(request)
        
        # Check that the response is a Response object
        assert isinstance(response, Response)
        
        # Check that the response has the correct content type
        assert response.content_type == "text/html"
        
        # Check that the response contains the table headers
        assert "<th>id</th>" in response.content
        assert "<th>name</th>" in response.content
        
        # Check that the response contains the table data
        assert "Alice" in response.content
        assert "Bob" in response.content
        assert "Charlie" in response.content
    
    async def test_web_decorator_with_async_function_response_object(self):
        """Test that the Web decorator passes through Response objects unchanged."""
        # Create a Web decorator
        web = Web(title="Test API", description="Test Description")
        
        # Create an async function to decorate that returns a Response
        @web
        async def test_function(request):
            return Response(
                content="Custom Response",
                content_type="text/plain",
                status_code=200
            )
        
        # Create a mock request with Accept: text/html
        request = MockRequest(headers={"accept": "text/html"})
        
        # Call the decorated function
        response = await test_function(request)
        
        # Check that the response is a Response object
        assert isinstance(response, Response)
        
        # Check that the response has the correct content type
        assert response.content_type == "text/plain"
        
        # Check that the response contains the custom content
        assert response.content == "Custom Response"
    
    async def test_web_decorator_with_different_themes(self):
        """Test that the Web decorator applies different themes correctly."""
        # Test the default theme
        web_default = Web(title="Default Theme")
        
        @web_default
        async def default_theme(request):
            return {"message": "Default Theme"}
        
        # Test the dark theme
        web_dark = Web(title="Dark Theme", theme="dark")
        
        @web_dark
        async def dark_theme(request):
            return {"message": "Dark Theme"}
        
        # Test the light theme
        web_light = Web(title="Light Theme", theme="light")
        
        @web_light
        async def light_theme(request):
            return {"message": "Light Theme"}
        
        # Create a mock request with Accept: text/html
        request = MockRequest(headers={"accept": "text/html"})
        
        # Call the decorated functions
        default_response = await default_theme(request)
        dark_response = await dark_theme(request)
        light_response = await light_theme(request)
        
        # Check that all responses are Response objects
        assert isinstance(default_response, Response)
        assert isinstance(dark_response, Response)
        assert isinstance(light_response, Response)
        
        # Check that the themes are applied correctly
        assert "background-color: #f8f9fa" in default_response.content
        assert "background-color: #1e1e1e" in dark_response.content
        assert "background-color: #ffffff" in light_response.content 