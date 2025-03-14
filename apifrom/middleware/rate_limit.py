"""
Rate limiting middleware for APIFromAnything.

This module provides middleware for rate limiting API requests to prevent abuse.
"""

import time
from collections import defaultdict, deque
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import json

from apifrom.core.request import Request
from apifrom.core.response import Response, JSONResponse
from apifrom.middleware.base import BaseMiddleware


class RateLimitBackend:
    """
    Base class for rate limit backends.
    
    Rate limit backends are responsible for storing and retrieving rate limit data.
    """
    
    def get(self, key: str) -> Any:
        """
        Get rate limit data for a key.
        
        Args:
            key: The key to get data for
            
        Returns:
            The rate limit data
        """
        raise NotImplementedError("Subclasses must implement get")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set rate limit data for a key.
        
        Args:
            key: The key to set data for
            value: The data to set
            ttl: Time to live in seconds
        """
        raise NotImplementedError("Subclasses must implement set")
    
    def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """
        Increment rate limit counter for a key.
        
        Args:
            key: The key to increment
            amount: The amount to increment by
            ttl: Time to live in seconds
            
        Returns:
            The new counter value
        """
        raise NotImplementedError("Subclasses must implement increment")
    
    def reset(self, key: str) -> None:
        """
        Reset rate limit data for a key.
        
        Args:
            key: The key to reset
        """
        raise NotImplementedError("Subclasses must implement reset")


class InMemoryRateLimitBackend(RateLimitBackend):
    """
    In-memory implementation of RateLimitBackend.
    
    This backend stores rate limit data in memory.
    """
    
    def __init__(self):
        """
        Initialize a new InMemoryRateLimitBackend instance.
        """
        self._data = {}
        self._expiry = {}
    
    def get(self, key: str) -> Any:
        """
        Get rate limit data for a key.
        
        Args:
            key: The key to get data for
            
        Returns:
            The rate limit data, or None if not found
        """
        self._cleanup()
        return self._data.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set rate limit data for a key.
        
        Args:
            key: The key to set data for
            value: The data to set
            ttl: Time to live in seconds
        """
        self._data[key] = value
        if ttl is not None:
            self._expiry[key] = time.time() + ttl
    
    def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """
        Increment rate limit counter for a key.
        
        Args:
            key: The key to increment
            amount: The amount to increment by
            ttl: Time to live in seconds
            
        Returns:
            The new counter value
        """
        self._cleanup()
        if key not in self._data:
            self._data[key] = 0
        self._data[key] += amount
        if ttl is not None:
            self._expiry[key] = time.time() + ttl
        return self._data[key]
    
    def reset(self, key: str) -> None:
        """
        Reset rate limit data for a key.
        
        Args:
            key: The key to reset
        """
        if key in self._data:
            del self._data[key]
        if key in self._expiry:
            del self._expiry[key]
    
    def _cleanup(self) -> None:
        """
        Clean up expired keys.
        """
        now = time.time()
        expired_keys = [k for k, v in self._expiry.items() if v <= now]
        for key in expired_keys:
            self.reset(key)


