"""
Tests for the Trusted Types middleware.
"""

import unittest
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import re

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.security.trusted_types import (
    TrustedTypesMiddleware,
    TrustedTypesPolicy,
    TrustedTypesBuilder,
    TrustedTypesViolationReporter,
)
from tests.middleware_test_helper import AsyncMiddlewareTester, MockRequest, MockResponse


class TestTrustedTypesPolicy(unittest.TestCase):
    """
    Tests for the TrustedTypesPolicy class.
    """
    
    def setUp(self):
        """
        Set up the test environment.
        """
        self.policy = TrustedTypesPolicy(name="test-policy")
    
    def test_create_script(self):
        """
        Test that script creation works.
        """
        # Add a script handler
        def validate_script(script: str) -> str:
            if "<script" in script.lower():
                raise ValueError("Invalid script")
            return script
        
        self.policy.add_script_handler(validate_script)
        
        # Test with valid script
        valid_script = "console.log('Hello, World!');"
        result = self.policy.create_script(valid_script)
        self.assertEqual(result, valid_script)
        
        # Test with invalid script
        invalid_script = "<script>alert('XSS');</script>"
        with self.assertRaises(ValueError):
            self.policy.create_script(invalid_script)
    
    def test_create_html(self):
        """
        Test that HTML creation works.
        """
        # Add an HTML handler
        def sanitize_html(html: str) -> str:
            # Use a safer approach to remove script tags
            try:
                # Try to use a proper HTML parser if available
                from html.parser import HTMLParser
                from io import StringIO
                
                class ScriptFilter(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.result = StringIO()
                        self.skip_content = False
                        
                    def handle_starttag(self, tag, attrs):
                        if tag.lower() == 'script':
                            self.skip_content = True
                        else:
                            self.result.write(f"<{tag}>")
                    
                    def handle_endtag(self, tag):
                        if tag.lower() == 'script':
                            self.skip_content = False
                        else:
                            self.result.write(f"</{tag}>")
                    
                    def handle_data(self, data):
                        if not self.skip_content:
                            self.result.write(data)
                
                parser = ScriptFilter()
                parser.feed(html)
                return parser.result.getvalue()
                
            except (ImportError, Exception):
                # Fallback to regex if HTML parser is not available or fails
                return re.sub(r'<\s*script\b[^>]*>.*?<\s*/\s*script\s*>', '', html, flags=re.IGNORECASE | re.DOTALL)
        
        self.policy.add_html_handler(sanitize_html)
        
        # Test with HTML containing a script tag
        html = "<div>Hello, World!</div><script>alert('XSS');</script>"
        result = self.policy.create_html(html)
        self.assertEqual(result, "<div>Hello, World!</div>")
    
    def test_create_script_url(self):
        """
        Test that script URL creation works.
        """
        # Add a script URL handler
        def validate_url(url: str) -> str:
            if "javascript:" in url.lower():
                raise ValueError("Invalid URL")
            return url
        
        self.policy.add_script_url_handler(validate_url)
        
        # Test with valid URL
        valid_url = "https://example.com/script.js"
        result = self.policy.create_script_url(valid_url)
        self.assertEqual(result, valid_url)
        
        # Test with invalid URL
        invalid_url = "javascript:alert('XSS');"
        with self.assertRaises(ValueError):
            self.policy.create_script_url(invalid_url)
    
    def test_create_url(self):
        """
        Test that URL creation works.
        """
        # Add a URL handler
        def validate_url(url: str) -> str:
            if "javascript:" in url.lower():
                raise ValueError("Invalid URL")
            return url
        
        self.policy.add_url_handler(validate_url)
        
        # Test with valid URL
        valid_url = "https://example.com/"
        result = self.policy.create_url(valid_url)
        self.assertEqual(result, valid_url)
        
        # Test with invalid URL
        invalid_url = "javascript:alert('XSS');"
        with self.assertRaises(ValueError):
            self.policy.create_url(invalid_url)
    
    def test_to_js(self):
        """
        Test that JavaScript code generation works.
        """
        js_code = self.policy.to_js()
        
        # Check that the policy name is included
        self.assertIn("test-policy", js_code)
        
        # Check that the createPolicy function is called
        self.assertIn("window.trustedTypes.createPolicy", js_code)
        
        # Check that the policy functions are defined
        self.assertIn("createHTML", js_code)
        self.assertIn("createScript", js_code)
        self.assertIn("createScriptURL", js_code)


class TestTrustedTypesMiddleware(unittest.TestCase):
    """
    Tests for the TrustedTypesMiddleware class.
    """
    
    def setUp(self):
        """
        Set up the test environment.
        """
        self.policy = TrustedTypesPolicy(name="test-policy")
        self.middleware = TrustedTypesMiddleware(
            policies=[self.policy],
            require_for_script=True,
            report_uri="/report",
            exempt_paths=["/exempt"]
        )
    
    async def _next_middleware(self, request):
        """
        Mock next middleware function.
        
        Args:
            request: The request object
            
        Returns:
            A mock response
        """
        return MockResponse(
            body="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test</title>
            </head>
            <body>
                <h1>Test</h1>
            </body>
            </html>
            """
        )
    
    def test_get_csp_header_name(self):
        """
        Test that the CSP header name is correct.
        """
        self.assertEqual(self.middleware._get_csp_header_name(), "Content-Security-Policy")
    
    def test_get_csp_header_value(self):
        """
        Test that the CSP header value is correct.
        """
        header_value = self.middleware._get_csp_header_value()
        
        self.assertIn("require-trusted-types-for 'script'", header_value)
        self.assertIn("trusted-types test-policy", header_value)
        self.assertIn("report-uri /report", header_value)
    
    def test_generate_policy_script(self):
        """
        Test that the policy script is generated correctly.
        """
        script = self.middleware._generate_policy_script()
        
        self.assertIn("<script>", script)
        self.assertIn("window.trustedTypes.createPolicy", script)
        self.assertIn("test-policy", script)
    
    def test_inject_policy_script(self):
        """
        Test that the policy script is injected correctly.
        """
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test</title>
        </head>
        <body>
            <h1>Test</h1>
        </body>
        </html>
        """
        
        modified_html = self.middleware._inject_policy_script(html)
        
        self.assertIn("<script>", modified_html)
        self.assertIn("window.trustedTypes.createPolicy", modified_html)
        
        # Check that the script is injected in the head
        head_end_pos = modified_html.find("</head>")
        script_pos = modified_html.find("<script>")
        
        self.assertGreater(head_end_pos, 0)
        self.assertGreater(script_pos, 0)
        self.assertLess(script_pos, head_end_pos)


class TestTrustedTypesBuilder(unittest.TestCase):
    """
    Tests for the TrustedTypesBuilder class.
    """
    
    def test_create_default_policy(self):
        """
        Test that the default policy is created correctly.
        """
        policy = TrustedTypesBuilder.create_default_policy()
        
        # Check that the policy name is correct
        self.assertEqual(policy.name, "default")
        
        # Check that the policy has handlers
        self.assertTrue(len(policy.script_handlers) > 0)
        self.assertTrue(len(policy.html_handlers) > 0)
        self.assertTrue(len(policy.url_handlers) > 0)
        self.assertTrue(len(policy.script_url_handlers) > 0)
        
        # Test the script handler
        with self.assertRaises(ValueError):
            policy.create_script("<script>alert('XSS');</script>")
        
        # Test the HTML handler
        html = "<div>Hello, World!</div><script>alert('XSS');</script>"
        sanitized_html = policy.create_html(html)
        self.assertEqual(sanitized_html, "<div>Hello, World!</div>")
        
        # Test the URL handler
        with self.assertRaises(ValueError):
            policy.create_url("javascript:alert('XSS');")
    
    def test_create_escape_policy(self):
        """
        Test that the escape policy is created correctly.
        """
        policy = TrustedTypesBuilder.create_escape_policy()
        
        # Check that the policy name is correct
        self.assertEqual(policy.name, "escape")
        
        # Check that the policy has an HTML handler
        self.assertTrue(len(policy.html_handlers) > 0)
        
        # Test the HTML handler
        html = "<div>Hello, World!</div>"
        escaped_html = policy.create_html(html)
        self.assertEqual(escaped_html, "&lt;div&gt;Hello, World!&lt;/div&gt;")
    
    def test_create_sanitize_policy(self):
        """
        Test that the sanitize policy is created correctly.
        """
        policy = TrustedTypesBuilder.create_sanitize_policy()
        
        # Check that the policy name is correct
        self.assertEqual(policy.name, "sanitize")
        
        # Check that the policy has an HTML handler
        self.assertTrue(len(policy.html_handlers) > 0)
        
        # Test the HTML handler
        html = "<div>Hello, World!</div><script>alert('XSS');</script>"
        sanitized_html = policy.create_html(html)
        self.assertEqual(sanitized_html, "<div>Hello, World!</div>")
    
    def test_create_url_policy(self):
        """
        Test that the URL policy is created correctly.
        """
        policy = TrustedTypesBuilder.create_url_policy()
        
        # Check that the policy name is correct
        self.assertEqual(policy.name, "url")
        
        # Check that the policy has URL handlers
        self.assertTrue(len(policy.url_handlers) > 0)
        self.assertTrue(len(policy.script_url_handlers) > 0)
        
        # Test the URL handler
        with self.assertRaises(ValueError):
            policy.create_url("javascript:alert('XSS');")
        
        # Test the script URL handler
        with self.assertRaises(ValueError):
            policy.create_script_url("javascript:alert('XSS');")


class TestTrustedTypesViolationReporter(unittest.TestCase):
    """
    Tests for the TrustedTypesViolationReporter class.
    """
    
    def test_get_report_uri(self):
        """
        Test that the report URI is correct.
        """
        reporter = TrustedTypesViolationReporter(report_uri="/report")
        self.assertEqual(reporter.get_report_uri(), "/report")


@pytest.fixture
def trusted_types_policy():
    """Create a Trusted Types policy for testing."""
    return TrustedTypesPolicy(name="test-policy")

@pytest.fixture
def trusted_types_middleware(trusted_types_policy):
    """Create a Trusted Types middleware instance for testing."""
    return TrustedTypesMiddleware(
        policies=[trusted_types_policy],
        require_for_script=True,
        report_uri="/report",
        exempt_paths=["/exempt"]
    )

@pytest.fixture
def html_response():
    """Create an HTML response for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test</title>
    </head>
    <body>
        <h1>Test</h1>
    </body>
    </html>
    """

@pytest.fixture
def trusted_types_reporter():
    """Create a Trusted Types violation reporter for testing."""
    mock_callback = AsyncMock()
    reporter = TrustedTypesViolationReporter(
        report_uri="/report",
        callback=mock_callback
    )
    return reporter, mock_callback

@pytest.mark.asyncio
async def test_handle_report(trusted_types_reporter):
    """
    Test that reports are handled correctly.
    """
    reporter, mock_callback = trusted_types_reporter
    
    # Create a mock report
    report = {
        "type": "trusted-types-violation",
        "message": "Trusted Types violation",
        "source": "https://example.com",
        "line": 42,
        "column": 13
    }
    
    # Handle the report
    await reporter.handle_report(report)
    
    # Check that the callback was called with the report
    mock_callback.assert_called_once_with(report)

@pytest.mark.asyncio
async def test_process_request(trusted_types_middleware, html_response):
    """
    Test that the middleware processes requests correctly.
    """
    request = Request(
        method="GET",
        path="/test",
        headers={},
        query_params={},
        body=None,
        path_params={},
        client_ip="127.0.0.1"
    )
    
    response = Response(content=html_response, status_code=200)
    response.headers["Content-Type"] = "text/html"
    response.body = response.content  # Set body to match content for the middleware
    
    # Process the request with the Trusted Types middleware
    result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [trusted_types_middleware],
        response,
        request
    )
    
    # Check that the CSP header is added
    assert "Content-Security-Policy" in result.headers
    
    # Check that the policy script is injected
    assert "<script>" in result.body
    assert "window.trustedTypes.createPolicy" in result.body

@pytest.mark.asyncio
async def test_exempt_path(trusted_types_middleware, html_response):
    """
    Test that exempt paths are not affected by Trusted Types.
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
    
    response = Response(content=html_response, status_code=200)
    response.headers["Content-Type"] = "text/html"
    response.body = response.content  # Set body to match content for the middleware
    
    # Process the request with the Trusted Types middleware
    result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [trusted_types_middleware],
        response,
        request
    )
    
    # Check that the CSP header is not added
    assert "Content-Security-Policy" not in result.headers
    
    # Check that the policy script is not injected
    assert "window.trustedTypes.createPolicy" not in result.body

@pytest.mark.asyncio
async def test_append_to_existing_csp(trusted_types_middleware, html_response):
    """
    Test that the middleware appends to existing CSP headers.
    """
    request = Request(
        method="GET",
        path="/test",
        headers={},
        query_params={},
        body=None,
        path_params={},
        client_ip="127.0.0.1"
    )
    
    response = Response(content=html_response, status_code=200)
    response.headers["Content-Type"] = "text/html"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.body = response.content  # Set body to match content for the middleware
    
    # Process the request with the Trusted Types middleware
    result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [trusted_types_middleware],
        response,
        request
    )
    
    # Check that the CSP header is present
    assert "Content-Security-Policy" in result.headers
    
    # Check that the required directives are in the CSP header
    assert "require-trusted-types-for 'script'" in result.headers["Content-Security-Policy"]
    assert "trusted-types test-policy" in result.headers["Content-Security-Policy"]
    assert "report-uri /report" in result.headers["Content-Security-Policy"]


if __name__ == "__main__":
    unittest.main() 