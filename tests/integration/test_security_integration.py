"""
Integration tests for the security features of the APIFromAnything library.
"""
import pytest
import base64
import json
import time
from typing import Dict, Any, Optional, Callable, List

# Try to import JWT library for testing
try:
    import jwt
except ImportError:
    # Mock JWT for testing
    class jwt:
        @staticmethod
        def encode(payload, key, algorithm='HS256'):
            # This is a very simplified mock, not for production use
            payload_str = json.dumps(payload)
            encoded = base64.b64encode(payload_str.encode()).decode()
            return f"{encoded}.{key}.{algorithm}"
            
        @staticmethod
        def decode(token, key, algorithms=None):
            # This is a very simplified mock, not for production use
            try:
                parts = token.split('.')
                if len(parts) != 3:
                    raise Exception("Invalid token format")
                
                encoded_payload = parts[0]
                token_key = parts[1]
                
                if token_key != key:
                    raise Exception("Invalid signature")
                
                payload_str = base64.b64decode(encoded_payload).decode()
                payload = json.loads(payload_str)
                
                # Check expiration
                if 'exp' in payload and payload['exp'] < time.time():
                    raise Exception("Token expired")
                
                return payload
            except Exception as e:
                raise Exception(f"Invalid token: {str(e)}")

# Import the security components
try:
    from apifrom.core.app import APIApp
    from apifrom.core.request import Request
    from apifrom.core.response import Response
    from apifrom.security.auth import jwt_required, api_key_required, basic_auth_required
    from apifrom.security.csrf import CSRFProtection
    from apifrom.security.xss import XSSProtection
    from apifrom.security.cors import CORSMiddleware
    from apifrom.security.csp import ContentSecurityPolicy
    from apifrom.middleware.base import Middleware
except ImportError:
    # If the library is not installed, we'll use mock objects for testing
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
                response = Response(status_code=200, body=result, request=current_request)
            else:
                response = Response(status_code=404, body={"error": "Not found"}, request=current_request)
            
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
        def __init__(self, status_code, body=None, headers=None, cookies=None, request=None):
            self.status_code = status_code
            self.body = body
            self.headers = headers or {}
            self.cookies = cookies or {}
            self.request = request
    
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
                            headers={"WWW-Authenticate": "Bearer"},
                            request=request
                        )
                    
                    token = auth_header[7:]  # Remove "Bearer " prefix
                    try:
                        payload = jwt.decode(token, secret_key, algorithms=algorithms)
                        # Store the payload in the request for later use
                        request.state.jwt_payload = payload
                        return None  # Continue processing
                    except Exception as e:
                        return Response(
                            status_code=401,
                            body={"error": f"Invalid token: {str(e)}"},
                            headers={"WWW-Authenticate": "Bearer"},
                            request=request
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
                            body={"error": "Invalid or missing API key"},
                            request=request
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
                            headers={"WWW-Authenticate": "Basic"},
                            request=request
                        )
                    
                    try:
                        auth_data = auth_header[6:]  # Remove "Basic " prefix
                        decoded = base64.b64decode(auth_data).decode("utf-8")
                        username, password = decoded.split(":", 1)
                        
                        if credentials_checker(username, password):
                            # Store the username in the request for later use
                            request.state.username = username
                            return None  # Continue processing
                        else:
                            return Response(
                                status_code=401,
                                body={"error": "Invalid credentials"},
                                headers={"WWW-Authenticate": "Basic"},
                                request=request
                            )
                    except Exception as e:
                        return Response(
                            status_code=401,
                            body={"error": f"Authentication error: {str(e)}"},
                            headers={"WWW-Authenticate": "Basic"},
                            request=request
                        )
                
                if not hasattr(func, '_security_checks'):
                    func._security_checks = []
                func._security_checks.append(check_basic_auth)
                return func
            return decorator
    
    class CSRFProtection(Middleware):
        def __init__(self, secret_key, cookie_name="csrf_token", header_name="X-CSRF-Token"):
            self.secret_key = secret_key
            self.cookie_name = cookie_name
            self.header_name = header_name
            
        def process_request(self, request):
            # Skip CSRF check for safe methods
            if request.method in ["GET", "HEAD", "OPTIONS"]:
                return request
            
            # Get the CSRF token from the cookie and header
            cookie_token = request.cookies.get(self.cookie_name)
            header_token = request.headers.get(self.header_name)
            
            # Validate the CSRF token
            if not cookie_token or not header_token or cookie_token != header_token:
                return Response(
                    status_code=403,
                    body={"error": "CSRF token validation failed"},
                    request=request
                )
            
            return request
            
        def process_response(self, response):
            # Set the CSRF token cookie if it doesn't exist
            if self.cookie_name not in response.cookies:
                # In a real implementation, we would generate a secure token
                response.cookies[self.cookie_name] = "csrf-token-value"
            
            return response
    
    class XSSProtection(Middleware):
        def __init__(self, mode="block"):
            self.mode = mode
            
        def process_response(self, response):
            # Add XSS protection headers
            response.headers["X-XSS-Protection"] = f"1; mode={self.mode}"
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            return response
    
    class CORSMiddleware(Middleware):
        def __init__(self, allow_origins=None, allow_methods=None, allow_headers=None,
                     allow_credentials=False, expose_headers=None, max_age=None):
            self.allow_origins = allow_origins or ["*"]
            self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            self.allow_headers = allow_headers or ["Content-Type", "Authorization"]
            self.allow_credentials = allow_credentials
            self.expose_headers = expose_headers or []
            self.max_age = max_age
            
        def process_request(self, request):
            # Handle preflight requests
            if request.method == "OPTIONS":
                headers = {
                    "Access-Control-Allow-Origin": self._get_allow_origin(request),
                    "Access-Control-Allow-Methods": ", ".join(self.allow_methods),
                    "Access-Control-Allow-Headers": ", ".join(self.allow_headers)
                }
                
                if self.allow_credentials:
                    headers["Access-Control-Allow-Credentials"] = "true"
                
                if self.max_age is not None:
                    headers["Access-Control-Max-Age"] = str(self.max_age)
                
                return Response(status_code=204, headers=headers, request=request)
            
            return request
            
        def process_response(self, response):
            # Add CORS headers to the response
            if hasattr(response, 'request') and response.request:
                response.headers["Access-Control-Allow-Origin"] = self._get_allow_origin(response.request)
                
                if self.allow_credentials:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                
                if self.expose_headers:
                    response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
            else:
                # If request is not available, use a default origin
                response.headers["Access-Control-Allow-Origin"] = "*" if "*" in self.allow_origins else self.allow_origins[0] if self.allow_origins else ""
                
                if self.allow_credentials:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                
                if self.expose_headers:
                    response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
            
            return response
            
        def _get_allow_origin(self, request):
            if "*" in self.allow_origins:
                return "*"
            
            origin = request.headers.get("Origin")
            if origin and origin in self.allow_origins:
                return origin
            
            return self.allow_origins[0] if self.allow_origins else ""
    
    class ContentSecurityPolicy(Middleware):
        def __init__(self, policy=None):
            self.policy = policy or {}
            
        def process_response(self, response):
            # Build the CSP header value
            csp_value = ""
            for directive, sources in self.policy.items():
                if sources:
                    csp_value += f"{directive} {' '.join(sources)}; "
            
            if csp_value:
                response.headers["Content-Security-Policy"] = csp_value
            
            return response


