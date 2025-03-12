"""
Tests for the security headers and XSS protection functionality of the APIFromAnything library.
"""

import unittest
import pytest
from typing import Dict, Optional

from apifrom.security.headers import (
    ContentSecurityPolicy,
    CSPDirective,
    ReferrerPolicy,
    XSSProtection,
    SecurityHeadersMiddleware,
    XSSFilter,
    XSSProtectionMiddleware,
)
from apifrom.core.request import Request
from apifrom.core.response import Response
from tests.middleware_test_helper import AsyncMiddlewareTester


class TestCSPDirective(unittest.TestCase):
    """
    Tests for the CSPDirective class.
    """
    
    def test_allow_self(self):
        """
        Test the allow_self method.
        """
        directive = CSPDirective("default-src")
        directive.allow_self()
        
        self.assertIn("'self'", directive.values)
        self.assertEqual(directive.to_string(), "default-src 'self'")
    
    def test_allow_none(self):
        """
        Test the allow_none method.
        """
        directive = CSPDirective("object-src")
        directive.allow_none()
        
        self.assertIn("'none'", directive.values)
        self.assertEqual(directive.to_string(), "object-src 'none'")
    
    def test_allow_unsafe_inline(self):
        """
        Test the allow_unsafe_inline method.
        """
        directive = CSPDirective("script-src")
        directive.allow_unsafe_inline()
        
        self.assertIn("'unsafe-inline'", directive.values)
        self.assertEqual(directive.to_string(), "script-src 'unsafe-inline'")
    
    def test_allow_unsafe_eval(self):
        """
        Test the allow_unsafe_eval method.
        """
        directive = CSPDirective("script-src")
        directive.allow_unsafe_eval()
        
        self.assertIn("'unsafe-eval'", directive.values)
        self.assertEqual(directive.to_string(), "script-src 'unsafe-eval'")
    
    def test_allow_strict_dynamic(self):
        """
        Test the allow_strict_dynamic method.
        """
        directive = CSPDirective("script-src")
        directive.allow_strict_dynamic()
        
        self.assertIn("'strict-dynamic'", directive.values)
        self.assertEqual(directive.to_string(), "script-src 'strict-dynamic'")
    
    def test_allow_sources(self):
        """
        Test the allow_sources method.
        """
        directive = CSPDirective("img-src")
        directive.allow_sources("https://example.com", "https://cdn.example.com")
        
        self.assertIn("https://example.com", directive.values)
        self.assertIn("https://cdn.example.com", directive.values)
        
        directive_str = directive.to_string()
        self.assertTrue(directive_str.startswith("img-src"))
        self.assertIn("https://example.com", directive_str)
        self.assertIn("https://cdn.example.com", directive_str)
    
    def test_allow_nonce(self):
        """
        Test the allow_nonce method.
        """
        directive = CSPDirective("script-src")
        directive.allow_nonce("abc123")
        
        self.assertIn("'nonce-abc123'", directive.values)
        self.assertEqual(directive.to_string(), "script-src 'nonce-abc123'")
    
    def test_allow_nonce_auto_generated(self):
        """
        Test the allow_nonce method with auto-generated nonce.
        """
        directive = CSPDirective("script-src")
        directive.allow_nonce()
        
        # Check that a nonce was generated
        nonce_values = [v for v in directive.values if v.startswith("'nonce-")]
        self.assertEqual(len(nonce_values), 1)
    
    def test_chaining(self):
        """
        Test method chaining.
        """
        directive = CSPDirective("script-src")
        result = directive.allow_self().allow_unsafe_inline().allow_sources("https://example.com")
        
        self.assertIn("'self'", result.values)
        self.assertIn("'unsafe-inline'", result.values)
        self.assertIn("https://example.com", result.values)
        self.assertEqual(
            result.to_string(),
            "script-src 'self' 'unsafe-inline' https://example.com"
        )
    
    def test_empty_directive(self):
        """
        Test an empty directive.
        """
        directive = CSPDirective("default-src")
        directive_str = directive.to_string()
        self.assertTrue(directive_str == "default-src" or directive_str == "")


