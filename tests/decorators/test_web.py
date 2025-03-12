"""
Tests for the Web decorator in the APIFromAnything library.

This module tests the functionality of the Web decorator, which is used to
create web-friendly API endpoints with automatic HTML rendering.
"""
import pytest
import json
from unittest.mock import patch, MagicMock

try:
    from apifrom.decorators.web import Web
    from apifrom.core.app import APIApp
    from apifrom.core.request import Request
    from apifrom.core.response import Response
    LIBRARY_AVAILABLE = True
except ImportError:
    LIBRARY_AVAILABLE = False
    # Mock implementation for testing
    class Web:
        def __init__(self, title=None, description=None, theme="default", template=None):
            self.title = title
            self.description = description
            self.theme = theme
            self.template = template
            
        def __call__(self, func):
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                
                # Check if we're in a request context
                request = kwargs.get('request')
                if not request:
                    # Not in a request context, return the raw result
                    return result
                
                # Check if the client accepts HTML
                accept_header = request.headers.get('Accept', '')
                if 'text/html' in accept_header:
                    # Render HTML
                    html = self._render_html(result)
                    return Response(
                        status_code=200,
                        body=html,
                        headers={"Content-Type": "text/html"}
                    )
                
                # Return JSON by default
                return Response(
                    status_code=200,
                    body=result,
                    headers={"Content-Type": "application/json"}
                )
            
            # Preserve the original function's metadata
            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper
        
        def _render_html(self, data):
            """Render the data as HTML."""
            if self.template:
                # Use the provided template
                return self._render_with_template(data)
            
            # Default HTML rendering
            html = f"<!DOCTYPE html><html><head><title>{self.title or 'API Response'}</title>"
            html += "<style>body{font-family:Arial,sans-serif;margin:20px;line-height:1.6}"
            html += "h1{color:#333}table{border-collapse:collapse;width:100%}"
            html += "th,td{border:1px solid #ddd;padding:8px;text-align:left}"
            html += "th{background-color:#f2f2f2}</style></head>"
            html += f"<body><h1>{self.title or 'API Response'}</h1>"
            
            if self.description:
                html += f"<p>{self.description}</p>"
            
            if isinstance(data, dict):
                html += "<table><tr><th>Key</th><th>Value</th></tr>"
                for key, value in data.items():
                    html += f"<tr><td>{key}</td><td>{self._format_value(value)}</td></tr>"
                html += "</table>"
            elif isinstance(data, list):
                if all(isinstance(item, dict) for item in data):
                    # Table of objects
                    if data:
                        keys = data[0].keys()
                        html += "<table><tr>"
                        for key in keys:
                            html += f"<th>{key}</th>"
                        html += "</tr>"
                        
                        for item in data:
                            html += "<tr>"
                            for key in keys:
                                html += f"<td>{self._format_value(item.get(key, ''))}</td>"
                            html += "</tr>"
                        html += "</table>"
                else:
                    # Simple list
                    html += "<ul>"
                    for item in data:
                        html += f"<li>{self._format_value(item)}</li>"
                    html += "</ul>"
            else:
                html += f"<p>{data}</p>"
            
            html += "</body></html>"
            return html
        
        def _format_value(self, value):
            """Format a value for HTML display."""
            if isinstance(value, (dict, list)):
                return f"<pre>{json.dumps(value, indent=2)}</pre>"
            return str(value)
        
        def _render_with_template(self, data):
            """Render the data using the provided template."""
            # In a real implementation, this would use a template engine
            return f"<html><body><h1>Template Rendering</h1><pre>{json.dumps(data, indent=2)}</pre></body></html>"


