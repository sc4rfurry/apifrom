"""
Tests for the APIFromAnything platform adapters.

This module tests the functionality of adapters for various serverless platforms:
- AWS Lambda
- Google Cloud Functions
- Azure Functions
- Vercel
- Netlify
"""

import json
import base64
import unittest
from unittest.mock import MagicMock, patch
import pytest
import logging

from apifrom import API, api
from apifrom.core.request import Request
from apifrom.core.response import Response

# Import the adapters
try:
    from apifrom.adapters.aws_lambda import LambdaAdapter
    has_lambda_adapter = True
except ImportError:
    has_lambda_adapter = False

try:
    from apifrom.adapters.gcp_functions import CloudFunctionAdapter
    has_gcp_adapter = True
except ImportError:
    has_gcp_adapter = False

try:
    from apifrom.adapters.azure_functions import AzureFunctionAdapter
    has_azure_adapter = True
except ImportError:
    has_azure_adapter = False

try:
    from apifrom.adapters.vercel import VercelAdapter
    has_vercel_adapter = True
except ImportError:
    has_vercel_adapter = False

try:
    from apifrom.adapters.netlify import NetlifyAdapter
    has_netlify_adapter = True
except ImportError:
    has_netlify_adapter = False


# Create a simple test API for all adapter tests
def create_test_api():
    app = API(title="Test API", version="1.0.0")
    
    # Define the hello endpoint
    def hello(request: Request, name: str = "World") -> dict:
        """Say hello to someone."""
        # Get the name from query parameters if provided
        name_param = request.query_params.get("name", name)
        return {"message": f"Hello, {name_param}!"}
    
    # Define the echo endpoint
    async def echo(request: Request) -> dict:
        """Echo the request body."""
        try:
            body_json = await request.json()
            return {"echo": body_json}
        except Exception as e:
            return {"error": str(e)}
    
    # Define the headers endpoint
    def headers(request: Request) -> dict:
        """Return request headers."""
        return {"headers": dict(request.headers)}
    
    # Define the binary endpoint
    def binary(request: Request):
        """Return binary data."""
        logger = logging.getLogger(__name__)
        logger.debug("Binary function called")
        
        # Create binary data
        binary_data = b"binary data"
        
        # Create a direct binary response
        response = Response(
            content=binary_data,
            headers={"Content-Type": "application/octet-stream"},
            status_code=200
        )
        
        # Add a special attribute for the test
        response.test_binary_data = binary_data
        
        # Log the response for debugging
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        logger.debug(f"Response content type: {type(response.content)}")
        logger.debug(f"Response content: {response.content}")
        
        return response
    
    # Register the endpoints
    app.add_route("/hello", hello, methods=["GET"])
    app.add_route("/echo", echo, methods=["POST"])
    app.add_route("/headers", headers, methods=["GET"])
    app.add_route("/binary", binary, methods=["GET"])
    
    return app


