"""
Tests for the CSRF protection functionality of the APIFromAnything library.
"""

import pytest
import time
import json
from typing import Dict, Optional

from apifrom.security.csrf import CSRFToken, CSRFMiddleware, csrf_exempt
from tests.middleware_test_helper import MockRequest, MockResponse, AsyncMiddlewareTester


class TestCSRFToken:
    """
    Tests for the CSRFToken class.
    """
    
    def setup_method(self):
        """
        Set up the test environment.
        """
        self.csrf_token = CSRFToken(secret="test-secret")
    
    def test_generate_token(self):
        """
        Test generating a CSRF token.
        """
        token = self.csrf_token.generate_token()
        
        # Check that the token is a string
        assert isinstance(token, str)
        
        # Check that the token has the correct format
        parts = token.split(":")
        assert len(parts) == 3  # random_token:timestamp:signature
    
    def test_generate_token_with_session(self):
        """
        Test generating a CSRF token with a session ID.
        """
        token = self.csrf_token.generate_token(session_id="test-session")
        
        # Check that the token is a string
        assert isinstance(token, str)
        
        # Check that the token has the correct format
        parts = token.split(":")
        assert len(parts) == 4  # random_token:timestamp:session_id:signature
    
    def test_validate_token(self):
        """
        Test validating a CSRF token.
        """
        token = self.csrf_token.generate_token()
        result = self.csrf_token.validate_token(token)
        
        assert result is True
    
    def test_validate_token_with_session(self):
        """
        Test validating a CSRF token with a session ID.
        """
        token = self.csrf_token.generate_token(session_id="test-session")
        result = self.csrf_token.validate_token(token, session_id="test-session")
        
        assert result is True
    
    def test_validate_expired_token(self):
        """
        Test validating an expired CSRF token.
        """
        # Create a token with a short expiration time
        csrf_token = CSRFToken(secret="test-secret", max_age=1)
        token = csrf_token.generate_token()
        
        # Wait for the token to expire
        time.sleep(2)
        
        # Check that the token is invalid
        assert csrf_token.validate_token(token) is False
    
    def test_validate_invalid_token(self):
        """
        Test validating an invalid CSRF token.
        """
        # Test with an invalid token format
        result = self.csrf_token.validate_token("invalid-token")
        assert result is False
        
        # Test with a token that has an invalid signature
        token_parts = ["random", str(int(time.time())), "invalid-signature"]
        token = ":".join(token_parts)
        result = self.csrf_token.validate_token(token)
        assert result is False


@pytest.fixture
def csrf_middleware():
    """
    Fixture for creating a CSRFMiddleware instance.
    """
    return CSRFMiddleware(secret="test-secret")


@pytest.fixture
def csrf_middleware_with_exempt_routes():
    """
    Fixture for creating a CSRFMiddleware instance with exempt routes.
    """
    return CSRFMiddleware(
        secret="test-secret",
        exempt_routes=["/exempt"],
    )


@pytest.fixture
async def next_middleware():
    """
    Fixture for creating a mock next middleware function.
    """
    async def _next_middleware(request):
        """
        Mock next middleware function.
        
        Args:
            request: The request object
            
        Returns:
            Response: A mock response
        """
        return MockResponse(status_code=200, body={"success": True})
    
    return _next_middleware


