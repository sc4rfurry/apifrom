"""
Tests for the monitoring middleware with async support.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.monitoring.middleware import MetricsMiddleware
from apifrom.monitoring.metrics import MetricsCollector
from tests.middleware_test_helper import AsyncMiddlewareTester


@pytest.fixture
def metrics_middleware():
    """Create a MetricsMiddleware instance for testing."""
    collector = MetricsCollector()
    collector.reset()
    middleware = MetricsMiddleware(collector)
    
    # Store the collector on the middleware for access in tests
    middleware.collector = collector
    return middleware


@pytest.mark.asyncio
async def test_request_processing(metrics_middleware):
    """
    Test that the middleware tracks request metrics.
    """
    # Create a request and response
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
    
    # Patch the collector methods
    with patch.object(metrics_middleware.collector, 'track_request', return_value="test_timer") as mock_track:
        with patch.object(metrics_middleware.collector, 'track_request_end') as mock_track_end:
            # Process the request with the middleware
            await metrics_middleware.pre_request(request, "/test")
            
            # Check that track_request was called
            mock_track.assert_called_once_with("/test")
            
            # Process the response
            await metrics_middleware.post_request(request, response)
            
            # Check that track_request_end was called
            mock_track_end.assert_called_once_with("test_timer", "/test", 200)


@pytest.mark.asyncio
async def test_error_processing(metrics_middleware):
    """
    Test that the middleware tracks error metrics.
    """
    # Create a request
    request = Request(
        method="GET",
        path="/test",
        headers={},
        query_params={},
        body=None,
        path_params={},
        client_ip="127.0.0.1"
    )
    
    # Patch the collector methods
    with patch.object(metrics_middleware.collector, 'track_request', return_value="test_timer") as mock_track:
        with patch.object(metrics_middleware.collector, 'track_error') as mock_track_error:
            with patch.object(metrics_middleware.collector, 'track_request_end') as mock_track_end:
                # Process the request
                await metrics_middleware.pre_request(request, "/test")
                
                # Check that track_request was called
                mock_track.assert_called_once_with("/test")
                
                # Process an error
                error = ValueError("Test error")
                await metrics_middleware.on_error(request, error, "/test")
                
                # Check that track_error was called
                mock_track_error.assert_called_once_with("ValueError", "/test")
                
                # Check that track_request_end was called
                mock_track_end.assert_called_once_with("test_timer", "/test", 500) 