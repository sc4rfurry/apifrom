"""
AWS Lambda adapter for APIFromAnything.

This module provides an adapter for running APIFromAnything applications on AWS Lambda
with API Gateway integration.
"""

import json
import base64
from typing import Dict, Any, Optional, Tuple, List, Union
import logging
from types import SimpleNamespace

from apifrom.core.app import API
from apifrom.core.request import Request
from apifrom.core.response import Response

# Configure the logger
logger = logging.getLogger(__name__)

class LambdaAdapter:
    """
    Adapter for running APIFromAnything applications on AWS Lambda.
    
    This adapter translates between AWS Lambda event/context objects and
    APIFromAnything's Request/Response objects.
    """
    
    def __init__(self, app: API):
        """
        Initialize the Lambda adapter.
        
        Args:
            app: The APIFromAnything application to adapt.
        """
        self.app = app
    
    def handle(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle an AWS Lambda event.
        
        Args:
            event: The AWS Lambda event object.
            context: The AWS Lambda context object.
            
        Returns:
            A dictionary that can be returned to API Gateway.
        """
        # Create a request object from the Lambda event
        request = self._create_request(event, context)
        
        # Process the request with the application
        import asyncio
        response = asyncio.run(self.app.process_request(request))
        
        # Convert the response to a Lambda response
        return self._create_lambda_response(response)
    
    def _create_request(self, event: Dict[str, Any], context: Dict[str, Any]) -> Request:
        """
        Create a Request object from a Lambda event.
        
        Args:
            event: The Lambda event.
            context: The Lambda context.
            
        Returns:
            A Request object.
        """
        # Extract request information from the event
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters', {}) or {}
        headers = event.get('headers', {}) or {}
        
        # Handle the body
        body = event.get('body', None)
        if body is not None and event.get('isBase64Encoded', False):
            # Decode base64 encoded body
            body = base64.b64decode(body)
        elif body is not None and isinstance(body, str):
            # Convert string body to bytes
            body = body.encode('utf-8')
        
        # Create the request
        request = Request(
            method=method,
            path=path,
            query_params=query_params,
            headers=headers,
            body=body
        )
        
        # Store the original event and context in the request state
        request.state = SimpleNamespace()
        request.state.aws_event = event
        request.state.aws_context = context
        
        return request
    
    def _create_lambda_response(self, response: Union[Response, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a Lambda response from an APIFromAnything response.
        
        Args:
            response: The APIFromAnything response or a dictionary
            
        Returns:
            A response object that Lambda can understand
        """
        # Check if response is already a dictionary
        if isinstance(response, dict):
            # For direct dictionary responses, create a simple Lambda response
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(response)
            }
        
        # Convert the response to a Lambda-compatible format
        lambda_response = {
            "statusCode": response.status_code,
            "headers": dict(response.headers),
            "isBase64Encoded": False
        }
        
        # Handle different response body types
        if isinstance(response.content, (dict, list)):
            # JSON response
            lambda_response["headers"]["Content-Type"] = "application/json"
            lambda_response["body"] = json.dumps(response.content)
        elif isinstance(response.content, bytes):
            # Binary response
            lambda_response["isBase64Encoded"] = True
            lambda_response["body"] = base64.b64encode(response.content).decode("utf-8")
        else:
            # String response
            lambda_response["body"] = str(response.content)
        
        return lambda_response


# Example usage
if __name__ == "__main__":
    # This code is for demonstration purposes only
    from apifrom.decorators.api import api
    
    # Create an API application
    app = API(title="Lambda API Example")
    
    # Define an API endpoint
    @api(app)
    def hello(name: str = "World") -> Dict[str, str]:
        """Say hello to someone."""
        return {"message": f"Hello, {name}!"}
    
    # Create a Lambda adapter
    adapter = LambdaAdapter(app)
    
    # Simulate a Lambda event
    event = {
        'httpMethod': 'GET',
        'path': '/hello',
        'queryStringParameters': {'name': 'Lambda'},
        'headers': {'Content-Type': 'application/json'},
        'body': None
    }
    
    # Simulate a Lambda context
    context = {}
    
    # Handle the event
    response = adapter.handle(event, context)
    
    # Print the response
    print(json.dumps(response, indent=2)) 