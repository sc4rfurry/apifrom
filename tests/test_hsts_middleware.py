"""
Tests for the HSTS middleware.
"""

import pytest
from typing import Dict, Any, Optional

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.security.hsts import HSTSMiddleware, HSTSPreloadChecker
from tests.middleware_test_helper import AsyncMiddlewareTester


class MockURL:
    """
    Mock URL for testing.
    """
    
    def __init__(self, scheme="http"):
        """
        Initialize the mock URL.
        
        Args:
            scheme: The URL scheme
        """
        self.scheme = scheme
    
    def __str__(self):
        """
        Convert the URL to a string.
        
        Returns:
            The URL as a string
        """
        return f"{self.scheme}://example.com"


class MockRequest:
    """
    Mock request for testing.
    """
    
    def __init__(self, path="/", headers=None, scheme="http"):
        """
        Initialize the mock request.
        
        Args:
            path: The request path
            headers: The request headers
            scheme: The URL scheme
        """
        self.path = path
        self.headers = headers or {}
        self.url = MockURL(scheme)
        self.state = type('obj', (object,), {})  # Create a state object


class MockResponse:
    """
    Mock response for testing.
    """
    
    def __init__(self, status_code=200, headers=None):
        """
        Initialize the mock response.
        
        Args:
            status_code: The HTTP status code
            headers: The response headers
        """
        self.status_code = status_code
        self.headers = headers or {}
        self.request = None


@pytest.fixture
def hsts_middleware():
    """
    Fixture for creating an HSTSMiddleware instance.
    """
    return HSTSMiddleware(
        max_age=31536000,
        include_subdomains=True,
        preload=True,
        force_https_redirect=True,
        exempt_paths=["/exempt"]
    )


@pytest.fixture
def hsts_middleware_no_preload():
    """
    Fixture for creating an HSTSMiddleware instance without preload.
    """
    return HSTSMiddleware(
        max_age=31536000,
        include_subdomains=True,
        preload=False,
        force_https_redirect=True
    )


@pytest.fixture
def hsts_middleware_no_subdomains():
    """
    Fixture for creating an HSTSMiddleware instance without subdomains.
    """
    return HSTSMiddleware(
        max_age=31536000,
        include_subdomains=False,
        preload=True,
        force_https_redirect=True
    )


@pytest.mark.asyncio
async def test_exempt_path(hsts_middleware):
    """
    Test that exempt paths are not affected by HSTS.
    """
    request = MockRequest(path="/exempt")
    
    # Create a response with the request attribute
    response = MockResponse()
    response.request = request
    
    # Test the middleware
    response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [hsts_middleware], 
        response,
        request
    )
    
    # Check that the HSTS header is not added
    assert "Strict-Transport-Security" not in response.headers


@pytest.mark.asyncio
async def test_http_redirect(hsts_middleware):
    """
    Test that HTTP requests are redirected to HTTPS.
    """
    request = MockRequest(scheme="http")
    
    # Create a response with the request attribute
    response = MockResponse()
    response.request = request
    
    # Test the middleware
    response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [hsts_middleware], 
        response,
        request
    )
    
    # Check that the response is a redirect to HTTPS
    assert response.status_code == 301
    assert response.headers.get("Location", "").startswith("https://")


@pytest.mark.asyncio
async def test_https_request(hsts_middleware):
    """
    Test that HTTPS requests have the HSTS header added.
    """
    request = MockRequest(scheme="https")
    
    # Create a response with the request attribute
    response = MockResponse()
    response.request = request
    
    # Test the middleware
    response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [hsts_middleware], 
        response,
        request
    )
    
    # Check that the HSTS header is added
    assert "Strict-Transport-Security" in response.headers
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    assert "includeSubDomains" in response.headers["Strict-Transport-Security"]
    assert "preload" in response.headers["Strict-Transport-Security"]


@pytest.mark.asyncio
async def test_forwarded_proto_header(hsts_middleware):
    """
    Test that requests with X-Forwarded-Proto header are handled correctly.
    """
    # Create a request with X-Forwarded-Proto: http
    request = MockRequest(
        headers={"X-Forwarded-Proto": "http"}
    )
    
    # Create a response with the request attribute
    response = MockResponse()
    response.request = request
    
    # Test the middleware
    response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [hsts_middleware], 
        response,
        request
    )
    
    # Check that the response is a redirect to HTTPS
    assert response.status_code == 301
    assert response.headers.get("Location", "").startswith("https://")
    
    # Create a request with X-Forwarded-Proto: https
    request = MockRequest(
        headers={"X-Forwarded-Proto": "https"}
    )
    
    # Create a response with the request attribute
    response = MockResponse()
    response.request = request
    
    # Test the middleware
    response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [hsts_middleware], 
        response,
        request
    )
    
    # Check that the HSTS header is added
    assert "Strict-Transport-Security" in response.headers


@pytest.mark.asyncio
async def test_no_preload(hsts_middleware_no_preload):
    """
    Test that the preload directive is not added when preload=False.
    """
    request = MockRequest(scheme="https")
    
    # Create a response with the request attribute
    response = MockResponse()
    response.request = request
    
    # Test the middleware
    response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [hsts_middleware_no_preload], 
        response,
        request
    )
    
    # Check that the HSTS header is added without preload
    assert "Strict-Transport-Security" in response.headers
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    assert "includeSubDomains" in response.headers["Strict-Transport-Security"]
    assert "preload" not in response.headers["Strict-Transport-Security"]