@pytest.mark.skipif(not LIBRARY_AVAILABLE, reason="APIFromAnything library not available")
class TestWebDecorator:
    """Tests for the Web decorator."""
    
    def test_web_decorator_initialization(self):
        """Test that the Web decorator can be initialized with various parameters."""
        # Default initialization
        web = Web()
        assert web.title is None
        assert web.description is None
        assert web.theme == "default"
        assert web.template is None
        
        # Custom initialization
        web = Web(
            title="Test API",
            description="A test API endpoint",
            theme="dark",
            template="custom.html"
        )
        assert web.title == "Test API"
        assert web.description == "A test API endpoint"
        assert web.theme == "dark"
        assert web.template == "custom.html"
    
    def test_web_decorator_json_response(self):
        """Test that the Web decorator returns JSON when Accept header is not HTML."""
        @Web(title="Test API")
        def test_endpoint(request):
            return {"message": "Hello, World!"}
        
        # Create a request with Accept: application/json
        request = Request(
            method="GET",
            path="/test",
            headers={"Accept": "application/json"}
        )
        
        # Call the decorated function
        response = test_endpoint(request=request)
        
        # Check that we got a JSON response
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/json"
        assert response.body == {"message": "Hello, World!"}
    
    def test_web_decorator_html_response(self):
        """Test that the Web decorator returns HTML when Accept header includes text/html."""
        @Web(title="Test API", description="A test API endpoint")
        def test_endpoint(request):
            return {"message": "Hello, World!"}
        
        # Create a request with Accept: text/html
        request = Request(
            method="GET",
            path="/test",
            headers={"Accept": "text/html"}
        )
        
        # Call the decorated function
        response = test_endpoint(request=request)
        
        # Check that we got an HTML response
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "text/html"
        assert isinstance(response.body, str)
        assert "<!DOCTYPE html>" in response.body
        assert "<title>Test API</title>" in response.body
        assert "A test API endpoint" in response.body
        assert "Hello, World!" in response.body
    
    def test_web_decorator_with_list_data(self):
        """Test that the Web decorator can render list data as HTML."""
        @Web(title="List API")
        def test_endpoint(request):
            return ["item1", "item2", "item3"]
        
        # Create a request with Accept: text/html
        request = Request(
            method="GET",
            path="/test",
            headers={"Accept": "text/html"}
        )
        
        # Call the decorated function
        response = test_endpoint(request=request)
        
        # Check that we got an HTML response with a list
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "text/html"
        assert "<ul>" in response.body
        assert "<li>item1</li>" in response.body
        assert "<li>item2</li>" in response.body
        assert "<li>item3</li>" in response.body
    
    def test_web_decorator_with_list_of_dicts(self):
        """Test that the Web decorator can render a list of dictionaries as an HTML table."""
        @Web(title="Table API")
        def test_endpoint(request):
            return [
                {"id": 1, "name": "Item 1", "price": 10.99},
                {"id": 2, "name": "Item 2", "price": 20.99},
                {"id": 3, "name": "Item 3", "price": 30.99}
            ]
        
        # Create a request with Accept: text/html
        request = Request(
            method="GET",
            path="/test",
            headers={"Accept": "text/html"}
        )
        
        # Call the decorated function
        response = test_endpoint(request=request)
        
        # Check that we got an HTML response with a table
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "text/html"
        assert "<table>" in response.body
        assert "<th>id</th>" in response.body
        assert "<th>name</th>" in response.body
        assert "<th>price</th>" in response.body
        assert "<td>1</td>" in response.body
        assert "<td>Item 1</td>" in response.body
        assert "<td>10.99</td>" in response.body
    
    def test_web_decorator_with_custom_template(self):
        """Test that the Web decorator can use a custom template."""
        @Web(title="Template API", template="custom.html")
        def test_endpoint(request):
            return {"message": "Hello, World!"}
        
        # Create a request with Accept: text/html
        request = Request(
            method="GET",
            path="/test",
            headers={"Accept": "text/html"}
        )
        
        # Call the decorated function
        response = test_endpoint(request=request)
        
        # Check that we got an HTML response with the template
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "text/html"
        assert "<h1>Template Rendering</h1>" in response.body
        assert "Hello, World!" in response.body
    
    def test_web_decorator_without_request(self):
        """Test that the Web decorator returns raw data when not in a request context."""
        @Web(title="Test API")
        def test_function():
            return {"message": "Hello, World!"}
        
        # Call the decorated function without a request
        result = test_function()
        
        # Check that we got the raw data
        assert isinstance(result, dict)
        assert result == {"message": "Hello, World!"}
    
    def test_web_decorator_integration_with_app(self):
        """Test that the Web decorator works with an APIApp."""
        app = APIApp()
        
        @app.api("/web-test")
        @Web(title="Web Test API")
        def web_test(request):
            return {"message": "Hello from Web API!"}
        
        # Create a request with Accept: text/html
        request = Request(
            method="GET",
            path="/web-test",
            headers={"Accept": "text/html"}
        )
        
        # Handle the request
        response = app.handle_request(request)
        
        # Check that we got an HTML response
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "text/html"
        assert "<!DOCTYPE html>" in response.body
        assert "<title>Web Test API</title>" in response.body
        assert "Hello from Web API!" in response.body
        
        # Create a request with Accept: application/json
        request = Request(
            method="GET",
            path="/web-test",
            headers={"Accept": "application/json"}
        )
        
        # Handle the request
        response = app.handle_request(request)
        
        # Check that we got a JSON response
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/json"
        assert response.body == {"message": "Hello from Web API!"} 