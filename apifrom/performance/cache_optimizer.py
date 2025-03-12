"""
Cache optimization utilities for APIFromAnything.

This module provides tools for optimizing cache performance in high-load scenarios,
including cache strategy optimization, monitoring, and auto-tuning.
"""

import time
import threading
import asyncio
from typing import Dict, List, Optional, Callable, Any, Union, Tuple
import logging
import json
import os
from datetime import datetime
import hashlib

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware.base import BaseMiddleware
from apifrom.middleware.cache_advanced import CacheBackend


# Set up logging
logger = logging.getLogger("apifrom.performance.cache_optimizer")


class CacheAnalytics:
    """
    Collects and analyzes cache performance metrics.
    
    This class collects cache performance metrics such as hit rates,
    latency, and memory usage, and provides tools for analyzing
    and visualizing this data.
    """
    
    def __init__(self):
        """
        Initialize cache analytics.
        """
        self._lock = threading.Lock()
        self.reset()
    
    def reset(self):
        """
        Reset all analytics data.
        """
        with self._lock:
            self.start_time = time.time()
            self.requests = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.cache_errors = 0
            self.cache_size = 0
            self.key_sizes = {}
            self.value_sizes = {}
            self.ttls = {}
            self.hit_latencies = []
            self.miss_latencies = []
    
    def record_request(self):
        """
        Record a cache request.
        """
        with self._lock:
            self.requests += 1
    
    def record_hit(self, key: str, value_size: int, latency: float):
        """
        Record a cache hit.
        
        Args:
            key: The cache key
            value_size: The size of the cached value in bytes
            latency: The cache lookup latency in seconds
        """
        with self._lock:
            self.cache_hits += 1
            self.key_sizes[key] = len(key.encode('utf-8'))
            self.value_sizes[key] = value_size
            self.hit_latencies.append(latency * 1000)  # Convert to ms
    
    def record_miss(self, key: str, latency: float):
        """
        Record a cache miss.
        
        Args:
            key: The cache key
            latency: The cache lookup latency in seconds
        """
        with self._lock:
            self.cache_misses += 1
            self.key_sizes[key] = len(key.encode('utf-8'))
            self.miss_latencies.append(latency * 1000)  # Convert to ms
    
    def record_error(self, key: str):
        """
        Record a cache error.
        
        Args:
            key: The cache key
        """
        with self._lock:
            self.cache_errors += 1
    
    def record_set(self, key: str, value_size: int, ttl: int):
        """
        Record a cache set operation.
        
        Args:
            key: The cache key
            value_size: The size of the cached value in bytes
            ttl: The TTL in seconds
        """
        with self._lock:
            self.key_sizes[key] = len(key.encode('utf-8'))
            self.value_sizes[key] = value_size
            self.ttls[key] = ttl
            self.cache_size += value_size
    
    def record_delete(self, key: str, value_size: int):
        """
        Record a cache delete operation.
        
        Args:
            key: The cache key
            value_size: The size of the cached value in bytes
        """
        with self._lock:
            if key in self.key_sizes:
                del self.key_sizes[key]
            if key in self.value_sizes:
                del self.value_sizes[key]
            if key in self.ttls:
                del self.ttls[key]
            self.cache_size -= value_size
    
    @property
    def hit_rate(self) -> float:
        """
        Get the cache hit rate.
        
        Returns:
            The cache hit rate (0.0 to 1.0)
        """
        with self._lock:
            if self.requests == 0:
                return 0.0
            return self.cache_hits / self.requests
    
    @property
    def avg_hit_latency(self) -> float:
        """
        Get the average cache hit latency in milliseconds.
        
        Returns:
            The average cache hit latency
        """
        with self._lock:
            if not self.hit_latencies:
                return 0.0
            return sum(self.hit_latencies) / len(self.hit_latencies)
    
    @property
    def avg_miss_latency(self) -> float:
        """
        Get the average cache miss latency in milliseconds.
        
        Returns:
            The average cache miss latency
        """
        with self._lock:
            if not self.miss_latencies:
                return 0.0
            return sum(self.miss_latencies) / len(self.miss_latencies)
    
    @property
    def avg_key_size(self) -> float:
        """
        Get the average key size in bytes.
        
        Returns:
            The average key size
        """
        with self._lock:
            if not self.key_sizes:
                return 0.0
            return sum(self.key_sizes.values()) / len(self.key_sizes)
    
    @property
    def avg_value_size(self) -> float:
        """
        Get the average value size in bytes.
        
        Returns:
            The average value size
        """
        with self._lock:
            if not self.value_sizes:
                return 0.0
            return sum(self.value_sizes.values()) / len(self.value_sizes)
    
    @property
    def avg_ttl(self) -> float:
        """
        Get the average TTL in seconds.
        
        Returns:
            The average TTL
        """
        with self._lock:
            if not self.ttls:
                return 0.0
            return sum(self.ttls.values()) / len(self.ttls)
    
    def get_hot_keys(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get the most frequently accessed cache keys.
        
        Args:
            limit: The maximum number of keys to return
            
        Returns:
            A list of (key, access_count) tuples
        """
        # This is a placeholder; in a real implementation, you would track key access counts
        return []
    
    def get_large_keys(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get the largest cache keys by value size.
        
        Args:
            limit: The maximum number of keys to return
            
        Returns:
            A list of (key, size) tuples
        """
        with self._lock:
            return sorted(self.value_sizes.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the analytics data to a dictionary.
        
        Returns:
            A dictionary representation of the analytics data
        """
        with self._lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": time.time() - self.start_time,
                "requests": self.requests,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_errors": self.cache_errors,
                "hit_rate": self.hit_rate,
                "avg_hit_latency_ms": self.avg_hit_latency,
                "avg_miss_latency_ms": self.avg_miss_latency,
                "cache_size_bytes": self.cache_size,
                "avg_key_size_bytes": self.avg_key_size,
                "avg_value_size_bytes": self.avg_value_size,
                "avg_ttl_seconds": self.avg_ttl,
                "hot_keys": self.get_hot_keys(),
                "large_keys": self.get_large_keys(),
            }
    
    def to_json(self, pretty: bool = True) -> str:
        """
        Convert the analytics data to a JSON string.
        
        Args:
            pretty: Whether to format the JSON with indentation
            
        Returns:
            A JSON string representation of the analytics data
        """
        indent = 2 if pretty else None
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, file_path: str) -> None:
        """
        Save the analytics data to a file.
        
        Args:
            file_path: The path to save the data to
        """
        with open(file_path, 'w') as f:
            f.write(self.to_json())
    
    def print_summary(self) -> None:
        """
        Print a summary of the analytics data to the console.
        """
        print("=== Cache Analytics Summary ===")
        print(f"Duration: {time.time() - self.start_time:.2f} seconds")
        print(f"Total Requests: {self.requests}")
        print(f"Cache Hits: {self.cache_hits}")
        print(f"Cache Misses: {self.cache_misses}")
        print(f"Cache Errors: {self.cache_errors}")
        print(f"Hit Rate: {self.hit_rate:.2%}")
        print(f"Average Hit Latency: {self.avg_hit_latency:.2f} ms")
        print(f"Average Miss Latency: {self.avg_miss_latency:.2f} ms")
        print(f"Cache Size: {self.cache_size / 1024:.2f} KB")
        print(f"Average Key Size: {self.avg_key_size:.2f} bytes")
        print(f"Average Value Size: {self.avg_value_size:.2f} bytes")
        print(f"Average TTL: {self.avg_ttl:.2f} seconds")
        
        print("\nTop 5 Largest Keys:")
        for i, (key, size) in enumerate(self.get_large_keys(5)):
            print(f"{i+1}. {key}: {size / 1024:.2f} KB")


class OptimizedCacheStrategy:
    """
    A cache strategy that optimizes caching based on runtime analytics.
    
    This class provides cache optimization strategies such as TTL adjustment,
    key compression, and value compression, based on runtime analytics.
    """
    
    def __init__(self,
                 min_ttl: int = 60,
                 max_ttl: int = 86400,
                 hit_rate_threshold: float = 0.8,
                 compress_values: bool = True,
                 compress_keys: bool = False,
                 prefetch_keys: bool = False,
                 auto_tune: bool = True):
        """
        Initialize an optimized cache strategy.
        
        Args:
            min_ttl: The minimum TTL in seconds
            max_ttl: The maximum TTL in seconds
            hit_rate_threshold: The hit rate threshold for TTL adjustment
            compress_values: Whether to compress cached values
            compress_keys: Whether to compress cache keys
            prefetch_keys: Whether to prefetch related keys
            auto_tune: Whether to auto-tune caching parameters
        """
        self.min_ttl = min_ttl
        self.max_ttl = max_ttl
        self.hit_rate_threshold = hit_rate_threshold
        self.compress_values = compress_values
        self.compress_keys = compress_keys
        self.prefetch_keys = prefetch_keys
        self.auto_tune = auto_tune
        
        self.key_ttls = {}
        self.key_hit_counts = {}
        self.key_access_times = {}
        self.analytics = CacheAnalytics()
    
    def get_optimized_ttl(self, key: str, default_ttl: int) -> int:
        """
        Get an optimized TTL for a key based on access patterns.
        
        Args:
            key: The cache key
            default_ttl: The default TTL in seconds
            
        Returns:
            The optimized TTL in seconds
        """
        if not self.auto_tune:
            return default_ttl
        
        # If this is a new key, use the default TTL
        if key not in self.key_hit_counts:
            return default_ttl
        
        hit_count = self.key_hit_counts.get(key, 0)
        last_access = self.key_access_times.get(key, 0)
        current_ttl = self.key_ttls.get(key, default_ttl)
        
        # Adjust TTL based on hit count and recency
        if hit_count > 10:
            # Frequently accessed key, increase TTL
            return min(current_ttl * 2, self.max_ttl)
        elif time.time() - last_access > 3600:
            # Infrequently accessed key, decrease TTL
            return max(current_ttl // 2, self.min_ttl)
        
        return current_ttl
    
    def optimize_key(self, key: str) -> str:
        """
        Optimize a cache key.
        
        Args:
            key: The original cache key
            
        Returns:
            The optimized cache key
        """
        if not self.compress_keys:
            return key
        
        # Simple key compression using a hash
        return hashlib.md5(key.encode('utf-8')).hexdigest()
    
    def optimize_value(self, value: Any) -> Any:
        """
        Optimize a cached value.
        
        Args:
            value: The original value
            
        Returns:
            The optimized value
        """
        # Note: In a real implementation, you would compress the value
        return value
    
    def record_hit(self, key: str):
        """
        Record a cache hit for a key.
        
        Args:
            key: The cache key
        """
        self.key_hit_counts[key] = self.key_hit_counts.get(key, 0) + 1
        self.key_access_times[key] = time.time()
    
    def record_miss(self, key: str):
        """
        Record a cache miss for a key.
        
        Args:
            key: The cache key
        """
        # No action needed for misses in this implementation
        pass
    
    def record_set(self, key: str, ttl: int):
        """
        Record a cache set operation.
        
        Args:
            key: The cache key
            ttl: The TTL in seconds
        """
        self.key_ttls[key] = ttl
        self.key_access_times[key] = time.time()


class CacheOptimizer:
    """
    Optimizes caching for high-load scenarios.
    
    This class provides tools for optimizing cache performance,
    including strategy optimization, monitoring, and auto-tuning.
    """
    
    def __init__(self,
                 cache_backend: CacheBackend,
                 strategy: Optional[OptimizedCacheStrategy] = None,
                 analytics: Optional[CacheAnalytics] = None,
                 auto_tune_interval: Optional[int] = None,
                 output_dir: Optional[str] = None):
        """
        Initialize a cache optimizer.
        
        Args:
            cache_backend: The cache backend to optimize
            strategy: The optimization strategy to use
            analytics: The cache analytics instance to use
            auto_tune_interval: The interval in seconds at which to auto-tune
            output_dir: The directory to save analytics data to
        """
        self.cache_backend = cache_backend
        self.strategy = strategy or OptimizedCacheStrategy()
        self.analytics = analytics or CacheAnalytics()
        self.auto_tune_interval = auto_tune_interval
        self.output_dir = output_dir
        
        self._last_auto_tune = time.time()
        self._lock = threading.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache with optimization.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value, or None if not found
        """
        self.analytics.record_request()
        
        # Optimize the key
        optimized_key = self.strategy.optimize_key(key)
        
        # Measure cache latency
        start_time = time.time()
        
        try:
            # Get from cache
            cached_value = await self.cache_backend.get(optimized_key)
            
            # Record latency
            latency = time.time() - start_time
            
            if cached_value is None:
                # Cache miss
                self.analytics.record_miss(key, latency)
                self.strategy.record_miss(key)
                return None
            
            # Cache hit
            value_size = len(json.dumps(cached_value).encode('utf-8'))
            self.analytics.record_hit(key, value_size, latency)
            self.strategy.record_hit(key)
            
            return cached_value
        except Exception as e:
            # Cache error
            logger.warning(f"Cache error: {e}")
            self.analytics.record_error(key)
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 60) -> bool:
        """
        Set a value in the cache with optimization.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: The TTL in seconds
            
        Returns:
            True if the value was cached, False otherwise
        """
        # Optimize the key and value
        optimized_key = self.strategy.optimize_key(key)
        optimized_value = self.strategy.optimize_value(value)
        
        # Optimize TTL
        optimized_ttl = self.strategy.get_optimized_ttl(key, ttl)
        
        try:
            # Set in cache
            success = await self.cache_backend.set(optimized_key, optimized_value, optimized_ttl)
            
            if success:
                # Record successful set
                value_size = len(json.dumps(optimized_value).encode('utf-8'))
                self.analytics.record_set(key, value_size, optimized_ttl)
                self.strategy.record_set(key, optimized_ttl)
            
            return success
        except Exception as e:
            # Cache error
            logger.warning(f"Cache error: {e}")
            self.analytics.record_error(key)
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the value was deleted, False otherwise
        """
        # Optimize the key
        optimized_key = self.strategy.optimize_key(key)
        
        try:
            # Get the value size before deleting
            cached_value = await self.cache_backend.get(optimized_key)
            value_size = 0
            if cached_value is not None:
                value_size = len(json.dumps(cached_value).encode('utf-8'))
            
            # Delete from cache
            success = await self.cache_backend.delete(optimized_key)
            
            if success and value_size > 0:
                # Record successful delete
                self.analytics.record_delete(key, value_size)
            
            return success
        except Exception as e:
            # Cache error
            logger.warning(f"Cache error: {e}")
            self.analytics.record_error(key)
            return False
    
    def auto_tune(self) -> None:
        """
        Auto-tune caching parameters based on analytics.
        """
        # Check if auto-tuning is enabled and due
        if (self.auto_tune_interval is None or
            time.time() - self._last_auto_tune < self.auto_tune_interval):
            return
        
        logger.info("Auto-tuning cache parameters...")
        
        # Get analytics data
        hit_rate = self.analytics.hit_rate
        avg_hit_latency = self.analytics.avg_hit_latency
        avg_value_size = self.analytics.avg_value_size
        
        # Adjust strategy parameters based on analytics
        with self._lock:
            # Adjust TTL based on hit rate
            if hit_rate < 0.5:
                # Low hit rate, decrease TTL
                self.strategy.max_ttl = max(self.strategy.max_ttl // 2, self.strategy.min_ttl)
                logger.info(f"Decreased max TTL to {self.strategy.max_ttl} seconds")
            elif hit_rate > 0.9:
                # High hit rate, increase TTL
                self.strategy.max_ttl = min(self.strategy.max_ttl * 2, 86400 * 7)  # Max 1 week
                logger.info(f"Increased max TTL to {self.strategy.max_ttl} seconds")
            
            # Enable value compression for large values
            if avg_value_size > 10 * 1024:  # 10 KB
                self.strategy.compress_values = True
                logger.info("Enabled value compression for large values")
            
            # Enable key compression for slow cache lookups
            if avg_hit_latency > 20:  # 20 ms
                self.strategy.compress_keys = True
                logger.info("Enabled key compression for slow cache lookups")
        
        # Save analytics data
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(self.output_dir, f"cache_analytics_{timestamp}.json")
            self.analytics.save(file_path)
            logger.info(f"Saved cache analytics to {file_path}")
        
        # Reset auto-tune timer
        self._last_auto_tune = time.time()
    
    def get_analytics(self) -> CacheAnalytics:
        """
        Get the cache analytics.
        
        Returns:
            The cache analytics instance
        """
        return self.analytics
    
    def reset_analytics(self) -> None:
        """
        Reset the cache analytics.
        """
        self.analytics.reset()


class OptimizedCacheMiddleware(BaseMiddleware):
    """
    Middleware for adding optimized caching to an API.
    
    This middleware adds optimized caching to an API, using the CacheOptimizer
    to optimize caching strategies based on request patterns.
    """
    
    def __init__(
        self,
        cache_backend=None,
        ttl: int = 60,
        auto_tune: bool = True,
        auto_tune_interval: int = 300,
        output_dir: Optional[str] = None,
        compression: bool = True,
        **options
    ):
        """
        Initialize the optimized cache middleware.
        
        Args:
            cache_backend: The cache backend to use
            ttl: Default time-to-live in seconds
            auto_tune: Whether to auto-tune cache parameters
            auto_tune_interval: The interval to auto-tune cache parameters in seconds
            output_dir: The directory to save analytics to
            compression: Whether to compress cached responses
            **options: Additional options
        """
        super().__init__(**options)
        
        # Import necessary middleware here to avoid circular imports
        try:
            from apifrom.middleware.cache_advanced import (
                MemoryCacheBackend, 
                AdvancedCacheMiddleware,
                HybridEvictionPolicy
            )
            have_advanced_cache = True
        except ImportError:
            from apifrom.middleware.cache import CacheMiddleware
            have_advanced_cache = False
        
        # Create the cache backend if not provided
        if cache_backend is None:
            if have_advanced_cache:
                self.cache_backend = MemoryCacheBackend(
                    eviction_policy=HybridEvictionPolicy()
                )
            else:
                # Fall back to default cache implementation
                self.cache_backend = {}
        else:
            self.cache_backend = cache_backend
        
        # Create the cache middleware
        if have_advanced_cache:
            self.cache_middleware = AdvancedCacheMiddleware(
                cache_backend=self.cache_backend,
                ttl=ttl,
                compress_responses=compression,
                auto_vary=True,
                **options
            )
        else:
            self.cache_middleware = CacheMiddleware(
                ttl=ttl,
                **options
            )
        
        self.ttl = ttl
        self.auto_tune = auto_tune
        self.auto_tune_interval = auto_tune_interval
        self.output_dir = output_dir
        self.compression = compression
        
        # Create the cache optimizer
        self.optimizer = CacheOptimizer(
            cache_backend=self.cache_backend,
            output_dir=output_dir
        )
        
        # Analytics collection
        self.analytics = CacheAnalytics()
        
        # Auto-tuning
        self.last_tune_time = time.time()
        
        # Create the output directory if it doesn't exist
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

    async def process_request(self, request):
        """
        Process a request (required by BaseMiddleware).
        
        Args:
            request: The request to process
            
        Returns:
            The processed request
        """
        return request
    
    async def process_response(self, response):
        """
        Process a response (required by BaseMiddleware).
        
        Args:
            response: The response to process
            
        Returns:
            The processed response
        """
        return response
    
    async def dispatch(
        self,
        request,
        call_next
    ):
        """
        Process a request through the middleware.
        
        Args:
            request: The request to process
            call_next: The next middleware in the chain
            
        Returns:
            The response from the next middleware
        """
        # Record the cache request
        cache_key = self._generate_cache_key(request)
        
        # Start the timer for cache operations
        start_time = time.time()
        
        # Check if the response is cached
        cached_response = await self._get_from_cache(cache_key)
        
        # If we have a cached response, return it
        if cached_response is not None:
            # Record analytics for cache hit
            request_time = (time.time() - start_time) * 1000  # ms
            self.analytics.record_hit(request_time)
            
            return cached_response
        
        # Record analytics for cache miss
        miss_time = (time.time() - start_time) * 1000  # ms
        self.analytics.record_miss(miss_time)
        
        # Process the request normally
        response = await call_next(request)
        
        # Cache the response if it's cacheable
        if self._is_cacheable(request, response):
            await self._cache_response(cache_key, response)
        
        # Auto-tune cache parameters if needed
        if self.auto_tune and (time.time() - self.last_tune_time) > self.auto_tune_interval:
            await self._auto_tune()
            self.last_tune_time = time.time()
        
        return response
    
    def _generate_cache_key(self, request) -> str:
        """
        Generate a cache key for a request.
        
        Args:
            request: The request to generate a key for
            
        Returns:
            The cache key
        """
        # Get the URL path and query string
        path = request.url.path
        query = str(request.query_params)
        method = request.method
        
        # Generate a hash of the key components
        key_components = f"{method}:{path}:{query}"
        
        # Include headers that affect the response
        for header in ["Accept", "Accept-Encoding", "Accept-Language"]:
            if header in request.headers:
                key_components += f":{header}={request.headers[header]}"
        
        # Generate a hash of the key components
        import hashlib
        return hashlib.md5(key_components.encode()).hexdigest()
    
    async def _get_from_cache(self, cache_key: str):
        """
        Get a response from the cache.
        
        Args:
            cache_key: The cache key
            
        Returns:
            The cached response, or None if not found
        """
        try:
            # Get the cached response using the CacheMiddleware
            if hasattr(self.cache_middleware, "get_cached_response"):
                return await self.cache_middleware.get_cached_response(cache_key)
            
            # Fall back to direct cache access
            if hasattr(self.cache_backend, "get"):
                cached_data = self.cache_backend.get(cache_key)
                if cached_data:
                    from starlette.responses import JSONResponse
                    return JSONResponse(content=cached_data, headers={"X-Cache": "HIT"})
                
            return None
        except Exception as e:
            logger.error(f"Error getting response from cache: {e}")
            self.analytics.record_error()
            return None
    
    async def _cache_response(self, cache_key: str, response):
        """
        Cache a response.
        
        Args:
            cache_key: The cache key
            response: The response to cache
        """
        try:
            # Cache the response using the CacheMiddleware
            if hasattr(self.cache_middleware, "cache_response"):
                await self.cache_middleware.cache_response(cache_key, response, self.ttl)
                return
            
            # Fall back to direct cache access
            if hasattr(self.cache_backend, "set"):
                # Extract the response data
                if hasattr(response, "body"):
                    import json
                    try:
                        data = json.loads(response.body)
                        self.cache_backend.set(cache_key, data, self.ttl)
                    except:
                        logger.error("Error parsing response body as JSON")
        except Exception as e:
            logger.error(f"Error caching response: {e}")
            self.analytics.record_error()
    
    def _is_cacheable(self, request, response) -> bool:
        """
        Check if a response is cacheable.
        
        Args:
            request: The request
            response: The response
            
        Returns:
            True if the response is cacheable, False otherwise
        """
        # Check if the response is successful
        if response.status_code < 200 or response.status_code >= 400:
            return False
        
        # Check if the method is cacheable
        if request.method not in ["GET", "HEAD"]:
            return False
        
        # Check cache control headers
        cache_control = response.headers.get("Cache-Control", "")
        if "no-store" in cache_control or "no-cache" in cache_control:
            return False
        
        return True
    
    async def _auto_tune(self):
        """Auto-tune cache parameters based on analytics."""
        try:
            # Skip auto-tuning if we don't have enough data
            if self.analytics.request_count < 100:
                return
            
            # Get the current cache stats
            stats = self.get_stats()
            
            # Adjust TTL based on hit rate and request frequency
            hit_rate = stats.get("hit_rate", 0)
            avg_hit_latency = stats.get("avg_hit_latency_ms", 0)
            avg_miss_latency = stats.get("avg_miss_latency_ms", 0)
            
            new_ttl = self.ttl
            
            if hit_rate < 0.3:
                # Low hit rate, decrease TTL to refresh data more often
                new_ttl = max(10, int(self.ttl * 0.8))
            elif hit_rate > 0.7 and avg_hit_latency < avg_miss_latency * 0.1:
                # High hit rate and significant performance benefit, increase TTL
                new_ttl = min(3600, int(self.ttl * 1.2))
            
            # Apply the new TTL if it's different
            if new_ttl != self.ttl:
                self.ttl = new_ttl
                logger.info(f"Auto-tuned cache TTL to {new_ttl} seconds")
            
            # Save analytics if output directory is specified
            if self.output_dir:
                self.save_analytics()
        except Exception as e:
            logger.error(f"Error during cache auto-tuning: {e}")
    
    def get_analytics(self) -> CacheAnalytics:
        """
        Get cache analytics.
        
        Returns:
            The cache analytics
        """
        # Update the analytics with the current cache stats
        try:
            if hasattr(self.cache_backend, "get_stats"):
                backend_stats = self.cache_backend.get_stats()
                self.analytics.cache_size_bytes = backend_stats.get("total_size_bytes", 0)
                self.analytics.item_count = backend_stats.get("item_count", 0)
                if "large_keys" in backend_stats:
                    self.analytics.large_keys = backend_stats["large_keys"]
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
        
        return self.analytics
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            A dictionary of cache statistics
        """
        analytics = self.get_analytics()
        return analytics.to_dict()
    
    def save_analytics(self) -> Optional[str]:
        """
        Save cache analytics to a file.
        
        Returns:
            The path to the saved file, or None if saving failed
        """
        if not self.output_dir:
            return None
        
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = os.path.join(self.output_dir, f"cache_analytics_{timestamp}.json")
            
            with open(filename, "w") as f:
                json.dump(self.get_stats(), f, indent=2)
            
            return filename
        except Exception as e:
            logger.error(f"Error saving cache analytics: {e}")
            return None
    
    def clear_cache(self):
        """Clear the cache."""
        try:
            if hasattr(self.cache_backend, "clear"):
                self.cache_backend.clear()
            self.analytics.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}") 