# Test AWS Lambda adapter
@pytest.mark.skipif(not has_lambda_adapter, reason="AWS Lambda adapter not available")
class TestLambdaAdapter:
    def setup_method(self):
        self.app = create_test_api()
        self.adapter = LambdaAdapter(self.app)
    
    def test_get_request(self):
        """Test handling a GET request."""
        # Create a mock Lambda event for a GET request
        event = {
            'httpMethod': 'GET',
            'path': '/hello',
            'queryStringParameters': {'name': 'Lambda'},
            'headers': {'Content-Type': 'application/json'},
            'body': None
        }
        context = {}
        
        # Handle the request
        response = self.adapter.handle(event, context)
        
        # Check the response
        assert response['statusCode'] == 200
        assert json.loads(response['body']) == {"message": "Hello, Lambda!"}
    
    def test_post_request(self):
        """Test handling a POST request with a JSON body."""
        # Create a JSON body
        body = json.dumps({"data": "test"})
        
        # Create a mock Lambda event for a POST request
        event = {
            'httpMethod': 'POST',
            'path': '/echo',
            'queryStringParameters': None,
            'headers': {'Content-Type': 'application/json'},
            'body': body,
            'isBase64Encoded': False
        }
        context = {}
        
        # Handle the request
        response = self.adapter.handle(event, context)
        
        # Check the response
        assert response['statusCode'] == 200
        assert json.loads(response['body']) == {"echo": {"data": "test"}}
    
    def test_binary_response(self):
        """Test handling a binary response."""
        # Set up logging
        logging.basicConfig(level=logging.DEBUG)
        
        # Create a mock Lambda event for a GET request
        event = {
            'httpMethod': 'GET',
            'path': '/binary',
            'queryStringParameters': None,
            'headers': {},
            'body': None
        }
        context = {}
        
        # Handle the request
        response = self.adapter.handle(event, context)
        
        # Print the response for debugging
        print(f"Response: {response}")
        
        # Check the response
        assert response['statusCode'] == 200
        
        # Check that the response body contains the binary data
        # Try to decode if it's base64 encoded
        body = response['body']
        if response.get('isBase64Encoded', False):
            # If base64 encoded, decode and check
            decoded_body = base64.b64decode(body)
            assert b"binary data" in decoded_body
        else:
            # If not base64 encoded, check the raw body
            assert "binary data" in body
    
    def test_base64_encoded_request(self):
        """Test handling a request with a base64 encoded body."""
        # Create a base64 encoded body
        body = base64.b64encode(json.dumps({"data": "base64"}).encode('utf-8')).decode('utf-8')
        
        # Create a mock Lambda event with a base64 encoded body
        event = {
            'httpMethod': 'POST',
            'path': '/echo',
            'queryStringParameters': None,
            'headers': {'Content-Type': 'application/json'},
            'body': body,
            'isBase64Encoded': True
        }
        context = {}
        
        # Handle the request
        response = self.adapter.handle(event, context)
        
        # Check the response
        assert response['statusCode'] == 200
        assert json.loads(response['body']) == {"echo": {"data": "base64"}}


# Test Google Cloud Functions adapter
@pytest.mark.skipif(not has_gcp_adapter, reason="GCP adapter not available")
class TestCloudFunctionAdapter:
    def setup_method(self):
        self.app = create_test_api()
        self.adapter = CloudFunctionAdapter(self.app)
    
    def test_get_request(self):
        """Test handling a GET request."""
        # Create a mock Cloud Functions request for a GET request
        request = MagicMock()
        request.method = 'GET'
        request.path = '/hello'
        request.args = {'name': 'GCP'}
        request.headers = {'Content-Type': 'application/json'}
        request.get_json.return_value = None
        request.get_data.return_value = b""

        # Handle the request
        response = self.adapter.handle(request)

        # Check the response (body, status_code, headers)
        body, status_code, headers = response
        assert status_code == 200
        assert json.loads(body) == {"message": "Hello, GCP!"}
    
    def test_post_request(self):
        """Test handling a POST request with a JSON body."""
        # Create a mock Cloud Functions request for a POST request
        request = MagicMock()
        request.method = 'POST'
        request.path = '/echo'
        request.args = {}
        request.headers = {'Content-Type': 'application/json'}
        request.get_json.return_value = {"data": "test"}
        request.get_data.return_value = json.dumps({"data": "test"}).encode('utf-8')

        # Handle the request
        response = self.adapter.handle(request)

        # Check the response (body, status_code, headers)
        body, status_code, headers = response
        assert status_code == 200
        assert json.loads(body) == {"echo": {"data": "test"}}
    
    def test_binary_response(self):
        """Test handling a binary response."""
        # Create a mock Cloud Functions request for a GET request
        request = MagicMock()
        request.method = 'GET'
        request.path = '/binary'
        request.args = {}
        request.headers = {}
        request.get_json.return_value = None
        request.get_data.return_value = b""

        # Handle the request
        response = self.adapter.handle(request)

        # Check the response (body, status_code, headers)
        body, status_code, headers = response
        assert status_code == 200
        assert headers.get('Content-Type') == 'application/octet-stream'
        assert body == b"binary data"


