"""
Example demonstrating the monitoring and metrics collection features of APIFromAnything.

This example shows how to use the monitoring module to collect and export metrics
for API endpoints, including request counts, durations, and error rates.
"""

import time
import random
import logging
from typing import Dict, List, Optional

from apifrom.core.app import API
from apifrom.decorators.api import api
from apifrom.monitoring.metrics import MetricsCollector
from apifrom.monitoring.exporters import PrometheusExporter, JSONExporter, LogExporter
from apifrom.monitoring.middleware import MetricsMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create an API application
app = API(title="Monitoring Example API")

# Create a metrics collector
metrics = MetricsCollector()

# Register the metrics middleware
app.add_middleware(MetricsMiddleware(collector=metrics))

# Create metrics exporters
prometheus_exporter = PrometheusExporter(collector=metrics)
json_exporter = JSONExporter(collector=metrics)
log_exporter = LogExporter(collector=metrics)

# Create some custom metrics
metrics.create_counter("custom_counter", "A custom counter metric")
metrics.create_gauge("custom_gauge", "A custom gauge metric")
metrics.create_histogram("custom_histogram", "A custom histogram metric")
metrics.create_summary("custom_summary", "A custom summary metric")


# Define API endpoints
@api(app)
def hello(name: str = "World") -> Dict[str, str]:
    """
    Say hello to someone.
    
    Args:
        name: The name to greet.
        
    Returns:
        A greeting message.
    """
    # Increment a custom counter
    metrics.increment("custom_counter")
    
    # Set a custom gauge
    metrics.set("custom_gauge", random.randint(1, 100))
    
    # Simulate some work
    time.sleep(random.uniform(0.01, 0.1))
    
    return {"message": f"Hello, {name}!"}


@api(app)
def random_numbers(count: int = 10, min_value: int = 1, max_value: int = 100) -> List[int]:
    """
    Generate a list of random numbers.
    
    Args:
        count: The number of random numbers to generate.
        min_value: The minimum value for the random numbers.
        max_value: The maximum value for the random numbers.
        
    Returns:
        A list of random numbers.
    """
    # Start a timer
    timer_id = metrics.start_timer("custom_histogram")
    
    # Simulate some work
    time.sleep(random.uniform(0.05, 0.2))
    
    # Generate random numbers
    numbers = [random.randint(min_value, max_value) for _ in range(count)]
    
    # Stop the timer and record the duration
    metrics.stop_timer(timer_id)
    
    return numbers


@api(app)
def calculate_statistics(numbers: List[float]) -> Dict[str, float]:
    """
    Calculate statistics for a list of numbers.
    
    Args:
        numbers: The list of numbers to calculate statistics for.
        
    Returns:
        A dictionary of statistics.
    """
    # Start a timer
    timer_id = metrics.start_timer("custom_summary")
    
    # Simulate some work
    time.sleep(random.uniform(0.1, 0.3))
    
    # Calculate statistics
    if not numbers:
        raise ValueError("The list of numbers cannot be empty")
        
    result = {
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mean": sum(numbers) / len(numbers)
    }
    
    # Stop the timer and record the duration
    metrics.stop_timer(timer_id)
    
    return result


@api(app)
def error_endpoint() -> Dict[str, str]:
    """
    An endpoint that always raises an error.
    
    Returns:
        This endpoint never returns successfully.
    """
    # Simulate some work
    time.sleep(random.uniform(0.01, 0.1))
    
    # Raise an error
    raise ValueError("This endpoint always fails")


# Define a function to export metrics periodically
def export_metrics():
    """Export metrics to various formats."""
    # Export metrics to Prometheus format
    prometheus_metrics = prometheus_exporter.export()
    print("\n=== Prometheus Metrics ===")
    print(prometheus_metrics)
    
    # Export metrics to JSON format
    json_metrics = json_exporter.export(pretty=True)
    print("\n=== JSON Metrics ===")
    print(json_metrics)
    
    # Export metrics to logs
    print("\n=== Log Metrics ===")
    log_exporter.export(include_details=True)


# Define a function to simulate API traffic
def simulate_traffic(num_requests: int = 100):
    """
    Simulate API traffic by making requests to the endpoints.
    
    Args:
        num_requests: The number of requests to simulate.
    """
    print(f"Simulating {num_requests} API requests...")
    
    for i in range(num_requests):
        # Choose a random endpoint
        endpoint = random.choice([hello, random_numbers, calculate_statistics, error_endpoint])
        
        try:
            if endpoint == hello:
                # Call the hello endpoint
                name = random.choice(["Alice", "Bob", "Charlie", "Dave", "Eve"])
                result = hello(name=name)
                print(f"Request {i+1}/{num_requests}: hello({name}) -> {result}")
                
            elif endpoint == random_numbers:
                # Call the random_numbers endpoint
                count = random.randint(5, 15)
                result = random_numbers(count=count)
                print(f"Request {i+1}/{num_requests}: random_numbers({count}) -> {len(result)} numbers")
                
            elif endpoint == calculate_statistics:
                # Call the calculate_statistics endpoint
                numbers = [random.uniform(1, 100) for _ in range(random.randint(5, 15))]
                result = calculate_statistics(numbers=numbers)
                print(f"Request {i+1}/{num_requests}: calculate_statistics({len(numbers)} numbers) -> {result}")
                
            elif endpoint == error_endpoint:
                # Call the error_endpoint
                try:
                    result = error_endpoint()
                except ValueError as e:
                    print(f"Request {i+1}/{num_requests}: error_endpoint() -> Error: {str(e)}")
        
        except Exception as e:
            print(f"Request {i+1}/{num_requests}: Error: {str(e)}")
        
        # Sleep briefly between requests
        time.sleep(random.uniform(0.01, 0.05))


if __name__ == "__main__":
    # Start the metrics exporter in a separate thread
    log_exporter.export_periodic(interval_seconds=5, include_details=True)
    
    # Simulate API traffic
    simulate_traffic(num_requests=50)
    
    # Export metrics
    export_metrics()
    
    # Start a Prometheus metrics server
    print("\nStarting Prometheus metrics server on http://localhost:8000/metrics")
    print("Press Ctrl+C to stop the server")
    prometheus_exporter.serve_metrics(host="localhost", port=8000, endpoint="/metrics") 