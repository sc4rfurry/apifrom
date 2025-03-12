"""
Base middleware classes for APIFromAnything.

This module defines the base middleware classes that can be used to process
requests and responses.
"""

import abc
import logging
import typing as t

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse

logger = logging.getLogger(__name__)


class BaseMiddleware(abc.ABC):
    """
    Base middleware class for APIFromAnything.
    
    This abstract class defines the interface for middleware components.
    Middleware components can process requests and responses.
    
    Attributes:
        options (dict): Options for the middleware.
    """
    
    def __init__(self, **options):
        """
        Initialize a new BaseMiddleware instance.
        
        Args:
            **options: Options for the middleware.
        """
        self.options = options
    
    @abc.abstractmethod
    async def process_request(self, request: t.Any) -> t.Any:
        """
        Process a request.
        
        Args:
            request: The request to process.
            
        Returns:
            The processed request.
        """
        pass
    
    @abc.abstractmethod
    async def process_response(self, response: t.Any) -> t.Any:
        """
        Process a response.
        
        Args:
            response: The response to process.
            
        Returns:
            The processed response.
        """
        pass


class Middleware(BaseHTTPMiddleware, BaseMiddleware):
    """
    Middleware class for APIFromAnything.
    
    This class implements the BaseMiddleware interface and extends
    Starlette's BaseHTTPMiddleware to provide a middleware component
    that can be used with Starlette.
    """
    
    async def dispatch(
        self,
        request: StarletteRequest,
        call_next: t.Callable[[StarletteRequest], t.Awaitable[StarletteResponse]]
    ) -> StarletteResponse:
        """
        Dispatch a request.
        
        This method is called by Starlette to process a request.
        
        Args:
            request: The request to process.
            call_next: A function to call the next middleware or route handler.
            
        Returns:
            The response.
        """
        # Process request
        try:
            request = await self.process_request(request)
        except Exception as e:
            logger.error(f"Error processing request in middleware {self.__class__.__name__}: {e}")
            raise
        
        # Call next middleware or route handler
        response = await call_next(request)
        
        # Process response
        try:
            response = await self.process_response(response)
        except Exception as e:
            logger.error(f"Error processing response in middleware {self.__class__.__name__}: {e}")
            raise
        
        return response 

    @abc.abstractmethod
    async def process_request(self, request: t.Any) -> t.Any:
        """
        Process a request before it is handled by the API.
        
        Args:
            request: The request to process.
            
        Returns:
            The processed request.
        """
        pass

    async def process_response(self, response: t.Any) -> t.Any:
        """
        Process a response after it is handled by the API.
        
        Args:
            response: The response to process.
            
        Returns:
            The processed response.
        """
        return response 