"""
Request coalescing module for APIFromAnything.

This module provides functionality to coalesce multiple identical requests into a single request,
reducing the load on backend services and improving performance.
"""

import threading
import time
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast, Union, overload

# Type variables for generic typing
T = TypeVar('T')
R = TypeVar('R')

# Set up logging
logger = logging.getLogger(__name__)


class CoalescedRequest:
    """
    Represents a coalesced request.
    
    This class is used to track multiple identical requests that have been coalesced into a single request.
    """
    
    def __init__(self, key: str, func: Callable, args: tuple, kwargs: dict):
        """
        Initialize a coalesced request.
        
        Args:
            key (str): Cache key for the request.
            func (Callable): Function to execute.
            args (tuple): Positional arguments for the function.
            kwargs (dict): Keyword arguments for the function.
        """
        self.key = key
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.timestamp = time.time()
        self.count = 1
        self.result = None
        self.is_executed = False
        self.is_error = False
        self.is_error = False
        self.error: Optional[Exception] = None
    def execute(self) -> Any:
        """
        Execute the request.
        
        Returns:
            Any: Result of executing the function.
        """
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.is_executed = True
            return self.result
        except Exception as e:
            self.is_error = True
            self.error = e
            raise e


class RequestCoalescingManager:
    """
    Manager for coalescing requests across the application.
    
    This class provides a centralized way to manage request coalescing across the application.
    """
    
    def __init__(self):
        """Initialize the request coalescing manager."""
        self.coalescers: Dict[str, RequestCoalescer] = {}
        self.lock = threading.Lock()
        self.stats = {
            "total_requests": 0,
            "coalesced_requests": 0,
            "executed_requests": 0
        }
    
    def get_coalescer(self, func: Callable, window_time: float = 0.1, max_requests: Optional[int] = None) -> 'RequestCoalescer':
        """
        Get or create a coalescer for a function.
        
        Args:
            func (Callable): Function to coalesce.
            window_time (float): Time window in seconds to coalesce requests.
            max_requests (int, optional): Maximum number of requests to coalesce.
            
        Returns:
            RequestCoalescer: Coalescer for the function.
        """
        func_id = str(id(func))

        with self.lock:
            if func_id not in self.coalescers:
                self.coalescers[func_id] = RequestCoalescer(func, window_time, max_requests)
            
            return self.coalescers[func_id]
    
    def execute(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a request, potentially coalescing it with other identical requests.
        
        Args:
            func (Callable): Function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.
            
        Returns:
            Any: Result of executing the function.
        """
        coalescer = self.get_coalescer(func)
        return coalescer.execute(*args, **kwargs)
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the manager.
        
        Returns:
            dict: Statistics about the manager.
        """
        with self.lock:
            stats = self.stats.copy()
            
            # Add stats from all coalescers
            for coalescer in self.coalescers.values():
                coalescer_stats = coalescer.get_stats()
                stats["total_requests"] += coalescer_stats["total_requests"]
                stats["coalesced_requests"] += coalescer_stats["coalesced_requests"]
                stats["executed_requests"] += coalescer_stats["executed_requests"]
            
            return stats


class RequestCoalescingMiddleware:
    """
    Middleware for coalescing requests.
    
    This middleware can be used to coalesce requests at the middleware level.
    """
    
    def __init__(self, window_time: float = 0.1, max_requests: Optional[int] = None):
        """
        Initialize the request coalescing middleware.
        
        Args:
            window_time (float): Time window in seconds to coalesce requests.
            max_requests (int, optional): Maximum number of requests to coalesce.
        """
        self.window_time = window_time
        self.max_requests = max_requests
        self.manager = RequestCoalescingManager()
    
    def process_request(self, request: Any) -> Any:
        """
        Process a request, potentially coalescing it with other identical requests.
        
        Args:
            request (Any): Request to process.
            
        Returns:
            Any: Processed request.
        """
        # This is a simplified implementation for testing
        # In a real implementation, you would need to extract the function and arguments from the request
        return request
    
    def process_response(self, request: Any, response: Any) -> Any:
        """
        Process a response.
        
        Args:
            request (Any): Request that generated the response.
            response (Any): Response to process.
            
        Returns:
            Any: Processed response.
        """
        return response
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the middleware.
        
        Returns:
            dict: Statistics about the middleware.
        """
        return self.manager.get_stats()


class RequestCoalescer:
    """
    Coalescer for handling duplicate requests.
    
    This class provides functionality to coalesce multiple identical requests into a single request,
    reducing the load on backend services and improving performance.
    """
    
    def __init__(self, func: Callable[..., R], window_time: float = 0.1, max_requests: Optional[int] = None):
        """
        Initialize the request coalescer.
        
        Args:
            func (Callable): Function to execute.
            window_time (float): Time window in seconds to coalesce requests.
            max_requests (int, optional): Maximum number of requests to coalesce.
        """
        self.func = func
        self.window_time = window_time
        self.max_requests = max_requests
        self.pending_requests: Dict[str, Dict[str, Any]] = {}
        self.results_cache: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.stats = {
            "total_requests": 0,
            "coalesced_requests": 0,
            "executed_requests": 0
        }
        self.request_counts: Dict[str, int] = {}
        self.lock_acquired = False

        def execute(self, *args: Any, **kwargs: Any) -> R:
            """
            Execute a request, potentially coalescing it with other identical requests.
            
            Args:
                *args: Positional arguments for the function.
                **kwargs: Keyword arguments for the function.
                
            Returns:
                Any: Result of executing the function.
            """
        # Create a cache key from the arguments
        # Create a cache key from the arguments
        key = self._create_key(*args, **kwargs)
        
        self.lock.acquire()
        self.lock_acquired = True
        
        try:
            self.stats["total_requests"] += 1
            
            # Check if we need to execute a new request
            execute_new_request = False
            
            # Check if the key exists in the cache
            if key not in self.pending_requests:
                execute_new_request = True
            # Check if the window time has elapsed
            elif time.time() - self.pending_requests[key]["timestamp"] > self.window_time:
                execute_new_request = True
            # Check if we've reached max_requests
            elif self.max_requests is not None:
                request_count = self.request_counts.get(key, 0) + 1
                self.request_counts[key] = request_count
                if request_count >= self.max_requests:
                    execute_new_request = True
                    self.request_counts[key] = 0
            
            # If we need to execute a new request
            if execute_new_request:
                # Mark this request as pending
                self.pending_requests[key] = {
                    "timestamp": time.time()
                }
                
                # Release the lock while executing the function
                # to avoid blocking other requests
                self.lock.release()
                self.lock_acquired = False
                
                try:
                    self.stats["executed_requests"] += 1
                    result = self.func(*args, **kwargs)
                    
                    # Acquire the lock again to update the cache
                    self.lock.acquire()
                    self.lock_acquired = True
                    
                    self.results_cache[key] = result

                    # Remove the pending request
                    if key in self.pending_requests:
                        del self.pending_requests[key]
                except Exception as e:
                    # Acquire the lock again to update the cache
                    if not self.lock_acquired:
                        self.lock.acquire()
                        self.lock_acquired = True
                    
                    # Remove the pending request
                    if key in self.pending_requests:
                        del self.pending_requests[key]
                    
                    # Re-raise the exception
                    raise e
            else:
                # Return the cached result if available
                if key in self.results_cache:
                    self.stats["coalesced_requests"] += 1
                    result = self.results_cache[key]
                    self.lock.release()
                    self.lock_acquired = False
                    return cast(R, result)
                
                # Wait for the result to be available
                # This should not happen in normal operation
                logger.warning(f"Request {key} is pending but no result is available")
                self.lock.release()
                self.lock_acquired = False
                return None  # type: ignore
        finally:
            # Make sure the lock is released
            if self.lock_acquired:
                self.lock.release()
                self.lock_acquired = False
    
    def _create_key(self, args: Any, kwargs: Any) -> str:
        """
        Create a cache key from the arguments.
        
        Args:
            args: Positional arguments.
            kwargs: Keyword arguments.
            
        Returns:
            str: Cache key.
        """
        # This is a simplified key creation method
        # In a production environment, you might want to use a more robust method
        return f"{str(args)}:{str(kwargs)}"
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the coalescer.
        
        Returns:
            dict: Statistics about the coalescer.
        """
        with self.lock:
            return self.stats.copy()


def coalesce_requests(window_time: float = 0.1, max_requests: Optional[int] = None) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator for coalescing multiple identical requests into a single request.
    
    Args:
        window_time (float): Time window in seconds to coalesce requests.
        max_requests (int, optional): Maximum number of requests to coalesce.
        
    Returns:
        Callable: Decorated function that coalesces requests.
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        # Create a request coalescer for this function
        coalescer = RequestCoalescer(func, window_time, max_requests)
        
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # Coalesce the request and get the result
            return coalescer.execute(*args, **kwargs)
        
        # Attach the coalescer to the wrapper for testing
        wrapper.coalescer = coalescer  # type: ignore
        
        return wrapper
    
    return decorator 