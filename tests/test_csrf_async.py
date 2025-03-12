"""
Tests for the CSRF protection functionality using AsyncMiddlewareTester.
"""

import pytest
import time
from typing import Dict, Optional

from apifrom.security.csrf import CSRFToken, CSRFMiddleware, csrf_exempt
from tests.middleware_test_helper import MockRequest, MockResponse, AsyncMiddlewareTester


@pytest.fixture
def csrf_token():
    """
    Fixture for creating a CSRFToken instance.
    """
    return CSRFToken(secret="test-secret")


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


class TestCSRFTokenGeneration:
    """
    Tests for the CSRFToken class.
    """
    
    def test_generate_token(self, csrf_token):
        """
        Test generating a CSRF token.
        """
        token = csrf_token.generate_token()
        
        # Check that the token is a string
        assert isinstance(token, str)
        
        # Check that the token has the correct format
        parts = token.split(":")
        assert len(parts) == 3  # random_token:timestamp:signature
    
    def test_generate_token_with_session(self, csrf_token):
        """
        Test generating a CSRF token with a session ID.
        """
        token = csrf_token.generate_token(session_id="test-session")
        
        # Check that the token is a string
        assert isinstance(token, str)
        
        # Check that the token has the correct format
        parts = token.split(":")
        assert len(parts) == 4  # random_token:timestamp:session_id:signature
    
    def test_validate_token(self, csrf_token):
        """
        Test validating a CSRF token.
        """
        token = csrf_token.generate_token()
        
        # Check that the token is valid
        assert csrf_token.validate_token(token)
    
    def test_validate_token_with_session(self, csrf_token):
        """
        Test validating a CSRF token with a session ID.
        """
        token = csrf_token.generate_token(session_id="test-session")
        
        # Check that the token is valid with the correct session ID
        assert csrf_token.validate_token(token, session_id="test-session")
        
        # Check that the token is invalid with an incorrect session ID
        assert not csrf_token.validate_token(token, session_id="wrong-session")
    
    def test_validate_expired_token(self, csrf_token):
        """
        Test validating an expired CSRF token.
        """
        # Create a token with a timestamp from the past (older than the default max_age)
        # The default max_age is 3600 seconds (1 hour), so we'll use a timestamp from 2 hours ago
        timestamp = int(time.time()) - 7200  # 2 hours ago
        random_token = "random"
        signature = csrf_token._create_signature(f"{random_token}:{timestamp}")
        token = f"{random_token}:{timestamp}:{signature}"
        
        # Check that the token is invalid due to expiration
        assert not csrf_token.validate_token(token)
    
    def test_validate_invalid_token(self, csrf_token):
        """
        Test validating an invalid CSRF token.
        """
        # Create a token with an invalid signature
        timestamp = int(time.time())
        random_token = "random"
        token = f"{random_token}:{timestamp}:invalid-signature"
        
        # Check that the token is invalid
        assert not csrf_token.validate_token(token)


