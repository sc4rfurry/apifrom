"""
Profiling utilities for APIFromAnything.

This module provides tools for profiling API endpoints, measuring performance,
and generating reports to help identify and fix performance bottlenecks.
"""

import time
import functools
import statistics
import cProfile
import pstats
import io
from typing import Dict, List, Optional, Callable, Any, Union
import json
import os
from datetime import datetime
import threading
import asyncio
from contextvars import ContextVar

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware.base import BaseMiddleware


# Context variable to track profiler state
_profiler_ctx = ContextVar('profiler_ctx', default=None)


class ProfileReport:
    """
    Represents a performance profile report for an API endpoint.
    
    This class provides methods for analyzing and visualizing profile data,
    as well as exporting it to various formats.
    """
    
    def __init__(self, endpoint_name: str, profile_data: Dict[str, Any]):
        """
        Initialize a profile report.
        
        Args:
            endpoint_name: The name of the endpoint being profiled
            profile_data: The raw profile data
        """
        self.endpoint_name = endpoint_name
        self.profile_data = profile_data
        self.created_at = datetime.now()
    
    @property
    def avg_response_time(self) -> float:
        """
        Get the average response time in milliseconds.
        
        Returns:
            The average response time
        """
        if "response_times" in self.profile_data and self.profile_data["response_times"]:
            return statistics.mean(self.profile_data["response_times"])
        return 0.0
    
    @property
    def max_response_time(self) -> float:
        """
        Get the maximum response time in milliseconds.
        
        Returns:
            The maximum response time
        """
        if "response_times" in self.profile_data and self.profile_data["response_times"]:
            return max(self.profile_data["response_times"])
        return 0.0
    
    @property
    def min_response_time(self) -> float:
        """
        Get the minimum response time in milliseconds.
        
        Returns:
            The minimum response time
        """
        if "response_times" in self.profile_data and self.profile_data["response_times"]:
            return min(self.profile_data["response_times"])
        return 0.0
    
    @property
    def p95_response_time(self) -> float:
        """
        Get the 95th percentile response time in milliseconds.
        
        Returns:
            The 95th percentile response time
        """
        if "response_times" in self.profile_data and len(self.profile_data["response_times"]) > 0:
            sorted_times = sorted(self.profile_data["response_times"])
            idx = int(len(sorted_times) * 0.95)
            return sorted_times[idx]
        return 0.0
    
    @property
    def request_count(self) -> int:
        """
        Get the number of requests processed.
        
        Returns:
            The number of requests
        """
        return self.profile_data.get("request_count", 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the report to a dictionary.
        
        Returns:
            A dictionary representation of the report
        """
        return {
            "endpoint": self.endpoint_name,
            "created_at": self.created_at.isoformat(),
            "avg_response_time_ms": self.avg_response_time,
            "max_response_time_ms": self.max_response_time,
            "min_response_time_ms": self.min_response_time,
            "p95_response_time_ms": self.p95_response_time,
            "request_count": self.request_count,
            "function_stats": self.profile_data.get("function_stats", {}),
            "memory_usage": self.profile_data.get("memory_usage", {}),
            "cpu_usage": self.profile_data.get("cpu_usage", {}),
        }
    
    def to_json(self, pretty: bool = True) -> str:
        """
        Convert the report to a JSON string.
        
        Args:
            pretty: Whether to format the JSON with indentation
            
        Returns:
            A JSON string representation of the report
        """
        indent = 2 if pretty else None
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, file_path: str) -> None:
        """
        Save the report to a file.
        
        Args:
            file_path: The path to save the report to
        """
        with open(file_path, 'w') as f:
            f.write(self.to_json())
    
    def print_summary(self) -> None:
        """
        Print a summary of the report to the console.
        """
        print(f"=== Profile Report: {self.endpoint_name} ===")
        print(f"Created At: {self.created_at.isoformat()}")
        print(f"Request Count: {self.request_count}")
        print(f"Average Response Time: {self.avg_response_time:.2f} ms")
        print(f"Maximum Response Time: {self.max_response_time:.2f} ms")
        print(f"Minimum Response Time: {self.min_response_time:.2f} ms")
        print(f"95th Percentile Response Time: {self.p95_response_time:.2f} ms")
        
        if "function_stats" in self.profile_data and self.profile_data["function_stats"]:
            print("\nTop 5 Functions by Cumulative Time:")
            for i, (func, time_ms) in enumerate(sorted(
                self.profile_data["function_stats"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]):
                print(f"{i+1}. {func}: {time_ms:.2f} ms")
    
    def get_recommendations(self) -> List[str]:
        """
        Get performance optimization recommendations based on the profile data.
        
        Returns:
            A list of recommendations
        """
        recommendations = []
        
        # Check for slow response time
        if self.avg_response_time > 200:  # More than 200ms is considered slow
            recommendations.append(
                f"Average response time ({self.avg_response_time:.2f} ms) is high. "
                f"Consider optimizing the endpoint implementation."
            )
        
        # Check for high p95
        if self.p95_response_time > 500:  # More than 500ms for p95 is concerning
            recommendations.append(
                f"95th percentile response time ({self.p95_response_time:.2f} ms) is high. "
                f"There may be outliers or inconsistent performance."
            )
        
        # Check for high memory usage
        if "memory_usage" in self.profile_data and self.profile_data["memory_usage"].get("peak_mb", 0) > 100:
            recommendations.append(
                f"Peak memory usage ({self.profile_data['memory_usage'].get('peak_mb', 0):.2f} MB) is high. "
                f"Consider optimizing memory usage in the endpoint."
            )
        
        # Check for CPU-intensive functions
        if "function_stats" in self.profile_data and self.profile_data["function_stats"]:
            for func, time_ms in sorted(
                self.profile_data["function_stats"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]:
                if time_ms > 100:  # More than 100ms is considered expensive
                    recommendations.append(
                        f"Function '{func}' is taking {time_ms:.2f} ms to execute. "
                        f"Consider optimizing this function or using caching."
                    )
        
        # If everything looks good
        if not recommendations:
            recommendations.append(
                f"The endpoint '{self.endpoint_name}' is performing well. "
                f"No immediate optimizations needed."
            )
        
        return recommendations


class APIProfiler:
    """
    Profiles API endpoints to measure performance and identify bottlenecks.
    
    This class provides tools for profiling API endpoints, measuring response times,
    memory usage, and CPU usage, and generating profile reports.
    """
    
    def __init__(self, output_dir: Optional[str] = None, enabled: bool = True):
        """
        Initialize an API profiler.
        
        Args:
            output_dir: The directory to save profile reports to (defaults to current directory)
            enabled: Whether profiling is enabled
        """
        self.output_dir = output_dir or os.getcwd()
        self.enabled = enabled
        self.profiles = {}
        self._lock = threading.Lock()
    
    def profile_endpoint(self, endpoint_name: str) -> Callable:
        """
        Decorator for profiling an API endpoint.
        
        Args:
            endpoint_name: The name of the endpoint being profiled
            
        Returns:
            A decorated function
        """
        def decorator(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)
                
                # Initialize profile data if needed
                with self._lock:
                    if endpoint_name not in self.profiles:
                        self.profiles[endpoint_name] = {
                            "request_count": 0,
                            "response_times": [],
                            "function_stats": {},
                            "memory_usage": {},
                            "cpu_usage": {},
                        }
                
                # Set up profiling
                profiler = cProfile.Profile()
                start_time = time.time()
                profiler.enable()
                
                # Store profiler in context
                _profiler_ctx.set((self, endpoint_name, profiler, start_time))
                
                try:
                    # Call the original function
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    # Get profiler from context
                    ctx_data = _profiler_ctx.get()
                    if ctx_data:
                        _, _, profiler, start_time = ctx_data
                        
                        # End profiling
                        end_time = time.time()
                        profiler.disable()
                        
                        # Update profile data
                        response_time = (end_time - start_time) * 1000  # Convert to ms
                        
                        # Process profile data
                        s = io.StringIO()
                        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                        ps.print_stats(10)  # Top 10 functions
                        
                        # Extract function stats
                        stats_output = s.getvalue()
                        function_stats = {}
                        for line in stats_output.split('\n')[5:15]:  # Skip header lines
                            if line.strip():
                                parts = line.strip().split()
                                if len(parts) >= 6:
                                    # Extract function name and cumulative time
                                    func_name = ' '.join(parts[5:])
                                    cum_time = float(parts[3]) * 1000  # Convert to ms
                                    function_stats[func_name] = cum_time
                        
                        # Update profile data
                        with self._lock:
                            self.profiles[endpoint_name]["request_count"] += 1
                            self.profiles[endpoint_name]["response_times"].append(response_time)
                            
                            # Update function stats
                            for func_name, time_ms in function_stats.items():
                                if func_name in self.profiles[endpoint_name]["function_stats"]:
                                    self.profiles[endpoint_name]["function_stats"][func_name] = (
                                        (self.profiles[endpoint_name]["function_stats"][func_name] + time_ms) / 2
                                    )
                                else:
                                    self.profiles[endpoint_name]["function_stats"][func_name] = time_ms
                        
                        # Clear context
                        _profiler_ctx.set(None)
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                
                # Initialize profile data if needed
                with self._lock:
                    if endpoint_name not in self.profiles:
                        self.profiles[endpoint_name] = {
                            "request_count": 0,
                            "response_times": [],
                            "function_stats": {},
                            "memory_usage": {},
                            "cpu_usage": {},
                        }
                
                # Set up profiling
                profiler = cProfile.Profile()
                start_time = time.time()
                profiler.enable()
                
                # Store profiler in context
                _profiler_ctx.set((self, endpoint_name, profiler, start_time))
                
                try:
                    # Call the original function
                    result = func(*args, **kwargs)
                    return result
                finally:
                    # Get profiler from context
                    ctx_data = _profiler_ctx.get()
                    if ctx_data:
                        _, _, profiler, start_time = ctx_data
                        
                        # End profiling
                        end_time = time.time()
                        profiler.disable()
                        
                        # Update profile data
                        response_time = (end_time - start_time) * 1000  # Convert to ms
                        
                        # Process profile data
                        s = io.StringIO()
                        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                        ps.print_stats(10)  # Top 10 functions
                        
                        # Extract function stats
                        stats_output = s.getvalue()
                        function_stats = {}
                        for line in stats_output.split('\n')[5:15]:  # Skip header lines
                            if line.strip():
                                parts = line.strip().split()
                                if len(parts) >= 6:
                                    # Extract function name and cumulative time
                                    func_name = ' '.join(parts[5:])
                                    cum_time = float(parts[3]) * 1000  # Convert to ms
                                    function_stats[func_name] = cum_time
                        
                        # Update profile data
                        with self._lock:
                            self.profiles[endpoint_name]["request_count"] += 1
                            self.profiles[endpoint_name]["response_times"].append(response_time)
                            
                            # Update function stats
                            for func_name, time_ms in function_stats.items():
                                if func_name in self.profiles[endpoint_name]["function_stats"]:
                                    self.profiles[endpoint_name]["function_stats"][func_name] = (
                                        (self.profiles[endpoint_name]["function_stats"][func_name] + time_ms) / 2
                                    )
                                else:
                                    self.profiles[endpoint_name]["function_stats"][func_name] = time_ms
                        
                        # Clear context
                        _profiler_ctx.set(None)
            
            # Return the appropriate wrapper based on whether the function is a coroutine
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def get_report(self, endpoint_name: str) -> Optional[ProfileReport]:
        """
        Get a profile report for an endpoint.
        
        Args:
            endpoint_name: The name of the endpoint
            
        Returns:
            A ProfileReport instance or None if no profile data exists
        """
        if endpoint_name in self.profiles:
            return ProfileReport(endpoint_name, self.profiles[endpoint_name])
        return None
    
    def get_all_reports(self) -> List[ProfileReport]:
        """
        Get profile reports for all endpoints.
        
        Returns:
            A list of ProfileReport instances
        """
        return [ProfileReport(name, data) for name, data in self.profiles.items()]
    
    def save_reports(self, prefix: Optional[str] = None) -> List[str]:
        """
        Save all profile reports to files.
        
        Args:
            prefix: A prefix to add to the filenames
            
        Returns:
            A list of file paths where reports were saved
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        prefix = prefix or f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_paths = []
        
        for name, data in self.profiles.items():
            report = ProfileReport(name, data)
            
            # Create a safe filename from the endpoint name
            safe_name = name.replace('/', '_').replace('\\', '_').replace('.', '_')
            file_path = os.path.join(self.output_dir, f"{prefix}_{safe_name}.json")
            
            report.save(file_path)
            file_paths.append(file_path)
        
        return file_paths
    
    def clear(self) -> None:
        """
        Clear all profile data.
        """
        with self._lock:
            self.profiles = {}
    
    def enable(self) -> None:
        """
        Enable profiling.
        """
        self.enabled = True
    
    def disable(self) -> None:
        """
        Disable profiling.
        """
        self.enabled = False


class ProfileMiddleware(BaseMiddleware):
    """
    Middleware for profiling API requests and responses.
    
    This middleware profiles API requests and responses, collecting performance metrics
    and generating profile reports. It can be used to identify performance bottlenecks
    and optimize API performance.
    """
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        save_interval: int = 300,
        enabled: bool = True,
        profiler: Optional[APIProfiler] = None,
    ):
        """
        Initialize the profile middleware.
        
        Args:
            output_dir: The directory to save profile reports to
            save_interval: The interval to save profile reports in seconds
            enabled: Whether profiling is enabled
            profiler: The profiler to use (creates a new one if None)
        """
        super().__init__()
        self.output_dir = output_dir
        self.save_interval = save_interval
        self.enabled = enabled
        self.profiler = profiler or APIProfiler(output_dir=output_dir)
        self.last_save_time = time.time()
    
    async def process_request(self, request):
        """
        Process a request (required by BaseMiddleware).
        
        Args:
            request: The request to process
            
        Returns:
            The processed request
        """
        # Initialize request context for profiling
        if self.enabled:
            request.state.profile_start_time = time.time()
            
        return request
    
    async def process_response(self, response):
        """
        Process a response (required by BaseMiddleware).
        
        Args:
            response: The response to process
            
        Returns:
            The processed response
        """
        # Nothing to do here, profiling is handled in dispatch
        return response
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Dispatch a request, profiling the execution time.
        
        Args:
            request: The request to process
            call_next: The next middleware or route handler
            
        Returns:
            The response
        """
        # Skip profiling if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Get the endpoint and path
        endpoint = f"{request.method}:{request.url.path}"
        
        # Start profiling
        profile_id = self.profiler.start_profile(endpoint)
        start_time = time.time()
        
        try:
            # Call the next middleware or route handler
            response = await call_next(request)
            
            # Record the successful response
            end_time = time.time()
            self.profiler.end_profile(
                profile_id=profile_id,
                status_code=response.status_code,
                duration_ms=(end_time - start_time) * 1000,
                endpoint=endpoint,
                response_size=len(response.body) if hasattr(response, "body") else 0,
                is_error=response.status_code >= 400,
            )
            
            # Save profile reports if the save interval has passed
            if self.output_dir and (time.time() - self.last_save_time) > self.save_interval:
                self.profiler.save_profile_reports()
                self.last_save_time = time.time()
            
            return response
        except Exception as e:
            # Record the error
            end_time = time.time()
            self.profiler.end_profile(
                profile_id=profile_id,
                status_code=500,
                duration_ms=(end_time - start_time) * 1000,
                endpoint=endpoint,
                response_size=0,
                is_error=True,
                error=str(e),
            )
            
            # Re-raise the exception
            raise
    
    def get_all_reports(self) -> List[ProfileReport]:
        """
        Get all profile reports.
        
        Returns:
            A list of profile reports
        """
        return self.profiler.get_all_reports()
    
    def get_report(self, endpoint: str) -> Optional[ProfileReport]:
        """
        Get a profile report for an endpoint.
        
        Args:
            endpoint: The endpoint to get the report for
            
        Returns:
            The profile report, or None if not found
        """
        return self.profiler.get_report(endpoint)
    
    def clear(self) -> None:
        """Clear all profile data."""
        self.profiler.clear()
    
    def enable(self) -> None:
        """Enable profiling."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable profiling."""
        self.enabled = False 