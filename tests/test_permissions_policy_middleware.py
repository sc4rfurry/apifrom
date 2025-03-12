"""
Tests for the Permissions Policy middleware.
"""

import unittest
from unittest.mock import MagicMock, AsyncMock
import pytest

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.security.permissions_policy import (
    PermissionsPolicyMiddleware,
    PermissionsPolicy,
    PermissionsDirective,
    PermissionsAllowlist,
    PermissionsPolicyBuilder,
)
from tests.middleware_test_helper import AsyncMiddlewareTester, MockRequest, MockResponse


class TestPermissionsDirective(unittest.TestCase):
    """
    Tests for the PermissionsDirective class.
    """
    
    def test_directives(self):
        """
        Test that directives are defined correctly.
        """
        self.assertEqual(PermissionsDirective.ACCELEROMETER, "accelerometer")
        self.assertEqual(PermissionsDirective.AMBIENT_LIGHT_SENSOR, "ambient-light-sensor")
        self.assertEqual(PermissionsDirective.AUTOPLAY, "autoplay")
        self.assertEqual(PermissionsDirective.CAMERA, "camera")
        self.assertEqual(PermissionsDirective.DISPLAY_CAPTURE, "display-capture")
        self.assertEqual(PermissionsDirective.DOCUMENT_DOMAIN, "document-domain")
        self.assertEqual(PermissionsDirective.ENCRYPTED_MEDIA, "encrypted-media")
        self.assertEqual(PermissionsDirective.EXECUTION_WHILE_NOT_RENDERED, "execution-while-not-rendered")
        self.assertEqual(PermissionsDirective.EXECUTION_WHILE_OUT_OF_VIEWPORT, "execution-while-out-of-viewport")
        self.assertEqual(PermissionsDirective.FULLSCREEN, "fullscreen")
        self.assertEqual(PermissionsDirective.GYROSCOPE, "gyroscope")
        self.assertEqual(PermissionsDirective.MAGNETOMETER, "magnetometer")
        self.assertEqual(PermissionsDirective.MICROPHONE, "microphone")
        self.assertEqual(PermissionsDirective.MIDI, "midi")
        self.assertEqual(PermissionsDirective.NAVIGATION_OVERRIDE, "navigation-override")
        self.assertEqual(PermissionsDirective.PAYMENT, "payment")
        self.assertEqual(PermissionsDirective.PICTURE_IN_PICTURE, "picture-in-picture")
        self.assertEqual(PermissionsDirective.SCREEN_WAKE_LOCK, "screen-wake-lock")
        self.assertEqual(PermissionsDirective.SYNC_XHR, "sync-xhr")
        self.assertEqual(PermissionsDirective.USB, "usb")
        self.assertEqual(PermissionsDirective.WEB_SHARE, "web-share")
        self.assertEqual(PermissionsDirective.XR_SPATIAL_TRACKING, "xr-spatial-tracking")


class TestPermissionsAllowlist(unittest.TestCase):
    """
    Tests for the PermissionsAllowlist class.
    """
    
    def test_allowlist_values(self):
        """
        Test that allowlist values are defined correctly.
        """
        self.assertEqual(PermissionsAllowlist.NONE, "none")
        self.assertEqual(PermissionsAllowlist.SELF, "self")
        self.assertEqual(PermissionsAllowlist.SRC, "src")
        self.assertEqual(PermissionsAllowlist.ANY, "*")


