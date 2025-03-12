"""
Common fixtures for the APIFromAnything tests.
"""
import pytest
import json
import base64
import time
from typing import Dict, Any, Optional, List, Callable

# Try to import the library
try:
    from apifrom.core.app import APIApp
    from apifrom.core.request import Request
    from apifrom.core.response import Response
    from apifrom.decorators.api import api
    from apifrom.middleware.base import Middleware
    from apifrom.security.auth import jwt_required, api_key_required, basic_auth_required
    LIBRARY_AVAILABLE = True
except ImportError:
    # If the library is not installed, we'll use mock objects for testing
    LIBRARY_AVAILABLE = False
    
    class APIApp:
        def __init__(self):
            self.routes = {}
            self.middleware = []
            self.security = SecurityManager(self)
            
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
            
        def add_middleware(self, middleware):
            self.middleware.append(middleware)
            
        def handle_request(self, request):
            # Apply request middleware
            current_request = request
            for middleware in self.middleware:
                if hasattr(middleware, 'process_request'):
                    result = middleware.process_request(current_request)
                    if isinstance(result, Response):
                        # Short-circuit: middleware returned a response
                        response = result
                        # Apply response middleware
                        for m in reversed(self.middleware):
                            if hasattr(m, 'process_response'):
                                response = m.process_response(response)
                        return response
                    current_request = result
            
            # Handle the request
            if current_request.path in self.routes:
                handler = self.routes[current_request.path]["handler"]
                
                # Check if the handler has security decorators
                if hasattr(handler, '_security_checks'):
                    for check in handler._security_checks:
                        result = check(current_request)
                        if isinstance(result, Response):
                            return result
                
                kwargs = {}
                for param_name, param_value in current_request.query_params.items():
                    kwargs[param_name] = param_value
                result = handler(**kwargs)
                response = Response(status_code=200, body=result)
            else:
                response = Response(status_code=404, body={"error": "Not found"})
            
            # Apply response middleware
            current_response = response
            for middleware in reversed(self.middleware):
                if hasattr(middleware, 'process_response'):
                    current_response = middleware.process_response(current_response)
            
            return current_response
    
    class Request:
        def __init__(self, method, path, query_params=None, headers=None, body=None, cookies=None):
            self.method = method
            self.path = path
            self.query_params = query_params or {}
            self.headers = headers or {}
            self.body = body
            self.cookies = cookies or {}
            self.state = RequestState()
    
    class RequestState:
        """A container for request state that can be modified by middleware."""
        pass
    
    class Response:
        def __init__(self, status_code, body=None, headers=None, cookies=None):
            self.status_code = status_code
            self.body = body
            self.headers = headers or {}
            self.cookies = cookies or {}
    
    class Middleware:
        def process_request(self, request):
            return request
            
        def process_response(self, response):
            return response
    
    class SecurityManager:
        def __init__(self, app):
            self.app = app
        
        def jwt_required(self, secret_key, algorithms=None):
            if algorithms is None:
                algorithms = ["HS256"]
                
            def decorator(func):
                def check_jwt(request):
                    auth_header = request.headers.get("Authorization", "")
                    if not auth_header.startswith("Bearer "):
                        return Response(
                            status_code=401,
                            body={"error": "Missing or invalid Authorization header"},
                            headers={"WWW-Authenticate": "Bearer"}
                        )
                    
                    token = auth_header[7:]  # Remove "Bearer " prefix
                    try:
                        import jwt
                        payload = jwt.decode(token, secret_key, algorithms=algorithms)
                        # Store the payload in the request for later use
                        request.state.jwt_payload = payload
                        return None  # Continue processing
                    except Exception as e:
                        return Response(
                            status_code=401,
                            body={"error": f"Invalid token: {str(e)}"},
                            headers={"WWW-Authenticate": "Bearer"}
                        )
                
                if not hasattr(func, '_security_checks'):
                    func._security_checks = []
                func._security_checks.append(check_jwt)
                return func
            return decorator
        
        def api_key_required(self, api_keys, header_name="X-API-Key"):
            if isinstance(api_keys, str):
                api_keys = [api_keys]
                
            def decorator(func):
                def check_api_key(request):
                    api_key = request.headers.get(header_name)
                    if not api_key or api_key not in api_keys:
                        return Response(
                            status_code=401,
                            body={"error": "Missing or invalid API key"}
                        )
                    return None  # Continue processing
                
                if not hasattr(func, '_security_checks'):
                    func._security_checks = []
                func._security_checks.append(check_api_key)
                return func
            return decorator
        
        def basic_auth_required(self, credentials_checker):
            def decorator(func):
                def check_basic_auth(request):
                    auth_header = request.headers.get("Authorization", "")
                    if not auth_header.startswith("Basic "):
                        return Response(
                            status_code=401,
                            body={"error": "Missing or invalid Authorization header"},
                            headers={"WWW-Authenticate": "Basic"}
                        )
                    
                    try:
                        encoded = auth_header[6:]  # Remove "Basic " prefix
                        decoded = base64.b64decode(encoded).decode('utf-8')
                        username, password = decoded.split(':', 1)
                        
                        if not credentials_checker(username, password):
                            raise Exception("Invalid credentials")
                        
                        # Store the username in the request for later use
                        request.state.username = username
                        return None  # Continue processing
                    except Exception as e:
                        return Response(
                            status_code=401,
                            body={"error": f"Authentication failed: {str(e)}"},
                            headers={"WWW-Authenticate": "Basic"}
                        )
                
                if not hasattr(func, '_security_checks'):
                    func._security_checks = []
                func._security_checks.append(check_basic_auth)
                return func
            return decorator

# Fixtures for the tests
@pytest.fixture
def app():
    """Create an API app for testing."""
    return APIApp()

@pytest.fixture
def request_factory():
    """Create a factory for requests."""
    def _request_factory(method="GET", path="/", query_params=None, headers=None, body=None, cookies=None):
        return Request(method, path, query_params, headers, body, cookies)
    return _request_factory

@pytest.fixture
def response_factory():
    """Create a factory for responses."""
    def _response_factory(status_code=200, body=None, headers=None, cookies=None):
        return Response(status_code, body, headers, cookies)
    return _response_factory

@pytest.fixture
def middleware_factory():
    """Create a factory for middleware."""
    def _middleware_factory(process_request_func=None, process_response_func=None):
        class TestMiddleware(Middleware):
            def process_request(self, request):
                if process_request_func:
                    return process_request_func(request)
                return super().process_request(request)
                
            def process_response(self, response):
                if process_response_func:
                    return process_response_func(response)
                return super().process_response(response)
        return TestMiddleware()
    return _middleware_factory

@pytest.fixture
def jwt_token_factory():
    """Create a factory for JWT tokens."""
    def _jwt_token_factory(payload, secret_key, algorithm="HS256"):
        try:
            import jwt
            return jwt.encode(payload, secret_key, algorithm=algorithm)
        except ImportError:
            # Mock JWT for testing
            payload_str = json.dumps(payload)
            encoded = base64.b64encode(payload_str.encode()).decode()
            return f"{encoded}.{secret_key}.{algorithm}"
    return _jwt_token_factory 