class TestCSRFMiddlewareAsync:
    """
    Tests for the CSRFMiddleware class using AsyncMiddlewareTester.
    """
    
    @pytest.mark.asyncio
    async def test_exempt_get_request(self, csrf_middleware):
        """
        Test that GET requests are exempt from CSRF protection.
        """
        request = MockRequest(method="GET", path="/")
        
        # Add the attributes that CSRFMiddleware expects
        request.body = {}
        request.json = {}
        request.form = {}
        request.state = type('obj', (object,), {})  # Create a state object
        
        # Create a response with the request attribute
        response = MockResponse()
        response.request = request
        
        # Test the middleware
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [csrf_middleware], 
            response,
            request
        )
        
        assert response.status_code == 200
        assert "csrf_token=" in response.headers.get("Set-Cookie", "")
    
    @pytest.mark.asyncio
    async def test_exempt_route(self, csrf_middleware_with_exempt_routes):
        """
        Test that exempt routes are not protected.
        """
        # Create a POST request to an exempt route
        request = MockRequest(method="POST", path="/exempt")
        
        # Add the attributes that CSRFMiddleware expects
        request.body = {}
        request.json = {}
        request.form = {}
        request.state = type('obj', (object,), {})  # Create a state object
        
        # Create a response with the request attribute
        response = MockResponse()
        response.request = request
        
        # Test the middleware
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [csrf_middleware_with_exempt_routes], 
            response,
            request
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_protected_request_without_token(self, csrf_middleware):
        """
        Test that protected requests without a token are rejected.
        """
        request = MockRequest(method="POST", path="/")
        
        # Add the attributes that CSRFMiddleware expects
        request.body = {}
        request.json = {}
        request.form = {}
        request.state = type('obj', (object,), {})  # Create a state object
        
        # Create a response with the request attribute
        response = MockResponse()
        response.request = request
        
        # Test the middleware
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [csrf_middleware], 
            response,
            request
        )
        
        assert response.status_code == 403
        
        # Check the error message in the response body
        if isinstance(response.body, bytes):
            body_dict = json.loads(response.body.decode('utf-8'))
            assert "CSRF token" in body_dict.get("error", "")
        else:
            assert "CSRF token" in str(response.body.get("error", ""))
    
    @pytest.mark.asyncio
    async def test_protected_request_with_valid_token(self, csrf_middleware):
        """
        Test that protected requests with a valid token are allowed.
        """
        # Generate a valid token
        token = csrf_middleware._generate_token()
        
        # Create a request with the token in the header
        request = MockRequest(
            method="POST",
            path="/",
            headers={"X-CSRF-Token": token}
        )
        
        # Add the attributes that CSRFMiddleware expects
        request.body = {}
        request.json = {}
        request.form = {}
        request.state = type('obj', (object,), {})  # Create a state object
        
        # Create a response with the request attribute
        response = MockResponse()
        response.request = request
        
        # Test the middleware
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [csrf_middleware], 
            response,
            request
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_protected_request_with_invalid_token(self, csrf_middleware):
        """
        Test that protected requests with an invalid token are rejected.
        """
        # Create a request with an invalid token
        request = MockRequest(
            method="POST",
            path="/",
            headers={"X-CSRF-Token": "invalid-token"}
        )
        
        # Add the attributes that CSRFMiddleware expects
        request.body = {}
        request.json = {}
        request.form = {}
        request.state = type('obj', (object,), {})  # Create a state object
        
        # Create a response with the request attribute
        response = MockResponse()
        response.request = request
        
        # Test the middleware
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [csrf_middleware], 
            response,
            request
        )
        
        assert response.status_code == 403
        
        # Check the error message in the response body
        if isinstance(response.body, bytes):
            body_dict = json.loads(response.body.decode('utf-8'))
            assert "CSRF token" in body_dict.get("error", "")
        else:
            assert "CSRF token" in str(response.body.get("error", ""))
    
    @pytest.mark.asyncio
    async def test_token_in_json(self, csrf_middleware):
        """
        Test that CSRF tokens can be provided in the request body.
        """
        # Generate a valid token
        token = csrf_middleware._generate_token()
        
        # Create a request with the token in the JSON body
        request = MockRequest(
            method="POST",
            path="/"
        )
        
        # Add the attributes that CSRFMiddleware expects
        request.body = {}
        request.json = {"csrf_token": token}
        request.form = {}
        request.state = type('obj', (object,), {})  # Create a state object
        
        # Create a response with the request attribute
        response = MockResponse()
        response.request = request
        
        # Test the middleware
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [csrf_middleware], 
            response,
            request
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_token_in_query_params(self, csrf_middleware):
        """
        Test that CSRF tokens can be provided in query parameters.
        """
        # Generate a valid token
        token = csrf_middleware._generate_token()
        
        # Create a request with the token in the query parameters
        request = MockRequest(
            method="POST",
            path="/",
            query_params={"csrf_token": token}
        )
        
        # Add the attributes that CSRFMiddleware expects
        request.body = {}
        request.json = {}
        request.form = {}
        request.state = type('obj', (object,), {})  # Create a state object
        
        # Create a response with the request attribute
        response = MockResponse()
        response.request = request
        
        # Test the middleware
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [csrf_middleware], 
            response,
            request
        )
        
        assert response.status_code == 200


def test_csrf_exempt():
    """
    Test the csrf_exempt decorator.
    """
    @csrf_exempt
    def test_function():
        return "test"
    
    assert hasattr(test_function, "_csrf_exempt")
    assert test_function._csrf_exempt is True 