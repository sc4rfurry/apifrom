"""
Tests for the Content Security Policy middleware.
"""

import unittest
import pytest
from unittest.mock import MagicMock, AsyncMock

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.security.csp import (
    CSPMiddleware,
    CSPPolicy,
    CSPDirective,
    CSPSource,
    CSPNonce,
    CSPViolationReporter,
    CSPBuilder,
)
from tests.middleware_test_helper import MockRequest, MockResponse, AsyncMiddlewareTester


class TestCSPDirective(unittest.TestCase):
    """
    Tests for the CSPDirective class.
    """
    
    def test_directives(self):
        """
        Test that directives are defined correctly.
        """
        self.assertEqual(CSPDirective.DEFAULT_SRC, "default-src")
        self.assertEqual(CSPDirective.SCRIPT_SRC, "script-src")
        self.assertEqual(CSPDirective.STYLE_SRC, "style-src")
        self.assertEqual(CSPDirective.IMG_SRC, "img-src")
        self.assertEqual(CSPDirective.CONNECT_SRC, "connect-src")
        self.assertEqual(CSPDirective.FONT_SRC, "font-src")
        self.assertEqual(CSPDirective.OBJECT_SRC, "object-src")
        self.assertEqual(CSPDirective.FRAME_ANCESTORS, "frame-ancestors")
        self.assertEqual(CSPDirective.FORM_ACTION, "form-action")
        self.assertEqual(CSPDirective.BASE_URI, "base-uri")
        self.assertEqual(CSPDirective.REPORT_URI, "report-uri")
        self.assertEqual(CSPDirective.REPORT_TO, "report-to")
        self.assertEqual(CSPDirective.UPGRADE_INSECURE_REQUESTS, "upgrade-insecure-requests")
        self.assertEqual(CSPDirective.BLOCK_ALL_MIXED_CONTENT, "block-all-mixed-content")


class TestCSPSource(unittest.TestCase):
    """
    Tests for the CSPSource class.
    """
    
    def test_sources(self):
        """
        Test that sources are defined correctly.
        """
        self.assertEqual(CSPSource.NONE, "'none'")
        self.assertEqual(CSPSource.SELF, "'self'")
        self.assertEqual(CSPSource.UNSAFE_INLINE, "'unsafe-inline'")
        self.assertEqual(CSPSource.UNSAFE_EVAL, "'unsafe-eval'")
        self.assertEqual(CSPSource.STRICT_DYNAMIC, "'strict-dynamic'")
        self.assertEqual(CSPSource.HTTPS, "https:")
        self.assertEqual(CSPSource.DATA, "data:")
        self.assertEqual(CSPSource.BLOB, "blob:")


class TestCSPNonce(unittest.TestCase):
    """
    Tests for the CSPNonce class.
    """
    
    def test_generate(self):
        """
        Test that nonce generation works.
        """
        nonce = CSPNonce.generate()
        self.assertTrue(nonce.startswith("'nonce-"))
        # Check that the nonce has a reasonable length, but don't hardcode the exact length
        # since it might vary based on implementation details
        self.assertTrue(len(nonce) > 20)  # Should be long enough for security
        self.assertTrue(nonce.endswith("'"))  # Should end with a single quote


class TestCSPViolationReporter(unittest.TestCase):
    """
    Tests for the CSPViolationReporter class.
    """
    
    def test_get_directives(self):
        """
        Test that directives are returned correctly.
        """
        reporter = CSPViolationReporter(report_uri="/report-uri", report_to="default")
        directives = reporter.get_directives()
        
        self.assertEqual(directives[CSPDirective.REPORT_URI], "/report-uri")
        self.assertEqual(directives[CSPDirective.REPORT_TO], "default")


