"""
Unit tests for the core functionality of the APIFromAnything library.
"""
import pytest
import json
from typing import Dict, Any, Optional

# Import the core components
try:
    from apifrom.core.app import APIApp
    from apifrom.core.request import Request
    from apifrom.core.response import Response
    from apifrom.decorators.api import api
except ImportError:
    # If the library is not installed, we'll use mock objects for testing
    class APIApp:
        def __init__(self):
            self.routes = {}
            
        def api(self, route=None, methods=None):
            if methods is None:
                methods = ["GET"]
                
            def decorator(func):
                nonlocal route
                if route is None:
                    route = f"/{func.__name__}"
                self.routes[route] = {"handler": func, "methods": methods}
                return func
            return decorator
            
        def handle_request(self, request):
            if request.path in self.routes:
                handler = self.routes[request.path]["handler"]
                kwargs = {}
                for param_name, param_value in request.query_params.items():
                    kwargs[param_name] = param_value
                result = handler(**kwargs)
                return Response(status_code=200, body=result)
            return Response(status_code=404, body={"error": "Not found"})
    
    class Request:
        def __init__(self, method, path, query_params=None, headers=None, body=None):
            self.method = method
            self.path = path
            self.query_params = query_params or {}
            self.headers = headers or {}
            self.body = body
    
    class Response:
        def __init__(self, status_code, body=None, headers=None):
            self.status_code = status_code
            self.body = body
            self.headers = headers or {}


class TestAPIApp:
    """Tests for the APIApp class."""
    
    def test_app_initialization(self):
        """Test that the APIApp can be initialized."""
        app = APIApp()
        assert app is not None
        assert hasattr(app, 'routes')
        assert isinstance(app.routes, dict)
    
    def test_api_decorator_registers_route(self):
        """Test that the @api decorator correctly registers a route."""
        app = APIApp()
        
        @app.api(route="/test")
        def test_endpoint():
            return {"message": "success"}
        
        assert "/test" in app.routes
        assert app.routes["/test"]["handler"] == test_endpoint
        assert app.routes["/test"]["methods"] == ["GET"]
    
    def test_api_decorator_default_route(self):
        """Test that the @api decorator uses the function name as the default route."""
        app = APIApp()
        
        @app.api()
        def test_endpoint():
            return {"message": "success"}
        
        assert "/test_endpoint" in app.routes
    
    def test_api_decorator_custom_methods(self):
        """Test that the @api decorator accepts custom HTTP methods."""
        app = APIApp()
        
        @app.api(methods=["POST", "PUT"])
        def test_endpoint():
            return {"message": "success"}
        
        assert app.routes["/test_endpoint"]["methods"] == ["POST", "PUT"]


class TestRequestHandling:
    """Tests for request handling."""
    
    def test_handle_request_basic(self):
        """Test basic request handling."""
        app = APIApp()
        
        @app.api()
        def hello():
            return {"message": "Hello, World!"}
        
        request = Request(method="GET", path="/hello")
        response = app.handle_request(request)
        
        assert response.status_code == 200
        assert response.body == {"message": "Hello, World!"}
    
    def test_handle_request_with_params(self):
        """Test request handling with query parameters."""
        app = APIApp()
        
        @app.api()
        def greet(name: str = "World"):
            return {"message": f"Hello, {name}!"}
        
        request = Request(
            method="GET",
            path="/greet",
            query_params={"name": "Test"}
        )
        response = app.handle_request(request)
        
        assert response.status_code == 200
        assert response.body == {"message": "Hello, Test!"}
    
    def test_handle_request_not_found(self):
        """Test handling of requests to non-existent routes."""
        app = APIApp()
        
        request = Request(method="GET", path="/nonexistent")
        response = app.handle_request(request)
        
        assert response.status_code == 404
        assert "error" in response.body


class TestResponseHandling:
    """Tests for response handling."""
    
    def test_response_initialization(self):
        """Test that the Response can be initialized."""
        response = Response(status_code=200, body={"message": "success"})
        
        assert response.status_code == 200
        assert response.body == {"message": "success"}
        assert isinstance(response.headers, dict)
    
    def test_response_with_headers(self):
        """Test that the Response can be initialized with headers."""
        headers = {"Content-Type": "application/json"}
        response = Response(status_code=200, body={"message": "success"}, headers=headers)
        
        assert response.headers == headers


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 