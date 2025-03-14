from typing import Optional, Callable, Dict, List, Any, Union, TypeVar, Generic, cast
import time
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    """
    A rate limiter implementation that limits the number of requests in a specified time period.
    """
    
    def __init__(
        self, 
        rate: int, 
        period: int, 
        burst: Optional[int] = None, 
        key_func: Optional[Callable[[Any], str]] = None,
        error_message: Optional[str] = None
    ):
        """
        Initialize a rate limiter.
        
        Args:
            rate: Maximum number of requests allowed in the time period
            period: Time period in seconds
            burst: Optional burst limit (maximum number of consecutive requests)
            key_func: Optional function to extract a key from the request
            error_message: Optional custom error message when rate limit is exceeded
        """
        self.rate = rate
        self.period = period
        self.burst = burst or rate
        self.key_func = key_func or (lambda r: str(r))
        self.error_message = error_message or f"Rate limit exceeded: {rate} requests per {period} seconds allowed"
        self._tokens: Dict[str, List[float]] = {}
        
    async def is_rate_limited(self, request: Any) -> bool:
        """
        Check if a request exceeds the rate limit.
        
        Args:
            request: The request to check
            
        Returns:
            bool: True if the request is rate limited, False otherwise
        """
        key = self.key_func(request)
        now = time.time()
        
        # Initialize token bucket if it doesn't exist
        if key not in self._tokens:
            self._tokens[key] = []
        
        # Remove expired tokens
        self._tokens[key] = [t for t in self._tokens[key] if now - t <= self.period]
        
        # Check if rate limit is exceeded
        if len(self._tokens[key]) >= self.rate:
            return True
            
        # Add token for this request
        self._tokens[key].append(now)
        return False
        
    async def acquire(self, request: Any) -> bool:
        """
        Try to acquire a token for the request.
        
        Args:
            request: The request to acquire a token for
            
        Returns:
            bool: True if a token was acquired, False if rate limited
        """
        is_limited = await self.is_rate_limited(request)
        return not is_limited
        
    def get_remaining(self, request: Any) -> int:
        """
        Get the number of remaining requests allowed.
        
        Args:
            request: The request to check
            
        Returns:
            int: Number of remaining requests allowed
        """
        key = self.key_func(request)
        now = time.time()
        
        # Initialize token bucket if it doesn't exist
        if key not in self._tokens:
            return self.rate
        
        # Count valid tokens
        valid_tokens = [t for t in self._tokens[key] if now - t <= self.period]
        return max(0, self.rate - len(valid_tokens))
        
    def get_reset_time(self, request: Any) -> float:
        """
        Get the time until the rate limit resets.
        
        Args:
            request: The request to check
            
        Returns:
            float: Time in seconds until the rate limit resets
        """
        key = self.key_func(request)
        now = time.time()
        
        if key not in self._tokens or not self._tokens[key]:
            return 0.0
        
        oldest_token = min(self._tokens[key])
        reset_time = max(0.0, self.period - (now - oldest_token))
        return reset_time

class TokenBucketRateLimiter(RateLimiter):
    """
    A token bucket implementation of rate limiting.
    """
    
    def __init__(
        self, 
        rate: int, 
        period: int, 
        burst: Optional[int] = None, 
        key_func: Optional[Callable[[Any], str]] = None,
        error_message: Optional[str] = None
    ):
        """
        Initialize a token bucket rate limiter.
        
        Args:
            rate: Rate at which tokens are added to the bucket (tokens/second)
            period: How often to add tokens (in seconds)
            burst: Maximum bucket size (defaults to rate)
            key_func: Function to extract a key from the request
            error_message: Custom error message when rate limit is exceeded
        """
        super().__init__(rate, period, burst, key_func, error_message)
        self._last_refill: Dict[str, float] = {}
        self._tokens = {}  # Override the type from parent to store token counts instead of timestamps
        
    async def is_rate_limited(self, request: Any) -> bool:
        """
        Check if a request exceeds the rate limit using the token bucket algorithm.
        
        Args:
            request: The request to check
            
        Returns:
            bool: True if the request is rate limited, False otherwise
        """
        key = self.key_func(request)
        now = time.time()
        
        # Initialize bucket if it doesn't exist
        if key not in self._tokens:
            self._tokens[key] = self.burst
            self._last_refill[key] = now
            
        # Refill tokens based on elapsed time
        elapsed = now - self._last_refill.get(key, now)
        new_tokens = min(self.burst, self._tokens.get(key, 0) + elapsed * (self.rate / self.period))
        
        # If no tokens available, rate limited
        if new_tokens < 1:
            self._tokens[key] = new_tokens
            self._last_refill[key] = now
            return True
            
        # Consume a token
        self._tokens[key] = new_tokens - 1
        self._last_refill[key] = now
        return False

class FixedWindowRateLimiter(RateLimiter):
    """
    A fixed window implementation of rate limiting.
    """
    
    def __init__(
        self, 
        rate: int, 
        period: int, 
        key_func: Optional[Callable[[Any], str]] = None,
        error_message: Optional[str] = None
    ):
        """
        Initialize a fixed window rate limiter.
        
        Args:
            rate: Maximum number of requests allowed in the window
            period: Window size in seconds
            key_func: Function to extract a key from the request
            error_message: Custom error message when rate limit is exceeded
        """
        super().__init__(rate, period, None, key_func, error_message)
        self._windows: Dict[str, Dict[int, int]] = {}
        
    async def is_rate_limited(self, request: Any) -> bool:
        """
        Check if a request exceeds the rate limit using a fixed window algorithm.
        
        Args:
            request: The request to check
            
        Returns:
            bool: True if the request is rate limited, False otherwise
        """
        key = self.key_func(request)
        now = time.time()
        current_window = int(now / self.period)
        
        # Initialize window if it doesn't exist
        if key not in self._windows:
            self._windows[key] = {}
            
        # Clear old windows
        self._windows[key] = {w: count for w, count in self._windows[key].items() 
                            if w >= current_window - 1}
            
        # Check if current window exceeds limit
        current_count = self._windows[key].get(current_window, 0)
        if current_count >= self.rate:
            return True
            
        # Increment the count for this window
        self._windows[key][current_window] = current_count + 1
        return False