@pytest.mark.asyncio
async def test_csp_violation_reporter_handle_report():
    """
    Test that CSP violation reports are handled correctly.
    """
    mock_callback = AsyncMock()
    reporter = CSPViolationReporter(callback=mock_callback)
    
    report_data = {
        "csp-report": {
            "document-uri": "https://example.com",
            "violated-directive": "script-src",
            "effective-directive": "script-src",
            "original-policy": "default-src 'self'",
            "blocked-uri": "https://evil.com/script.js"
        }
    }
    
    await reporter.handle_report(report_data)
    mock_callback.assert_called_once_with(report_data)


class TestCSPPolicy(unittest.TestCase):
    """
    Tests for the CSPPolicy class.
    """
    
    def test_add_directive(self):
        """
        Test that directives can be added.
        """
        policy = CSPPolicy()
        policy.add_directive(CSPDirective.DEFAULT_SRC, CSPSource.SELF)
        
        self.assertIn(CSPDirective.DEFAULT_SRC, policy.directives)
        self.assertIn(CSPSource.SELF, policy.directives[CSPDirective.DEFAULT_SRC])
    
    def test_add_directive_list(self):
        """
        Test that directives can be added as lists.
        """
        policy = CSPPolicy()
        policy.add_directive(CSPDirective.DEFAULT_SRC, [CSPSource.SELF, CSPSource.HTTPS])
        
        self.assertIn(CSPDirective.DEFAULT_SRC, policy.directives)
        self.assertIn(CSPSource.SELF, policy.directives[CSPDirective.DEFAULT_SRC])
        self.assertIn(CSPSource.HTTPS, policy.directives[CSPDirective.DEFAULT_SRC])
    
    def test_add_default_src(self):
        """
        Test that default-src can be added.
        """
        policy = CSPPolicy()
        policy.add_default_src(CSPSource.SELF)
        
        self.assertIn(CSPDirective.DEFAULT_SRC, policy.directives)
        self.assertIn(CSPSource.SELF, policy.directives[CSPDirective.DEFAULT_SRC])
    
    def test_add_script_src(self):
        """
        Test that script-src can be added.
        """
        policy = CSPPolicy()
        policy.add_script_src(CSPSource.SELF)
        
        self.assertIn(CSPDirective.SCRIPT_SRC, policy.directives)
        self.assertIn(CSPSource.SELF, policy.directives[CSPDirective.SCRIPT_SRC])
    
    def test_add_style_src(self):
        """
        Test that style-src can be added.
        """
        policy = CSPPolicy()
        policy.add_style_src(CSPSource.SELF)
        
        self.assertIn(CSPDirective.STYLE_SRC, policy.directives)
        self.assertIn(CSPSource.SELF, policy.directives[CSPDirective.STYLE_SRC])
    
    def test_add_img_src(self):
        """
        Test that img-src can be added.
        """
        policy = CSPPolicy()
        policy.add_img_src(CSPSource.SELF)
        
        self.assertIn(CSPDirective.IMG_SRC, policy.directives)
        self.assertIn(CSPSource.SELF, policy.directives[CSPDirective.IMG_SRC])
    
    def test_add_connect_src(self):
        """
        Test that connect-src can be added.
        """
        policy = CSPPolicy()
        policy.add_connect_src(CSPSource.SELF)
        
        self.assertIn(CSPDirective.CONNECT_SRC, policy.directives)
        self.assertIn(CSPSource.SELF, policy.directives[CSPDirective.CONNECT_SRC])
    
    def test_add_font_src(self):
        """
        Test that font-src can be added.
        """
        policy = CSPPolicy()
        policy.add_font_src(CSPSource.SELF)
        
        self.assertIn(CSPDirective.FONT_SRC, policy.directives)
        self.assertIn(CSPSource.SELF, policy.directives[CSPDirective.FONT_SRC])
    
    def test_add_object_src(self):
        """
        Test that object-src can be added.
        """
        policy = CSPPolicy()
        policy.add_object_src(CSPSource.NONE)
        
        self.assertIn(CSPDirective.OBJECT_SRC, policy.directives)
        self.assertIn(CSPSource.NONE, policy.directives[CSPDirective.OBJECT_SRC])
    
    def test_add_frame_ancestors(self):
        """
        Test that frame-ancestors can be added.
        """
        policy = CSPPolicy()
        policy.add_frame_ancestors(CSPSource.NONE)
        
        self.assertIn(CSPDirective.FRAME_ANCESTORS, policy.directives)
        self.assertIn(CSPSource.NONE, policy.directives[CSPDirective.FRAME_ANCESTORS])
    
    def test_add_form_action(self):
        """
        Test that form-action can be added.
        """
        policy = CSPPolicy()
        policy.add_form_action(CSPSource.SELF)
        
        self.assertIn(CSPDirective.FORM_ACTION, policy.directives)
        self.assertIn(CSPSource.SELF, policy.directives[CSPDirective.FORM_ACTION])
    
    def test_add_base_uri(self):
        """
        Test that base-uri can be added.
        """
        policy = CSPPolicy()
        policy.add_base_uri(CSPSource.SELF)
        
        self.assertIn(CSPDirective.BASE_URI, policy.directives)
        self.assertIn(CSPSource.SELF, policy.directives[CSPDirective.BASE_URI])
    
    def test_add_upgrade_insecure_requests(self):
        """
        Test that upgrade-insecure-requests can be added.
        """
        policy = CSPPolicy()
        policy.add_upgrade_insecure_requests()
        
        self.assertIn(CSPDirective.UPGRADE_INSECURE_REQUESTS, policy.directives)
    
    def test_add_block_all_mixed_content(self):
        """
        Test that block-all-mixed-content can be added.
        """
        policy = CSPPolicy()
        policy.add_block_all_mixed_content()
        
        self.assertIn(CSPDirective.BLOCK_ALL_MIXED_CONTENT, policy.directives)
    
    def test_set_reporter(self):
        """
        Test that a reporter can be set.
        """
        policy = CSPPolicy()
        reporter = CSPViolationReporter(report_uri="/report-uri")
        policy.set_reporter(reporter)
        
        self.assertEqual(policy.reporter, reporter)
    
    def test_to_header_value(self):
        """
        Test that the header value is generated correctly.
        """
        policy = CSPPolicy()
        policy.add_default_src(CSPSource.SELF)
        policy.add_script_src([CSPSource.SELF, CSPSource.UNSAFE_INLINE])
        
        header_value = policy.to_header_value()
        
        self.assertIn("default-src 'self'", header_value)
        # Check that script-src directive contains both sources without requiring a specific order
        self.assertIn("script-src", header_value)
        self.assertIn("'self'", header_value)
        self.assertIn("'unsafe-inline'", header_value)
        
        # Verify that the script-src directive contains both required values
        script_src_part = [part for part in header_value.split("; ") if part.startswith("script-src")][0]
        self.assertIn("'self'", script_src_part)
        self.assertIn("'unsafe-inline'", script_src_part)
    
    def test_to_header_value_with_reporter(self):
        """
        Test that the header value with a reporter is generated correctly.
        """
        policy = CSPPolicy()
        policy.add_default_src(CSPSource.SELF)
        reporter = CSPViolationReporter(report_uri="/report-uri", report_to="default")
        policy.set_reporter(reporter)
        
        header_value = policy.to_header_value()
        
        self.assertIn("default-src 'self'", header_value)
        self.assertIn("report-uri /report-uri", header_value)
        self.assertIn("report-to default", header_value)
    
    def test_get_header_name(self):
        """
        Test that the header name is generated correctly.
        """
        policy = CSPPolicy()
        self.assertEqual(policy.get_header_name(), "Content-Security-Policy")
        
        policy.report_only = True
        self.assertEqual(policy.get_header_name(), "Content-Security-Policy-Report-Only")