class TestCSRFMiddlewareAsync:
    """
    Tests for the CSRFMiddleware class.
    """
    
    @pytest.mark.asyncio
    async def test_exempt_get_request(self, csrf_middleware):
        """
        Test that GET requests are exempt from CSRF protection.
        """
        request = MockRequest(method="GET", path="/test")
        
        # Add the attributes that CSRFMiddleware expects
        request.body = {}
        request.json = {}
        request.form = {}
        request.state = type('obj', (object,), {})  # Create a state object
        
        # Create a response with the request attribute
        response = MockResponse()
        response.request = request
        
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response([csrf_middleware], 
                                                                                  response, 
                                                                                  request)
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Check that a CSRF token cookie is set
        assert "Set-Cookie" in response.headers
        assert "csrf_token=" in response.headers["Set-Cookie"]
    
    @pytest.mark.asyncio
    async def test_exempt_route(self, csrf_middleware_with_exempt_routes):
        """
        Test that exempt routes are not protected.
        """
        request = MockRequest(method="POST", path="/exempt")
        
        # Add the attributes that CSRFMiddleware expects
        request.body = {}
        request.json = {}
        request.form = {}
        request.state = type('obj', (object,), {})  # Create a state object
        
        # Create a response with the request attribute
        response = MockResponse()
        response.request = request
        
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [csrf_middleware_with_exempt_routes], 
            response,
            request
        )
        
        # Check that the response is successful
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_protected_request_without_token(self, csrf_middleware):
        """
        Test that protected requests without a token are rejected.
        """
        request = MockRequest(method="POST", path="/test")
        
        # Add the attributes that CSRFMiddleware expects
        request.body = {}
        request.json = {}
        request.form = {}
        request.state = type('obj', (object,), {})  # Create a state object
        
        # Create a response with the request attribute
        response = MockResponse()
        response.request = request
        
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [csrf_middleware], 
            response,
            request
        )
        
        # Check that the response is a 403 Forbidden
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_protected_request_with_valid_token(self, csrf_middleware):
        """
        Test that protected requests with a valid token are allowed.
        """
        # Generate a token using the middleware's _generate_token method
        token = csrf_middleware._generate_token()
        print(f"Generated token: {token}")
        
        # Create a request with the token in the header
        # The MockRequest needs to be adapted to work with the CSRFMiddleware
        request = MockRequest(
            method="POST",
            path="/test",
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
        
        # Debug: Print the request headers to verify the token is set correctly
        print(f"Request headers: {request.headers}")
        print(f"Header name in middleware: {csrf_middleware.header_name}")
        
        # Debug: Check if the token is being extracted correctly
        token_from_request = csrf_middleware._get_token_from_request(request)
        print(f"Token extracted from request: {token_from_request}")
        
        # Debug: Check if the token is being validated correctly
        is_valid = csrf_middleware._validate_token(token_from_request) if token_from_request else False
        print(f"Is token valid: {is_valid}")
        
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [csrf_middleware], 
            response,
            request
        )
        
        # Debug: Print the response status code
        print(f"Response status code: {response.status_code}")
        if hasattr(response, 'body'):
            print(f"Response body: {response.body}")
        
        # Check that the response is successful
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_protected_request_with_invalid_token(self, csrf_middleware):
        """
        Test that protected requests with an invalid token are rejected.
        """
        request = MockRequest(
            method="POST",
            path="/test",
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
        
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [csrf_middleware], 
            response,
            request
        )
        
        # Check that the response is a 403 Forbidden
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_token_in_json(self, csrf_middleware):
        """
        Test that CSRF tokens can be provided in the request body.
        """
        # Generate a token using the middleware's _generate_token method
        token = csrf_middleware._generate_token()
        print(f"Generated token for JSON: {token}")
        
        request = MockRequest(
            method="POST",
            path="/test"
        )
        
        # Add the json attribute with the token
        request.json = {"csrf_token": token}
        
        # Add other attributes that CSRFMiddleware expects
        request.body = {}
        request.form = {}
        request.state = type('obj', (object,), {})  # Create a state object
        
        # Create a response with the request attribute
        response = MockResponse()
        response.request = request
        
        # Debug: Check if the token is being extracted correctly
        token_from_request = csrf_middleware._get_token_from_request(request)
        print(f"Token extracted from JSON: {token_from_request}")
        
        # Debug: Check if the token is being validated correctly
        is_valid = csrf_middleware._validate_token(token_from_request) if token_from_request else False
        print(f"Is token valid: {is_valid}")
        
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [csrf_middleware], 
            response,
            request
        )
        
        # Debug: Print the response status code
        print(f"Response status code: {response.status_code}")
        
        # Check that the response is successful
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_token_in_query_params(self, csrf_middleware):
        """
        Test that CSRF tokens can be provided in query parameters.
        """
        # Generate a token using the middleware's _generate_token method
        token = csrf_middleware._generate_token()
        print(f"Generated token for query params: {token}")
        
        request = MockRequest(
            method="POST",
            path="/test",
            query_params={"csrf_token": token}
        )
        
        # Add other attributes that CSRFMiddleware expects
        request.body = {}
        request.json = {}
        request.form = {}
        request.state = type('obj', (object,), {})  # Create a state object
        
        # Create a response with the request attribute
        response = MockResponse()
        response.request = request
        
        # Debug: Check if the token is being extracted correctly
        token_from_request = csrf_middleware._get_token_from_request(request)
        print(f"Token extracted from query params: {token_from_request}")
        print(f"Query params: {request.query_params}")
        print(f"Token name in middleware: {csrf_middleware.token_name}")
        
        # Debug: Check if the token is being validated correctly
        is_valid = csrf_middleware._validate_token(token_from_request) if token_from_request else False
        print(f"Is token valid: {is_valid}")
        
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [csrf_middleware], 
            response,
            request
        )
        
        # Debug: Print the response status code
        print(f"Response status code: {response.status_code}")
        
        # Check that the response is successful
        assert response.status_code == 200


def test_csrf_exempt():
    """
    Test the csrf_exempt decorator.
    """
    @csrf_exempt
    def test_function():
        pass
    
    assert hasattr(test_function, "_csrf_exempt")
    assert test_function._csrf_exempt is True
