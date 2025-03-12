"""
Tests for the CORS middleware using AsyncMiddlewareTester.
"""

import pytest
from apifrom.middleware.cors import CORSMiddleware
from tests.middleware_test_helper import MockRequest, MockResponse, AsyncMiddlewareTester


@pytest.fixture
def cors_middleware():
    """
    Fixture for creating a CORS middleware instance with specific settings.
    """
    return CORSMiddleware(
        allow_origins=["https://example.com"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
        allow_credentials=True,
        expose_headers=["X-Custom-Header"],
        max_age=3600
    )


@pytest.fixture
def wildcard_middleware():
    """
    Fixture for creating a CORS middleware instance with wildcard origin.
    """
    return CORSMiddleware(
        allow_origins=["*"]
    )


@pytest.mark.asyncio
async def test_non_cors_request(cors_middleware):
    """
    Test that non-CORS requests are not modified.
    """
    request = MockRequest()
    response = MockResponse()
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [cors_middleware], response, request
    )
    
    # No CORS headers should be added since there's no Origin header
    assert "Access-Control-Allow-Origin" not in processed_response.headers


@pytest.mark.asyncio
async def test_cors_request_allowed_origin(cors_middleware):
    """
    Test that CORS requests from allowed origins get appropriate headers.
    """
    request = MockRequest(headers={"Origin": "https://example.com"})
    response = MockResponse()
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [cors_middleware], response, request
    )
    
    # CORS headers should be added
    assert processed_response.headers["Access-Control-Allow-Origin"] == "https://example.com"
    assert processed_response.headers["Access-Control-Allow-Credentials"] == "true"
    assert processed_response.headers["Access-Control-Expose-Headers"] == "X-Custom-Header"


@pytest.mark.asyncio
async def test_cors_request_disallowed_origin(cors_middleware):
    """
    Test that CORS requests from disallowed origins don't get CORS headers.
    """
    request = MockRequest(headers={"Origin": "https://attacker.com"})
    response = MockResponse()
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [cors_middleware], response, request
    )
    
    # No CORS headers should be added for disallowed origins
    assert "Access-Control-Allow-Origin" not in processed_response.headers


@pytest.mark.asyncio
async def test_cors_request_wildcard_origin(wildcard_middleware):
    """
    Test that CORS requests with wildcard origin configuration work.
    """
    request = MockRequest(headers={"Origin": "https://any-domain.com"})
    response = MockResponse()
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [wildcard_middleware], response, request
    )
    
    # CORS headers should be added with wildcard
    assert processed_response.headers["Access-Control-Allow-Origin"] == "*"


@pytest.mark.asyncio
async def test_preflight_request_allowed_origin(cors_middleware):
    """
    Test that preflight requests from allowed origins get appropriate headers.
    """
    request = MockRequest(
        method="OPTIONS",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
    )
    response = MockResponse()
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [cors_middleware], response, request
    )
    
    # Preflight response headers should be added
    assert processed_response.headers["Access-Control-Allow-Origin"] == "https://example.com"
    assert processed_response.headers["Access-Control-Allow-Methods"] == "GET, POST"
    # The middleware uses the requested headers as-is, not the configured allow_headers
    assert processed_response.headers["Access-Control-Allow-Headers"] == "Content-Type"
    assert processed_response.headers["Access-Control-Allow-Credentials"] == "true"
    assert processed_response.headers["Access-Control-Max-Age"] == "3600"


@pytest.mark.asyncio
async def test_preflight_request_disallowed_origin(cors_middleware):
    """
    Test that preflight requests from disallowed origins don't get CORS headers.
    """
    request = MockRequest(
        method="OPTIONS",
        headers={
            "Origin": "https://attacker.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
    )
    response = MockResponse()
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [cors_middleware], response, request
    )
    
    # No CORS headers should be added for disallowed origins
    assert "Access-Control-Allow-Origin" not in processed_response.headers


@pytest.mark.asyncio
async def test_preflight_request_with_method(cors_middleware):
    """
    Test that preflight requests with a method get appropriate headers.
    The middleware doesn't actually check if the method is allowed.
    """
    request = MockRequest(
        method="OPTIONS",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "DELETE"
        }
    )
    response = MockResponse()
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [cors_middleware], response, request
    )
    
    # The middleware adds the configured allow_methods, not checking the requested method
    assert processed_response.headers["Access-Control-Allow-Methods"] == "GET, POST"
    assert processed_response.headers["Access-Control-Allow-Origin"] == "https://example.com"


@pytest.mark.asyncio
async def test_preflight_request_with_headers(cors_middleware):
    """
    Test that preflight requests with headers get appropriate headers.
    The middleware doesn't actually check if the headers are allowed.
    """
    request = MockRequest(
        method="OPTIONS",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Custom-Header-Not-Allowed"
        }
    )
    response = MockResponse()
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [cors_middleware], response, request
    )
    
    # The middleware adds the requested headers as-is, not checking if they're allowed
    assert processed_response.headers["Access-Control-Allow-Headers"] == "X-Custom-Header-Not-Allowed"
    assert processed_response.headers["Access-Control-Allow-Origin"] == "https://example.com" 