@pytest.fixture
def csp_middleware():
    """
    Fixture for creating a CSP middleware instance with specific settings.
    """
    policy = CSPPolicy()
    policy.add_default_src(CSPSource.SELF)
    
    return CSPMiddleware(
        policy=policy,
        exempt_paths=["/exempt"]
    )


@pytest.fixture
def csp_middleware_with_regex():
    """
    Fixture for creating a CSP middleware instance with regex exempt paths.
    """
    policy = CSPPolicy()
    policy.add_default_src(CSPSource.SELF)
    
    return CSPMiddleware(
        policy=policy,
        exempt_path_regex=r"^/api/.*$"
    )


@pytest.mark.asyncio
async def test_process_request(csp_middleware):
    """
    Test that the middleware adds CSP headers to responses.
    """
    request = MockRequest()
    response = MockResponse()
    
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [csp_middleware], response, request
    )
    
    # CSP headers should be added
    assert "Content-Security-Policy" in processed_response.headers
    assert "default-src 'self'" in processed_response.headers["Content-Security-Policy"]


@pytest.mark.asyncio
async def test_exempt_path(csp_middleware):
    """
    Test that exempt paths are not affected by CSP.
    """
    request = MockRequest(path="/exempt")
    response = MockResponse()
    
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [csp_middleware], response, request
    )
    
    # No CSP headers should be added for exempt paths
    assert "Content-Security-Policy" not in processed_response.headers


