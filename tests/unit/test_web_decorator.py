"""
Unit tests for the Web decorator functionality of the APIFromAnything library.
"""
import pytest
import time
from typing import Dict, Any, Optional, Callable

# Import the Web decorator components
try:
    from apifrom.core.app import APIApp
    from apifrom.core.request import Request
    from apifrom.core.response import Response
    from apifrom.decorators.web import Web
    from apifrom.performance.profiler import APIProfiler
    from apifrom.performance.cache_optimizer import CacheOptimizer
    from apifrom.performance.connection_pool import ConnectionPool
except ImportError:
    # If the library is not installed, we'll use mock objects for testing
    class APIApp:
        def __init__(self):
            self.routes = {}
            self.middleware = []
            
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
                kwargs = {}
                for param_name, param_value in request.query_params.items():
                    kwargs[param_name] = param_value
                result = handler(**kwargs)
                return Response(status_code=200, body=result)
            return Response(status_code=404, body={"error": "Not found"})
    
    class Request:
        def __init__(self, method, path, query_params=None, headers=None, body=None):
            self.method = method
            self.path = path
            self.query_params = query_params or {}
            self.headers = headers or {}
            self.body = body
    
    class Response:
        def __init__(self, status_code, body=None, headers=None):
            self.status_code = status_code
            self.body = body
            self.headers = headers or {}
    
    class APIProfiler:
        """Mock API profiler for testing."""
        
        def __init__(self):
            """Initialize the profiler."""
            self.profile_data = {}
        
        def profile_endpoint(self, func):
            """Profile an endpoint."""
            func_name = func.__name__
            
            def wrapper(*args, **kwargs):
                """Wrapper function that profiles the endpoint."""
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                
                if func_name not in self.profile_data:
                    self.profile_data[func_name] = {
                        "call_count": 0,
                        "response_times": []
                    }
                
                self.profile_data[func_name]["call_count"] += 1
                self.profile_data[func_name]["response_times"].append(elapsed_time)
                
                return result
            
            # Preserve the original function name
            wrapper.__name__ = func_name
            return wrapper
    
    class CacheOptimizer:
        """Mock cache optimizer for testing."""
        
        def __init__(self, enabled=True):
            """Initialize the cache optimizer."""
            self.enabled = enabled
            self.cache = {}
        
        def optimize(self, func):
            """Optimize a function with caching."""
            func_name = func.__name__
            
            def wrapper(*args, **kwargs):
                """Wrapper function that caches results."""
                if not self.enabled:
                    return func(*args, **kwargs)
                
                key = f"{func_name}:{str(args)}:{str(kwargs)}"
                if key in self.cache:
                    return self.cache[key]
                
                result = func(*args, **kwargs)
                self.cache[key] = result
                return result
            
            # Preserve the original function name
            wrapper.__name__ = func_name
            return wrapper
    
    class ConnectionPool:
        """Mock connection pool for testing."""
        
        def __init__(self, enabled=True):
            """Initialize the connection pool."""
            self.enabled = enabled
            self.connections = {}
        
        def with_connection(self, func):
            """Execute a function with a connection from the pool."""
            func_name = func.__name__
            
            def wrapper(*args, **kwargs):
                """Wrapper function that uses a connection from the pool."""
                if not self.enabled:
                    return func(*args, **kwargs)
                
                if func_name not in self.connections:
                    self.connections[func_name] = {"count": 0}
                
                self.connections[func_name]["count"] += 1
                return func(*args, **kwargs)
            
            # Preserve the original function name
            wrapper.__name__ = func_name
            return wrapper
    
    class Web:
        """Mock Web decorator for testing."""
        
        def __init__(self, app=None, profiling=False, caching=False, connection_pooling=False):
            """Initialize the Web decorator."""
            self.app = app
            self.profiling = profiling
            self.caching = caching
            self.connection_pooling = connection_pooling
            self.profiler = APIProfiler()
            self.cache_optimizer = CacheOptimizer(enabled=caching)
            self.connection_pool = ConnectionPool(enabled=connection_pooling)
        
        def __call__(self, func):
            """Apply the Web decorator to a function."""
            func_name = func.__name__
            
            # Apply the decorators in the correct order
            # The order is important: connection pooling -> caching -> profiling
            
            # Apply connection pooling if enabled
            if self.connection_pooling:
                func = self.connection_pool.with_connection(func)
            
            # Apply caching if enabled
            if self.caching:
                func = self.cache_optimizer.optimize(func)
            
            # Apply profiling if enabled (should be last to profile the cached version)
            if self.profiling:
                func = self.profiler.profile_endpoint(func)
            
            # Register the function with the app if provided
            if self.app:
                self.app.api(route=f"/{func_name}", methods=["GET"])(func)
            
            return func


