"""
Tests for the API decorator using async/await syntax.
"""

import pytest
from unittest.mock import patch, MagicMock

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.decorators.api import api


@pytest.mark.asyncio
async def test_endpoint():
    """
    Test that the API decorator works with async functions.
    """
    # Create a mock request
    request = Request(
        method="GET",
        path="/api/test",
        headers={},
        query_params={},
        body=None
    )
    
    # Create a decorated function
    @api()
    async def test_function(request):
        assert request.method == "GET"
        assert request.path == "/api/test"
        return {"message": "Hello, World!"}
    
    # Call the decorated function
    response = await test_function(request)
    
    # The API decorator returns a JSONResponse from Starlette
    assert response.status_code == 200
    assert response.body == b'{"message":"Hello, World!"}'
    assert "application/json" in response.headers["content-type"] 