"""
Request module for APIFromAnything.

This module defines the Request class that represents an HTTP request
and provides methods for accessing request data.
"""

import json
import logging
import typing as t
from urllib.parse import parse_qs

from starlette.requests import Request as StarletteRequest

logger = logging.getLogger(__name__)


class Request:
    """
    Request class for APIFromAnything.
    
    This class wraps a Starlette request and provides methods for accessing
    request data in a convenient way.
    
    Attributes:
        _request: The underlying Starlette request.
        path_params: Path parameters extracted from the URL.
        query_params: Query parameters extracted from the URL.
        headers: HTTP headers.
        method: HTTP method.
        path: Request path.
        _body: Cached request body.
    """
    
    def __init__(
        self, 
        request: t.Optional[StarletteRequest] = None, 
        path_params: t.Optional[dict[t.Any, t.Any]] = None,
        method: t.Optional[str] = None,
        path: t.Optional[str] = None,
        query_params: t.Optional[dict[t.Any, t.Any]] = None,
        headers: t.Optional[dict[t.Any, t.Any]] = None,
        body: t.Optional[t.Union[str, bytes]] = None,
        client_ip: t.Optional[str] = None
    ):
        """
        Initialize a new Request instance.
        
        Args:
            request: The underlying Starlette request.
            path_params: Path parameters extracted from the URL.
            method: The HTTP method.
            path: The request path.
            query_params: Query parameters.
            headers: HTTP headers.
            body: Request body.
            client_ip: Client IP address.
        """
        self.state = type('State', (), {})()
        
        if request is not None:
            # Initialize from a Starlette request
            self._request = request
            self.method = request.method
            self.path = request.url.path
            self.query_params = dict(request.query_params)
            self.headers = dict(request.headers)
            self.path_params = path_params or {}
            self.client_ip = request.client.host if request.client else None
        else:
            # Initialize from individual parameters
            self._request = None
            self.method = method
            self.path = path
            self.query_params = query_params or {}
            self.headers = headers or {}
            self.path_params = path_params or {}
            self.client_ip = client_ip
            self._body = body
    
    async def body(self) -> bytes:
        """
        Get the request body.
        
        Returns:
            The request body as bytes.
        """
        if self._body is not None:
            if isinstance(self._body, str):
                return self._body.encode('utf-8')
            return self._body
            
        if self._request is None:
            return b''
            
        if self._body is None:
            self._body = await self._request.body()
        return self._body
    
    async def json(self) -> t.Dict:
        """
        Get the request body as JSON.
        
        Returns:
            The request body parsed as JSON.
            
        Raises:
            ValueError: If the request body is not valid JSON.
        """
        logger.debug(f"Request body type: {type(self._body)}")
        logger.debug(f"Request body: {self._body}")
        
        if self._request is None and isinstance(self._body, str):
            try:
                logger.debug(f"Parsing string body as JSON: {self._body}")
                return json.loads(self._body)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse request body as JSON: {e}")
                raise ValueError(f"Invalid JSON: {e}")
                
        body = await self.body()
        logger.debug(f"Body from body() method: {body}")
        
        if not body:
            logger.debug("Body is empty, returning empty dict")
            return {}
            
        try:
            decoded_body = body.decode()
            logger.debug(f"Decoded body: {decoded_body}")
            parsed_json = json.loads(decoded_body)
            logger.debug(f"Parsed JSON: {parsed_json}")
            return parsed_json
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse request body as JSON: {e}")
            raise ValueError(f"Invalid JSON: {e}")
    
    async def form(self) -> t.Dict:
        """
        Get the request body as form data.
        
        Returns:
            The request body parsed as form data.
        """
        form = await self._request.form()
        return {k: v for k, v in form.items()}
    
    def get_param(self, name: str, default: t.Any = None) -> t.Any:
        """
        Get a parameter from the request.
        
        This method looks for the parameter in path parameters, query parameters,
        and then the request body (in that order).
        
        Args:
            name: The name of the parameter.
            default: The default value to return if the parameter is not found.
            
        Returns:
            The parameter value, or the default value if not found.
        """
        # Check path parameters
        if name in self.path_params:
            return self.path_params[name]
        
        # Check query parameters
        if name in self.query_params:
            return self.query_params[name]
        
        # Default
        return default
    
    @property
    def client(self) -> t.Tuple[str, int]:
        """
        Get the client address.
        
        Returns:
            A tuple of (host, port).
        """
        return self._request.client
    
    @property
    def cookies(self) -> t.Dict[str, str]:
        """
        Get the request cookies.
        
        Returns:
            A dictionary of cookies.
        """
        return self._request.cookies
    
    def __getattr__(self, name: str) -> t.Any:
        """
        Get an attribute from the underlying request.
        
        Args:
            name: The name of the attribute.
            
        Returns:
            The attribute value.
            
        Raises:
            AttributeError: If the attribute is not found.
        """
        if self._request is None:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
            
        return getattr(self._request, name) 