"""
Tests for the HSTS middleware using async/await syntax.
"""

import pytest
from typing import Dict, Any, Optional, List

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.security.hsts import HSTSMiddleware
from tests.middleware_test_helper import AsyncMiddlewareTester


class TestHSTSMiddleware:
    """
    Tests for the HSTSMiddleware class using async/await syntax.
    """
    
    @pytest.fixture
    def hsts_middleware(self):
        """
        Create an instance of HSTSMiddleware for testing.
        
        Returns:
            An instance of HSTSMiddleware
        """
        return HSTSMiddleware(
            max_age=31536000,
            include_subdomains=True,
            preload=True,
            force_https_redirect=True,
            exempt_paths=["/exempt"]
        )
    
    @pytest.mark.asyncio
    async def test_exempt_path(self, hsts_middleware):
        """
        Test that exempt paths are not affected by HSTS.
        """
        request = Request(
            method="GET",
            path="/exempt",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        response = Response(
            content="Exempt path",
            status_code=200,
            headers={}
        )
        
        result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [hsts_middleware],
            response,
            request
        )
        
        # No HSTS header should be added
        assert "Strict-Transport-Security" not in result.headers
        assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_http_redirect(self, hsts_middleware):
        """
        Test that HTTP requests are redirected to HTTPS.
        """
        request = Request(
            method="GET",
            path="/test",
            headers={"Host": "example.com", "X-Forwarded-Proto": "http"},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Add a URL property to the request with a __str__ method
        class URL:
            def __init__(self, scheme, path):
                self.scheme = scheme
                self.path = path
            
            def __str__(self):
                return f"{self.scheme}://example.com{self.path}"
        
        request.url = URL('http', '/test')
        
        # Process the request with the middleware
        processed_request = await hsts_middleware.process_request(request)
        
        # Check if the redirect information is stored in the request state
        assert hasattr(processed_request.state, 'hsts_redirect')
        assert processed_request.state.hsts_redirect is True
        assert hasattr(processed_request.state, 'hsts_redirect_url')
        
        # The redirect URL should now be a string starting with https://
        redirect_url = str(processed_request.state.hsts_redirect_url)
        assert redirect_url.startswith("https://")
        assert "/test" in redirect_url
        
        # Create a response based on the redirect information
        response = Response(
            content="",
            status_code=301,
            headers={"Location": redirect_url}
        )
        
        # Verify the response
        assert response.status_code == 301
        assert response.headers["Location"].startswith("https://")
        assert "/test" in response.headers["Location"]
    
    @pytest.mark.asyncio
    async def test_https_request(self, hsts_middleware):
        """
        Test that HTTPS requests get the HSTS header.
        """
        request = Request(
            method="GET",
            path="/test",
            headers={"Host": "example.com", "X-Forwarded-Proto": "https"},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Add a URL property to the request
        request.url = type('URL', (), {'scheme': 'https', 'path': '/test'})
        
        response = Response(
            content="Test response",
            status_code=200,
            headers={}
        )
        
        result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [hsts_middleware],
            response,
            request
        )
        
        # HSTS header should be added
        assert "Strict-Transport-Security" in result.headers
        assert result.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains; preload"
        assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_forwarded_proto_header(self, hsts_middleware):
        """
        Test that the X-Forwarded-Proto header is respected.
        """
        # HTTP request with X-Forwarded-Proto: https
        request = Request(
            method="GET",
            path="/test",
            headers={"X-Forwarded-Proto": "https", "Host": "example.com"},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Add a URL property to the request
        request.url = type('URL', (), {'scheme': 'http', 'path': '/test'})
        
        response = Response(
            content="Test response",
            status_code=200,
            headers={}
        )
        
        result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [hsts_middleware],
            response,
            request
        )
        
        # Should not redirect, but add HSTS header
        assert result.status_code == 200
        assert "Strict-Transport-Security" in result.headers
        assert result.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains; preload"
    
    @pytest.mark.asyncio
    async def test_no_preload(self, hsts_middleware):
        """
        Test that the preload directive can be disabled.
        """
        # Create middleware without preload
        middleware = HSTSMiddleware(
            max_age=31536000,
            include_subdomains=True,
            preload=False,
            force_https_redirect=True
        )
        
        request = Request(
            method="GET",
            path="/test",
            headers={"Host": "example.com", "X-Forwarded-Proto": "https"},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Add a URL property to the request
        request.url = type('URL', (), {'scheme': 'https', 'path': '/test'})
        
        response = Response(
            content="Test response",
            status_code=200,
            headers={}
        )
        
        result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [middleware],
            response,
            request
        )
        
        # HSTS header should be added without preload
        assert "Strict-Transport-Security" in result.headers
        assert result.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
        assert "preload" not in result.headers["Strict-Transport-Security"]
    
    @pytest.mark.asyncio
    async def test_no_subdomains(self, hsts_middleware):
        """
        Test that the includeSubDomains directive can be disabled.
        """
        # Create middleware without includeSubDomains
        middleware = HSTSMiddleware(
            max_age=31536000,
            include_subdomains=False,
            preload=True,
            force_https_redirect=True
        )
        
        request = Request(
            method="GET",
            path="/test",
            headers={"Host": "example.com", "X-Forwarded-Proto": "https"},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Add a URL property to the request
        request.url = type('URL', (), {'scheme': 'https', 'path': '/test'})
        
        response = Response(
            content="Test response",
            status_code=200,
            headers={}
        )
        
        result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [middleware],
            response,
            request
        )
        
        # HSTS header should be added without includeSubDomains
        assert "Strict-Transport-Security" in result.headers
        assert result.headers["Strict-Transport-Security"] == "max-age=31536000; preload"
        assert "includeSubDomains" not in result.headers["Strict-Transport-Security"] 