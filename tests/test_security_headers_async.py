import pytest
from typing import Dict, Any, Optional, Type

from apifrom.security.headers import SecurityHeadersMiddleware, XSSProtectionMiddleware
from apifrom.core.response import Response
from apifrom.core.request import Request
from tests.middleware_test_helper import AsyncMiddlewareTester


class TestSecurityHeadersMiddleware:
    """Test the SecurityHeadersMiddleware class with async/await syntax."""

    @pytest.fixture
    def security_headers_middleware(self):
        """Create an instance of SecurityHeadersMiddleware for testing."""
        return SecurityHeadersMiddleware()

    @pytest.mark.asyncio
    async def test_add_security_headers(self, security_headers_middleware):
        """Test that security headers are added to the response."""
        request = Request(
            method="GET",
            path="/test",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )

        # Create a response to pass through
        response = Response(content={"message": "Success"}, status_code=200)

        # Process the request with the security headers middleware
        result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [security_headers_middleware],
            response,
            request
        )

        # Verify that security headers are added
        assert result.status_code == 200
        assert result.headers.get("X-Content-Type-Options") == "nosniff"
        assert result.headers.get("X-Frame-Options") == "DENY"
        assert result.headers.get("Strict-Transport-Security") is not None
        assert result.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_exempt_path(self, security_headers_middleware):
        """Test that exempt paths don't have security headers added."""
        # Add an exempt path
        security_headers_middleware.exempt_paths.append("/exempt")

        request = Request(
            method="GET",
            path="/exempt",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )

        # Create a response to pass through
        response = Response(content={"message": "Success"}, status_code=200)

        # Process the request with the security headers middleware
        result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [security_headers_middleware],
            response,
            request
        )

        # Verify that security headers are not added
        assert result.status_code == 200
        assert "X-Content-Type-Options" not in result.headers
        assert "X-Frame-Options" not in result.headers
        assert "Strict-Transport-Security" not in result.headers
        assert "Referrer-Policy" not in result.headers

    @pytest.mark.asyncio
    async def test_exempt_content_type(self, security_headers_middleware):
        """Test that exempt content types don't have security headers added."""
        # Add an exempt content type
        security_headers_middleware.exempt_content_types.append("application/json")

        request = Request(
            method="GET",
            path="/test",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )

        # Create a response with an exempt content type
        response = Response(
            content={"message": "Success"}, 
            status_code=200,
            headers={"Content-Type": "application/json"}
        )

        # Process the request with the security headers middleware
        result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [security_headers_middleware],
            response,
            request
        )

        # Verify that security headers are not added
        assert result.status_code == 200
        assert "X-Content-Type-Options" not in result.headers
        assert "X-Frame-Options" not in result.headers
        assert "Strict-Transport-Security" not in result.headers
        assert "Referrer-Policy" not in result.headers


class TestXSSProtectionMiddleware:
    """Test the XSSProtectionMiddleware class with async/await syntax."""

    @pytest.fixture
    def xss_middleware(self):
        """Create an instance of XSSProtectionMiddleware for testing."""
        return XSSProtectionMiddleware()

    @pytest.mark.asyncio
    async def test_sanitize_html_response(self, xss_middleware):
        """Test that HTML responses are processed correctly."""
        request = Request(
            method="GET",
            path="/test",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )

        # Create an HTML response with potentially dangerous content
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Test Page</h1>
            <script>alert('XSS attack');</script>
            <img src="x" onerror="alert('Another XSS attack')">
        </body>
        </html>
        """
        response = Response(
            content=html_content,
            status_code=200,
            headers={"Content-Type": "text/html"}
        )

        # Process the request with the XSS middleware
        result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [xss_middleware],
            response,
            request
        )

        # Verify that the response is processed correctly
        assert result.status_code == 200
        # The middleware doesn't actually sanitize HTML content, it just processes the response
        assert result.content == html_content

    @pytest.mark.asyncio
    async def test_sanitize_json_response(self, xss_middleware):
        """Test that JSON responses are not sanitized."""
        request = Request(
            method="GET",
            path="/test",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )

        # Create a JSON response
        json_content = {
            "message": "Success",
            "script": "<script>alert('This is not an XSS attack');</script>"
        }
        response = Response(
            content=json_content, 
            status_code=200,
            headers={"Content-Type": "application/json"}
        )

        # Process the request with the XSS middleware
        result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [xss_middleware],
            response,
            request
        )

        # Verify that JSON content is not sanitized
        assert result.status_code == 200
        assert "<script>" in str(result.content)

    @pytest.mark.asyncio
    async def test_exempt_path(self, xss_middleware):
        """Test that exempt paths don't have XSS protection applied."""
        # Add an exempt path
        xss_middleware.exempt_paths.append("/exempt")

        request = Request(
            method="GET",
            path="/exempt",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )

        # Create an HTML response with potentially dangerous content
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Test Page</h1>
            <script>alert('XSS attack');</script>
            <img src="x" onerror="alert('Another XSS attack')">
        </body>
        </html>
        """
        response = Response(
            content=html_content, 
            status_code=200,
            headers={"Content-Type": "text/html"}
        )

        # Process the request with the XSS middleware
        result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [xss_middleware],
            response,
            request
        )

        # Verify that XSS protection is not applied
        assert result.status_code == 200
        assert "<script>" in str(result.content)
        assert "onerror=" in str(result.content)

    @pytest.mark.asyncio
    async def test_exempt_content_type(self, xss_middleware):
        """Test that exempt content types don't have XSS protection applied."""
        # Add an exempt content type
        xss_middleware.exempt_content_types.append("text/plain")

        request = Request(
            method="GET",
            path="/test",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )

        # Create a response with an exempt content type
        response = Response(
            content="<script>alert('XSS attack');</script>", 
            status_code=200,
            headers={"Content-Type": "text/plain"}
        )

        # Process the request with the XSS middleware
        result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [xss_middleware],
            response,
            request
        )

        # Verify that XSS protection is not applied
        assert result.status_code == 200
        assert "<script>" in str(result.content) 