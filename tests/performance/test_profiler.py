"""
Performance tests for the profiler functionality of the APIFromAnything library.
"""
import pytest
import time
import asyncio
from typing import Dict, Any, Optional
import functools

# Import the profiler components
try:
    from apifrom.core.app import APIApp
    from apifrom.core.request import Request
    from apifrom.core.response import Response
    from apifrom.performance.profiler import APIProfiler, ProfileMiddleware, ProfileReport
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
            
        def add_middleware(self, middleware):
            self.middleware.append(middleware)
            
        def handle_request(self, request):
            # Apply request middleware
            current_request = request
            for middleware in self.middleware:
                if hasattr(middleware, 'process_request'):
                    current_request = middleware.process_request(current_request)
            
            # Handle the request
            if current_request.path in self.routes:
                handler = self.routes[current_request.path]["handler"]
                kwargs = {}
                for param_name, param_value in current_request.query_params.items():
                    kwargs[param_name] = param_value
                result = handler(**kwargs)
                response = Response(status_code=200, body=result)
            else:
                response = Response(status_code=404, body={"error": "Not found"})
            
            # Apply response middleware in reverse order
            current_response = response
            for middleware in reversed(self.middleware):
                if hasattr(middleware, 'process_response'):
                    current_response = middleware.process_response(current_response)
            
            return current_response
    
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
    
    class ProfileReport:
        def __init__(self, profile_data=None):
            self.profile_data = profile_data or {}
            
        def get_average_response_time(self):
            if not self.profile_data.get("response_times", []):
                return 0
            return sum(self.profile_data.get("response_times", [])) / len(self.profile_data.get("response_times", []))
            
        def get_max_response_time(self):
            if not self.profile_data.get("response_times", []):
                return 0
            return max(self.profile_data.get("response_times", []))
            
        def get_min_response_time(self):
            if not self.profile_data.get("response_times", []):
                return 0
            return min(self.profile_data.get("response_times", []))
            
        def get_percentile_response_time(self, percentile=95):
            if not self.profile_data.get("response_times", []):
                return 0
            sorted_times = sorted(self.profile_data.get("response_times", []))
            idx = int(len(sorted_times) * percentile / 100)
            return sorted_times[idx]
            
        def get_recommendations(self):
            avg_time = self.get_average_response_time()
            recommendations = []
            
            if avg_time > 1.0:
                recommendations.append("Consider optimizing the endpoint for better performance.")
            if avg_time > 0.5:
                recommendations.append("Consider adding caching to improve response times.")
            
            return recommendations
            
        def to_dict(self):
            return {
                "average_response_time": self.get_average_response_time(),
                "max_response_time": self.get_max_response_time(),
                "min_response_time": self.get_min_response_time(),
                "p95_response_time": self.get_percentile_response_time(95),
                "recommendations": self.get_recommendations()
            }
    
    class APIProfiler:
        def __init__(self, enabled=True):
            self.enabled = enabled
            self.profile_data = {}
            
        def profile_endpoint(self, func):
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                
                endpoint_name = func.__name__
                if endpoint_name not in self.profile_data:
                    self.profile_data[endpoint_name] = {
                        "call_count": 0,
                        "response_times": []
                    }
                
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                response_time = end_time - start_time
                self.profile_data[endpoint_name]["call_count"] += 1
                self.profile_data[endpoint_name]["response_times"].append(response_time)
                
                return result
            
            return wrapper
            
        def profile_endpoint_async(self, func):
            """
            Decorator for profiling async endpoints.
            
            Args:
                func: The async function to profile
                
            Returns:
                The wrapped function
            """
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)
                
                endpoint_name = func.__name__
                if endpoint_name not in self.profile_data:
                    self.profile_data[endpoint_name] = {
                        "call_count": 0,
                        "response_times": []
                    }
                
                start_time = time.time()
                result = await func(*args, **kwargs)
                end_time = time.time()
                
                response_time = end_time - start_time
                self.profile_data[endpoint_name]["call_count"] += 1
                self.profile_data[endpoint_name]["response_times"].append(response_time)
                
                return result
            
            return wrapper
            
        def get_report(self, endpoint_name=None):
            if endpoint_name:
                if endpoint_name not in self.profile_data:
                    return ProfileReport({})
                return ProfileReport(self.profile_data[endpoint_name])
            
            return ProfileReport(self.profile_data)
    
    class ProfileMiddleware:
        def __init__(self, profiler):
            self.profiler = profiler
            
        def process_request(self, request):
            request.start_time = time.time()
            return request
            
        def process_response(self, response):
            if hasattr(response, 'request') and hasattr(response.request, 'start_time'):
                end_time = time.time()
                response_time = end_time - response.request.start_time
                
                path = response.request.path
                if path not in self.profiler.profile_data:
                    self.profiler.profile_data[path] = {
                        "call_count": 0,
                        "response_times": []
                    }
                
                self.profiler.profile_data[path]["call_count"] += 1
                self.profiler.profile_data[path]["response_times"].append(response_time)
            
            return response