class TestContentSecurityPolicy(unittest.TestCase):
    """
    Tests for the ContentSecurityPolicy class.
    """
    
    def test_add_directive(self):
        """
        Test adding a directive to the policy.
        """
        policy = ContentSecurityPolicy()
        directive = CSPDirective("default-src")
        directive.allow_self()
        policy.add_directive(directive)
        
        self.assertIn("default-src", policy.directives)
        self.assertEqual(policy.to_string(), "default-src 'self'")
    
    def test_directive_getters(self):
        """
        Test the directive getter methods.
        """
        policy = ContentSecurityPolicy()
        
        # Test default-src
        default_src = policy.default_src()
        self.assertIsInstance(default_src, CSPDirective)
        self.assertEqual(default_src.name, "default-src")
        
        # Test script-src
        script_src = policy.script_src()
        self.assertIsInstance(script_src, CSPDirective)
        self.assertEqual(script_src.name, "script-src")
        
        # Test style-src
        style_src = policy.style_src()
        self.assertIsInstance(style_src, CSPDirective)
        self.assertEqual(style_src.name, "style-src")
        
        # Test img-src
        img_src = policy.img_src()
        self.assertIsInstance(img_src, CSPDirective)
        self.assertEqual(img_src.name, "img-src")
    
    def test_to_string(self):
        """
        Test converting the policy to a string.
        """
        policy = ContentSecurityPolicy()
        policy.default_src().allow_self()
        policy.script_src().allow_self().allow_unsafe_inline()
        
        header_value = policy.to_string()
        self.assertIn("default-src 'self'", header_value)
        self.assertIn("script-src 'self' 'unsafe-inline'", header_value)
    
    def test_report_only(self):
        """
        Test the report_only flag.
        """
        policy = ContentSecurityPolicy()
        policy.set_report_only(True)
        
        self.assertEqual(policy.get_header_name(), "Content-Security-Policy-Report-Only")
    
    def test_report_uri(self):
        """
        Test setting a report URI.
        """
        policy = ContentSecurityPolicy()
        policy.set_report_uri("/csp-report")
        
        header_value = policy.to_string()
        self.assertIn("report-uri /csp-report", header_value)
    
    def test_create_strict_policy(self):
        """
        Test creating a strict policy.
        """
        policy = ContentSecurityPolicy.create_strict_policy()
        
        header_value = policy.to_string()
        self.assertIn("default-src 'self'", header_value)
        self.assertIn("object-src 'none'", header_value)
    
    def test_create_api_policy(self):
        """
        Test creating an API policy.
        """
        policy = ContentSecurityPolicy.create_api_policy()
        
        header_value = policy.to_string()
        self.assertIn("default-src 'none'", header_value)


class MockRequest:
    """
    Mock Request class for testing.
    """
    
    def __init__(
        self,
        method: str = "GET",
        path: str = "/",
        headers: Dict[str, str] = None,
        content_type: str = "application/json",
    ):
        self.method = method
        self.path = path
        self.headers = headers or {}
        self.content_type = content_type
        self.query_params = {}
        self.body = None
        self.path_params = {}
        self.client_ip = "127.0.0.1"
    
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a header value.
        """
        return self.headers.get(name, default)


class MockResponse:
    """
    Mock Response class for testing.
    """
    
    def __init__(
        self,
        status_code: int = 200,
        body: Optional[Dict] = None,
        headers: Dict[str, str] = None,
        content_type: str = "application/json",
    ):
        self.status_code = status_code
        self.body = body or {}
        self.headers = headers or {}
        self.content_type = content_type
    
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a header value.
        """
        return self.headers.get(name, default)
    
    def set_header(self, name: str, value: str) -> None:
        """
        Set a header value.
        """
        self.headers[name] = value


@pytest.fixture
def security_headers_middleware():
    """Create a SecurityHeadersMiddleware instance for testing."""
    return SecurityHeadersMiddleware(
        exempt_paths=["/exempt"],
        exempt_content_types=["text/plain"]
    )


@pytest.mark.asyncio
async def test_add_security_headers(security_headers_middleware):
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
async def test_exempt_path(security_headers_middleware):
    """Test that exempt paths don't have security headers added."""
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


@pytest.mark.asyncio
async def test_exempt_content_type(security_headers_middleware):
    """Test that exempt content types don't have security headers added."""
    request = Request(
        method="GET",
        path="/test",
        headers={},
        query_params={},
        body=None,
        path_params={},
        client_ip="127.0.0.1"
    )
    
    # Create a response with exempt content type
    response = Response(content="Plain text", status_code=200)
    response.content_type = "text/plain"
    
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


