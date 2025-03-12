"""
Helper module for middleware testing.
This module provides utilities for testing middleware components with proper async support.
"""
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from types import SimpleNamespace

class MockRequest:
    """
    A mock request object for testing middleware.
    """
    def __init__(self, method: str = "GET", path: str = "/", 
                 headers: Optional[Dict[str, str]] = None,
                 query_params: Optional[Dict[str, Any]] = None,
                 body: Optional[Any] = None):
        """
        Initialize a mock request.

        Args:
            method: The HTTP method
            path: The request path
            headers: The request headers
            query_params: The query parameters
            body: The request body
        """
        self.method = method
        self.path = path
        self.headers = headers or {}
        self.query_params = query_params or {}
        self.body = body
        self.state = SimpleNamespace()  # Add state attribute for middleware that needs it
        
    def __repr__(self):
        """Return a string representation of the request."""
        return f"MockRequest(method={self.method}, path={self.path})"


class MockResponse:
    """
    A mock response object for testing middleware.
    """
    def __init__(self, status_code: int = 200,
                 body: Optional[Any] = None,
                 headers: Optional[Dict[str, str]] = None):
        """
        Initialize a mock response.

        Args:
            status_code: The HTTP status code
            body: The response body
            headers: The response headers
        """
        self.status_code = status_code
        self.body = body
        self.headers = headers or {}
        self.request = None  # Add request attribute for middleware that needs it

    def __repr__(self):
        """Return a string representation of the response."""
        return f"MockResponse(status_code={self.status_code})"
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the response to a dictionary for caching.
        
        Returns:
            A dictionary representation of the response
        """
        return {
            "status_code": self.status_code,
            "content": self.body,
            "headers": self.headers
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MockResponse':
        """
        Create a response from a dictionary.
        
        Args:
            data: The dictionary data
            
        Returns:
            A new MockResponse instance
        """
        return cls(
            status_code=data.get("status_code", 200),
            body=data.get("content"),
            headers=data.get("headers", {})
        )


class AsyncMiddlewareTester:
    """
    A utility for testing middleware components with async support.
    """
    
    @staticmethod
    async def test_process_request(middleware, request: Optional[MockRequest] = None):
        """
        Test the process_request method of a middleware component.
        
        Args:
            middleware: The middleware component to test
            request: A mock request object (created if not provided)
            
        Returns:
            The processed request
        """
        if request is None:
            request = MockRequest()
            
        if hasattr(middleware, 'process_request'):
            if asyncio.iscoroutinefunction(middleware.process_request):
                return await middleware.process_request(request)
            else:
                return middleware.process_request(request)
        return request
    
    @staticmethod
    async def test_process_response(middleware, response: Optional[MockResponse] = None, 
                                   request: Optional[MockRequest] = None):
        """
        Test the process_response method of a middleware component.
        
        Args:
            middleware: The middleware component to test
            response: A mock response object (created if not provided)
            request: A mock request object (created if not provided)
            
        Returns:
            The processed response
        """
        if response is None:
            response = MockResponse()
            
        if request is None:
            request = MockRequest()
            
        # Set the request on the response
        response.request = request

        if hasattr(middleware, 'process_response'):
            if asyncio.iscoroutinefunction(middleware.process_response):
                # Check the number of parameters the process_response method expects
                import inspect
                sig = inspect.signature(middleware.process_response)
                if len(sig.parameters) > 2:  # self, request, response
                    return await middleware.process_response(request, response)
                else:  # self, response
                    return await middleware.process_response(response)
            else:
                # Same check for synchronous methods
                import inspect
                sig = inspect.signature(middleware.process_response)
                if len(sig.parameters) > 2:  # self, request, response
                    return middleware.process_response(request, response)
                else:  # self, response
                    return middleware.process_response(response)
        return response
    
    @staticmethod
    async def test_middleware_chain(middleware_list, request: Optional[MockRequest] = None):
        """
        Test a chain of middleware components.
        
        Args:
            middleware_list: A list of middleware components to test
            request: A mock request object (created if not provided)
            
        Returns:
            The final processed request
        """
        if request is None:
            request = MockRequest()
            
        current_request = request
        for middleware in middleware_list:
            current_request = await AsyncMiddlewareTester.test_process_request(middleware, current_request)
            
        return current_request
    
    @staticmethod
    async def test_middleware_chain_with_response(middleware_list, 
                                                response: Optional[MockResponse] = None,
                                                request: Optional[MockRequest] = None):
        """
        Test a chain of middleware components with a response.
        
        Args:
            middleware_list: A list of middleware components to test
            response: A mock response object (created if not provided)
            request: A mock request object (created if not provided)
            
        Returns:
            The final processed response
        """
        if request is None:
            request = MockRequest()
            
        if response is None:
            response = MockResponse()
            
        # Apply request middleware in order
        current_request = request
        for middleware in middleware_list:
            current_request = await AsyncMiddlewareTester.test_process_request(middleware, current_request)
            
        # Apply response middleware in reverse order
        current_response = response
        for middleware in reversed(middleware_list):
            current_response = await AsyncMiddlewareTester.test_process_response(
                middleware, current_response, current_request)
            
        return current_response 