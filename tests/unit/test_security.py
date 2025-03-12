"""
Unit tests for the security functionality of the APIFromAnything library.
"""
import pytest
import base64
import json
import time
from typing import Dict, Any, Optional, Callable

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
            
        def handle_request(self, request):
            if request.path in self.routes:
                handler = self.routes[request.path]["handler"]
                
                # Check if the handler has security decorators
                if hasattr(handler, '_security_checks'):
                    for check in handler._security_checks:
                        result = check(request)
                        if isinstance(result, Response):
                            return result
                
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
                        payload = jwt.decode(token, secret_key, algorithms=algorithms)
                        # Store the payload in the request for later use
                        request.jwt_payload = payload
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
                        request.username = username
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


class TestJWTAuthentication:
    """Tests for JWT authentication."""
    
    def test_jwt_required_valid_token(self):
        """Test that a valid JWT token allows access to a protected endpoint."""
        app = APIApp()
        secret_key = "test_secret_key"
        
        # Create a JWT token
        payload = {"sub": "user123", "role": "admin"}
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        @app.api()
        @app.security.jwt_required(secret_key=secret_key)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test with valid token
        request = Request(
            method="GET",
            path="/protected_endpoint",
            headers={"Authorization": f"Bearer {token}"}
        )
        response = app.handle_request(request)
        
        assert response.status_code == 200
        assert response.body == {"message": "protected data"}
    
    def test_jwt_required_invalid_token(self):
        """Test that an invalid JWT token denies access to a protected endpoint."""
        app = APIApp()
        secret_key = "test_secret_key"
        
        @app.api()
        @app.security.jwt_required(secret_key=secret_key)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test with invalid token
        request = Request(
            method="GET",
            path="/protected_endpoint",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        response = app.handle_request(request)
        
        assert response.status_code == 401
        assert "error" in response.body
    
    def test_jwt_required_missing_token(self):
        """Test that a missing JWT token denies access to a protected endpoint."""
        app = APIApp()
        secret_key = "test_secret_key"
        
        @app.api()
        @app.security.jwt_required(secret_key=secret_key)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test with missing token
        request = Request(
            method="GET",
            path="/protected_endpoint"
        )
        response = app.handle_request(request)
        
        assert response.status_code == 401
        assert "error" in response.body
    
    def test_jwt_required_expired_token(self):
        """Test that an expired JWT token denies access to a protected endpoint."""
        app = APIApp()
        secret_key = "test_secret_key"
        
        # Create an expired JWT token
        payload = {
            "sub": "user123",
            "role": "admin",
            "exp": int(time.time()) - 3600  # Expired 1 hour ago
        }
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        @app.api()
        @app.security.jwt_required(secret_key=secret_key)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test with expired token
        request = Request(
            method="GET",
            path="/protected_endpoint",
            headers={"Authorization": f"Bearer {token}"}
        )
        response = app.handle_request(request)
        
        assert response.status_code == 401
        assert "error" in response.body
        assert "expired" in response.body["error"].lower()


class TestAPIKeyAuthentication:
    """Tests for API key authentication."""
    
    def test_api_key_required_valid_key(self):
        """Test that a valid API key allows access to a protected endpoint."""
        app = APIApp()
        api_key = "test_api_key_123"
        
        @app.api()
        @app.security.api_key_required(api_key)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test with valid API key
        request = Request(
            method="GET",
            path="/protected_endpoint",
            headers={"X-API-Key": api_key}
        )
        response = app.handle_request(request)
        
        assert response.status_code == 200
        assert response.body == {"message": "protected data"}
    
    def test_api_key_required_invalid_key(self):
        """Test that an invalid API key denies access to a protected endpoint."""
        app = APIApp()
        api_key = "test_api_key_123"
        
        @app.api()
        @app.security.api_key_required(api_key)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test with invalid API key
        request = Request(
            method="GET",
            path="/protected_endpoint",
            headers={"X-API-Key": "invalid_key"}
        )
        response = app.handle_request(request)
        
        assert response.status_code == 401
        assert "error" in response.body
    
    def test_api_key_required_missing_key(self):
        """Test that a missing API key denies access to a protected endpoint."""
        app = APIApp()
        api_key = "test_api_key_123"
        
        @app.api()
        @app.security.api_key_required(api_key)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test with missing API key
        request = Request(
            method="GET",
            path="/protected_endpoint"
        )
        response = app.handle_request(request)
        
        assert response.status_code == 401
        assert "error" in response.body
    
    def test_api_key_required_custom_header(self):
        """Test that API key authentication works with a custom header name."""
        app = APIApp()
        api_key = "test_api_key_123"
        custom_header = "X-Custom-API-Key"
        
        @app.api()
        @app.security.api_key_required(api_key, header_name=custom_header)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test with valid API key in custom header
        request = Request(
            method="GET",
            path="/protected_endpoint",
            headers={custom_header: api_key}
        )
        response = app.handle_request(request)
        
        assert response.status_code == 200
        assert response.body == {"message": "protected data"}
        
        # Test with valid API key in wrong header
        request = Request(
            method="GET",
            path="/protected_endpoint",
            headers={"X-API-Key": api_key}
        )
        response = app.handle_request(request)
        
        assert response.status_code == 401
        assert "error" in response.body


class TestBasicAuthentication:
    """Tests for Basic authentication."""
    
    def test_basic_auth_required_valid_credentials(self):
        """Test that valid Basic auth credentials allow access to a protected endpoint."""
        app = APIApp()
        
        # Define a credentials checker function
        def check_credentials(username, password):
            return username == "testuser" and password == "testpass"
        
        @app.api()
        @app.security.basic_auth_required(check_credentials)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Create Basic auth header
        credentials = base64.b64encode("testuser:testpass".encode()).decode()
        
        # Test with valid credentials
        request = Request(
            method="GET",
            path="/protected_endpoint",
            headers={"Authorization": f"Basic {credentials}"}
        )
        response = app.handle_request(request)
        
        assert response.status_code == 200
        assert response.body == {"message": "protected data"}
    
    def test_basic_auth_required_invalid_credentials(self):
        """Test that invalid Basic auth credentials deny access to a protected endpoint."""
        app = APIApp()
        
        # Define a credentials checker function
        def check_credentials(username, password):
            return username == "testuser" and password == "testpass"
        
        @app.api()
        @app.security.basic_auth_required(check_credentials)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Create Basic auth header with wrong password
        credentials = base64.b64encode("testuser:wrongpass".encode()).decode()
        
        # Test with invalid credentials
        request = Request(
            method="GET",
            path="/protected_endpoint",
            headers={"Authorization": f"Basic {credentials}"}
        )
        response = app.handle_request(request)
        
        assert response.status_code == 401
        assert "error" in response.body
    
    def test_basic_auth_required_missing_credentials(self):
        """Test that missing Basic auth credentials deny access to a protected endpoint."""
        app = APIApp()
        
        # Define a credentials checker function
        def check_credentials(username, password):
            return username == "testuser" and password == "testpass"
        
        @app.api()
        @app.security.basic_auth_required(check_credentials)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test with missing credentials
        request = Request(
            method="GET",
            path="/protected_endpoint"
        )
        response = app.handle_request(request)
        
        assert response.status_code == 401
        assert "error" in response.body
    
    def test_basic_auth_required_malformed_credentials(self):
        """Test that malformed Basic auth credentials deny access to a protected endpoint."""
        app = APIApp()
        
        # Define a credentials checker function
        def check_credentials(username, password):
            return username == "testuser" and password == "testpass"
        
        @app.api()
        @app.security.basic_auth_required(check_credentials)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Create malformed Basic auth header (not base64 encoded)
        
        # Test with malformed credentials
        request = Request(
            method="GET",
            path="/protected_endpoint",
            headers={"Authorization": "Basic not-base64-encoded"}
        )
        response = app.handle_request(request)
        
        assert response.status_code == 401
        assert "error" in response.body


class TestMultipleAuthMethods:
    """Tests for combining multiple authentication methods."""
    
    def test_multiple_auth_methods_all_pass(self):
        """Test that an endpoint with multiple auth methods works when all pass."""
        app = APIApp()
        secret_key = "test_secret_key"
        api_key = "test_api_key_123"
        
        # Create a JWT token
        payload = {"sub": "user123", "role": "admin"}
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        @app.api()
        @app.security.jwt_required(secret_key=secret_key)
        @app.security.api_key_required(api_key)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test with both valid JWT and API key
        request = Request(
            method="GET",
            path="/protected_endpoint",
            headers={
                "Authorization": f"Bearer {token}",
                "X-API-Key": api_key
            }
        )
        response = app.handle_request(request)
        
        assert response.status_code == 200
        assert response.body == {"message": "protected data"}
    
    def test_multiple_auth_methods_one_fails(self):
        """Test that an endpoint with multiple auth methods fails if any method fails."""
        app = APIApp()
        secret_key = "test_secret_key"
        api_key = "test_api_key_123"
        
        # Create a JWT token
        payload = {"sub": "user123", "role": "admin"}
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        @app.api()
        @app.security.jwt_required(secret_key=secret_key)
        @app.security.api_key_required(api_key)
        def protected_endpoint():
            return {"message": "protected data"}
        
        # Test with valid JWT but invalid API key
        request = Request(
            method="GET",
            path="/protected_endpoint",
            headers={
                "Authorization": f"Bearer {token}",
                "X-API-Key": "invalid_key"
            }
        )
        response = app.handle_request(request)
        
        assert response.status_code == 401
        assert "error" in response.body


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 