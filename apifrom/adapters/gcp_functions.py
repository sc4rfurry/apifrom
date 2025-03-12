"""
Google Cloud Functions adapter for APIFromAnything.

This module provides an adapter for running APIFromAnything applications on Google Cloud Functions.
"""

import json
import base64
import asyncio
from typing import Dict, Any, Optional, Tuple, List, Union, Callable

from apifrom.core.app import API
from apifrom.core.request import Request
from apifrom.core.response import Response


class CloudFunctionAdapter:
    """
    Adapter for running APIFromAnything applications on Google Cloud Functions.
    
    This adapter translates between Google Cloud Functions request/response objects and
    APIFromAnything's Request/Response objects.
    """
    
    def __init__(self, app: API):
        """
        Initialize the Cloud Function adapter.
        
        Args:
            app: The APIFromAnything application to adapt.
        """
        self.app = app
    
    def handle(self, request) -> Any:
        """
        Handle a Google Cloud Functions request.
        
        Args:
            request: The Google Cloud Functions request object.
            
        Returns:
            A response that can be returned from a Cloud Function.
        """
        # Create a request object from the Cloud Function request
        api_request = self._create_request(request)
        
        # Process the request with the application
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        api_response = loop.run_until_complete(self.app.process_request(api_request))
        
        # Convert the response to a Cloud Function response
        return self._create_cloud_function_response(api_response)
    
    def _create_request(self, request) -> Request:
        """
        Create a Request object from a Cloud Function request.
        
        Args:
            request: The Google Cloud Functions request object.
            
        Returns:
            A Request object.
        """
        # Extract request information
        http_method = request.method
        path = request.path
        query_params = dict(request.args) if hasattr(request, 'args') else {}
        headers = dict(request.headers) if hasattr(request, 'headers') else {}
        
        # Extract body if present
        body = None
        if hasattr(request, 'get_json'):
            try:
                body_json = request.get_json(silent=True)
                if body_json is not None:
                    body = json.dumps(body_json).encode('utf-8')
            except:
                # If JSON parsing fails, try to get the raw data
                if hasattr(request, 'data'):
                    body = request.data if isinstance(request.data, bytes) else request.data.encode('utf-8')
        elif hasattr(request, 'get_data'):
            body = request.get_data()
        
        # Create the request object
        api_request = Request(
            method=http_method,
            path=path,
            query_params=query_params,
            headers=headers,
            body=body
        )
        
        # Add Cloud Function-specific information to the request state
        api_request.state.gcp_request = request
        
        return api_request
    
    def _create_cloud_function_response(self, response: Union[Response, Dict[str, Any]]) -> Union[Dict[str, Any], Tuple[str, int, Dict[str, str]]]:
        """
        Create a Cloud Function response from an APIFromAnything response.
        
        Args:
            response: The APIFromAnything response or a dictionary
            
        Returns:
            A response object that Cloud Functions can understand
        """
        # Check if Flask is available
        try:
            from flask import Response as FlaskResponse
            has_flask = True
        except ImportError:
            has_flask = False
        
        # Convert the response to a GCP-compatible format
        if isinstance(response, dict):
            # For direct dictionary responses
            return (json.dumps(response), 200, {"Content-Type": "application/json"})
        
        status_code = response.status_code
        headers = dict(response.headers)
        body = response.content
        
        # Create a Flask response
        if isinstance(body, (dict, list)):
            # JSON response
            return (json.dumps(body), status_code, headers)
        elif isinstance(body, bytes):
            # Binary response
            return (body, status_code, headers)
        else:
            # String response
            return (str(body), status_code, headers)


# Example usage
if __name__ == "__main__":
    # This code is for demonstration purposes only
    from apifrom.decorators.api import api
    
    # Create an API application
    app = API(title="Cloud Function API Example")
    
    # Define an API endpoint
    @api(app)
    def hello(name: str = "World") -> Dict[str, str]:
        """Say hello to someone."""
        return {"message": f"Hello, {name}!"}
    
    # Create a Cloud Function adapter
    adapter = CloudFunctionAdapter(app)
    
    # Simulate a Cloud Function request
    class MockRequest:
        method = 'GET'
        path = '/hello'
        args = {'name': 'Cloud Function'}
        headers = {'Content-Type': 'application/json'}
        data = b''
        
        def get_json(self, silent=False):
            return None
    
    # Handle the request
    response = adapter.handle(MockRequest())
    
    # Print the response
    if hasattr(response, 'get_data'):
        print(f"Status: {response.status_code}")
        print(f"Headers: {response.headers}")
        print(f"Body: {response.get_data(as_text=True)}")
    else:
        body, status, headers = response
        print(f"Status: {status}")
        print(f"Headers: {headers}")
        print(f"Body: {body}") 