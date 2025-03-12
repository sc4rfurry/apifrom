"""
Performance benchmarks for the APIFromAnything library.

This module contains performance benchmarks to measure the performance of
various components of the APIFromAnything library.
"""

import time
import statistics
import concurrent.futures
import requests
import threading
from typing import Dict, List, Callable, Any

from apifrom import API, api
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware import CacheMiddleware, RateLimitMiddleware
from apifrom.middleware.rate_limit import FixedWindowRateLimiter


class TestServer:
    """
    Test server for performance testing.
    """
    
    @classmethod
    def create(cls, api_instance: API, host: str = "127.0.0.1", port: int = 8889):
        """
        Create a new TestServer instance.
        
        Args:
            api_instance: The API instance to test
            host: The host to bind to
            port: The port to bind to
            
        Returns:
            A new TestServer instance
        """
        server = cls()
        server.api = api_instance
        server.host = host
        server.port = port
        server.server_thread = None
        server.is_running = False
        server.base_url = f"http://{host}:{port}"
        return server
    
    def start(self):
        """
        Start the test server in a separate thread.
        """
        if self.is_running:
            return
        
        self.is_running = True
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Wait for the server to start
        time.sleep(1)
    
    def stop(self):
        """
        Stop the test server.
        """
        self.is_running = False
        if self.server_thread:
            self.server_thread.join(timeout=5)
    
    def _run_server(self):
        """
        Run the server.
        """
        self.api.run(host=self.host, port=self.port)
    
    def __enter__(self):
        """
        Start the server when entering a context.
        """
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Stop the server when exiting a context.
        """
        self.stop()


class Benchmark:
    """
    Benchmark utility for measuring performance.
    """
    
    def __init__(self, name: str):
        """
        Initialize the benchmark.
        
        Args:
            name: The name of the benchmark
        """
        self.name = name
        self.results = []
    
    def measure(self, func: Callable, *args, **kwargs) -> Any:
        """
        Measure the execution time of a function.
        
        Args:
            func: The function to measure
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        self.results.append(execution_time)
        
        return result
    
    def summarize(self) -> Dict:
        """
        Summarize the benchmark results.
        
        Returns:
            A dictionary with the benchmark summary
        """
        if not self.results:
            return {
                "name": self.name,
                "count": 0,
                "min": 0,
                "max": 0,
                "mean": 0,
                "median": 0,
                "p95": 0,
                "p99": 0,
            }
        
        sorted_results = sorted(self.results)
        p95_index = int(len(sorted_results) * 0.95)
        p99_index = int(len(sorted_results) * 0.99)
        
        return {
            "name": self.name,
            "count": len(self.results),
            "min": min(self.results),
            "max": max(self.results),
            "mean": statistics.mean(self.results),
            "median": statistics.median(self.results),
            "p95": sorted_results[p95_index],
            "p99": sorted_results[p99_index],
        }
    
    def print_summary(self):
        """
        Print the benchmark summary.
        """
        summary = self.summarize()
        
        print(f"Benchmark: {summary['name']}")
        print(f"  Count: {summary['count']}")
        print(f"  Min: {summary['min']:.2f} ms")
        print(f"  Max: {summary['max']:.2f} ms")
        print(f"  Mean: {summary['mean']:.2f} ms")
        print(f"  Median: {summary['median']:.2f} ms")
        print(f"  P95: {summary['p95']:.2f} ms")
        print(f"  P99: {summary['p99']:.2f} ms")


def run_benchmarks():
    """
    Run performance benchmarks.
    """
    # Create an API instance
    api = API(
        title="Performance Test API",
        description="API for performance testing",
        version="1.0.0",
        debug=False  # Disable debug mode for performance testing
    )
    
    # Define API endpoints
    
    # Simple endpoint
    @api(route="/simple", method="GET")
    def simple_endpoint() -> Dict:
        return {"message": "Hello, World!"}
    
    # Endpoint with path parameters
    @api(route="/users/{user_id}", method="GET")
    def get_user(user_id: int) -> Dict:
        return {"user_id": user_id, "name": f"User {user_id}"}
    
    # Endpoint with complex processing
    @api(route="/complex", method="GET")
    def complex_endpoint(iterations: int = 1000) -> Dict:
        # Simulate complex processing
        result = 0
        for i in range(iterations):
            result += i
        
        return {"result": result}
    
    # Endpoint with request body
    @api(route="/users", method="POST")
    def create_user(name: str, age: int) -> Dict:
        return {"name": name, "age": age, "id": 1}
    
    # Start the server and run benchmarks
    with TestServer.create(api) as server:
        base_url = server.base_url
        # Benchmark 1: Simple endpoint
        simple_benchmark = Benchmark("Simple Endpoint")
        
        for _ in range(1000):
            simple_benchmark.measure(
                requests.get,
                f"{base_url}/simple"
            )
        
        simple_benchmark.print_summary()
        
        # Benchmark 2: Endpoint with path parameters
        path_params_benchmark = Benchmark("Path Parameters Endpoint")
        
        for i in range(1000):
            path_params_benchmark.measure(
                requests.get,
                f"{base_url}/users/{i}"
            )
        
        path_params_benchmark.print_summary()
        
        # Benchmark 3: Endpoint with complex processing
        complex_benchmark = Benchmark("Complex Endpoint")
        
        for _ in range(100):
            complex_benchmark.measure(
                requests.get,
                f"{base_url}/complex"
            )
        
        complex_benchmark.print_summary()
        
        # Benchmark 4: Endpoint with request body
        request_body_benchmark = Benchmark("Request Body Endpoint")
        
        for i in range(1000):
            request_body_benchmark.measure(
                requests.post,
                f"{base_url}/users",
                json={"name": f"User {i}", "age": 30}
            )
        
        request_body_benchmark.print_summary()
        
        # Benchmark 5: Concurrent requests
        concurrent_benchmark = Benchmark("Concurrent Requests")
        
        def make_request():
            return requests.get(f"{base_url}/simple")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for _ in range(10):
                futures = [executor.submit(concurrent_benchmark.measure, make_request) for _ in range(100)]
                concurrent.futures.wait(futures)
        
        concurrent_benchmark.print_summary()


