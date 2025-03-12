"""
Monitoring module for APIFromAnything.

This module provides functionality for monitoring the application using Prometheus.
It includes metrics for request counts, request duration, and error counts.
"""

import time
from typing import Callable, Dict, Optional, Union

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Gauge, Histogram, Summary
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry, multiprocess
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Route
from starlette.types import ASGIApp, Receive, Scope, Send

# Create a registry for metrics
try:
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
except (ImportError, ValueError):
    # Fallback to default registry if not in multiprocess mode
    registry = None

# Define metrics
REQUEST_COUNT = Counter(
    'apifrom_request_count',
    'Count of requests received',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

REQUEST_LATENCY = Histogram(
    'apifrom_request_latency_seconds',
    'Histogram of request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
    registry=registry
)

REQUESTS_IN_PROGRESS = Gauge(
    'apifrom_requests_in_progress',
    'Gauge of requests currently being processed',
    ['method', 'endpoint'],
    registry=registry
)

ERROR_COUNT = Counter(
    'apifrom_error_count',
    'Count of errors occurred',
    ['method', 'endpoint', 'exception_type'],
    registry=registry
)

SYSTEM_INFO = Gauge(
    'apifrom_system_info',
    'System information',
    ['version', 'python_version'],
    registry=registry
)

DB_QUERY_LATENCY = Histogram(
    'apifrom_db_query_latency_seconds',
    'Histogram of database query latency in seconds',
    ['operation', 'table'],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0],
    registry=registry
)

CACHE_HIT_COUNT = Counter(
    'apifrom_cache_hit_count',
    'Count of cache hits',
    ['cache_name'],
    registry=registry
)

CACHE_MISS_COUNT = Counter(
    'apifrom_cache_miss_count',
    'Count of cache misses',
    ['cache_name'],
    registry=registry
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and collect metrics.

        Args:
            request: The incoming request.
            call_next: The next middleware or endpoint to call.

        Returns:
            The response from the next middleware or endpoint.
        """
        method = request.method
        path = request.url.path
        
        # Skip metrics endpoint to avoid recursion
        if path == "/metrics":
            return await call_next(request)
        
        # Use the route path if available for better grouping
        route_path = path
        for route in request.app.routes:
            if isinstance(route, Route) and route.path_regex.match(path):
                route_path = route.path
                break
        
        REQUESTS_IN_PROGRESS.labels(method=method, endpoint=route_path).inc()
        
        start_time = time.time()
        status_code = 500  # Default if something goes wrong
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            ERROR_COUNT.labels(
                method=method,
                endpoint=route_path,
                exception_type=type(e).__name__
            ).inc()
            raise
        finally:
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=route_path
            ).observe(time.time() - start_time)
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=route_path,
                status_code=status_code
            ).inc()
            
            REQUESTS_IN_PROGRESS.labels(
                method=method,
                endpoint=route_path
            ).dec()


async def metrics_endpoint(request: Request) -> Response:
    """
    Endpoint for exposing Prometheus metrics.

    Args:
        request: The incoming request.

    Returns:
        Response with Prometheus metrics.
    """
    return Response(
        content=generate_latest(registry or None),
        media_type=CONTENT_TYPE_LATEST
    )


def setup_monitoring(app: FastAPI, system_info: Dict[str, str]) -> None:
    """
    Set up monitoring for the application.

    Args:
        app: The FastAPI application.
        system_info: Dictionary containing system information.
    """
    # Add middleware for collecting metrics
    app.add_middleware(PrometheusMiddleware)
    
    # Add endpoint for exposing metrics
    app.add_route("/metrics", metrics_endpoint)
    
    # Set system info
    for key, value in system_info.items():
        SYSTEM_INFO.labels(
            version=system_info.get('version', 'unknown'),
            python_version=system_info.get('python_version', 'unknown')
        ).set(1)


class DatabaseMetrics:
    """Helper class for tracking database metrics."""
    
    @staticmethod
    def track_query_time(operation: str, table: str) -> 'QueryTimer':
        """
        Create a context manager for tracking database query time.

        Args:
            operation: The database operation (e.g., "select", "insert").
            table: The database table being queried.

        Returns:
            A context manager for tracking query time.
        """
        return QueryTimer(operation, table)


class QueryTimer:
    """Context manager for tracking database query time."""
    
    def __init__(self, operation: str, table: str):
        """
        Initialize the query timer.

        Args:
            operation: The database operation.
            table: The database table.
        """
        self.operation = operation
        self.table = table
        self.start_time = None
    
    async def __aenter__(self):
        """Start timing when entering the context."""
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Record the query time when exiting the context."""
        if self.start_time is not None:
            DB_QUERY_LATENCY.labels(
                operation=self.operation,
                table=self.table
            ).observe(time.time() - self.start_time)


class CacheMetrics:
    """Helper class for tracking cache metrics."""
    
    @staticmethod
    def record_hit(cache_name: str) -> None:
        """
        Record a cache hit.

        Args:
            cache_name: The name of the cache.
        """
        CACHE_HIT_COUNT.labels(cache_name=cache_name).inc()
    
    @staticmethod
    def record_miss(cache_name: str) -> None:
        """
        Record a cache miss.

        Args:
            cache_name: The name of the cache.
        """
        CACHE_MISS_COUNT.labels(cache_name=cache_name).inc() 