class TestXSSFilter(unittest.TestCase):
    """
    Tests for the XSSFilter class.
    """
    
    def test_escape_html(self):
        """
        Test escaping HTML.
        """
        html = "<script>alert('XSS')</script>"
        escaped = XSSFilter.escape_html(html)
        
        self.assertIn("&lt;script&gt;", escaped)
        self.assertIn("alert", escaped)
        self.assertIn("&lt;/script&gt;", escaped)
    
    def test_sanitize_html(self):
        """
        Test sanitizing HTML.
        """
        html = """
        <div>
            <h1>Title</h1>
            <p>Text</p>
            <script>alert('XSS')</script>
            <iframe src="evil.com"></iframe>
        </div>
        """
        sanitized = XSSFilter.sanitize_html(html)
        
        self.assertIn("Title", sanitized)
        self.assertIn("Text", sanitized)
        self.assertNotIn("<script>", sanitized)
        self.assertNotIn("<iframe", sanitized)
    
    def test_sanitize_html_with_allowed_tags(self):
        """
        Test sanitizing HTML with allowed tags.
        """
        html = "<div><h1>Title</h1><script>alert('XSS')</script></div>"
        sanitized = XSSFilter.sanitize_html(html, allowed_tags=["div"])
        
        self.assertIn("<div>", sanitized)
        self.assertNotIn("<h1>", sanitized)
        self.assertNotIn("<script>", sanitized)
    
    def test_sanitize_json(self):
        """
        Test sanitizing JSON.
        """
        data = {
            "name": "<script>alert('XSS')</script>",
            "description": "Normal text",
            "nested": {
                "html": "<iframe src='evil.com'></iframe>",
                "array": ["<img src='x' onerror='alert(1)'>", "Normal"]
            }
        }
        
        sanitized = XSSFilter.sanitize_json(data)
        
        self.assertIn("&lt;script&gt;", sanitized["name"])
        self.assertIn("alert", sanitized["name"])
        self.assertIn("&lt;/script&gt;", sanitized["name"])
        self.assertEqual(sanitized["description"], "Normal text")
        self.assertIn("&lt;iframe", sanitized["nested"]["html"])
        self.assertIn("&lt;img", sanitized["nested"]["array"][0])
        self.assertEqual(sanitized["nested"]["array"][1], "Normal")


@pytest.fixture
def xss_middleware():
    """Create an XSSProtectionMiddleware instance for testing."""
    return XSSProtectionMiddleware(
        exempt_paths=["/exempt"],
        exempt_content_types=["text/plain"]
    )


@pytest.mark.asyncio
async def test_sanitize_json_response(xss_middleware):
    """Test that JSON responses are sanitized."""
    request = Request(
        method="GET",
        path="/test",
        headers={},
        query_params={},
        body=None,
        path_params={},
        client_ip="127.0.0.1"
    )

    # Create a response with potentially malicious JSON
    response = Response(
        content={
            "name": "<script>alert('XSS')</script>",
            "description": "Normal text"
        },
        status_code=200
    )
    response.headers["Content-Type"] = "application/json"
    response.body = response.content  # Set body to match content for the middleware

    # Process the request with the XSS middleware
    result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [xss_middleware],
        response,
        request
    )

    # Verify that the JSON was sanitized
    assert result.status_code == 200
    # Check that the script tags are escaped, but don't check the exact format of the quotes
    assert "&lt;script&gt;" in result.body["name"]
    assert "&lt;/script&gt;" in result.body["name"]
    assert "alert" in result.body["name"]


@pytest.mark.asyncio
async def test_sanitize_html_response(xss_middleware):
    """Test that HTML responses are sanitized."""
    request = Request(
        method="GET",
        path="/test",
        headers={},
        query_params={},
        body=None,
        path_params={},
        client_ip="127.0.0.1"
    )

    # Create a response with potentially malicious HTML
    html_content = "<div><h1>Title</h1><script>alert('XSS')</script></div>"
    response = Response(content=html_content, status_code=200)
    response.headers["Content-Type"] = "text/html"
    response.body = response.content  # Set body to match content for the middleware
    
    # Enable HTML sanitization for this test
    xss_middleware.sanitize_html_response = True

    # Process the request with the XSS middleware
    result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [xss_middleware],
        response,
        request
    )

    # Verify that the HTML was sanitized - the implementation might strip all tags
    # or just remove the script tag, so we'll check for the content instead
    assert result.status_code == 200
    assert "Title" in result.body
    assert "<script>" not in result.body
    assert "alert('XSS')" not in result.body


@pytest.mark.asyncio
async def test_exempt_path(xss_middleware):
    """Test that exempt paths are not sanitized."""
    request = Request(
        method="GET",
        path="/exempt",
        headers={},
        query_params={},
        body=None,
        path_params={},
        client_ip="127.0.0.1"
    )
    
    # Create a response with potentially malicious JSON
    response = Response(
        content={
            "name": "<script>alert('XSS')</script>",
            "description": "Normal text"
        }, 
        status_code=200
    )
    
    # Process the request with the XSS middleware
    result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [xss_middleware],
        response,
        request
    )
    
    # Verify that the JSON was not sanitized
    assert result.status_code == 200
    assert result.content["name"] == "<script>alert('XSS')</script>"
    assert result.content["description"] == "Normal text"


@pytest.mark.asyncio
async def test_exempt_content_type(xss_middleware):
    """Test that exempt content types are not sanitized."""
    request = Request(
        method="GET",
        path="/test",
        headers={},
        query_params={},
        body=None,
        path_params={},
        client_ip="127.0.0.1"
    )
    
    # Create a response with exempt content type
    response = Response(content="<script>alert('XSS')</script>", status_code=200)
    response.content_type = "text/plain"
    
    # Process the request with the XSS middleware
    result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [xss_middleware],
        response,
        request
    )
    
    # Verify that the content was not sanitized
    assert result.status_code == 200
    assert result.content == "<script>alert('XSS')</script>"


if __name__ == "__main__":
    unittest.main() 