@pytest.mark.asyncio
async def test_exempt_path_regex(csp_middleware_with_regex):
    """
    Test that exempt path regex works.
    """
    request = MockRequest(path="/api/v1/resource")
    response = MockResponse()
    
    processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [csp_middleware_with_regex], response, request
    )
    
    # No CSP headers should be added for paths matching the regex
    assert "Content-Security-Policy" not in processed_response.headers


class TestCSPBuilder:
    """
    Tests for the CSPBuilder class.
    """
    
    def test_create_default_policy(self):
        """
        Test that the default policy is created correctly.
        """
        middleware = CSPMiddleware()
        policy = middleware._create_default_policy()
        
        # Default policy should have default-src 'self'
        assert CSPDirective.DEFAULT_SRC in policy.directives
        assert CSPSource.SELF in policy.directives[CSPDirective.DEFAULT_SRC]

    def test_create_api_policy(self):
        """
        Test that the API policy is created correctly.
        """
        policy = CSPBuilder.create_api_policy()
        
        # API policy should have default-src 'none' and other API-specific directives
        assert CSPDirective.DEFAULT_SRC in policy.directives
        assert CSPSource.NONE in policy.directives[CSPDirective.DEFAULT_SRC]

    def test_create_web_policy(self):
        """
        Test that the web policy is created correctly.
        """
        policy = CSPBuilder.create_web_policy()
        
        # Web policy should have default-src 'self' and other web-specific directives
        assert CSPDirective.DEFAULT_SRC in policy.directives
        assert CSPSource.SELF in policy.directives[CSPDirective.DEFAULT_SRC]

    def test_create_strict_policy(self):
        """
        Test that the strict policy is created correctly.
        """
        policy = CSPBuilder.create_strict_policy()
        
        # Strict policy should have strict directives
        assert CSPDirective.DEFAULT_SRC in policy.directives
        assert CSPSource.NONE in policy.directives[CSPDirective.DEFAULT_SRC]
        assert CSPDirective.SCRIPT_SRC in policy.directives
        assert CSPSource.SELF in policy.directives[CSPDirective.SCRIPT_SRC]

    def test_create_report_only_policy(self):
        """
        Test that the report-only policy is created correctly.
        """
        policy = CSPBuilder.create_report_only_policy("/report-uri")
        
        # Report-only policy should be marked as report-only and have a report-uri
        assert policy.report_only is True
        assert policy.reporter is not None
        assert policy.reporter.report_uri == "/report-uri"


if __name__ == "__main__":
    unittest.main() 