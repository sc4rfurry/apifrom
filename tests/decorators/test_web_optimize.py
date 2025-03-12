"""
Tests for the WebOptimize decorator in the APIFromAnything library.

This module tests the functionality of the WebOptimize decorator, which combines
the Web decorator with performance optimization features.
"""
import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

try:
    from apifrom.decorators.web_optimize import WebOptimize
    from apifrom.core.app import APIApp
    from apifrom.core.request import Request
    from apifrom.core.response import Response
    from apifrom.performance.profiler import APIProfiler
    from apifrom.performance.cache_optimizer import CacheOptimizer
    from apifrom.performance.connection_pool import PoolManager, ConnectionPool
    LIBRARY_AVAILABLE = True
except ImportError:
    LIBRARY_AVAILABLE = False
    # Mock implementations for testing
    class WebOptimize:
        _profiler = MagicMock()
        _cache_optimizer = MagicMock()
        _pool_manager = MagicMock()
        
        @classmethod
        def get_profiler(cls):
            return cls._profiler
        
        @classmethod
        def get_cache_optimizer(cls):
            return cls._cache_optimizer
        
        @classmethod
        def get_pool_manager(cls):
            return cls._pool_manager
        
        @classmethod
        def get_performance_metrics(cls):
            return {
                "profiler": {
                    "uptime": 60,
                    "total_requests": 100,
                    "average_response_time": 50,
                    "requests_per_minute": 60,
                    "error_rate": 0.01,
                    "endpoint_stats": {}
                },
                "cache": {
                    "hit_rate": 0.8,
                    "hits": 80,
                    "misses": 20,
                    "size": 100
                },
                "connection_pools": {
                    "utilization": 0.5,
                    "pools": {
                        "database": {
                            "size": 10,
                            "active": 5,
                            "idle": 5
                        }
                    }
                }
            }
        
        @classmethod
        def create_pool(cls, name, min_size=5, max_size=20, validate_func=None):
            pool = MagicMock()
            pool.name = name
            pool.min_size = min_size
            pool.max_size = max_size
            pool.acquire = AsyncMock()
            cls._pool_manager.create_pool.return_value = pool
            return pool
        
        @classmethod
        def get_pool(cls, name):
            pool = MagicMock()
            pool.name = name
            cls._pool_manager.get_pool.return_value = pool
            return pool
        
        def __init__(
            self,
            title=None,
            description=None,
            theme="default",
            template=None,
            enable_profiling=False,
            enable_caching=False,
            cache_ttl=60,
            enable_connection_pooling=False,
            pool_name=None,
            enable_request_coalescing=False,
            coalesce_window_time=0.5,
            coalesce_max_requests=10,
            enable_batch_processing=False,
            batch_size=10,
            batch_wait_time=0.5
        ):
            self.title = title
            self.description = description
            self.theme = theme
            self.template = template
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
        
        def __call__(self, func):
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                
                # Check if we're in a request context
                request = kwargs.get('request')
                if not request:
                    # Not in a request context, return the raw result
                    return result
                
                # Check if the client accepts HTML
                accept_header = request.headers.get('Accept', '')
                if 'text/html' in accept_header:
                    # Render HTML
                    html = self._render_html(result)
                    return Response(
                        status_code=200,
                        body=html,
                        headers={"Content-Type": "text/html"}
                    )
                
                # Return JSON by default
                return Response(
                    status_code=200,
                    body=result,
                    headers={"Content-Type": "application/json"}
                )
            
            # Preserve the original function's metadata
            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper
        
        def _render_html(self, data):
            """Render the data as HTML."""
            # Simple HTML rendering for testing
            html = f"<!DOCTYPE html><html><head><title>{self.title or 'API Response'}</title></head>"
            html += f"<body><h1>{self.title or 'API Response'}</h1>"
            
            if self.description:
                html += f"<p>{self.description}</p>"
            
            html += f"<pre>{json.dumps(data, indent=2)}</pre>"
            html += "</body></html>"
            return html
    
    class APIApp:
        def __init__(self):
            self.routes = {}
            
        def api(self, route=None, methods=None):
            if methods is None:
                methods = ["GET"]
                
            def decorator(func):
                nonlocal route
                if route is None:
                    route = f"/{func.__name__}"
                self.routes[route] = {"handler": func, "methods": methods}
                return func
            return decorator
            
        def handle_request(self, request):
            if request.path in self.routes:
                handler = self.routes[request.path]["handler"]
                result = handler(request=request)
                if isinstance(result, Response):
                    return result
                return Response(status_code=200, body=result)
            return Response(status_code=404, body={"error": "Not found"})
    
    class Request:
        def __init__(self, method, path, query_params=None, headers=None, body=None, cookies=None):
            self.method = method
            self.path = path
            self.query_params = query_params or {}
            self.headers = headers or {}
            self.body = body
            self.cookies = cookies or {}
    
    class Response:
        def __init__(self, status_code, body=None, headers=None, cookies=None):
            self.status_code = status_code
            self.body = body
            self.headers = headers or {}
            self.cookies = cookies or {}
    
    class APIProfiler:
        def profile_endpoint(self, func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        
        def get_uptime(self):
            return 60
        
        def get_total_requests(self):
            return 100
        
        def get_average_response_time(self):
            return 50
        
        def get_requests_per_minute(self):
            return 60
        
        def get_error_rate(self):
            return 0.01
        
        def get_endpoint_stats(self):
            return {}
    
    class CacheOptimizer:
        def optimize(self, ttl=60):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)
                return wrapper
            return decorator
        
        def get_stats(self):
            return {
                "hit_rate": 0.8,
                "hits": 80,
                "misses": 20,
                "size": 100
            }
    
    class PoolManager:
        def __init__(self):
            self.pools = {}
        
        def create_pool(self, name, min_size=5, max_size=20, validate_func=None):
            pool = ConnectionPool(name, min_size, max_size, validate_func)
            self.pools[name] = pool
            return pool
        
        def get_pool(self, name):
            return self.pools.get(name)
        
        def get_stats(self):
            return {
                "utilization": 0.5,
                "pools": {
                    "database": {
                        "size": 10,
                        "active": 5,
                        "idle": 5
                    }
                }
            }
    
    class ConnectionPool:
        def __init__(self, name, min_size=5, max_size=20, validate_func=None):
            self.name = name
            self.min_size = min_size
            self.max_size = max_size
            self.validate_func = validate_func
            self.connections = []
        
        async def acquire(self):
            class ConnectionContext:
                async def __aenter__(self):
                    return MagicMock()
                
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            
            return ConnectionContext()


