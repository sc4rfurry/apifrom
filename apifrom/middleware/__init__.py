"""
Middleware for APIFromAnything.

This module provides middleware for common tasks such as CORS, caching, rate limiting,
security headers, authentication, and more.
"""

from apifrom.middleware.base import Middleware, BaseMiddleware
from apifrom.middleware.cors import CORSMiddleware
from apifrom.middleware.rate_limit import RateLimitMiddleware, RateLimitBackend, InMemoryRateLimitBackend
from apifrom.middleware.cache import CacheMiddleware
from apifrom.middleware.cache_advanced import (
    AdvancedCacheMiddleware,
    MemoryCacheBackend,
    RedisCacheBackend,
    CacheBackend,
    LRUEvictionPolicy,
    LFUEvictionPolicy,
    TTLEvictionPolicy,
    SizeEvictionPolicy,
    HybridEvictionPolicy,
    TagBasedInvalidation,
    DependencyBasedInvalidation,
    CacheControl
)
from apifrom.middleware.error_handling import (
    ErrorHandlingMiddleware,
    APIError,
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    MethodNotAllowedError,
    ConflictError,
    UnprocessableEntityError,
    TooManyRequestsError,
    InternalServerError,
    ServiceUnavailableError
)

__all__ = [
    "Middleware",
    "BaseMiddleware",
    "CORSMiddleware",
    "RateLimitMiddleware",
    "RateLimitBackend",
    "InMemoryRateLimitBackend",
    "CacheMiddleware",
    "AdvancedCacheMiddleware",
    "MemoryCacheBackend",
    "RedisCacheBackend",
    "CacheBackend",
    "LRUEvictionPolicy",
    "LFUEvictionPolicy",
    "TTLEvictionPolicy",
    "SizeEvictionPolicy",
    "HybridEvictionPolicy",
    "TagBasedInvalidation",
    "DependencyBasedInvalidation",
    "CacheControl",
    # Error handling middleware
    "ErrorHandlingMiddleware",
    "APIError",
    "BadRequestError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "MethodNotAllowedError",
    "ConflictError",
    "UnprocessableEntityError",
    "TooManyRequestsError",
    "InternalServerError",
    "ServiceUnavailableError",
] 