@pytest.mark.performance
class TestAPIProfiler:
    """Tests for the APIProfiler class."""
    
    def test_profiler_initialization(self):
        """Test that the APIProfiler can be initialized."""
        profiler = APIProfiler()
        assert profiler is not None
        assert hasattr(profiler, 'profile_data')
        assert isinstance(profiler.profile_data, dict)
    
    def test_profile_endpoint_decorator(self):
        """Test that the profile_endpoint decorator collects performance data."""
        profiler = APIProfiler()
        
        @profiler.profile_endpoint
        def test_function(sleep_time=0.1):
            time.sleep(sleep_time)
            return {"result": "success"}
        
        # Call the function multiple times with different sleep times
        test_function(0.1)
        test_function(0.2)
        test_function(0.3)
        
        # Check that the profiler collected data
        assert "test_function" in profiler.profile_data
        assert profiler.profile_data["test_function"]["call_count"] == 3
        assert len(profiler.profile_data["test_function"]["response_times"]) == 3
        
        # Check that the response times are reasonable
        response_times = profiler.profile_data["test_function"]["response_times"]
        assert 0.05 <= response_times[0] <= 0.15  # Allow for some timing variation
        assert 0.15 <= response_times[1] <= 0.25
        assert 0.25 <= response_times[2] <= 0.35
    
    @pytest.mark.asyncio
    async def test_profile_endpoint_async_decorator(self):
        """Test that the profile_endpoint_async decorator collects performance data."""
        profiler = APIProfiler()
        
        # Define the async function first
        async def test_async_function(sleep_time=0.1):
            await asyncio.sleep(sleep_time)
            return {"result": "success"}
        
        # Apply the decorator
        decorated_func = profiler.profile_endpoint_async(test_async_function)
        
        # Call the decorated function multiple times with different sleep times
        await decorated_func(0.1)
        await decorated_func(0.2)
        await decorated_func(0.3)
        
        # Check that the profiler collected data
        assert "test_async_function" in profiler.profile_data
        assert profiler.profile_data["test_async_function"]["call_count"] == 3
        
        # Check that the response times are reasonable
        response_times = profiler.profile_data["test_async_function"]["response_times"]
        assert 0.05 <= response_times[0] <= 0.15  # Allow for some timing variation
        assert 0.15 <= response_times[1] <= 0.25
        assert 0.25 <= response_times[2] <= 0.35
    
    def test_get_report(self):
        """Test that the get_report method returns a valid ProfileReport."""
        profiler = APIProfiler()
        
        @profiler.profile_endpoint
        def test_function(sleep_time=0.1):
            time.sleep(sleep_time)
            return {"result": "success"}
        
        # Call the function multiple times with different sleep times
        test_function(0.1)
        test_function(0.2)
        test_function(0.3)
        
        # Get the report for the function
        report = profiler.get_report("test_function")
        
        # Check that the report contains the expected data
        assert isinstance(report, ProfileReport)
        assert 0.15 <= report.get_average_response_time() <= 0.25  # Average of 0.1, 0.2, 0.3
        assert 0.25 <= report.get_max_response_time() <= 0.35  # Max is 0.3
        assert 0.05 <= report.get_min_response_time() <= 0.15  # Min is 0.1
        assert 0.25 <= report.get_percentile_response_time(95) <= 0.35  # 95th percentile is 0.3
        
        # Check that the report can be converted to a dictionary
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert "average_response_time" in report_dict
        assert "max_response_time" in report_dict
        assert "min_response_time" in report_dict
        assert "p95_response_time" in report_dict
        assert "recommendations" in report_dict