@pytest.mark.asyncio
async def test_no_subdomains(hsts_middleware_no_subdomains):
    """
    Test that the includeSubDomains directive is not added when include_subdomains=False.
    """
    request = MockRequest(scheme="https")
    
    # Create a response with the request attribute
    response = MockResponse()
    response.request = request
    
    # Test the middleware
    response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [hsts_middleware_no_subdomains], 
        response,
        request
    )
    
    # Check that the HSTS header is added without includeSubDomains
    assert "Strict-Transport-Security" in response.headers
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    assert "includeSubDomains" not in response.headers["Strict-Transport-Security"]
    assert "preload" in response.headers["Strict-Transport-Security"]


class TestHSTSPreloadChecker:
    """
    Tests for the HSTSPreloadChecker class.
    """
    
    def test_eligible_domain(self):
        """
        Test that a domain with all requirements is eligible for preloading.
        """
        checker = HSTSPreloadChecker()
        
        # Create a mock response with all required headers
        response = MockResponse(
            headers={
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload"
            }
        )
        
        # Extract the header value from the response
        hsts_header = response.headers.get("Strict-Transport-Security", "")
        
        result = checker.check_eligibility("example.com", hsts_header, all_subdomains_https=True)
        
        assert result["eligible"]
        assert len(result["issues"]) == 0
    
    def test_missing_max_age(self):
        """
        Test that a domain without max-age is not eligible.
        """
        checker = HSTSPreloadChecker()
        
        # Create a mock response without max-age
        response = MockResponse(
            headers={
                "Strict-Transport-Security": "includeSubDomains; preload"
            }
        )
        
        # Extract the header value from the response
        hsts_header = response.headers.get("Strict-Transport-Security", "")
        
        result = checker.check_eligibility("example.com", hsts_header)
        
        assert not result["eligible"]
        assert any("max-age" in issue for issue in result["issues"])
    
    def test_short_max_age(self):
        """
        Test that a domain with a short max-age is not eligible.
        """
        checker = HSTSPreloadChecker()
        
        # Create a mock response with a short max-age
        response = MockResponse(
            headers={
                "Strict-Transport-Security": "max-age=3600; includeSubDomains; preload"
            }
        )
        
        # Extract the header value from the response
        hsts_header = response.headers.get("Strict-Transport-Security", "")
        
        result = checker.check_eligibility("example.com", hsts_header)
        
        assert not result["eligible"]
        assert any("max-age is too short" in issue for issue in result["issues"])
    
    def test_missing_include_subdomains(self):
        """
        Test that a domain without includeSubDomains is not eligible.
        """
        checker = HSTSPreloadChecker()
        
        # Create a mock response without includeSubDomains
        response = MockResponse(
            headers={
                "Strict-Transport-Security": "max-age=31536000; preload"
            }
        )
        
        # Extract the header value from the response
        hsts_header = response.headers.get("Strict-Transport-Security", "")
        
        result = checker.check_eligibility("example.com", hsts_header)
        
        assert not result["eligible"]
        assert any("includeSubDomains" in issue for issue in result["issues"])
    
    def test_missing_preload(self):
        """
        Test that a domain without preload is not eligible.
        """
        checker = HSTSPreloadChecker()
        
        # Create a mock response without preload
        response = MockResponse(
            headers={
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
            }
        )
        
        # Extract the header value from the response
        hsts_header = response.headers.get("Strict-Transport-Security", "")
        
        result = checker.check_eligibility("example.com", hsts_header)
        
        assert not result["eligible"]
        assert any("preload" in issue for issue in result["issues"])
    
    def test_no_certificate(self):
        """
        Test that a domain without a valid certificate is not eligible.
        """
        checker = HSTSPreloadChecker()
        
        # Create a mock response with all required headers
        response = MockResponse(
            headers={
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload"
            }
        )
        
        # Extract the header value from the response
        hsts_header = response.headers.get("Strict-Transport-Security", "")
        
        result = checker.check_eligibility("example.com", hsts_header, has_valid_certificate=False)
        
        assert not result["eligible"]
        assert any("certificate" in issue for issue in result["issues"])
    
    def test_no_https_subdomains(self):
        """
        Test that a domain without HTTPS on subdomains is not eligible.
        """
        checker = HSTSPreloadChecker()
        
        # Create a mock response with all required headers
        response = MockResponse(
            headers={
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload"
            }
        )
        
        # Extract the header value from the response
        hsts_header = response.headers.get("Strict-Transport-Security", "")
        
        result = checker.check_eligibility("example.com", hsts_header, all_subdomains_https=False)
        
        assert not result["eligible"]
        assert any("subdomains" in issue for issue in result["issues"])
    
    def test_no_redirect(self):
        """
        Test that a domain without HTTP to HTTPS redirect is not eligible.
        """
        checker = HSTSPreloadChecker()
        
        # Create a mock response with all required headers
        response = MockResponse(
            headers={
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload"
            }
        )
        
        # Extract the header value from the response
        hsts_header = response.headers.get("Strict-Transport-Security", "")
        
        result = checker.check_eligibility("example.com", hsts_header, redirect_to_https=False)
        
        assert not result["eligible"]
        assert any("redirect" in issue for issue in result["issues"])
    
    def test_submission_instructions(self):
        """
        Test that submission instructions are included in the result.
        """
        checker = HSTSPreloadChecker()
        
        # Create a mock response with all required headers
        response = MockResponse(
            headers={
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload"
            }
        )
        
        # Extract the header value from the response
        hsts_header = response.headers.get("Strict-Transport-Security", "")
        
        result = checker.check_eligibility("example.com", hsts_header)
        
        instructions = checker.get_submission_instructions("example.com")
        assert "hstspreload.org" in instructions 