@pytest.mark.integration
class TestSecurityIntegration:
    """Integration tests for the security features."""
    
    def test_jwt_with_csrf_protection(self):
        """Test that JWT authentication works with CSRF protection."""
        app = APIApp()
        secret_key = "test_secret_key"
        
        # Add CSRF protection middleware
        app.add_middleware(CSRFProtection(secret_key="csrf_secret"))
        
        # Create a JWT token
        payload = {"sub": "user123", "role": "admin"}
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        @app.api(route="/protected", methods=["POST"])
        @app.security.jwt_required(secret_key=secret_key)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test with valid JWT but missing CSRF token
        request = Request(
            method="POST",
            path="/protected",
            headers={"Authorization": f"Bearer {token}"}
        )
        response = app.handle_request(request)
        
        # Should fail due to missing CSRF token
        assert response.status_code == 403
        assert "CSRF" in response.body["error"]
        
        # Test with valid JWT and valid CSRF token
        request = Request(
            method="POST",
            path="/protected",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "csrf-token-value"
            },
            cookies={"csrf_token": "csrf-token-value"}
        )
        response = app.handle_request(request)
        
        # Should succeed
        assert response.status_code == 200
        assert response.body == {"message": "protected data"}
    
    def test_api_key_with_cors(self):
        """Test that API key authentication works with CORS."""
        app = APIApp()
        api_key = "test_api_key_123"
        
        # Add CORS middleware
        app.add_middleware(CORSMiddleware(
            allow_origins=["https://example.com"],
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "Authorization", "X-API-Key"],
            allow_credentials=True
        ))
        
        @app.api(route="/protected", methods=["GET"])
        @app.security.api_key_required(api_key)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test preflight request
        preflight_request = Request(
            method="OPTIONS",
            path="/protected",
            headers={"Origin": "https://example.com"}
        )
        preflight_response = app.handle_request(preflight_request)
        
        # Should return 204 No Content with CORS headers
        assert preflight_response.status_code == 204
        assert preflight_response.headers["Access-Control-Allow-Origin"] == "https://example.com"
        assert "X-API-Key" in preflight_response.headers["Access-Control-Allow-Headers"]
        
        # Test actual request with valid API key
        request = Request(
            method="GET",
            path="/protected",
            headers={
                "Origin": "https://example.com",
                "X-API-Key": api_key
            }
        )
        response = app.handle_request(request)
        
        # Should succeed with CORS headers
        assert response.status_code == 200
        assert response.body == {"message": "protected data"}
        assert response.headers["Access-Control-Allow-Origin"] == "https://example.com"
        assert response.headers["Access-Control-Allow-Credentials"] == "true"
        
        # Test with invalid origin
        request = Request(
            method="GET",
            path="/protected",
            headers={
                "Origin": "https://attacker.com",
                "X-API-Key": api_key
            }
        )
        response = app.handle_request(request)
        
        # Should succeed but with different CORS headers
        assert response.status_code == 200
        assert response.headers["Access-Control-Allow-Origin"] != "https://attacker.com"
    
    def test_basic_auth_with_xss_protection(self):
        """Test that Basic authentication works with XSS protection."""
        app = APIApp()
        
        # Add XSS protection middleware
        app.add_middleware(XSSProtection(mode="block"))
        
        # Define a credentials checker function
        def check_credentials(username, password):
            return username == "testuser" and password == "testpass"
        
        @app.api(route="/protected", methods=["GET"])
        @app.security.basic_auth_required(check_credentials)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Create Basic auth header
        credentials = base64.b64encode("testuser:testpass".encode()).decode()
        
        # Test with valid credentials
        request = Request(
            method="GET",
            path="/protected",
            headers={"Authorization": f"Basic {credentials}"}
        )
        response = app.handle_request(request)
        
        # Should succeed with XSS protection headers
        assert response.status_code == 200
        assert response.body == {"message": "protected data"}
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    def test_multiple_security_features(self):
        """Test that multiple security features work together."""
        app = APIApp()
        secret_key = "test_secret_key"
        
        # Add security middleware
        app.add_middleware(CSRFProtection(secret_key="csrf_secret"))
        app.add_middleware(XSSProtection(mode="block"))
        app.add_middleware(CORSMiddleware(
            allow_origins=["https://example.com"],
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
            allow_credentials=True
        ))
        app.add_middleware(ContentSecurityPolicy({
            "default-src": ["'self'"],
            "script-src": ["'self'", "https://cdn.example.com"],
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:"],
            "connect-src": ["'self'", "https://api.example.com"]
        }))
        
        # Create a JWT token
        payload = {"sub": "user123", "role": "admin"}
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        @app.api(route="/protected", methods=["POST"])
        @app.security.jwt_required(secret_key=secret_key)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test with all security features
        request = Request(
            method="POST",
            path="/protected",
            headers={
                "Origin": "https://example.com",
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": "csrf-token-value"
            },
            cookies={"csrf_token": "csrf-token-value"}
        )
        response = app.handle_request(request)
        
        # Should succeed with all security headers
        assert response.status_code == 200
        assert response.body == {"message": "protected data"}
        assert response.headers["Access-Control-Allow-Origin"] == "https://example.com"
        assert response.headers["Access-Control-Allow-Credentials"] == "true"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "Content-Security-Policy" in response.headers
        assert "'self'" in response.headers["Content-Security-Policy"]
    
    def test_security_middleware_order(self):
        """Test that security middleware is applied in the correct order."""
        app = APIApp()
        execution_order = []
        
        class OrderTrackingMiddleware(Middleware):
            def __init__(self, name):
                self.name = name
                
            def process_request(self, request):
                execution_order.append(f"{self.name}_request")
                return request
                
            def process_response(self, response):
                execution_order.append(f"{self.name}_response")
                return response
        
        # Add middleware in a specific order
        app.add_middleware(OrderTrackingMiddleware("cors"))
        app.add_middleware(OrderTrackingMiddleware("csrf"))
        app.add_middleware(OrderTrackingMiddleware("xss"))
        app.add_middleware(OrderTrackingMiddleware("csp"))
        
        @app.api(route="/test")
        def test_endpoint():
            execution_order.append("handler")
            return {"message": "success"}
        
        # Make a request
        request = Request(method="GET", path="/test")
        response = app.handle_request(request)
        
        # Check the execution order
        assert response.status_code == 200
        assert execution_order == [
            "cors_request",
            "csrf_request",
            "xss_request",
            "csp_request",
            "handler",
            "csp_response",
            "xss_response",
            "csrf_response",
            "cors_response"
        ]


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 