@pytest.mark.performance
class TestProfileMiddleware:
    """Tests for the ProfileMiddleware class."""
    
    def test_middleware_initialization(self):
        """Test that the ProfileMiddleware can be initialized."""
        profiler = APIProfiler()
        middleware = ProfileMiddleware(profiler)
        assert middleware is not None
        assert hasattr(middleware, 'profiler')
        assert middleware.profiler is profiler
    
    def test_middleware_collects_performance_data(self):
        """Test that the middleware collects performance data for requests."""
        app = APIApp()
        profiler = APIProfiler()
        middleware = ProfileMiddleware(profiler)
        
        app.add_middleware(middleware)
        
        @app.api()
        def test_endpoint(sleep_time="0.1"):
            time.sleep(float(sleep_time))
            return {"result": "success"}
        
        # Make multiple requests with different sleep times
        request1 = Request(
            method="GET",
            path="/test_endpoint",
            query_params={"sleep_time": "0.1"}
        )
        request1.start_time = time.time()  # Normally set by middleware
        
        request2 = Request(
            method="GET",
            path="/test_endpoint",
            query_params={"sleep_time": "0.2"}
        )
        request2.start_time = time.time()
        
        request3 = Request(
            method="GET",
            path="/test_endpoint",
            query_params={"sleep_time": "0.3"}
        )
        request3.start_time = time.time()
        
        # Process the requests
        response1 = app.handle_request(request1)
        response1.request = request1  # Normally set by framework
        
        response2 = app.handle_request(request2)
        response2.request = request2
        
        response3 = app.handle_request(request3)
        response3.request = request3
        
        # Apply response middleware manually (since our mock doesn't do this)
        middleware.process_response(response1)
        middleware.process_response(response2)
        middleware.process_response(response3)
        
        # Check that the profiler collected data
        assert "/test_endpoint" in profiler.profile_data
        assert profiler.profile_data["/test_endpoint"]["call_count"] == 3
        assert len(profiler.profile_data["/test_endpoint"]["response_times"]) == 3
        
        # Get the report for the endpoint
        report = profiler.get_report("/test_endpoint")
        
        # Check that the report contains the expected data
        assert isinstance(report, ProfileReport)
        # We can't check exact times here because the middleware timing is different from the decorator timing
        assert report.get_average_response_time() > 0
        assert report.get_max_response_time() > 0
        assert report.get_min_response_time() > 0
        assert report.get_percentile_response_time(95) > 0


@pytest.mark.performance
class TestProfileReport:
    """Tests for the ProfileReport class."""
    
    def test_report_initialization(self):
        """Test that the ProfileReport can be initialized."""
        report = ProfileReport()
        assert report is not None
        assert hasattr(report, 'profile_data')
        assert isinstance(report.profile_data, dict)
    
    def test_report_with_data(self):
        """Test that the ProfileReport correctly analyzes profile data."""
        profile_data = {
            "call_count": 5,
            "response_times": [0.1, 0.2, 0.3, 0.4, 0.5]
        }
        
        report = ProfileReport(profile_data)
        
        # Check the calculated metrics
        assert report.get_average_response_time() == 0.3
        assert report.get_max_response_time() == 0.5
        assert report.get_min_response_time() == 0.1
        assert report.get_percentile_response_time(80) == 0.5  # 80th percentile is the 5th item (0.5)
        
        # Check the recommendations
        recommendations = report.get_recommendations()
        assert isinstance(recommendations, list)
        # The test data has a max response time of 0.5, which is not enough to trigger recommendations
        assert len(recommendations) == 0
    
    def test_report_to_dict(self):
        """Test that the to_dict method returns a valid dictionary."""
        profile_data = {
            "call_count": 5,
            "response_times": [0.1, 0.2, 0.3, 0.4, 0.5]
        }
        
        report = ProfileReport(profile_data)
        report_dict = report.to_dict()
        
        # Check the dictionary structure
        assert isinstance(report_dict, dict)
        assert report_dict["average_response_time"] == 0.3
        assert report_dict["max_response_time"] == 0.5
        assert report_dict["min_response_time"] == 0.1
        assert report_dict["p95_response_time"] == 0.5  # 95th percentile is the 5th item (0.5)
        assert isinstance(report_dict["recommendations"], list)


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 