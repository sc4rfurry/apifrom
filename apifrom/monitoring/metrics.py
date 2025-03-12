"""
Metrics collection and management for APIFromAnything.

This module provides classes and utilities for collecting, managing, and
tracking various metrics related to API performance and usage.
"""

import time
import enum
import threading
import statistics
import uuid
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field


class MetricType(enum.Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"  # Metrics that increment (e.g., request count)
    GAUGE = "gauge"  # Metrics that can go up and down (e.g., active requests)
    HISTOGRAM = "histogram"  # Distribution of values (e.g., response times)
    SUMMARY = "summary"  # Similar to histogram but with quantiles


@dataclass
class Metric:
    """Represents a single metric with its metadata and values."""
    name: str
    type: MetricType
    description: str
    labels: Dict[str, str] = field(default_factory=dict)
    value: Union[float, int, List[float]] = field(default_factory=list)
    
    # For histogram/summary metrics
    buckets: List[float] = field(default_factory=list)
    quantiles: List[float] = field(default_factory=lambda: [0.5, 0.9, 0.95, 0.99])
    
    def __post_init__(self):
        """Initialize the metric based on its type."""
        if self.type in (MetricType.COUNTER, MetricType.GAUGE) and not isinstance(self.value, (int, float)):
            self.value = 0
        elif self.type in (MetricType.HISTOGRAM, MetricType.SUMMARY) and not isinstance(self.value, list):
            self.value = []
            
        # Set default buckets for histograms if not provided
        if self.type == MetricType.HISTOGRAM and not self.buckets:
            # Default buckets for response time in ms: 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000
            self.buckets = [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
    
    def increment(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        if self.type != MetricType.COUNTER:
            raise ValueError(f"Cannot increment metric of type {self.type}")
        
        if labels:
            self.labels.update(labels)
            
        self.value += amount
    
    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric to a specific value."""
        if self.type != MetricType.GAUGE:
            raise ValueError(f"Cannot set value for metric of type {self.type}")
            
        if labels:
            self.labels.update(labels)
            
        self.value = value
    
    def observe(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Add an observation to a histogram or summary metric."""
        if self.type not in (MetricType.HISTOGRAM, MetricType.SUMMARY):
            raise ValueError(f"Cannot observe value for metric of type {self.type}")
            
        if labels:
            self.labels.update(labels)
            
        if isinstance(self.value, list):
            self.value.append(value)
        else:
            self.value = [value]
    
    def get_histogram_buckets(self) -> Dict[float, int]:
        """Get histogram bucket counts."""
        if self.type != MetricType.HISTOGRAM:
            raise ValueError(f"Cannot get histogram buckets for metric of type {self.type}")
            
        result = {bucket: 0 for bucket in self.buckets}
        for value in self.value:
            for bucket in self.buckets:
                if value <= bucket:
                    result[bucket] += 1
                    
        return result
    
    def get_summary_quantiles(self) -> Dict[float, float]:
        """Get summary quantiles."""
        if self.type != MetricType.SUMMARY:
            raise ValueError(f"Cannot get summary quantiles for metric of type {self.type}")
            
        if not self.value:
            return {q: 0 for q in self.quantiles}
            
        result = {}
        sorted_values = sorted(self.value)
        for q in self.quantiles:
            idx = int(q * len(sorted_values))
            if idx >= len(sorted_values):
                idx = len(sorted_values) - 1
            result[q] = sorted_values[idx]
            
        return result
    
    def get_stats(self) -> Dict[str, float]:
        """Get basic statistics for histogram and summary metrics."""
        if self.type not in (MetricType.HISTOGRAM, MetricType.SUMMARY):
            raise ValueError(f"Cannot get statistics for metric of type {self.type}")
            
        if not self.value:
            return {
                "count": 0,
                "sum": 0,
                "min": 0,
                "max": 0,
                "mean": 0,
                "median": 0
            }
            
        return {
            "count": len(self.value),
            "sum": sum(self.value),
            "min": min(self.value),
            "max": max(self.value),
            "mean": statistics.mean(self.value),
            "median": statistics.median(self.value)
        }


class MetricsCollector:
    """
    Collects and manages metrics for the API.
    
    This class provides a centralized way to create, update, and retrieve metrics
    for monitoring API performance and usage.
    """
    
    _instance = None
    
    def __new__(cls):
        """Implement the singleton pattern."""
        if cls._instance is None:
            cls._instance = super(MetricsCollector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the metrics collector."""
        # Only initialize once
        if getattr(self, '_initialized', False):
            return
            
        self._metrics = {}
        self._timers = {}
        self._initialized = True
        
        # Create default metrics
        self.create_counter("api_requests_total", "Total number of API requests")
        self.create_counter("api_errors_total", "Total number of API errors")
        self.create_gauge("api_requests_active", "Number of currently active API requests")
        self.create_histogram("api_request_duration_ms", "API request duration in milliseconds")
        self.create_counter("api_requests_by_endpoint", "API requests by endpoint")
        self.create_counter("api_errors_by_type", "API errors by type")
    
    def create_metric(self, metric: Metric) -> Metric:
        """
        Register a new metric with the collector.
        
        Args:
            metric: The metric to register
            
        Returns:
            The registered metric
        """
        # Check if metric already exists
        if metric.name in self._metrics:
            raise ValueError(f"Metric with name '{metric.name}' already exists")
        
        # Register the metric
        self._metrics[metric.name] = metric
        return metric
    
    def create_counter(self, name: str, description: str, labels: Optional[Dict[str, str]] = None) -> Metric:
        """Create a new counter metric."""
        metric = Metric(
            name=name,
            type=MetricType.COUNTER,
            description=description,
            labels=labels or {},
            value=0
        )
        return self.create_metric(metric)
    
    def create_gauge(self, name: str, description: str, labels: Optional[Dict[str, str]] = None) -> Metric:
        """Create a new gauge metric."""
        metric = Metric(
            name=name,
            type=MetricType.GAUGE,
            description=description,
            labels=labels or {},
            value=0
        )
        return self.create_metric(metric)
    
    def create_histogram(self, name: str, description: str, 
                         buckets: Optional[List[float]] = None,
                         labels: Optional[Dict[str, str]] = None) -> Metric:
        """Create a new histogram metric."""
        metric = Metric(
            name=name,
            type=MetricType.HISTOGRAM,
            description=description,
            labels=labels or {},
            buckets=buckets or []
        )
        return self.create_metric(metric)
    
    def create_summary(self, name: str, description: str,
                      quantiles: Optional[List[float]] = None,
                      labels: Optional[Dict[str, str]] = None) -> Metric:
        """Create a new summary metric."""
        metric = Metric(
            name=name,
            type=MetricType.SUMMARY,
            description=description,
            labels=labels or {},
            quantiles=quantiles or [0.5, 0.9, 0.95, 0.99]
        )
        return self.create_metric(metric)
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name."""
        return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all metrics."""
        return self._metrics.copy()
    
    def increment(self, name: str, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        metric = self.get_metric(name)
        if not metric:
            raise ValueError(f"Metric with name '{name}' does not exist")
            
        metric.increment(amount, labels)
    
    def set(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric to a specific value."""
        metric = self.get_metric(name)
        if not metric:
            raise ValueError(f"Metric with name '{name}' does not exist")
            
        metric.set(value, labels)
    
    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Add an observation to a histogram or summary metric."""
        metric = self.get_metric(name)
        if not metric:
            raise ValueError(f"Metric with name '{name}' does not exist")
            
        metric.observe(value, labels)
    
    def start_timer(self, name: str) -> str:
        """
        Start a timer for measuring durations.
        
        Args:
            name: The name of the metric to record the duration
            
        Returns:
            A unique timer ID
        """
        timer_id = f"{name}_{uuid.uuid4()}"
        self._timers[timer_id] = time.time()
        return timer_id
    
    def stop_timer(self, timer_id: str, labels: Optional[Dict[str, str]] = None) -> float:
        """
        Stop a timer and return the duration in milliseconds.
        
        Args:
            timer_id: The timer ID
            labels: Optional labels to attach to the observation
            
        Returns:
            The duration in milliseconds
        """
        if timer_id not in self._timers:
            raise ValueError(f"Timer with ID '{timer_id}' does not exist")
        
        start_time = self._timers.pop(timer_id)
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Extract the metric name from the timer ID
        # The timer ID format is "metric_name_uuid"
        # We need to get everything before the last underscore
        parts = timer_id.split('_')
        if len(parts) >= 3:  # At least metric_name_uuid
            # Join all parts except the last one (which is the UUID)
            name = '_'.join(parts[:-1])
        else:
            name = parts[0] if parts else timer_id
        
        # Make sure the metric exists before observing
        if name in self._metrics:
            self.observe(name, duration_ms, labels)
        else:
            print(f"Warning: Metric with name '{name}' does not exist for timer {timer_id}")
        
        return duration_ms
    
    def track_request(self, endpoint: str) -> str:
        """
        Track the start of an API request.
        
        Args:
            endpoint: The API endpoint being called
            
        Returns:
            A timer ID for tracking the request duration
        """
        # Increment request counters
        self.increment("api_requests_total")
        self.increment("api_requests_by_endpoint", labels={"endpoint": endpoint})
        
        # Increment active requests gauge
        if "api_requests_active" in self._metrics:
            self.set("api_requests_active", self.get_metric("api_requests_active").value + 1)
        
        # Start a timer for the request duration
        return self.start_timer("api_request_duration_ms")
    
    def track_request_end(self, timer_id: str, endpoint: str, status_code: int) -> float:
        """
        Track the end of an API request.
        
        Args:
            timer_id: The timer ID returned by track_request
            endpoint: The API endpoint that was called
            status_code: The HTTP status code of the response
            
        Returns:
            The request duration in milliseconds
        """
        # Stop the timer and record the duration
        duration_ms = self.stop_timer(timer_id, labels={"endpoint": endpoint, "status_code": str(status_code)})
        
        # Decrement active requests gauge
        if "api_requests_active" in self._metrics:
            self.set("api_requests_active", max(0, self.get_metric("api_requests_active").value - 1))
        
        # If it's an error response, increment the error counter
        if status_code >= 400:
            self.increment("api_errors_total")
            error_type = "client_error" if 400 <= status_code < 500 else "server_error"
            self.increment("api_errors_by_type", labels={"type": error_type, "status_code": str(status_code)})
        
        return duration_ms
    
    def track_error(self, error_type: str, endpoint: Optional[str] = None) -> None:
        """Track an API error."""
        self.increment("api_errors_total")
        labels = {"type": error_type}
        if endpoint:
            labels["endpoint"] = endpoint
        self.increment("api_errors_by_type", labels=labels)
    
    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics = {}
        self._timers = {}
        
        # Re-create default metrics
        self.create_counter("api_requests_total", "Total number of API requests")
        self.create_counter("api_errors_total", "Total number of API errors")
        self.create_gauge("api_requests_active", "Number of currently active API requests")
        self.create_histogram("api_request_duration_ms", "API request duration in milliseconds")
        self.create_counter("api_requests_by_endpoint", "API requests by endpoint")
        self.create_counter("api_errors_by_type", "API errors by type") 