@pytest.mark.skipif(not LIBRARY_AVAILABLE, reason="APIFromAnything library not available")
class TestWebOptimizeDecorator:
    """Tests for the WebOptimize decorator."""
    
    def test_web_optimize_initialization(self):
        """Test that the WebOptimize decorator can be initialized with various parameters."""
        # Default initialization
        web_optimize = WebOptimize()
        assert web_optimize.title is None
        assert web_optimize.description is None
        assert web_optimize.theme == "default"
        assert web_optimize.template is None
        assert web_optimize.enable_profiling is False
        assert web_optimize.enable_caching is False
        assert web_optimize.cache_ttl == 60
        assert web_optimize.enable_connection_pooling is False
        assert web_optimize.pool_name is None
        assert web_optimize.enable_request_coalescing is False
        assert web_optimize.coalesce_window_time == 0.5
        assert web_optimize.coalesce_max_requests == 10
        assert web_optimize.enable_batch_processing is False
        assert web_optimize.batch_size == 10
        assert web_optimize.batch_wait_time == 0.5
        
        # Custom initialization
        web_optimize = WebOptimize(
            title="Test API",
            description="A test API endpoint",
            theme="dark",
            template="custom.html",
            enable_profiling=True,
            enable_caching=True,
            cache_ttl=120,
            enable_connection_pooling=True,
            pool_name="database",
            enable_request_coalescing=True,
            coalesce_window_time=1.0,
            coalesce_max_requests=20,
            enable_batch_processing=True,
            batch_size=5,
            batch_wait_time=0.2
        )
        assert web_optimize.title == "Test API"
        assert web_optimize.description == "A test API endpoint"
        assert web_optimize.theme == "dark"
        assert web_optimize.template == "custom.html"
        assert web_optimize.enable_profiling is True
        assert web_optimize.enable_caching is True
        assert web_optimize.cache_ttl == 120
        assert web_optimize.enable_connection_pooling is True
        assert web_optimize.pool_name == "database"
        assert web_optimize.enable_request_coalescing is True
        assert web_optimize.coalesce_window_time == 1.0
        assert web_optimize.coalesce_max_requests == 20
        assert web_optimize.enable_batch_processing is True
        assert web_optimize.batch_size == 5
        assert web_optimize.batch_wait_time == 0.2
    
    def test_web_optimize_json_response(self):
        """Test that the WebOptimize decorator returns JSON when Accept header is not HTML."""
        @WebOptimize(
            title="Test API",
            enable_profiling=True,
            enable_caching=True
        )
        def test_endpoint(request):
            return {"message": "Hello, World!"}
        
        # Create a request with Accept: application/json
        request = Request(
            method="GET",
            path="/test",
            headers={"Accept": "application/json"}
        )
        
        # Call the decorated function
        response = test_endpoint(request=request)
        
        # Check that we got a JSON response
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/json"
        assert response.body == {"message": "Hello, World!"}
    
    def test_web_optimize_html_response(self):
        """Test that the WebOptimize decorator returns HTML when Accept header includes text/html."""
        @WebOptimize(
            title="Test API",
            description="A test API endpoint",
            enable_profiling=True,
            enable_caching=True
        )
        def test_endpoint(request):
            return {"message": "Hello, World!"}
        
        # Create a request with Accept: text/html
        request = Request(
            method="GET",
            path="/test",
            headers={"Accept": "text/html"}
        )
        
        # Call the decorated function
        response = test_endpoint(request=request)
        
        # Check that we got an HTML response
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "text/html"
        assert isinstance(response.body, str)
        assert "<!DOCTYPE html>" in response.body
        assert "<title>Test API</title>" in response.body
        assert "A test API endpoint" in response.body
        assert "Hello, World!" in response.body
    
    def test_web_optimize_integration_with_app(self):
        """Test that the WebOptimize decorator works with an APIApp."""
        app = APIApp()
        
        @app.api("/web-optimize-test")
        @WebOptimize(
            title="Web Optimize Test",
            enable_profiling=True,
            enable_caching=True
        )
        def web_optimize_test(request):
            return {"message": "Hello from Web Optimize API!"}
        
        # Create a request with Accept: text/html
        request = Request(
            method="GET",
            path="/web-optimize-test",
            headers={"Accept": "text/html"}
        )
        
        # Handle the request
        response = app.handle_request(request)
        
        # Check that we got an HTML response
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "text/html"
        assert "<!DOCTYPE html>" in response.body
        assert "<title>Web Optimize Test</title>" in response.body
        assert "Hello from Web Optimize API!" in response.body
        
        # Create a request with Accept: application/json
        request = Request(
            method="GET",
            path="/web-optimize-test",
            headers={"Accept": "application/json"}
        )
        
        # Handle the request
        response = app.handle_request(request)
        
        # Check that we got a JSON response
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/json"
        assert response.body == {"message": "Hello from Web Optimize API!"}
    
    def test_web_optimize_class_methods(self):
        """Test the class methods of the WebOptimize decorator."""
        # Test get_profiler
        profiler = WebOptimize.get_profiler()
        assert isinstance(profiler, APIProfiler)
        
        # Test get_cache_optimizer
        cache_optimizer = WebOptimize.get_cache_optimizer()
        assert isinstance(cache_optimizer, CacheOptimizer)
        
        # Test get_pool_manager
        pool_manager = WebOptimize.get_pool_manager()
        assert isinstance(pool_manager, PoolManager)
        
        # Test create_pool
        pool = WebOptimize.create_pool("test_pool", min_size=10, max_size=30)
        assert pool.name == "test_pool"
        assert pool.min_size == 10
        assert pool.max_size == 30
        
        # Test get_pool
        pool = WebOptimize.get_pool("test_pool")
        assert pool is not None
        assert pool.name == "test_pool"
        
        # Test get_performance_metrics
        metrics = WebOptimize.get_performance_metrics()
        assert "profiler" in metrics
        assert "cache" in metrics
        assert "connection_pools" in metrics
        assert "uptime" in metrics["profiler"]
        assert "total_requests" in metrics["profiler"]
        assert "average_response_time" in metrics["profiler"]
        assert "requests_per_minute" in metrics["profiler"]
        assert "error_rate" in metrics["profiler"]
        assert "hit_rate" in metrics["cache"]
        assert "utilization" in metrics["connection_pools"]
    
    @pytest.mark.asyncio
    async def test_web_optimize_with_connection_pool(self):
        """Test that the WebOptimize decorator works with connection pooling."""
        # Create a connection pool
        pool = WebOptimize.create_pool("test_db", min_size=5, max_size=20)
        
        @WebOptimize(
            title="Database API",
            enable_profiling=True,
            enable_connection_pooling=True,
            pool_name="test_db"
        )
        async def get_data(request):
            async with pool.acquire() as connection:
                # Simulate a database query
                await asyncio.sleep(0.01)
                return {"data": "test data"}
        
        # Create a request
        request = Request(
            method="GET",
            path="/data",
            headers={"Accept": "application/json"}
        )
        
        # Call the decorated function
        response = await get_data(request=request)
        
        # Check the response
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.body == {"data": "test data"}
    
    def test_web_optimize_optimize_class_method(self):
        """Test the optimize class method of the WebOptimize decorator."""
        # Create a decorator using the optimize class method
        decorator = WebOptimize.optimize(
            title="Optimized API",
            description="An optimized API endpoint",
            theme="dark",
            enable_profiling=True,
            enable_caching=True,
            cache_ttl=120
        )
        
        # Apply the decorator to a function
        @decorator
        def test_function(request):
            return {"message": "Hello, World!"}
        
        # Create a request
        request = Request(
            method="GET",
            path="/test",
            headers={"Accept": "application/json"}
        )
        
        # Call the decorated function
        response = test_function(request=request)
        
        # Check the response
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.body == {"message": "Hello, World!"} 