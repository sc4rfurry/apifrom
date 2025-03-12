"""
Azure Functions adapter for APIFromAnything.

This module provides an adapter for running APIFromAnything applications on Azure Functions.
"""

import json
from typing import Dict, Any, Optional, Union

import azure.functions as func

from apifrom.core.app import API
from apifrom.core.request import Request
from apifrom.core.response import Response


class AzureFunctionAdapter:
    """
    Adapter for running APIFromAnything applications on Azure Functions.
    
    This adapter translates between Azure Functions request/response objects and
    APIFromAnything's Request/Response objects.
    """
    
    def __init__(self, app: API):
        """
        Initialize the Azure Function adapter.
        
        Args:
            app: The APIFromAnything application to adapt.
        """
        self.app = app
    
    def handle(self, req: func.HttpRequest) -> func.HttpResponse:
        """
        Handle an Azure Function HTTP request.
        
        Args:
            req: The Azure Function HTTP request object.
            
        Returns:
            An Azure Function HTTP response object.
        """
        # Create a request object from the Azure Function request
        api_request = self._create_request(req)
        
        # Process the request with the application
        api_response = self.app.process_request(api_request)
        
        # Convert the response to an Azure Function response
        return self._create_azure_function_response(api_response)
    
    def _create_request(self, req: func.HttpRequest) -> Request:
        """
        Create a Request object from an Azure Function request.
        
        Args:
            req: The Azure Function HTTP request object.
            
        Returns:
            A Request object.
        """
        # Extract request information
        http_method = req.method
        path = req.url.path if hasattr(req, 'url') else req.route.get('route', '/')
        
        # Extract query parameters
        query_params = {}
        for param_name, param_value in req.params.items():
            query_params[param_name] = param_value
        
        # Extract headers
        headers = {}
        for header_name, header_value in req.headers.items():
            headers[header_name] = header_value
        
        # Extract body if present
        body = ''
        if req.get_body():
            try:
                # Try to parse as JSON
                body_json = req.get_json()
                body = json.dumps(body_json)
            except ValueError:
                # If JSON parsing fails, use the raw body
                body = req.get_body().decode('utf-8')
        
        # Create the request object
        api_request = Request(
            method=http_method,
            path=path,
            query_params=query_params,
            headers=headers,
            body=body
        )
        
        # Add Azure Function-specific information to the request state
        api_request.state.azure_request = req
        
        return api_request
    
    def _create_azure_function_response(self, response: Response) -> func.HttpResponse:
        """
        Create an Azure Function response from a Response object.
        
        Args:
            response: The Response object.
            
        Returns:
            An Azure Function HTTP response object.
        """
        # Convert the response body
        body = response.content
        
        # If the body is not a string or bytes, convert it to JSON
        if not isinstance(body, (str, bytes)) and body is not None:
            body = json.dumps(body)
            if 'Content-Type' not in response.headers:
                response.headers['Content-Type'] = 'application/json'
        
        # If the body is a string, convert it to bytes
        if isinstance(body, str):
            body = body.encode('utf-8')
        
        # Create an Azure Function response
        azure_response = func.HttpResponse(
            body=body,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
        return azure_response


# Example usage
if __name__ == "__main__":
    # This code is for demonstration purposes only
    from apifrom.decorators.api import api
    
    # Create an API application
    app = API(title="Azure Function API Example")
    
    # Define an API endpoint
    @api(app)
    def hello(name: str = "World") -> Dict[str, str]:
        """Say hello to someone."""
        return {"message": f"Hello, {name}!"}
    
    # Create an Azure Function adapter
    adapter = AzureFunctionAdapter(app)
    
    # Note: This example won't run directly as it requires the Azure Functions runtime.
    # It's provided for reference only.
    print("This example requires the Azure Functions runtime to execute.") 