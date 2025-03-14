"""
Caching middleware for APIFromAnything.

This module provides middleware for caching API responses to improve performance.
"""

import hashlib
import json
import time
from typing import Any, Callable, Dict, List, Optional, Union

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware.base import BaseMiddleware


class MemoryCache:
    """
    Simple in-memory cache implementation.
    """
    
    def __init__(self, max_size: int = 1000, ttl: int = 60):
        """
        Initialize the memory cache.
        
        Args:
            max_size: Maximum number of items to store in the cache
            ttl: Time-to-live in seconds for cached items
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value, or None if not found or expired
        """
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        if time.time() > item["expires_at"]:
            # Item has expired
            del self.cache[key]
            return None
        
        return item["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds (overrides the default)
        """
        # If cache is full, remove the oldest item
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["expires_at"])
            del self.cache[oldest_key]
        
        # Set the new item
        self.cache[key] = {
            "value": value,
            "expires_at": time.time() + (ttl or self.ttl)
        }
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
        """
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """
        Clear the entire cache.
        """
        self.cache.clear()


class CacheMiddleware(BaseMiddleware):
    """
    Middleware for caching API responses.
    """
    
    def __init__(
        self,
        cache_backend: Any = None,
        ttl: int = 60,
        methods: Optional[list] = None,
        exclude_routes: Optional[list] = None,
        vary_headers: Optional[list] = None,
        key_prefix: str = "apifrom-cache:",
    ):
        """
        Initialize the cache middleware.
        
        Args:
            cache_backend: The cache backend to use (defaults to MemoryCache)
            ttl: Default time-to-live in seconds for cached items
            methods: HTTP methods to cache (defaults to ["GET"])
            exclude_routes: Routes to exclude from caching
            vary_headers: Headers to include in the cache key
            key_prefix: Prefix for cache keys
        """
        super().__init__(
            ttl=ttl,
            methods=methods,
            exclude_routes=exclude_routes,
            vary_headers=vary_headers,
            key_prefix=key_prefix
        )
        self.cache = cache_backend or MemoryCache(ttl=ttl)
        self.ttl = ttl
        self.methods = methods or ["GET"]
        self.exclude_routes = exclude_routes or []
        self.vary_headers = vary_headers or []
        self.key_prefix = key_prefix
    
    def _should_cache(self, request: Request) -> bool:
        """
        Determine if a request should be cached.
        
        Args:
            request: The request object
            
        Returns:
            True if the request should be cached, False otherwise
        """
        # Only cache specified methods
        if request.method not in self.methods:
            return False
        
        # Don't cache excluded routes
        for route in self.exclude_routes:
            if request.path.startswith(route):
                return False
        
        # Don't cache requests with Cache-Control: no-cache or no-store
        cache_control = request.headers.get("Cache-Control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False
        
        return True
    
    def _generate_cache_key(self, request: Request) -> str:
        """
        Generate a cache key for a request.
        
        Args:
            request: The request object
            
        Returns:
            The cache key
        """
        # Start with the method and path
        key_parts = [request.method, request.path]
        
        # Add query parameters
        if request.query_params:
            # Sort query params to ensure consistent keys
            sorted_params = sorted(request.query_params.items())
            key_parts.append(json.dumps(sorted_params))
        
        # Add vary headers
        for header in self.vary_headers:
            if header in request.headers:
                key_parts.append(f"{header}:{request.headers[header]}")
        
        # Generate a hash of the key parts
        key_str = ":".join(key_parts)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"{self.key_prefix}{key_hash}"
    
    async def process_request(self, request: Request) -> Request:
        """
        Process a request through the cache middleware.
        
        Args:
            request: The request object
            
        Returns:
            The request object
        """
        # Store whether we should cache this request in the request state
        # so we can use it in process_response
        request.state.should_cache = self._should_cache(request)
        if request.state.should_cache:
            request.state.cache_key = self._generate_cache_key(request)
            # Try to get from cache
            cached_response = self.cache.get(request.state.cache_key)
            if cached_response is not None:
                # Store the cached response in the request state
                request.state.cached_response = Response.from_dict(cached_response)
                request.state.cached_response.headers["X-Cache"] = "HIT"
        
        return request
    
    async def process_response(self, response: Response) -> Response:
        """
        Process a response through the cache middleware.
        
        Args:
            response: The response object
            
        Returns:
            The response object
        """
        # If we have a cached response in the request state, return it
        if hasattr(response.request.state, 'cached_response'):
            return response.request.state.cached_response
        
        # If we should cache this response and it's cacheable
        if (hasattr(response.request.state, 'should_cache') and 
            response.request.state.should_cache and 
            response.status_code >= 200 and response.status_code < 300):
            
            self.cache.set(response.request.state.cache_key, response.to_dict(), self.ttl)
            response.headers["X-Cache"] = "MISS"
        
        return response

    async def __call__(self, scope, receive, send):
        """
        ASGI callable.
        
        Args:
            scope: The ASGI scope.
            receive: The ASGI receive function.
            send: The ASGI send function.
        """
        # Only process HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        # Extract request information from scope
        method = scope["method"]
        path = scope["path"]
        headers = dict(scope["headers"])
        
        # Check if we should cache this request
        should_cache = method in self.methods
        for route in self.exclude_routes:
            if path.startswith(route):
                should_cache = False
                break
                
        if not should_cache:
            await self.app(scope, receive, send)
            return
            
        # Generate cache key
        key_parts = [method, path]
        if "query_string" in scope and scope["query_string"]:
            key_parts.append(scope["query_string"].decode("utf-8"))
        for header in self.vary_headers:
            header_bytes = header.encode("utf-8")
            for h_key, h_value in scope["headers"]:
                if h_key == header_bytes:
                    key_parts.append(f"{header}:{h_value.decode('utf-8')}")
                    break
        key_str = ":".join(key_parts)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        cache_key = f"{self.key_prefix}{key_hash}"
        
        # Try to get from cache
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            # Return cached response
            await send({
                "type": "http.response.start",
                "status": cached_response["status_code"],
                "headers": [(k.encode("utf-8"), v.encode("utf-8")) for k, v in cached_response["headers"].items()] + [(b"X-Cache", b"HIT")],
            })
            await send({
                "type": "http.response.body",
                "body": cached_response["content"].encode("utf-8") if isinstance(cached_response["content"], str) else cached_response["content"],
            })
            return
            
        # Not in cache, process request
        # Capture the response to cache it
        original_send = send
        response_started = False
        response_status = 0
        response_headers = []
        response_body = b""
        
        async def send_wrapper(message):
            nonlocal response_started, response_status, response_headers, response_body
            
            if message["type"] == "http.response.start":
                response_started = True
                response_status = message["status"]
                response_headers = message["headers"]
                
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")
                
                # If this is the last message and we should cache the response
                if not message.get("more_body", False) and should_cache and 200 <= response_status < 300:
                    # Cache the response
                    headers_dict = {}
                    for key, value in response_headers:
                        headers_dict[key.decode("utf-8")] = value.decode("utf-8")
                    
                    cached_data = {
                        "status_code": response_status,
                        "headers": headers_dict,
                        "content": response_body,
                    }
                    self.cache.set(cache_key, cached_data, self.ttl)
                    
                    # Add X-Cache header
                    new_headers = []
                    has_cache_header = False
                    for key, value in response_headers:
                        if key.lower() == b"x-cache":
                            has_cache_header = True
                            new_headers.append((key, b"MISS"))
                        else:
                            new_headers.append((key, value))
                    
                    if not has_cache_header:
                        new_headers.append((b"X-Cache", b"MISS"))
                    
                    message["headers"] = new_headers
            
            await original_send(message)
        
        await self.app(scope, receive, send_wrapper)


class CacheControl:
    """
    Decorator for controlling cache behavior on specific endpoints.
    """
    
    @staticmethod
    def cache(ttl: int = 60):
        """
        Cache an endpoint for the specified TTL.
        
        Args:
            ttl: Time-to-live in seconds
            
        Returns:
            A decorator function
        """
        def decorator(func):
            func._cache_ttl = ttl
            return func
        return decorator
    
    @staticmethod
    def no_cache(func):
        """
        Prevent an endpoint from being cached.
        
        Args:
            func: The function to decorate
            
        Returns:
            The decorated function
        """
        func._no_cache = True
        return func 