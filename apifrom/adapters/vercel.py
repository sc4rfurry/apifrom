"""
Vercel serverless functions adapter for APIFromAnything.

This module provides adapter functionality to integrate APIFromAnything with Vercel serverless functions.
"""

import json
import base64
import asyncio
from typing import Dict, Any, Callable, Optional, Union, List
from urllib.parse import parse_qsl, urlparse

from apifrom.core.app import API
from apifrom.core.request import Request
from apifrom.core.response import Response


class VercelAdapter:
    """
    Adapter for integrating APIFromAnything with Vercel serverless functions.
    
    This adapter transforms Vercel serverless functions events into APIFromAnything
    requests and responses.
    
    Example:
        ```python
        from apifrom import API
        from apifrom.decorators import api
        from apifrom.adapters.vercel import VercelAdapter
        
        app = API(title="Vercel API")
        
        @api(app, route="/api/hello", method="GET")
        def hello(name: str = "World") -> dict:
            return {"message": f"Hello, {name}!"}
        
        # Create a Vercel adapter
        vercel_adapter = VercelAdapter(app)
        
        # Export the handler function for Vercel
        handler = vercel_adapter.get_handler()
        ```
    """
    
    def __init__(self, app: API):
        """
        Initialize the Vercel adapter.
        
        Args:
            app: The APIFromAnything API instance
        """
        self.app = app
    
    def get_handler(self) -> Callable:
        """
        Get a handler function for Vercel serverless functions.
        
        Returns:
            Callable: A function that can be used as a Vercel serverless function handler
        """
        async def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
            """
            Handle a Vercel serverless function event.
            
            Args:
                event: The Vercel event object
                context: The Vercel context object
                
            Returns:
                A response object that Vercel can understand
            """
            request = self._create_request(event)
            response = await self.app.process_request(request)
            return self._create_vercel_response(response)
        
        return handler
    
    def _create_request(self, event: Dict[str, Any]) -> Request:
        """
        Create an APIFromAnything request from a Vercel event.
        
        Args:
            event: The Vercel event object
            
        Returns:
            An APIFromAnything request
        """
        # Extract request details from the Vercel event
        method = event.get("method", "GET")
        path = event.get("path", "/")
        url = event.get("url", "")
        
        # If path is not provided but URL is, extract path from URL
        if not path and url:
            parsed_url = urlparse(url)
            path = parsed_url.path
        
        # Handle base path from Vercel
        if not path:
            path = "/"
        
        # Process query parameters
        query_params = {}
        if "query" in event:
            query_params = event["query"]
        elif url and "?" in url:
            query_string = urlparse(url).query
            query_params = dict(parse_qsl(query_string))
        
        # Process headers
        headers = {}
        if "headers" in event:
            headers = {k.lower(): v for k, v in event["headers"].items()}
        
        # Process body
        body = None
        if "body" in event:
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
                        # If not valid JSON, encode as is
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
        request.state.vercel_event = event
        
        return request
    
    def _create_vercel_response(self, response: Response) -> Dict[str, Any]:
        """
        Create a Vercel response from an APIFromAnything response.
        
        Args:
            response: The APIFromAnything response
            
        Returns:
            A response object that Vercel can understand
        """
        # Convert the response to a Vercel-compatible format
        vercel_response = {
            "statusCode": response.status_code,
            "headers": dict(response.headers),
            "isBase64Encoded": False
        }
        
        # Handle different response body types
        if isinstance(response.content, (dict, list)):
            # JSON response
            vercel_response["headers"]["Content-Type"] = "application/json"
            vercel_response["body"] = json.dumps(response.content)
        elif isinstance(response.content, bytes):
            # Binary response
            vercel_response["isBase64Encoded"] = True
            vercel_response["body"] = base64.b64encode(response.content).decode("utf-8")
        else:
            # String response
            vercel_response["body"] = str(response.content)
        
        return vercel_response
    
    def handle(self, event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        """
        Handle a Vercel serverless function event synchronously.
        
        This is a wrapper around the async handler for compatibility with sync environments.
        
        Args:
            event: The Vercel event object
            context: The Vercel context object (optional)
            
        Returns:
            A response object that Vercel can understand
        """
        # Create an event loop if one doesn't exist
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Get the handler
        handler = self.get_handler()
        
        # Run the handler
        return loop.run_until_complete(handler(event, context)) 