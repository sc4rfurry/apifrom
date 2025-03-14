"""
Web Optimization Decorator for the APIFromAnything library.

This module provides the WebOptimize decorator, which combines the Web decorator
with performance optimization features like profiling, caching, connection pooling,
request coalescing, and batch processing.
"""
import functools
from typing import Any, Callable, Dict, List, Optional, Union, Type

from apifrom.decorators.web import Web
from apifrom.performance.profiler import APIProfiler
from apifrom.performance.cache_optimizer import CacheOptimizer
from apifrom.performance.connection_pool import ConnectionPool, PoolManager
from apifrom.performance.request_coalescing import coalesce_requests
from apifrom.performance.batch_processing import batch_process
from apifrom.middleware.cache_advanced import MemoryCacheBackend
from apifrom.core.app import API


class WebOptimize(Web):
    """
    Decorator that combines the Web decorator with performance optimization features.
    
    This decorator enhances API endpoints with HTML rendering capabilities and
    performance optimization features like profiling, caching, connection pooling,
    request coalescing, and batch processing.
    
    Attributes:
        title (str): The title to display in the HTML page
        description (str): A description of the endpoint to display in the HTML
        theme (str): The theme to use for styling ('default', 'dark', 'light')
        template (str): Optional path to a custom HTML template
        enable_profiling (bool): Whether to enable profiling
        enable_caching (bool): Whether to enable caching
        cache_ttl (int): Time-to-live for cached responses in seconds
        enable_connection_pooling (bool): Whether to enable connection pooling
        pool_name (str): Name of the connection pool to use
        enable_request_coalescing (bool): Whether to enable request coalescing
        coalesce_window_time (float): Time window for coalescing requests in seconds
        coalesce_max_requests (int): Maximum number of requests to coalesce
        enable_batch_processing (bool): Whether to enable batch processing
        batch_size (int): Maximum batch size for batch processing
        batch_wait_time (float): Maximum wait time for batch processing in seconds
    
    Example:
        ```python
        from apifrom.core.app import API
        from apifrom.decorators.web_optimize import WebOptimize
        
        app = API()
        
        @app.api('/users')
        @WebOptimize(
            title="Users API",
            description="Get a list of users",
            enable_caching=True,
            cache_ttl=60,
            enable_profiling=True
        )
        def get_users(request):
            return [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
                {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
            ]
        ```
    """
    
    # Class-level instances of optimization components
    _profiler = APIProfiler()
    _cache_optimizer = CacheOptimizer(cache_backend=MemoryCacheBackend())
    _pool_manager = PoolManager()
    
    @classmethod
    def get_profiler(cls) -> APIProfiler:
        """Get the class-level profiler instance."""
        return cls._profiler
    
    @classmethod
    def get_cache_optimizer(cls) -> CacheOptimizer:
        """Get the class-level cache optimizer instance."""
        return cls._cache_optimizer
    
    @classmethod
    def get_pool_manager(cls) -> PoolManager:
        """Get the class-level pool manager instance."""
        return cls._pool_manager
    
    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        theme: str = "default",
        template: Optional[str] = None,
        enable_profiling: bool = False,
        enable_caching: bool = False,
        cache_ttl: int = 60,
        enable_connection_pooling: bool = False,
        pool_name: Optional[str] = None,
        enable_request_coalescing: bool = False,
        coalesce_window_time: float = 0.5,
        coalesce_max_requests: int = 10,
        enable_batch_processing: bool = False,
        batch_size: int = 10,
        batch_wait_time: float = 0.5
    ):
        """
        Initialize the WebOptimize decorator.
        
        Args:
            title: The title to display in the HTML page
            description: A description of the endpoint to display in the HTML
            theme: The theme to use for styling ('default', 'dark', 'light')
            template: Optional path to a custom HTML template
            enable_profiling: Whether to enable profiling
            enable_caching: Whether to enable caching
            cache_ttl: Time-to-live for cached responses in seconds
            enable_connection_pooling: Whether to enable connection pooling
            pool_name: Name of the connection pool to use
            enable_request_coalescing: Whether to enable request coalescing
            coalesce_window_time: Time window for coalescing requests in seconds
            coalesce_max_requests: Maximum number of requests to coalesce
            enable_batch_processing: Whether to enable batch processing
            batch_size: Maximum batch size for batch processing
            batch_wait_time: Maximum wait time for batch processing in seconds
        """
        # Initialize the Web decorator
        super().__init__(title, description, theme, template)
        
        # Store optimization settings
        self.enable_profiling = enable_profiling
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl
        self.enable_connection_pooling = enable_connection_pooling
        self.pool_name = pool_name
        self.enable_request_coalescing = enable_request_coalescing
        self.coalesce_window_time = coalesce_window_time
        self.coalesce_max_requests = coalesce_max_requests
        self.enable_batch_processing = enable_batch_processing
        self.batch_size = batch_size
        self.batch_wait_time = batch_wait_time
    
    def __call__(self, func: Callable) -> Callable:
        """
        Apply the WebOptimize decorator to a function.
        
        Args:
            func: The function to decorate
            
        Returns:
            The decorated function
        """
        # Apply optimization decorators in the correct order
        decorated_func = func
        
        # Apply batch processing (should be first)
        if self.enable_batch_processing:
            decorated_func = batch_process(
                batch_size=self.batch_size,
                max_wait_time=self.batch_wait_time
            )(decorated_func)
        
        # Apply request coalescing
        if self.enable_request_coalescing:
            decorated_func = coalesce_requests(
                window_time=self.coalesce_window_time,
                max_requests=self.coalesce_max_requests
            )(decorated_func)
        
        # Apply caching
        if self.enable_caching:
            decorated_func = self._cache_optimizer.optimize(
                ttl=self.cache_ttl
            )(decorated_func)
        
        # Apply profiling (should be last before Web)
        if self.enable_profiling:
            decorated_func = self._profiler.profile_endpoint(decorated_func)
        
        # Apply the Web decorator
        decorated_func = super().__call__(decorated_func)
        
        # Return the fully decorated function
        return decorated_func
    
    @classmethod
    def optimize(
        cls,
        title: Optional[str] = None,
        description: Optional[str] = None,
        theme: str = "default",
        template: Optional[str] = None,
        enable_profiling: bool = True,
        enable_caching: bool = True,
        cache_ttl: int = 60,
        enable_connection_pooling: bool = True,
        pool_name: Optional[str] = None,
        enable_request_coalescing: bool = True,
        coalesce_window_time: float = 0.5,
        coalesce_max_requests: int = 10,
        enable_batch_processing: bool = False,
        batch_size: int = 10,
        batch_wait_time: float = 0.5
    ) -> Callable:
        """
        Class method to create a WebOptimize decorator with the specified settings.
        
        This is a convenience method for creating a WebOptimize decorator with
        common optimization settings.
        
        Args:
            title: The title to display in the HTML page
            description: A description of the endpoint to display in the HTML
            theme: The theme to use for styling ('default', 'dark', 'light')
            template: Optional path to a custom HTML template
            enable_profiling: Whether to enable profiling
            enable_caching: Whether to enable caching
            cache_ttl: Time-to-live for cached responses in seconds
            enable_connection_pooling: Whether to enable connection pooling
            pool_name: Name of the connection pool to use
            enable_request_coalescing: Whether to enable request coalescing
            coalesce_window_time: Time window for coalescing requests in seconds
            coalesce_max_requests: Maximum number of requests to coalesce
            enable_batch_processing: Whether to enable batch processing
            batch_size: Maximum batch size for batch processing
            batch_wait_time: Maximum wait time for batch processing in seconds
            
        Returns:
            A WebOptimize decorator with the specified settings
        """
        return cls(
            title=title,
            description=description,
            theme=theme,
            template=template,
            enable_profiling=enable_profiling,
            enable_caching=enable_caching,
            cache_ttl=cache_ttl,
            enable_connection_pooling=enable_connection_pooling,
            pool_name=pool_name,
            enable_request_coalescing=enable_request_coalescing,
            coalesce_window_time=coalesce_window_time,
            coalesce_max_requests=coalesce_max_requests,
            enable_batch_processing=enable_batch_processing,
            batch_size=batch_size,
            batch_wait_time=batch_wait_time
        )
    
    @classmethod
    def create_pool(
        cls,
        name: str,
        min_size: int = 5,
        max_size: int = 20,
        validate_func: Optional[Callable] = None
    ) -> ConnectionPool:
        """
        Create a connection pool with the specified settings.
        
        Args:
            name: Name of the connection pool
            min_size: Minimum number of connections in the pool
            max_size: Maximum number of connections in the pool
            validate_func: Function to validate connections
            
        Returns:
            A ConnectionPool instance
        """
        return cls._pool_manager.create_pool(
            name=name,
            min_size=min_size,
            max_size=max_size,
            validate_func=validate_func
        )
    
    @classmethod
    def get_pool(cls, name: str) -> Optional[ConnectionPool]:
        """
        Get a connection pool by name.
        
        Args:
            name: Name of the connection pool
            
        Returns:
            A ConnectionPool instance, or None if not found
        """
        return cls._pool_manager.get_pool(name)
    
    @classmethod
    def get_performance_metrics(cls) -> Dict[str, Any]:
        """
        Get performance metrics from all optimization components.
        
        Returns:
            A dictionary of performance metrics
        """
        return {
            "profiler": {
                "uptime": cls._profiler.get_uptime(),
                "total_requests": cls._profiler.get_total_requests(),
                "average_response_time": cls._profiler.get_average_response_time(),
                "requests_per_minute": cls._profiler.get_requests_per_minute(),
                "error_rate": cls._profiler.get_error_rate(),
                "endpoint_stats": cls._profiler.get_endpoint_stats()
            },
            "cache": cls._cache_optimizer.get_stats(),
            "connection_pools": cls._pool_manager.get_stats()
        }


# Alias for backward compatibility and convenience
Web.optimize = WebOptimize.optimize 

app = API() 