"""
Netlify Functions adapter for APIFromAnything.

This module provides adapter functionality to integrate APIFromAnything with Netlify Functions.
"""

import json
import base64
import asyncio
from typing import Dict, Any, Callable, Optional, Union, List
from urllib.parse import parse_qsl

from apifrom.core.app import API
from apifrom.core.request import Request
from apifrom.core.response import Response


class NetlifyAdapter:
    """
    Adapter for integrating APIFromAnything with Netlify Functions.
    
    This adapter transforms Netlify Functions events into APIFromAnything
    requests and responses.
    
    Example:
        ```python
        from apifrom import API
        from apifrom.decorators import api
        from apifrom.adapters.netlify import NetlifyAdapter
        
        app = API(title="Netlify API")
        
        @api(app, route="/.netlify/functions/api/hello", method="GET")
        def hello(name: str = "World") -> dict:
            return {"message": f"Hello, {name}!"}
        
        # Create a Netlify adapter
        netlify_adapter = NetlifyAdapter(app)
        
        # Export the handler function for Netlify Functions
        def handler(event, context):
            return netlify_adapter.handle(event, context)
        ```
    """
    
    def __init__(self, app: API):
        """
        Initialize the Netlify adapter.
        
        Args:
            app: The APIFromAnything API instance
        """
        self.app = app
    
    def _create_request(self, event: Dict[str, Any]) -> Request:
        """
        Create an APIFromAnything request from a Netlify event.
        
        Args:
            event: The Netlify event object
            
        Returns:
            An APIFromAnything request
        """
        # Extract request details from the Netlify event
        method = event.get("httpMethod", "GET")
        path = event.get("path", "/")
        
        # Handle base path from Netlify
        if not path:
            path = "/"
        
        # Process query parameters
        query_params = {}
        if "queryStringParameters" in event and event["queryStringParameters"]:
            query_params = event["queryStringParameters"]
        
        # Process multi-value query parameters
        if "multiValueQueryStringParameters" in event and event["multiValueQueryStringParameters"]:
            for key, values in event["multiValueQueryStringParameters"].items():
                if len(values) == 1:
                    query_params[key] = values[0]
                else:
                    query_params[key] = values
        
        # Process headers
        headers = {}
        if "headers" in event and event["headers"]:
            headers = {k.lower(): v for k, v in event["headers"].items()}
        
        # Process body
        body = None
        if "body" in event and event["body"]:
            body = event["body"]
            if event.get("isBase64Encoded", False):
                body = base64.b64decode(body)
            elif isinstance(body, str):
                # Try to parse JSON body
                content_type = headers.get("content-type", "")
                if "application/json" in content_type:
                    try:
                        json.loads(body)  # Just to validate it's JSON
                        body = body.encode("utf-8")
                    except (json.JSONDecodeError, TypeError):
                        # If not JSON, encode as is
                        body = body.encode("utf-8")
                elif "application/x-www-form-urlencoded" in content_type:
                    # Form data
                    body = body.encode("utf-8")
                else:
                    # Plain text or other
                    body = body.encode("utf-8")
        
        # Create the request
        request = Request(
            method=method,
            path=path,
            headers=headers,
            query_params=query_params,
            body=body
        )
        
        # Store original event in state
        request.state.netlify_event = event
        
        return request
    
    def _create_netlify_response(self, response: Response) -> Dict[str, Any]:
        """
        Create a Netlify response from an APIFromAnything response.
        
        Args:
            response: The APIFromAnything response
            
        Returns:
            A response object that Netlify can understand
        """
        # Convert the response to a Netlify-compatible format
        netlify_response = {
            "statusCode": response.status_code,
            "headers": dict(response.headers),
            "isBase64Encoded": False
        }
        
        # Handle different response body types
        if isinstance(response.content, (dict, list)):
            # JSON response
            netlify_response["headers"]["Content-Type"] = "application/json"
            netlify_response["body"] = json.dumps(response.content)
        elif isinstance(response.content, bytes):
            # Binary response
            netlify_response["isBase64Encoded"] = True
            netlify_response["body"] = base64.b64encode(response.content).decode("utf-8")
        else:
            # String response
            netlify_response["body"] = str(response.content)
        
        return netlify_response
    
    async def _handle_async(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle a Netlify Functions event asynchronously.
        
        Args:
            event: The Netlify event object
            context: The Netlify context object
            
        Returns:
            A response object that Netlify can understand
        """
        request = self._create_request(event)
        response = await self.app.process_request(request)
        return self._create_netlify_response(response)
    
    def handle(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle a Netlify Functions event.
        
        Args:
            event: The Netlify event object
            context: The Netlify context object
            
        Returns:
            A response object that Netlify can understand
        """
        # Create an event loop if one doesn't exist
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the handler and return the result
        return loop.run_until_complete(self._handle_async(event, context)) 