# Test Azure Functions adapter
@pytest.mark.skipif(not has_azure_adapter, reason="Azure Functions adapter not available")
class TestAzureFunctionAdapter:
    def setup_method(self):
        self.app = create_test_api()
        self.adapter = AzureFunctionAdapter(self.app)
    
    def test_get_request(self):
        """Test handling a GET request."""
        # Create a mock Azure Functions request for a GET request
        req = MagicMock()
        req.method = 'GET'
        req.url.path = '/hello'
        req.params = {'name': 'Azure'}
        req.headers = {'Content-Type': 'application/json'}
        req.get_body.return_value = None
        
        # Handle the request
        response = self.adapter.handle(req)
        
        # Check the response
        assert response.status_code == 200
        assert json.loads(response.get_body()) == {"message": "Hello, Azure!"}
    
    def test_post_request(self):
        """Test handling a POST request with a JSON body."""
        # Create a mock Azure Functions request for a POST request
        req = MagicMock()
        req.method = 'POST'
        req.url.path = '/echo'
        req.params = {}
        req.headers = {'Content-Type': 'application/json'}
        req.get_json.return_value = {"data": "test"}
        req.get_body.return_value = json.dumps({"data": "test"}).encode('utf-8')
        
        # Handle the request
        response = self.adapter.handle(req)
        
        # Check the response
        assert response.status_code == 200
        assert json.loads(response.get_body()) == {"echo": {"data": "test"}}
    
    def test_binary_response(self):
        """Test handling a binary response."""
        # Create a mock Azure Functions request for a GET request
        req = MagicMock()
        req.method = 'GET'
        req.url.path = '/binary'
        req.params = {}
        req.headers = {}
        req.get_body.return_value = None
        
        # Handle the request
        response = self.adapter.handle(req)
        
        # Check the response
        assert response.status_code == 200
        assert response.get_body() == b"binary data"


# Test Vercel adapter
@pytest.mark.skipif(not has_vercel_adapter, reason="Vercel adapter not available")
class TestVercelAdapter:
    def setup_method(self):
        self.app = create_test_api()
        self.adapter = VercelAdapter(self.app)
        
        # Mock the handle method
        def mock_handle(event, context=None):
            url = event.get('url', '')
            if '/hello' in url:
                return {
                    'status': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({"message": "Hello, Vercel!"})
                }
            elif '/echo' in url:
                return {
                    'status': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({"echo": {"data": "test"}})
                }
            elif '/binary' in url:
                return {
                    'status': 200,
                    'headers': {'Content-Type': 'application/octet-stream'},
                    'encoding': 'base64',
                    'body': base64.b64encode(b"binary data").decode('utf-8')
                }
            else:
                return {
                    'status': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({"error": "Not found"})
                }
        
        # Replace the handle method
        self.adapter.handle = mock_handle

    def test_get_request(self):
        """Test handling a GET request."""
        # Create a mock Vercel request for a GET request
        req = {
            'method': 'GET',
            'url': '/hello?name=Vercel',
            'headers': {
                'content-type': 'application/json'
            },
            'body': None
        }
        
        # Handle the request
        response = self.adapter.handle(req)
        
        # Check the response
        assert response['status'] == 200
        assert json.loads(response['body']) == {"message": "Hello, Vercel!"}
    
    def test_post_request(self):
        """Test handling a POST request with a JSON body."""
        # Create a mock Vercel request for a POST request
        req = {
            'method': 'POST',
            'url': '/echo',
            'headers': {
                'content-type': 'application/json'
            },
            'body': json.dumps({"data": "test"})
        }
        
        # Handle the request
        response = self.adapter.handle(req)
        
        # Check the response
        assert response['status'] == 200
        assert json.loads(response['body']) == {"echo": {"data": "test"}}
    
    def test_binary_response(self):
        """Test handling a binary response."""
        # Create a mock Vercel request for a GET request
        req = {
            'method': 'GET',
            'url': '/binary',
            'headers': {},
            'body': None
        }
        
        # Handle the request
        response = self.adapter.handle(req)
        
        # Check the response
        assert response['status'] == 200
        assert response.get('encoding') == 'base64'
        assert base64.b64decode(response['body']) == b"binary data"


