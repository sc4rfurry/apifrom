"""
APIFromAnything - Transform any Python function into a REST API endpoint.

This library allows developers to expose ordinary Python functions as API endpoints
with minimal boilerplate, automatically handling routing, input validation,
output serialization, error handling, and documentation generation.
"""

__version__ = "1.0.0"

from apifrom.core.app import API
from apifrom.decorators.api import api
from apifrom.middleware.base import Middleware
from apifrom.security.auth import jwt_required, api_key_required, basic_auth_required, oauth2_required
from apifrom.monitoring import MetricsCollector, MetricsMiddleware, PrometheusExporter, JSONExporter, LogExporter

# Import advanced caching components
from apifrom.middleware.cache_advanced import (
    AdvancedCacheMiddleware,
    CacheBackend,
    MemoryCacheBackend,
    RedisCacheBackend,
    LRUEvictionPolicy,
    LFUEvictionPolicy,
    TTLEvictionPolicy,
    SizeEvictionPolicy,
    HybridEvictionPolicy
)

# Import performance optimization components
from apifrom.performance.optimization import (
    OptimizationConfig,
    OptimizationLevel,
    OptimizationRecommendation,
    OptimizationAnalyzer,
    Web
)
from apifrom.performance.profiler import APIProfiler, ProfileMiddleware, ProfileReport
from apifrom.performance.cache_optimizer import CacheOptimizer, OptimizedCacheMiddleware, CacheAnalytics
from apifrom.performance.connection_pool import ConnectionPool, ConnectionPoolMiddleware, PoolManager
from apifrom.performance.request_coalescing import RequestCoalescingMiddleware, coalesce_requests
from apifrom.performance.batch_processing import BatchProcessor, batch_process

# Import adapters for serverless platforms
try:
    from apifrom.adapters.aws_lambda import LambdaAdapter
except ImportError:
    pass

try:
    from apifrom.adapters.gcp_functions import CloudFunctionAdapter
except ImportError:
    pass

try:
    from apifrom.adapters.azure_functions import AzureFunctionAdapter
except ImportError:
    pass

try:
    from apifrom.adapters.vercel import VercelAdapter
except ImportError:
    pass

try:
    from apifrom.adapters.netlify import NetlifyAdapter
except ImportError:
    pass

__all__ = [
    "API",
    "api",
    "Middleware",
    "jwt_required",
    "api_key_required",
    "basic_auth_required",
    "oauth2_required",
    "MetricsCollector",
    "MetricsMiddleware",
    "PrometheusExporter",
    "JSONExporter",
    "LogExporter",
    # Serverless adapters
    "LambdaAdapter",
    "CloudFunctionAdapter",
    "AzureFunctionAdapter",
    "VercelAdapter",
    "NetlifyAdapter",
    # Advanced caching components
    "AdvancedCacheMiddleware",
    "CacheBackend",
    "MemoryCacheBackend",
    "RedisCacheBackend",
    "LRUEvictionPolicy",
    "LFUEvictionPolicy",
    "TTLEvictionPolicy",
    "SizeEvictionPolicy",
    "HybridEvictionPolicy",
    # Performance optimization components
    "Web",
    "OptimizationConfig",
    "OptimizationLevel",
    "OptimizationRecommendation",
    "OptimizationAnalyzer",
    "APIProfiler",
    "ProfileMiddleware",
    "ProfileReport",
    "CacheOptimizer",
    "OptimizedCacheMiddleware",
    "CacheAnalytics",
    "ConnectionPool",
    "ConnectionPoolMiddleware",
    "PoolManager",
    "RequestCoalescingMiddleware",
    "coalesce_requests",
    "BatchProcessor",
    "batch_process"
] 