def benchmark_middleware():
    """
    Benchmark middleware performance.
    """
    # Create an API instance
    api = API(
        title="Middleware Performance Test API",
        description="API for middleware performance testing",
        version="1.0.0",
        debug=False  # Disable debug mode for performance testing
    )
    
    # Define API endpoints
    @api(route="/no-middleware", method="GET")
    def no_middleware_endpoint() -> Dict:
        return {"message": "Hello, World!"}
    
    # Create a new API instance with middleware
    api_with_middleware = API(
        title="Middleware Performance Test API",
        description="API for middleware performance testing",
        version="1.0.0",
        debug=False  # Disable debug mode for performance testing
    )
    
    # Add middleware
    cache_middleware = CacheMiddleware(ttl=60)
    rate_limiter = FixedWindowRateLimiter(limit=1000, window=60)
    rate_limit_middleware = RateLimitMiddleware(limiter=rate_limiter)
    
    api_with_middleware.add_middleware(cache_middleware)
    api_with_middleware.add_middleware(rate_limit_middleware)
    
    # Define API endpoints
    @api(route="/with-middleware", method="GET")
    def with_middleware_endpoint() -> Dict:
        return {"message": "Hello, World!"}
    
    # Run benchmarks with and without middleware
    with TestServer.create(api, port=8890) as server1, TestServer.create(api_with_middleware, port=8891) as server2:
        base_url1 = server1.base_url
        base_url2 = server2.base_url
        # Benchmark 1: No middleware
        no_middleware_benchmark = Benchmark("No Middleware")
        
        for _ in range(1000):
            no_middleware_benchmark.measure(
                requests.get,
                f"{base_url1}/no-middleware"
            )
        
        no_middleware_benchmark.print_summary()
        
        # Benchmark 2: With middleware
        with_middleware_benchmark = Benchmark("With Middleware")
        
        for _ in range(1000):
            with_middleware_benchmark.measure(
                requests.get,
                f"{base_url2}/with-middleware"
            )
        
        with_middleware_benchmark.print_summary()
        
        # Benchmark 3: With middleware (cached)
        with_middleware_cached_benchmark = Benchmark("With Middleware (Cached)")
        
        for _ in range(1000):
            with_middleware_cached_benchmark.measure(
                requests.get,
                f"{base_url2}/with-middleware"
            )
        
        with_middleware_cached_benchmark.print_summary()


def benchmark_serialization():
    """
    Benchmark serialization performance.
    """
    from apifrom.utils.serialization import serialize, deserialize
    
    # Simple object
    simple_obj = {"message": "Hello, World!"}
    
    # Complex object
    complex_obj = {
        "id": 1,
        "name": "Test",
        "items": [{"id": i, "value": f"Item {i}"} for i in range(100)],
        "metadata": {
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "tags": ["tag1", "tag2", "tag3"],
        }
    }
    
    # Benchmark 1: Simple serialization
    simple_serialization_benchmark = Benchmark("Simple Serialization")
    
    for _ in range(10000):
        simple_serialization_benchmark.measure(serialize, simple_obj)
    
    simple_serialization_benchmark.print_summary()
    
    # Benchmark 2: Complex serialization
    complex_serialization_benchmark = Benchmark("Complex Serialization")
    
    for _ in range(10000):
        complex_serialization_benchmark.measure(serialize, complex_obj)
    
    complex_serialization_benchmark.print_summary()
    
    # Benchmark 3: Simple deserialization
    simple_json = serialize(simple_obj)
    simple_deserialization_benchmark = Benchmark("Simple Deserialization")
    
    for _ in range(10000):
        simple_deserialization_benchmark.measure(deserialize, simple_json)
    
    simple_deserialization_benchmark.print_summary()
    
    # Benchmark 4: Complex deserialization
    complex_json = serialize(complex_obj)
    complex_deserialization_benchmark = Benchmark("Complex Deserialization")
    
    for _ in range(10000):
        complex_deserialization_benchmark.measure(deserialize, complex_json)
    
    complex_deserialization_benchmark.print_summary()


if __name__ == "__main__":
    print("Running API benchmarks...")
    run_benchmarks()
    
    print("\nRunning middleware benchmarks...")
    benchmark_middleware()
    
    print("\nRunning serialization benchmarks...")
    benchmark_serialization() 