class TestPermissionsPolicy(unittest.TestCase):
    """
    Tests for the PermissionsPolicy class.
    """
    
    def setUp(self):
        """
        Set up the test environment.
        """
        self.policy = PermissionsPolicy()
    
    def test_add_directive(self):
        """
        Test that directives can be added.
        """
        self.policy.add_directive(PermissionsDirective.CAMERA, PermissionsAllowlist.NONE)
        
        self.assertIn(PermissionsDirective.CAMERA, self.policy.directives)
        self.assertEqual(set(['']), self.policy.directives[PermissionsDirective.CAMERA])
    
    def test_add_directive_with_self(self):
        """
        Test that directives can be added with 'self'.
        """
        self.policy.add_directive(PermissionsDirective.CAMERA, PermissionsAllowlist.SELF)
        
        self.assertIn(PermissionsDirective.CAMERA, self.policy.directives)
        self.assertEqual(set(["'self'"]), self.policy.directives[PermissionsDirective.CAMERA])
    
    def test_add_directive_with_src(self):
        """
        Test that directives can be added with 'src'.
        """
        self.policy.add_directive(PermissionsDirective.CAMERA, PermissionsAllowlist.SRC)
        
        self.assertIn(PermissionsDirective.CAMERA, self.policy.directives)
        self.assertEqual(set(["'src'"]), self.policy.directives[PermissionsDirective.CAMERA])
    
    def test_add_directive_with_any(self):
        """
        Test that directives can be added with '*'.
        """
        self.policy.add_directive(PermissionsDirective.CAMERA, PermissionsAllowlist.ANY)
        
        self.assertIn(PermissionsDirective.CAMERA, self.policy.directives)
        self.assertEqual(set(['*']), self.policy.directives[PermissionsDirective.CAMERA])
    
    def test_add_directive_with_origin(self):
        """
        Test that directives can be added with an origin.
        """
        self.policy.add_directive(PermissionsDirective.CAMERA, "https://example.com")
        
        self.assertIn(PermissionsDirective.CAMERA, self.policy.directives)
        self.assertEqual(set(['https://example.com']), self.policy.directives[PermissionsDirective.CAMERA])
    
    def test_add_directive_with_list(self):
        """
        Test that directives can be added with a list of origins.
        """
        self.policy.add_directive(PermissionsDirective.CAMERA, ["https://example.com", "https://example.org"])
        
        self.assertIn(PermissionsDirective.CAMERA, self.policy.directives)
        self.assertEqual(set(['https://example.com', 'https://example.org']), self.policy.directives[PermissionsDirective.CAMERA])
    
    def test_disable_all(self):
        """
        Test that all features can be disabled.
        """
        self.policy.disable_all()
        
        for directive in PermissionsDirective.ALL:
            self.assertIn(directive, self.policy.directives)
            self.assertEqual(set(['']), self.policy.directives[directive])
    
    def test_enable_for_self(self):
        """
        Test that features can be enabled for 'self'.
        """
        self.policy.enable_for_self([PermissionsDirective.CAMERA, PermissionsDirective.MICROPHONE])
        
        self.assertIn(PermissionsDirective.CAMERA, self.policy.directives)
        self.assertEqual(set(["'self'"]), self.policy.directives[PermissionsDirective.CAMERA])
        
        self.assertIn(PermissionsDirective.MICROPHONE, self.policy.directives)
        self.assertEqual(set(["'self'"]), self.policy.directives[PermissionsDirective.MICROPHONE])
    
    def test_to_header_value(self):
        """
        Test that the header value is generated correctly.
        """
        self.policy.add_directive(PermissionsDirective.CAMERA, PermissionsAllowlist.NONE)
        self.policy.add_directive(PermissionsDirective.MICROPHONE, PermissionsAllowlist.SELF)
        self.policy.add_directive(PermissionsDirective.GEOLOCATION, ["https://example.com", "https://example.org"])
        
        header_value = self.policy.to_header_value()
        
        self.assertIn("camera=()", header_value)
        self.assertIn("microphone=('self')", header_value)
        self.assertIn("geolocation=(", header_value)
        self.assertIn("https://example.com", header_value)
        self.assertIn("https://example.org", header_value)