class RateLimiter:
    """
    Base rate limiter interface.
    """
    
    def check_limit(self, key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a key has exceeded its rate limit.
        
        Args:
            key: The key to check
            
        Returns:
            A tuple containing (allowed, limit_info)
        """
        raise NotImplementedError("Subclasses must implement check_limit")
    
    def update(self, key: str) -> None:
        """
        Update the rate limit counter for a key.
        
        Args:
            key: The key to update
        """
        raise NotImplementedError("Subclasses must implement update")


class FixedWindowRateLimiter(RateLimiter):
    """
    Fixed window rate limiter implementation.
    
    This rate limiter uses a fixed time window to limit requests.
    """
    
    def __init__(self, limit: int, window: int = 60):
        """
        Initialize the fixed window rate limiter.
        
        Args:
            limit: Maximum number of requests allowed in the window
            window: Time window in seconds
        """
        self.limit = limit
        self.window = window
        self.counters: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    
    def _get_current_window(self) -> int:
        """
        Get the current time window.
        
        Returns:
            The current time window as an integer
        """
        return int(time.time() / self.window)
    
    def check_limit(self, key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a key has exceeded its rate limit.
        
        Args:
            key: The key to check
            
        Returns:
            A tuple containing (allowed, limit_info)
        """
        current_window = self._get_current_window()
        current_count = self.counters[key][current_window]
        
        allowed = current_count < self.limit
        reset_time = (current_window + 1) * self.window
        
        limit_info = {
            "limit": self.limit,
            "remaining": max(0, self.limit - current_count),
            "reset": reset_time,
            "window": self.window,
        }
        
        return allowed, limit_info
    
    def update(self, key: str) -> None:
        """
        Update the rate limit counter for a key.
        
        Args:
            key: The key to update
        """
        current_window = self._get_current_window()
        self.counters[key][current_window] += 1
        
        # Clean up old windows
        for k in list(self.counters.keys()):
            for w in list(self.counters[k].keys()):
                if w < current_window:
                    del self.counters[k][w]
            if not self.counters[k]:
                del self.counters[k]


class SlidingWindowRateLimiter(RateLimiter):
    """
    Sliding window rate limiter implementation.
    
    This rate limiter uses a sliding time window to limit requests.
    """
    
    def __init__(self, limit: int, window: int = 60):
        """
        Initialize the sliding window rate limiter.
        
        Args:
            limit: Maximum number of requests allowed in the window
            window: Time window in seconds
        """
        self.limit = limit
        self.window = window
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def check_limit(self, key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a key has exceeded its rate limit.
        
        Args:
            key: The key to check
            
        Returns:
            A tuple containing (allowed, limit_info)
        """
        # Remove expired timestamps
        self._clean_old_requests(key)
        
        # Count current requests in window
        current_count = len(self.requests[key])
        
        allowed = current_count < self.limit
        
        # Calculate reset time
        reset_time = time.time() + self.window if not self.requests[key] else self.requests[key][0] + self.window
        
        limit_info = {
            "limit": self.limit,
            "remaining": max(0, self.limit - current_count),
            "reset": reset_time,
            "window": self.window,
        }
        
        return allowed, limit_info
    
    def update(self, key: str) -> None:
        """
        Update the rate limit counter for a key.
        
        Args:
            key: The key to update
        """
        # Remove expired timestamps
        self._clean_old_requests(key)
        
        # Add current timestamp
        self.requests[key].append(time.time())
    
    def _clean_old_requests(self, key: str) -> None:
        """
        Remove expired timestamps for a key.
        
        Args:
            key: The key to clean
        """
        if key not in self.requests:
            return
        
        current_time = time.time()
        cutoff_time = current_time - self.window
        
        while self.requests[key] and self.requests[key][0] <= cutoff_time:
            self.requests[key].popleft()
        
        if not self.requests[key]:
            del self.requests[key]


class TokenBucketRateLimiter(RateLimiter):
    """
    Token bucket rate limiter implementation.
    
    This rate limiter uses a token bucket algorithm to limit requests.
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        Initialize the token bucket rate limiter.
        
        Args:
            rate: Token refill rate per second
            capacity: Maximum number of tokens in the bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.buckets: Dict[str, Dict[str, float]] = {}
    
    def check_limit(self, key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a key has exceeded its rate limit.
        
        Args:
            key: The key to check
            
        Returns:
            A tuple containing (allowed, limit_info)
        """
        if key not in self.buckets:
            self.buckets[key] = {
                "tokens": self.capacity,
                "last_refill": time.time(),
            }
        
        # Refill tokens
        self._refill(key)
        
        # Check if we have enough tokens
        allowed = self.buckets[key]["tokens"] >= 1
        
        # Calculate time until next token
        time_until_next_token = 0 if allowed else (1 - self.buckets[key]["tokens"]) / self.rate
        
        limit_info = {
            "limit": self.capacity,
            "remaining": int(self.buckets[key]["tokens"]),
            "reset": time.time() + time_until_next_token,
            "rate": self.rate,
        }
        
        return allowed, limit_info
    
    def update(self, key: str) -> None:
        """
        Update the rate limit counter for a key.
        
        Args:
            key: The key to update
        """
        if key not in self.buckets:
            self.buckets[key] = {
                "tokens": self.capacity - 1,  # Consume one token
                "last_refill": time.time(),
            }
        else:
            # Refill tokens
            self._refill(key)
            
            # Consume one token
            self.buckets[key]["tokens"] -= 1
    
    def _refill(self, key: str) -> None:
        """
        Refill tokens for a key.
        
        Args:
            key: The key to refill
        """
        now = time.time()
        time_passed = now - self.buckets[key]["last_refill"]
        new_tokens = time_passed * self.rate
        
        self.buckets[key]["tokens"] = min(self.capacity, self.buckets[key]["tokens"] + new_tokens)
        self.buckets[key]["last_refill"] = now


class RateLimitMiddleware(BaseMiddleware):
    """
    Middleware for rate limiting API requests.
    """
    
    def __init__(
        self,
        limiter: RateLimiter,
        key_func: Optional[Callable[[Request], str]] = None,
        exclude_routes: Optional[List[str]] = None,
        headers_enabled: bool = True,
    ):
        """
        Initialize the rate limit middleware.
        
        Args:
            limiter: The rate limiter to use
            key_func: Function to extract the rate limit key from a request
            exclude_routes: Routes to exclude from rate limiting
            headers_enabled: Whether to include rate limit headers in responses
        """
        super().__init__(
            key_func=key_func,
            exclude_routes=exclude_routes,
            headers_enabled=headers_enabled
        )
        self.limiter = limiter
        self.key_func = key_func or self._default_key_func
        self.exclude_routes = exclude_routes or []
        self.headers_enabled = headers_enabled
    
    def _default_key_func(self, request: Request) -> str:
        """
        Default function to extract the rate limit key from a request.
        
        Args:
            request: The request object
            
        Returns:
            The rate limit key
        """
        # Use client IP as the default key
        return request.client_ip or "unknown"
    
    def _should_limit(self, request: Request) -> bool:
        """
        Determine if a request should be rate limited.
        
        Args:
            request: The request object
            
        Returns:
            True if the request should be rate limited, False otherwise
        """
        # Don't limit excluded routes
        for route in self.exclude_routes:
            if request.path.startswith(route):
                return False
        
        return True
    
    def _add_rate_limit_headers(self, response: Response, limit_info: Dict[str, Any]) -> None:
        """
        Add rate limit headers to a response.
        
        Args:
            response: The response object
            limit_info: Rate limit information
        """
        if not self.headers_enabled:
            return
        
        response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(int(limit_info["reset"]))
        
        if "window" in limit_info:
            response.headers["X-RateLimit-Window"] = str(limit_info["window"])
        if "rate" in limit_info:
            response.headers["X-RateLimit-Rate"] = str(limit_info["rate"])
    
    async def process_request(self, request: Request) -> Request:
        """
        Process a request through the rate limit middleware.
        
        Args:
            request: The request object
            
        Returns:
            The request object
        """
        # Check if we should rate limit this request
        if not self._should_limit(request):
            return request
        
        # Get the rate limit key
        key = self.key_func(request)
        
        # Check if the request is allowed
        allowed, limit_info = self.limiter.check_limit(key)
        
        if not allowed:
            # Request is rate limited
            response = JSONResponse(
                {"error": "Rate limit exceeded"},
                status_code=429,
            )
            self._add_rate_limit_headers(response, limit_info)
            # Store the rate limited response in the request state
            request.state.rate_limited_response = response
            return request
        
        # Update the rate limiter
        self.limiter.update(key)
        
        # Store the limit info in the request state for use in process_response
        request.state.rate_limit_info = limit_info
        
        return request
    
    async def process_response(self, response: Response) -> Response:
        """
        Process a response through the rate limit middleware.
        
        Args:
            response: The response object
            
        Returns:
            The response object
        """
        # If we have a rate limited response in the request state, return it
        if hasattr(response.request.state, 'rate_limited_response'):
            return response.request.state.rate_limited_response
        
        # Add rate limit headers to the response if we have limit info
        if hasattr(response.request.state, 'rate_limit_info'):
            self._add_rate_limit_headers(response, response.request.state.rate_limit_info)
        
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
        path = scope["path"]
        
        # Check if we should rate limit this request
        should_rate_limit = True
        for route in self.exclude_routes:
            if path.startswith(route):
                should_rate_limit = False
                break
                
        if not should_rate_limit:
            await self.app(scope, receive, send)
            return
            
        # Generate rate limit key
        client_ip = scope.get("client", ("127.0.0.1", 0))[0]
        key = f"{client_ip}:{path}"
        
        # Check rate limit
        allowed, limit_info = self.limiter.check_limit(key)
        
        # Update the rate limit counter
        self.limiter.update(key)
        
        # If rate limit is exceeded, return 429 response
        if not allowed:
            headers = [
                (b"content-type", b"application/json"),
            ]
            
            if self.headers_enabled:
                headers.extend([
                    (b"X-RateLimit-Limit", str(limit_info["limit"]).encode()),
                    (b"X-RateLimit-Remaining", b"0"),
                    (b"X-RateLimit-Reset", str(limit_info["reset"]).encode()),
                ])
            
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": headers,
            })
            await send({
                "type": "http.response.body",
                "body": json.dumps({"error": "Rate limit exceeded"}).encode(),
            })
            return
            
        # Not rate limited, process request
        # Add rate limit headers to response
        original_send = send
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start" and self.headers_enabled:
                # Add rate limit headers
                headers = list(message["headers"])
                headers.extend([
                    (b"X-RateLimit-Limit", str(limit_info["limit"]).encode()),
                    (b"X-RateLimit-Remaining", str(limit_info["remaining"]).encode()),
                    (b"X-RateLimit-Reset", str(limit_info["reset"]).encode()),
                ])
                message["headers"] = headers
            
            await original_send(message)
        
        await self.app(scope, receive, send_wrapper)


class RateLimit:
    """
    Decorator for controlling rate limiting on specific endpoints.
    """
    
    @staticmethod
    def limit(limit: int, window: int = 60, key_func: Optional[Callable] = None):
        """
        Apply a rate limit to an endpoint.
        
        Args:
            limit: Maximum number of requests allowed in the window
            window: Time window in seconds
            key_func: Function to extract the rate limit key from a request
            
        Returns:
            A decorator function
        """
        def decorator(func):
            func._rate_limit = {
                "limit": limit,
                "window": window,
                "key_func": key_func,
            }
            return func
        return decorator
    
    @staticmethod
    def exempt(func):
        """
        Exempt an endpoint from rate limiting.
        
        Args:
            func: The function to decorate
            
        Returns:
            The decorated function
        """
        func._rate_limit_exempt = True
        return func 