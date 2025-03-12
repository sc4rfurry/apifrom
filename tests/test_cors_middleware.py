"""
Tests for the CORS middleware.

This module contains tests for the CORS middleware functionality.
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
    Test that CORS requests from allowed origins get the appropriate headers.
    """
    request = MockRequest(headers={"Origin": "https://example.com"})
    response = MockResponse()
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [cors_middleware], response, request
    )
    
    # CORS headers should be added for allowed origin
    assert processed_response.headers["Access-Control-Allow-Origin"] == "https://example.com"
    assert processed_response.headers["Access-Control-Allow-Credentials"] == "true"
    assert "X-Custom-Header" in processed_response.headers["Access-Control-Expose-Headers"]


@pytest.mark.asyncio
async def test_cors_request_disallowed_origin(cors_middleware):
    """
    Test that CORS requests from disallowed origins don't get CORS headers.
    """
    request = MockRequest(headers={"Origin": "https://evil.com"})
    response = MockResponse()
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [cors_middleware], response, request
    )
    
    # No CORS headers should be added for disallowed origin
    assert "Access-Control-Allow-Origin" not in processed_response.headers


@pytest.mark.asyncio
async def test_cors_request_wildcard_origin(wildcard_middleware):
    """
    Test that CORS requests with wildcard origin configuration work correctly.
    """
    request = MockRequest(headers={"Origin": "https://example.com"})
    response = MockResponse()
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [wildcard_middleware], response, request
    )
    
    # CORS headers should be added for any origin with wildcard config
    assert processed_response.headers["Access-Control-Allow-Origin"] == "*"


@pytest.mark.asyncio
async def test_preflight_request_allowed_origin(cors_middleware):
    """
    Test that preflight requests from allowed origins get the appropriate headers.
    """
    request = MockRequest(
        method="OPTIONS",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, Authorization"
        }
    )
    response = MockResponse()
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [cors_middleware], response, request
    )
    
    # Preflight response should have appropriate CORS headers
    assert processed_response.headers["Access-Control-Allow-Origin"] == "https://example.com"
    assert "POST" in processed_response.headers["Access-Control-Allow-Methods"]
    assert "Content-Type" in processed_response.headers["Access-Control-Allow-Headers"]
    assert "Authorization" in processed_response.headers["Access-Control-Allow-Headers"]
    assert processed_response.headers["Access-Control-Allow-Credentials"] == "true"
    assert processed_response.headers["Access-Control-Max-Age"] == "3600"


@pytest.mark.asyncio
async def test_preflight_request_disallowed_origin(cors_middleware):
    """
    Test that preflight requests from disallowed origins are rejected.
    """
    request = MockRequest(
        method="OPTIONS",
        headers={
            "Origin": "https://evil.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
    )
    response = MockResponse()
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [cors_middleware], response, request
    )
    
    # No CORS headers should be added for disallowed origin
    assert "Access-Control-Allow-Origin" not in processed_response.headers 