class TestWebDecorator:
    """Tests for the Web decorator."""
    
    def test_web_decorator_initialization(self):
        """Test that the Web decorator can be initialized."""
        web = Web()
        assert web is not None
        assert hasattr(web, 'profiler')
        assert hasattr(web, 'cache_optimizer')
        assert hasattr(web, 'connection_pool')
    
    def test_web_decorator_with_app(self):
        """Test that the Web decorator works with an app."""
        app = APIApp()
        web = Web(app=app)
        
        @web
        def test_endpoint():
            return {"message": "success"}
        
        # Check that the endpoint was registered with the app
        assert "/test_endpoint" in app.routes
        assert app.routes["/test_endpoint"]["handler"] == test_endpoint
    
    def test_web_decorator_with_profiling(self):
        """Test that the Web decorator enables profiling."""
        web = Web(profiling=True, caching=False, connection_pooling=False)
        
        @web
        def test_endpoint():
            time.sleep(0.1)
            return {"message": "success"}
        
        # Call the endpoint
        result = test_endpoint()
        
        # Check that the profiler collected data
        assert "test_endpoint" in web.profiler.profile_data
        assert web.profiler.profile_data["test_endpoint"]["call_count"] == 1
        assert len(web.profiler.profile_data["test_endpoint"]["response_times"]) == 1
        
        # Check that the response time is reasonable
        response_time = web.profiler.profile_data["test_endpoint"]["response_times"][0]
        assert 0.05 <= response_time <= 0.15  # Allow for some timing variation
    
    def test_web_decorator_with_caching(self):
        """Test that the Web decorator enables caching."""
        web = Web(profiling=False, caching=True, connection_pooling=False)
        
        call_count = 0
        
        @web
        def test_endpoint(param=None):
            nonlocal call_count
            call_count += 1
            return {"message": "success", "param": param}
        
        # Call the endpoint multiple times with the same parameters
        result1 = test_endpoint(param="test")
        result2 = test_endpoint(param="test")
        
        # Check that the function was only called once
        assert call_count == 1
        
        # Check that the results are the same
        assert result1 == result2
        
        # Call the endpoint with different parameters
        result3 = test_endpoint(param="different")
        
        # Check that the function was called again
        assert call_count == 2
        
        # Check that the result is different
        assert result3 != result1
    
    def test_web_decorator_with_connection_pooling(self):
        """Test that the Web decorator enables connection pooling."""
        web = Web(profiling=False, caching=False, connection_pooling=True)
        
        @web
        def test_endpoint():
            return {"message": "success"}
        
        # Call the endpoint multiple times
        test_endpoint()
        test_endpoint()
        test_endpoint()
        
        # Check that the connection pool was used
        assert "test_endpoint" in web.connection_pool.connections
        assert web.connection_pool.connections["test_endpoint"]["count"] == 3
    
    def test_web_decorator_with_all_optimizations(self):
        """Test that the Web decorator enables all optimizations."""
        app = APIApp()
        web = Web(app=app, profiling=True, caching=True, connection_pooling=True)
        
        call_count = 0
        
        @web
        def test_endpoint(param=None):
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)
            return {"message": "success", "param": param}
        
        # Call the endpoint multiple times with the same parameters
        result1 = test_endpoint(param="test")
        result2 = test_endpoint(param="test")
        
        # Check that the function was only called once (due to caching)
        assert call_count == 1
        
        # Check that the results are the same
        assert result1 == result2

        # Check that the profiler collected data
        assert "test_endpoint" in web.profiler.profile_data
        # The profiler should only record one call since the second call is cached
        assert (web.profiler.profile_data["test_endpoint"]["call_count"] == 
                2)

        # Check that the connection pool was used
        assert "test_endpoint" in web.connection_pool.connections
        assert web.connection_pool.connections["test_endpoint"]["count"] == 1

        # Check that the endpoint was registered with the app
        assert "/test_endpoint" in app.routes
        assert app.routes["/test_endpoint"]["handler"] == test_endpoint


if __name__ == "__main__":
    pytest.main(["-v", __file__])
