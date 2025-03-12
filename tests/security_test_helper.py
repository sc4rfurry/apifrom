"""
Helper module for security testing.
This module provides utilities for testing security components with proper async support.
"""
import asyncio
import json
import base64
import hmac
import hashlib
import time
from typing import Dict, Any, Optional, Callable, Awaitable, List, Union

from tests.middleware_test_helper import MockRequest, MockResponse

class SecurityTestHelper:
    """
    A utility for testing security components.
    """
    
    @staticmethod
    def create_jwt(payload: Dict[str, Any], secret: str, algorithm: str = "HS256") -> str:
        """
        Create a JWT token for testing.
        
        Args:
            payload: The JWT payload
            secret: The secret key
            algorithm: The signing algorithm
            
        Returns:
            A JWT token
        """
        # Create the JWT header
        header = {
            "alg": algorithm,
            "typ": "JWT"
        }
        
        # Encode the header and payload
        header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        
        # Create the signature
        message = f"{header_encoded}.{payload_encoded}"
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip("=")
        
        # Return the complete JWT
        return f"{header_encoded}.{payload_encoded}.{signature_encoded}"
    
    @staticmethod
    def create_basic_auth(username: str, password: str) -> str:
        """
        Create a Basic Auth header value for testing.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            A Basic Auth header value
        """
        auth_string = f"{username}:{password}"
        auth_bytes = auth_string.encode()
        encoded = base64.b64encode(auth_bytes).decode()
        return f"Basic {encoded}"
    
    @staticmethod
    def create_api_key_header(api_key: str) -> Dict[str, str]:
        """
        Create an API key header for testing.
        
        Args:
            api_key: The API key
            
        Returns:
            A header dictionary with the API key
        """
        return {"X-API-Key": api_key}
    
    @staticmethod
    def create_csrf_token() -> str:
        """
        Create a CSRF token for testing.
        
        Returns:
            A CSRF token
        """
        # Create a simple token based on the current time
        token_data = str(time.time()).encode()
        return base64.urlsafe_b64encode(token_data).decode()
    
    @staticmethod
    async def test_jwt_auth(handler: Callable, request: Optional[MockRequest] = None, 
                           payload: Optional[Dict[str, Any]] = None, 
                           secret: str = "test-secret", algorithm: str = "HS256") -> MockResponse:
        """
        Test a JWT-protected handler.
        
        Args:
            handler: The handler function to test
            request: A mock request object (created if not provided)
            payload: The JWT payload (created if not provided)
            secret: The JWT secret
            algorithm: The JWT algorithm
            
        Returns:
            The response from the handler
        """
        if request is None:
            request = MockRequest()
            
        if payload is None:
            payload = {
                "sub": "test-user",
                "exp": int(time.time()) + 3600,
                "iat": int(time.time())
            }
            
        # Create the JWT token
        token = SecurityTestHelper.create_jwt(payload, secret, algorithm)
        
        # Add the token to the request
        request.headers["Authorization"] = f"Bearer {token}"
        
        # Call the handler
        if asyncio.iscoroutinefunction(handler):
            return await handler(request)
        else:
            return handler(request)
    
    @staticmethod
    async def test_api_key_auth(handler: Callable, request: Optional[MockRequest] = None,
                               api_key: str = "test-key") -> MockResponse:
        """
        Test an API key-protected handler.
        
        Args:
            handler: The handler function to test
            request: A mock request object (created if not provided)
            api_key: The API key to use
            
        Returns:
            The response from the handler
        """
        if request is None:
            request = MockRequest()
            
        # Add the API key to the request
        request.headers["X-API-Key"] = api_key
        
        # Call the handler
        if asyncio.iscoroutinefunction(handler):
            return await handler(request)
        else:
            return handler(request)
    
    @staticmethod
    async def test_basic_auth(handler: Callable, request: Optional[MockRequest] = None,
                             username: str = "test-user", password: str = "test-password") -> MockResponse:
        """
        Test a Basic Auth-protected handler.
        
        Args:
            handler: The handler function to test
            request: A mock request object (created if not provided)
            username: The username to use
            password: The password to use
            
        Returns:
            The response from the handler
        """
        if request is None:
            request = MockRequest()
            
        # Add the Basic Auth header to the request
        auth_header = SecurityTestHelper.create_basic_auth(username, password)
        request.headers["Authorization"] = auth_header
        
        # Call the handler
        if asyncio.iscoroutinefunction(handler):
            return await handler(request)
        else:
            return handler(request)
    
    @staticmethod
    async def test_csrf_protection(handler: Callable, request: Optional[MockRequest] = None,
                                  token: Optional[str] = None, include_token: bool = True) -> MockResponse:
        """
        Test a CSRF-protected handler.
        
        Args:
            handler: The handler function to test
            request: A mock request object (created if not provided)
            token: The CSRF token to use (created if not provided)
            include_token: Whether to include the token in the request
            
        Returns:
            The response from the handler
        """
        if request is None:
            request = MockRequest(method="POST")
            
        if token is None:
            token = SecurityTestHelper.create_csrf_token()
            
        # Add the CSRF token to the request if needed
        if include_token:
            request.headers["X-CSRF-Token"] = token
            
        # Call the handler
        if asyncio.iscoroutinefunction(handler):
            return await handler(request)
        else:
            return handler(request) 