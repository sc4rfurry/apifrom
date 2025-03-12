"""
Performance optimization modules for APIFromAnything.

This module provides tools for optimizing APIFromAnything applications for high-load
scenarios, including performance monitoring, profiling, and optimization.
"""

# Profiler
from apifrom.performance.profiler import APIProfiler, ProfileMiddleware, ProfileReport

# Cache optimization
from apifrom.performance.cache_optimizer import (
    CacheOptimizer,
    OptimizedCacheStrategy,
    OptimizedCacheMiddleware,
    CacheAnalytics
)

# Connection pooling
from apifrom.performance.connection_pool import (
    ConnectionPool,
    PoolManager,
    ConnectionPoolMiddleware,
    ConnectionPoolMetrics,
    ConnectionPoolSettings
)

# Request coalescing
from apifrom.performance.request_coalescing import (
    RequestCoalescingManager,
    RequestCoalescingMiddleware,
    coalesce_requests,
    CoalescedRequest
)

# Batch processing
from apifrom.performance.batch_processing import (
    BatchCollector,
    BatchExecutor,
    BatchProcessor,
    batch_process
)

# General optimization
from apifrom.performance.optimization import (
    OptimizationConfig,
    OptimizationLevel,
    OptimizationRecommendation,
    OptimizationAnalyzer,
    Web
)


__all__ = [
    # Profiler
    "APIProfiler",
    "ProfileMiddleware",
    "ProfileReport",
    
    # Cache optimization
    "CacheOptimizer",
    "OptimizedCacheStrategy",
    "OptimizedCacheMiddleware",
    "CacheAnalytics",
    
    # Connection pooling
    "ConnectionPool",
    "PoolManager",
    "ConnectionPoolMiddleware",
    "ConnectionPoolMetrics",
    "ConnectionPoolSettings",
    
    # Request coalescing
    "RequestCoalescingManager",
    "RequestCoalescingMiddleware",
    "coalesce_requests",
    "CoalescedRequest",
    
    # Batch processing
    "BatchCollector",
    "BatchExecutor",
    "BatchProcessor",
    "batch_process",
    
    # General optimization
    "OptimizationConfig",
    "OptimizationLevel",
    "OptimizationRecommendation",
    "OptimizationAnalyzer",
    "Web"
] 