"""
Tests for the Permissions Policy middleware using async/await syntax.
"""

import pytest
from typing import Dict, Any, Optional, List

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.security.permissions_policy import (
    PermissionsPolicyMiddleware,
    PermissionsPolicy,
    PermissionsDirective,
    PermissionsAllowlist,
    PermissionsPolicyBuilder,
)
from tests.middleware_test_helper import AsyncMiddlewareTester


class TestPermissionsPolicyMiddleware:
    """
    Tests for the PermissionsPolicyMiddleware class using async/await syntax.
    """
    
    @pytest.fixture
    def permissions_policy(self):
        """
        Create a permissions policy for testing.
        
        Returns:
            A PermissionsPolicy instance
        """
        policy = PermissionsPolicy()
        policy.add_directive(PermissionsDirective.CAMERA, PermissionsAllowlist.NONE)
        policy.add_directive(PermissionsDirective.FULLSCREEN, PermissionsAllowlist.SELF)
        return policy
    
    @pytest.fixture
    def permissions_middleware(self, permissions_policy):
        """
        Create a permissions policy middleware for testing.
        
        Args:
            permissions_policy: The permissions policy to use
            
        Returns:
            A PermissionsPolicyMiddleware instance
        """
        return PermissionsPolicyMiddleware(
            policy=permissions_policy,
            exempt_paths=["/exempt"]
        )
    
    def test_create_default_policy(self):
        """
        Test that the default policy is created correctly.
        """
        middleware = PermissionsPolicyMiddleware()
        policy = middleware._create_default_policy()
        
        assert PermissionsDirective.CAMERA in policy.directives
        assert PermissionsDirective.MICROPHONE in policy.directives
        assert PermissionsDirective.GEOLOCATION in policy.directives
        assert PermissionsDirective.PAYMENT in policy.directives
        assert PermissionsDirective.USB in policy.directives
        assert PermissionsDirective.MIDI in policy.directives
        assert PermissionsDirective.SYNC_XHR in policy.directives
    
    def test_is_exempt(self, permissions_middleware):
        """
        Test that exempt paths are correctly identified.
        """
        # Test with exempt path
        request = Request(
            method="GET",
            path="/exempt",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        assert permissions_middleware._is_exempt(request) is True
        
        # Test with non-exempt path
        request = Request(
            method="GET",
            path="/",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        assert permissions_middleware._is_exempt(request) is False
        
        # Test with path that starts with exempt path
        request = Request(
            method="GET",
            path="/exempt/subpath",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        assert permissions_middleware._is_exempt(request) is True
    
    @pytest.mark.asyncio
    async def test_process_request(self, permissions_middleware):
        """
        Test that the middleware adds the Permissions-Policy header.
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
        
        response = Response(
            content="Test response",
            status_code=200,
            headers={}
        )
        
        result = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [permissions_middleware],
            response,
            request
        )
        
        assert "Permissions-Policy" in result.headers
        assert "camera=()" in result.headers["Permissions-Policy"]
        assert "fullscreen=('self')" in result.headers["Permissions-Policy"]
    
    @pytest.mark.asyncio
    async def test_exempt_path(self, permissions_middleware):
        """
        Test that exempt paths do not get the Permissions-Policy header.
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
            [permissions_middleware],
            response,
            request
        )
        
        assert "Permissions-Policy" not in result.headers 