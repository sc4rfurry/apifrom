"""
Tests for the adapters module with async/await syntax.
"""

import pytest
import json
import base64
from unittest.mock import patch, MagicMock, AsyncMock

from apifrom.adapters.netlify import NetlifyAdapter
from apifrom.core.app import API
from apifrom.core.request import Request
from apifrom.core.response import Response


@pytest.fixture
def app():
    """Create an API instance for testing."""
    return API()


@pytest.fixture
def netlify_adapter(app):
    """Create a NetlifyAdapter instance with the app."""
    adapter = NetlifyAdapter(app)
    return adapter


@pytest.mark.asyncio
@patch('apifrom.adapters.netlify.NetlifyAdapter._create_request')
async def test_netlify_adapter_request_conversion(mock_create_request):
    """Test that the NetlifyAdapter correctly converts Netlify events to Request objects."""
    # Create a mock request
    mock_request = MagicMock(spec=Request)
    mock_create_request.return_value = mock_request
    
    # Create a mock app with an async process_request method
    mock_app = MagicMock()
    mock_app.process_request = AsyncMock(return_value=Response(
        content={"message": "Hello, World!"},
        status_code=200,
        headers={"Content-Type": "application/json"}
    ))
    
    adapter = NetlifyAdapter(mock_app)
    
    # Create a mock event
    event = {
        "path": "/test",
        "httpMethod": "GET",
        "headers": {"Content-Type": "application/json"},
        "queryStringParameters": {"param1": "value1"},
        "body": None,
        "isBase64Encoded": False
    }
    
    # Create a mock context
    context = MagicMock()
    
    # Handle the request
    response = await adapter._handle_async(event, context)
    
    # Verify the request was correctly created
    mock_create_request.assert_called_once_with(event)
    
    # Verify process_request was called with the request
    mock_app.process_request.assert_called_once_with(mock_request)
    
    # Verify the response was correctly converted
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"message": "Hello, World!"}
    assert response["headers"]["Content-Type"] == "application/json"


@pytest.mark.asyncio
@patch('apifrom.adapters.netlify.NetlifyAdapter._create_request')
async def test_netlify_adapter_binary_response(mock_create_request):
    """Test that the NetlifyAdapter correctly handles binary responses."""
    # Create a mock request
    mock_request = MagicMock(spec=Request)
    mock_create_request.return_value = mock_request
    
    # Create binary content
    binary_content = b"Binary content"
    
    # Create a mock app with an async process_request method
    mock_app = MagicMock()
    mock_app.process_request = AsyncMock(return_value=Response(
        content=binary_content,
        status_code=200,
        headers={"Content-Type": "application/octet-stream"}
    ))
    
    adapter = NetlifyAdapter(mock_app)
    
    # Create a mock event
    event = {
        "path": "/test",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
        "isBase64Encoded": False
    }
    
    # Create a mock context
    context = MagicMock()
    
    # Handle the request
    response = await adapter._handle_async(event, context)
    
    # Verify the response was correctly converted
    assert response["statusCode"] == 200
    assert response["isBase64Encoded"] is True
    # The binary content should be base64 encoded
    assert response["body"] == base64.b64encode(binary_content).decode("utf-8")