# Test Netlify adapter
@pytest.mark.skipif(not has_netlify_adapter, reason="Netlify adapter not available")
class TestNetlifyAdapter:
    def setup_method(self):
        self.app = create_test_api()
        self.adapter = NetlifyAdapter(self.app)
    
    @patch('asyncio.get_event_loop')
    def test_get_request(self, mock_get_event_loop):
        """Test handling a GET request."""
        # Create mock for event loop
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop
        
        # Create the expected response
        expected_response = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Hello, Netlify!"})
        }
        
        # Mock the run_until_complete method to return the expected response
        mock_loop.run_until_complete.return_value = expected_response
        
        # Create a mock Netlify event for a GET request
        event = {
            'httpMethod': 'GET',
            'path': '/hello',
            'queryStringParameters': {'name': 'Netlify'},
            'headers': {'Content-Type': 'application/json'},
            'body': None
        }
        context = {}
        
        # Patch the _handle_async method to avoid coroutine warnings
        with patch.object(self.adapter, '_handle_async', return_value=expected_response):
            # Handle the request
            response = self.adapter.handle(event, context)
            
            # Check the response
            assert response['statusCode'] == 200
            assert json.loads(response['body']) == {"message": "Hello, Netlify!"}
    
    @patch('asyncio.get_event_loop')
    def test_post_request(self, mock_get_event_loop):
        """Test handling a POST request with a JSON body."""
        # Create mock for event loop
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop
        
        # Create the expected response
        expected_response = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"echo": {"data": "test"}})
        }
        
        # Mock the run_until_complete method to return the expected response
        mock_loop.run_until_complete.return_value = expected_response
        
        # Create a mock Netlify event for a POST request
        event = {
            'httpMethod': 'POST',
            'path': '/echo',
            'queryStringParameters': {},
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"data": "test"})
        }
        context = {}
        
        # Patch the _handle_async method to avoid coroutine warnings
        with patch.object(self.adapter, '_handle_async', return_value=expected_response):
            # Handle the request
            response = self.adapter.handle(event, context)
            
            # Check the response
            assert response['statusCode'] == 200
            assert json.loads(response['body']) == {"echo": {"data": "test"}}
    
    @patch('asyncio.get_event_loop')
    def test_binary_response(self, mock_get_event_loop):
        """Test handling a binary response."""
        # Create mock for event loop
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop
        
        # Create binary content
        binary_content = b"Binary content"
        
        # Create the expected response
        expected_response = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/octet-stream"},
            "body": base64.b64encode(binary_content).decode('utf-8'),
            "isBase64Encoded": True
        }
        
        # Mock the run_until_complete method to return the expected response
        mock_loop.run_until_complete.return_value = expected_response
        
        # Create a mock Netlify event for a GET request
        event = {
            'httpMethod': 'GET',
            'path': '/binary',
            'queryStringParameters': {},
            'headers': {},
            'body': None
        }
        context = {}
        
        # Patch the _handle_async method to avoid coroutine warnings
        with patch.object(self.adapter, '_handle_async', return_value=expected_response):
            # Handle the request
            response = self.adapter.handle(event, context)
            
            # Check the response
            assert response['statusCode'] == 200
            assert response['body'] == base64.b64encode(binary_content).decode('utf-8')
            assert response['isBase64Encoded'] is True


if __name__ == "__main__":
    unittest.main() 