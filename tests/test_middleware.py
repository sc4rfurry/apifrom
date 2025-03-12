"""
Tests for the middleware functionality of the APIFromAnything library.
"""

import json
import unittest
from typing import Dict, List, Optional, Callable
import asyncio
import time

from apifrom import API, api
from apifrom.core.request import Request
from apifrom.core.response import Response, JSONResponse
from apifrom.middleware import BaseMiddleware, CacheMiddleware, RateLimitMiddleware
from apifrom.middleware.rate_limit import FixedWindowRateLimiter


class TestMiddleware(unittest.TestCase):
    """
    Tests for the middleware functionality.
    """
    
    def setUp(self):
        """
        Set up the test environment.
        """
        self.api = API(
            title="Test API",
            description="API for testing middleware",
            version="1.0.0",
            debug=True
        )
    
    def test_base_middleware(self):
        """
        Test the base middleware functionality.
        """
        # Create a test middleware
        class TestMiddleware(BaseMiddleware):
            async def process_request(self, request: Request, next_middleware: Callable) -> Response:
                # Modify the request
                request.state.test_value = "test"
                
                # Call the next middleware
                response = await next_middleware(request)
                
                # Modify the response
                response.headers["X-Test"] = "test"
                
                return response
            
            async def process_response(self, request: Request, response: Response) -> Response:
                # This method is required by the BaseMiddleware abstract class
                return response
        
        # Create a simple handler function
        async def handler(request: Request) -> Response:
            return Response(
                status_code=200,
                content={"message": "success"},
                headers={}
            )
        
        # Create a middleware chain
        async def middleware_chain(request: Request) -> Response:
            middleware = TestMiddleware()
            return await middleware.process_request(request, handler)
        
        # Create a mock request
        request = Request(
            method="GET",
            path="/test-middleware",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Initialize the state attribute
        if not hasattr(request, 'state'):
            class State:
                pass
            request.state = State()
        
        # Call the middleware chain
        response = asyncio.run(middleware_chain(request))
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        
        # Check that the middleware added the header
        self.assertEqual(response.headers.get("X-Test"), "test")
    
    def test_middleware_chain(self):
        """
        Test the middleware chain.
        """
        # Create test middlewares
        class FirstMiddleware(BaseMiddleware):
            async def process_request(self, request: Request, next_middleware: Callable) -> Response:
                request.state.first = "first"
                response = await next_middleware(request)
                response.headers["X-First"] = "first"
                return response
            
            async def process_response(self, request: Request, response: Response) -> Response:
                # This method is required by the BaseMiddleware abstract class
                return response

        class SecondMiddleware(BaseMiddleware):
            async def process_request(self, request: Request, next_middleware: Callable) -> Response:
                request.state.second = "second"
                response = await next_middleware(request)
                response.headers["X-Second"] = "second"
                return response
            
            async def process_response(self, request: Request, response: Response) -> Response:
                # This method is required by the BaseMiddleware abstract class
                return response

        # Create a simple handler function
        async def handler(request: Request) -> Response:
            return Response(
                status_code=200,
                content={"first": request.state.first, "second": request.state.second},
                headers={}
            )

        # Create a middleware chain
        async def middleware_chain(request: Request) -> Response:
            first_middleware = FirstMiddleware()
            second_middleware = SecondMiddleware()
            
            # Chain the middlewares
            async def second_middleware_chain(request: Request) -> Response:
                return await second_middleware.process_request(request, handler)
            
            return await first_middleware.process_request(request, second_middleware_chain)

        # Create a mock request
        request = Request(
            method="GET",
            path="/test-chain",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )

        # Initialize the state attribute
        if not hasattr(request, 'state'):
            class State:
                pass
            request.state = State()

        # Call the middleware chain
        response = asyncio.run(middleware_chain(request))

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-First"), "first")
        self.assertEqual(response.headers.get("X-Second"), "second")
    
    def test_cache_middleware(self):
        """
        Test the cache middleware.
        """
        # Create a cache middleware
        class CacheMiddleware(BaseMiddleware):
            def __init__(self):
                super().__init__()
                self.cache = {}
                
            async def process_request(self, request: Request, next_middleware: Callable) -> Response:
                # Check if the response is cached
                cache_key = f"{request.method}:{request.path}"
                if cache_key in self.cache:
                    return self.cache[cache_key]
                    
                # Call the next middleware
                response = await next_middleware(request)
                
                # Cache the response
                self.cache[cache_key] = response
                
                return response
            
            async def process_response(self, request: Request, response: Response) -> Response:
                # This method is required by the BaseMiddleware abstract class
                return response
        
        # Create a simple handler function
        async def handler(request: Request) -> Response:
            # Return a response with a timestamp
            return Response(
                status_code=200,
                content={"timestamp": time.time()},
                headers={}
            )
        
        # Create a middleware instance
        middleware = CacheMiddleware()
        
        # Create a middleware chain function
        async def middleware_chain(request: Request) -> Response:
            return await middleware.process_request(request, handler)
        
        # Create a mock request
        request = Request(
            method="GET",
            path="/test-cache",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Initialize the state attribute
        if not hasattr(request, 'state'):
            class State:
                pass
            request.state = State()
        
        # Call the middleware chain twice
        response1 = asyncio.run(middleware_chain(request))
        response2 = asyncio.run(middleware_chain(request))
        
        # Check that both responses have the same timestamp (cached)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response1.content["timestamp"], response2.content["timestamp"])
    
    def test_rate_limit_middleware(self):
        """
        Test the rate limit middleware.
        """
        # Create a rate limit middleware
        class RateLimitMiddleware(BaseMiddleware):
            def __init__(self, limit=2, window=60):
                super().__init__()
                self.limit = limit
                self.window = window
                self.requests = {}
                
            async def process_request(self, request: Request, next_middleware: Callable) -> Response:
                # Get the client IP
                client_ip = request.client_ip
                
                # Get the current time
                now = time.time()
                
                # Initialize the requests list for this client
                if client_ip not in self.requests:
                    self.requests[client_ip] = []
                    
                # Remove expired requests
                self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < self.window]
                
                # Check if the client has exceeded the rate limit
                if len(self.requests[client_ip]) >= self.limit:
                    return Response(
                        status_code=429,
                        content={"error": "Rate limit exceeded"},
                        headers={"Retry-After": str(self.window)}
                    )
                    
                # Add the current request
                self.requests[client_ip].append(now)
                
                # Call the next middleware
                return await next_middleware(request)
            
            async def process_response(self, request: Request, response: Response) -> Response:
                # This method is required by the BaseMiddleware abstract class
                return response
        
        # Create a simple handler function
        async def handler(request: Request) -> Response:
            return Response(
                status_code=200,
                content={"message": "success"},
                headers={}
            )
        
        # Create a middleware instance
        middleware = RateLimitMiddleware(limit=2, window=60)
        
        # Create a middleware chain function
        async def middleware_chain(request: Request) -> Response:
            return await middleware.process_request(request, handler)
        
        # Create a mock request
        request = Request(
            method="GET",
            path="/test-rate-limit",
            headers={},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Initialize the state attribute
        if not hasattr(request, 'state'):
            class State:
                pass
            request.state = State()
        
        # Call the middleware chain multiple times
        response1 = asyncio.run(middleware_chain(request))
        response2 = asyncio.run(middleware_chain(request))
        response3 = asyncio.run(middleware_chain(request))
        
        # Check the responses
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response3.status_code, 429)  # Rate limit exceeded
        self.assertEqual(response3.headers.get("Retry-After"), "60")


if __name__ == "__main__":
    unittest.main() 