class TestPermissionsPolicyMiddleware(unittest.TestCase):
    """
    Tests for the PermissionsPolicyMiddleware class.
    """
    
    def setUp(self):
        """
        Set up the test environment.
        """
        self.policy = PermissionsPolicy()
        self.policy.add_directive(PermissionsDirective.CAMERA, PermissionsAllowlist.NONE)
        
        self.middleware = PermissionsPolicyMiddleware(
            policy=self.policy,
            exempt_paths=["/exempt"]
        )
    
    def test_create_default_policy(self):
        """
        Test that the default policy is created correctly.
        """
        middleware = PermissionsPolicyMiddleware()
        policy = middleware._create_default_policy()
        
        # Default policy should have geolocation=none
        self.assertIn(PermissionsDirective.GEOLOCATION, policy.directives)
        self.assertEqual(set(['']), policy.directives[PermissionsDirective.GEOLOCATION])
    
    def test_is_exempt(self):
        """
        Test that exempt paths are correctly identified.
        """
        # Test exempt path
        request = Request(
            method="GET",
            path="/exempt",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        self.assertTrue(self.middleware._is_exempt(request))
        
        # Test non-exempt path
        request = Request(
            method="GET",
            path="/not-exempt",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        self.assertFalse(self.middleware._is_exempt(request))

        # Test with regex pattern
        middleware = PermissionsPolicyMiddleware(
            policy=self.policy,
            exempt_paths=["/api"]  # Use a simple path that will match exactly
        )
        
        # Test exempt path with regex
        request = Request(
            method="GET",
            path="/api",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        self.assertTrue(middleware._is_exempt(request))


@pytest.fixture
def permissions_middleware():
    """Create a PermissionsPolicyMiddleware instance for testing."""
    policy = PermissionsPolicy()
    policy.add_directive(PermissionsDirective.CAMERA, PermissionsAllowlist.NONE)
    
    return PermissionsPolicyMiddleware(
        policy=policy,
        exempt_paths=["/exempt"]
    )


@pytest.mark.asyncio
async def test_process_request(permissions_middleware):
    """
    Test that the middleware adds Permissions-Policy headers to responses.
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
    
    response = Response(content="Test", status_code=200)
    
    # Process the request with the middleware
    result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [permissions_middleware],
        response,
        request
    )
    
    # Check that the Permissions-Policy header was added
    assert "Permissions-Policy" in result.headers
    assert "camera=()" in result.headers["Permissions-Policy"]


@pytest.mark.asyncio
async def test_exempt_path(permissions_middleware):
    """
    Test that exempt paths are not affected by the Permissions-Policy middleware.
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
    
    response = Response(content="Test", status_code=200)
    
    # Process the request with the middleware
    result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
        [permissions_middleware],
        response,
        request
    )
    
    # Check that the Permissions-Policy header was not added
    assert "Permissions-Policy" not in result.headers


class TestPermissionsPolicyBuilder(unittest.TestCase):
    """
    Tests for the PermissionsPolicyBuilder class.
    """
    
    def test_create_strict_policy(self):
        """
        Test that the strict policy is created correctly.
        """
        policy = PermissionsPolicyBuilder.create_strict_policy()
        
        for directive in PermissionsDirective.ALL:
            self.assertIn(directive, policy.directives)
            self.assertEqual(policy.directives[directive], set(['']))
    
    def test_create_minimal_policy(self):
        """
        Test that the minimal policy is created correctly.
        """
        policy = PermissionsPolicyBuilder.create_minimal_policy()
        
        self.assertIn(PermissionsDirective.CAMERA, policy.directives)
        self.assertIn(PermissionsDirective.MICROPHONE, policy.directives)
        self.assertIn(PermissionsDirective.GEOLOCATION, policy.directives)
        self.assertIn(PermissionsDirective.PAYMENT, policy.directives)
        self.assertIn(PermissionsDirective.USB, policy.directives)
        self.assertIn(PermissionsDirective.MIDI, policy.directives)
        self.assertIn(PermissionsDirective.SYNC_XHR, policy.directives)
    
    def test_create_api_policy(self):
        """
        Test that the API policy is created correctly.
        """
        policy = PermissionsPolicyBuilder.create_api_policy()
        
        # Check that all directives are disabled
        for directive in PermissionsDirective.ALL:
            self.assertIn(directive, policy.directives)
        
        # Check that specific directives are enabled for 'self'
        self.assertEqual(policy.directives[PermissionsDirective.SYNC_XHR], set(["'self'"]))
        self.assertEqual(policy.directives[PermissionsDirective.FORMS], set(["'self'"]))
        self.assertEqual(policy.directives[PermissionsDirective.VERTICAL_SCROLL], set(["'self'"]))
    
    def test_create_web_policy(self):
        """
        Test that the web policy is created correctly.
        """
        policy = PermissionsPolicyBuilder.create_web_policy()
        
        # Check that sensitive features are disabled
        self.assertEqual(policy.directives[PermissionsDirective.CAMERA], set(['']))
        self.assertEqual(policy.directives[PermissionsDirective.MICROPHONE], set(['']))
        self.assertEqual(policy.directives[PermissionsDirective.GEOLOCATION], set(['']))
        self.assertEqual(policy.directives[PermissionsDirective.PAYMENT], set(['']))
        self.assertEqual(policy.directives[PermissionsDirective.USB], set(['']))
        self.assertEqual(policy.directives[PermissionsDirective.MIDI], set(['']))
        
        # Check that some features are enabled for 'self'
        self.assertEqual(policy.directives[PermissionsDirective.FULLSCREEN], set(["'self'"]))
        self.assertEqual(policy.directives[PermissionsDirective.PICTURE_IN_PICTURE], set(["'self'"]))
        self.assertEqual(policy.directives[PermissionsDirective.AUTOPLAY], set(["'self'"]))
        self.assertEqual(policy.directives[PermissionsDirective.CLIPBOARD_READ], set(["'self'"]))
        self.assertEqual(policy.directives[PermissionsDirective.CLIPBOARD_WRITE], set(["'self'"]))


if __name__ == "__main__":
    unittest.main() 