import pytest
from typing import Dict, Any, Optional, Type

from apifrom.middleware.error_handling import ErrorHandlingMiddleware
from apifrom.core.response import Response
from apifrom.core.request import Request
from tests.middleware_test_helper import AsyncMiddlewareTester


class CustomException(Exception):
    """Custom exception for testing purposes."""
    pass


class TestErrorHandlingMiddleware:
    """Tests for the ErrorHandlingMiddleware class."""

    @pytest.fixture
    def error_middleware(self) -> ErrorHandlingMiddleware:
        """Fixture for creating an ErrorHandlingMiddleware instance."""
        return ErrorHandlingMiddleware(app=None)

    @pytest.mark.asyncio
    async def test_no_error(self, error_middleware):
        """Test that requests without errors pass through successfully."""
        request = Request(
            method="GET",
            path="/test",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Create a response with no errors
        response = Response({"message": "success"}, status_code=200)
        
        processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [error_middleware],
            response,
            request
        )
        
        assert processed_response.status_code == 200
        assert processed_response.content == {"message": "success"}

    @pytest.mark.asyncio
    async def test_handle_unregistered_error(self, error_middleware):
        """Test handling an unregistered error type."""
        request = Request(
            method="GET",
            path="/test",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        class UnregisteredError(Exception):
            pass
        
        # Add an unregistered error to the request state
        request.state = type('State', (), {})()
        request.state.error = UnregisteredError("Unhandled error")
        
        # Process the request with the error middleware
        response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [error_middleware],
            Response(status_code=500, content={"error": "Internal Server Error"}),
            request
        )
        
        assert response.status_code == 500
        assert "error" in response.content 