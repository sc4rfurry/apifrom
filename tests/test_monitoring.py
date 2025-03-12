"""
Tests for the monitoring module of APIFromAnything.
"""

import unittest
import json
import time
from unittest.mock import MagicMock, patch
import pytest

from apifrom.monitoring.metrics import MetricsCollector, Metric, MetricType
from apifrom.monitoring.exporters import JSONExporter, PrometheusExporter, LogExporter
from apifrom.monitoring.middleware import MetricsMiddleware


class TestMetric(unittest.TestCase):
    """Tests for the Metric class."""
    
    def test_counter_metric(self):
        """Test counter metric functionality."""
        metric = Metric(
            name="test_counter",
            type=MetricType.COUNTER,
            description="A test counter",
            value=0
        )
        
        # Test increment
        metric.increment()
        self.assertEqual(metric.value, 1)
        
        metric.increment(5)
        self.assertEqual(metric.value, 6)
        
        # Test labels
        metric.increment(labels={"label1": "value1"})
        self.assertEqual(metric.value, 7)
        self.assertEqual(metric.labels, {"label1": "value1"})
        
        # Test invalid operations
        with self.assertRaises(ValueError):
            metric.set(10)
        
        with self.assertRaises(ValueError):
            metric.observe(10)
    
    def test_gauge_metric(self):
        """Test gauge metric functionality."""
        metric = Metric(
            name="test_gauge",
            type=MetricType.GAUGE,
            description="A test gauge",
            value=0
        )
        
        # Test set
        metric.set(10)
        self.assertEqual(metric.value, 10)
        
        metric.set(5)
        self.assertEqual(metric.value, 5)
        
        # Test labels
        metric.set(15, labels={"label1": "value1"})
        self.assertEqual(metric.value, 15)
        self.assertEqual(metric.labels, {"label1": "value1"})
        
        # Test invalid operations
        with self.assertRaises(ValueError):
            metric.increment()
        
        with self.assertRaises(ValueError):
            metric.observe(10)
    
    def test_histogram_metric(self):
        """Test histogram metric functionality."""
        metric = Metric(
            name="test_histogram",
            type=MetricType.HISTOGRAM,
            description="A test histogram",
            buckets=[10, 20, 50, 100]
        )
        
        # Test observe
        metric.observe(15)
        metric.observe(30)
        metric.observe(75)
        
        self.assertEqual(len(metric.value), 3)
        
        # Test get_histogram_buckets
        buckets = metric.get_histogram_buckets()
        self.assertEqual(buckets[10], 0)  # 0 values <= 10
        self.assertEqual(buckets[20], 1)  # 1 value <= 20 (15)
        self.assertEqual(buckets[50], 2)  # 2 values <= 50 (15, 30)
        self.assertEqual(buckets[100], 3)  # 3 values <= 100 (15, 30, 75)
        
        # Test get_stats
        stats = metric.get_stats()
        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["sum"], 120)
        self.assertEqual(stats["min"], 15)
        self.assertEqual(stats["max"], 75)
        self.assertEqual(stats["mean"], 40)
        
        # Test labels
        metric.observe(25, labels={"label1": "value1"})
        self.assertEqual(metric.labels, {"label1": "value1"})
        
        # Test invalid operations
        with self.assertRaises(ValueError):
            metric.increment()
        
        with self.assertRaises(ValueError):
            metric.set(10)
    
    def test_summary_metric(self):
        """Test summary metric functionality."""
        metric = Metric(
            name="test_summary",
            type=MetricType.SUMMARY,
            description="A test summary",
            quantiles=[0.5, 0.9, 0.99]
        )
        
        # Test observe
        metric.observe(10)
        metric.observe(20)
        metric.observe(30)
        metric.observe(40)
        metric.observe(50)
        
        self.assertEqual(len(metric.value), 5)
        
        # Test get_summary_quantiles
        quantiles = metric.get_summary_quantiles()
        self.assertEqual(quantiles[0.5], 30)  # Median is 30
        self.assertEqual(quantiles[0.9], 50)  # 90th percentile is 50
        self.assertEqual(quantiles[0.99], 50)  # 99th percentile is 50
        
        # Test get_stats
        stats = metric.get_stats()
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["sum"], 150)
        self.assertEqual(stats["min"], 10)
        self.assertEqual(stats["max"], 50)
        self.assertEqual(stats["mean"], 30)
        
        # Test labels
        metric.observe(25, labels={"label1": "value1"})
        self.assertEqual(metric.labels, {"label1": "value1"})
        
        # Test invalid operations
        with self.assertRaises(ValueError):
            metric.increment()
        
        with self.assertRaises(ValueError):
            metric.set(10)


class TestMetricsCollector(unittest.TestCase):
    """Tests for the MetricsCollector class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a fresh metrics collector for each test
        self.collector = MetricsCollector()
        self.collector.reset()
    
    def test_singleton(self):
        """Test that MetricsCollector is a singleton."""
        collector1 = MetricsCollector()
        collector2 = MetricsCollector()
        
        self.assertIs(collector1, collector2)
    
    def test_create_metrics(self):
        """Test creating metrics."""
        # Create a counter
        counter = self.collector.create_counter("test_counter", "A test counter")
        self.assertEqual(counter.name, "test_counter")
        self.assertEqual(counter.type, MetricType.COUNTER)
        self.assertEqual(counter.description, "A test counter")
        self.assertEqual(counter.value, 0)
        
        # Create a gauge
        gauge = self.collector.create_gauge("test_gauge", "A test gauge")
        self.assertEqual(gauge.name, "test_gauge")
        self.assertEqual(gauge.type, MetricType.GAUGE)
        self.assertEqual(gauge.description, "A test gauge")
        self.assertEqual(gauge.value, 0)
        
        # Create a histogram
        histogram = self.collector.create_histogram("test_histogram", "A test histogram")
        self.assertEqual(histogram.name, "test_histogram")
        self.assertEqual(histogram.type, MetricType.HISTOGRAM)
        self.assertEqual(histogram.description, "A test histogram")
        self.assertEqual(histogram.value, [])
        
        # Create a summary
        summary = self.collector.create_summary("test_summary", "A test summary")
        self.assertEqual(summary.name, "test_summary")
        self.assertEqual(summary.type, MetricType.SUMMARY)
        self.assertEqual(summary.description, "A test summary")
        self.assertEqual(summary.value, [])
        
        # Test duplicate metric
        with self.assertRaises(ValueError):
            self.collector.create_counter("test_counter", "Duplicate counter")
    
    def test_get_metrics(self):
        """Test getting metrics."""
        # Create some metrics
        self.collector.create_counter("test_counter", "A test counter")
        self.collector.create_gauge("test_gauge", "A test gauge")
        
        # Get a specific metric
        counter = self.collector.get_metric("test_counter")
        self.assertEqual(counter.name, "test_counter")
        self.assertEqual(counter.type, MetricType.COUNTER)
        
        # Get all metrics
        metrics = self.collector.get_all_metrics()
        self.assertIn("test_counter", metrics)
        self.assertIn("test_gauge", metrics)
        
        # Get a non-existent metric
        self.assertIsNone(self.collector.get_metric("non_existent"))
    
    def test_update_metrics(self):
        """Test updating metrics."""
        # Create some metrics
        self.collector.create_counter("test_counter", "A test counter")
        self.collector.create_gauge("test_gauge", "A test gauge")
        self.collector.create_histogram("test_histogram", "A test histogram")
        
        # Update counter
        self.collector.increment("test_counter")
        self.assertEqual(self.collector.get_metric("test_counter").value, 1)
        
        self.collector.increment("test_counter", 5)
        self.assertEqual(self.collector.get_metric("test_counter").value, 6)
        
        # Update gauge
        self.collector.set("test_gauge", 10)
        self.assertEqual(self.collector.get_metric("test_gauge").value, 10)
        
        # Update histogram
        self.collector.observe("test_histogram", 15)
        self.assertEqual(len(self.collector.get_metric("test_histogram").value), 1)
        
        # Test non-existent metric
        with self.assertRaises(ValueError):
            self.collector.increment("non_existent")
        
        with self.assertRaises(ValueError):
            self.collector.set("non_existent", 10)
        
        with self.assertRaises(ValueError):
            self.collector.observe("non_existent", 15)
    
    def test_timers(self):
        """Test timer functionality."""
        # Create a histogram for the timer
        self.collector.create_histogram("test_timer", "A test timer")
        
        # Start a timer
        timer_id = self.collector.start_timer("test_timer")
        
        # Sleep briefly
        time.sleep(0.01)
        
        # Stop the timer
        duration = self.collector.stop_timer(timer_id)
        
        # Check that the duration is positive
        self.assertGreater(duration, 0)
        
        # Check that the histogram has a value
        self.assertEqual(len(self.collector.get_metric("test_timer").value), 1)
        
        # Test non-existent timer
        with self.assertRaises(ValueError):
            self.collector.stop_timer("non_existent")
    
    def test_request_tracking(self):
        """Test request tracking functionality."""
        # Track a request
        timer_id = self.collector.track_request("/test")
        
        # Check that the request counters were incremented
        self.assertEqual(self.collector.get_metric("api_requests_total").value, 1)
        self.assertEqual(self.collector.get_metric("api_requests_active").value, 1)
        
        # End the request
        self.collector.track_request_end(timer_id, "/test", 200)
        
        # Check that the active requests counter was decremented
        self.assertEqual(self.collector.get_metric("api_requests_active").value, 0)
        
        # Track an error request
        timer_id = self.collector.track_request("/error")
        self.collector.track_request_end(timer_id, "/error", 500)
        
        # Check that the error counter was incremented
        self.assertEqual(self.collector.get_metric("api_errors_total").value, 1)
    
    def test_error_tracking(self):
        """Test error tracking functionality."""
        # Track an error
        self.collector.track_error("ValueError", "/test")
        
        # Check that the error counter was incremented
        self.assertEqual(self.collector.get_metric("api_errors_total").value, 1)


class TestJSONExporter(unittest.TestCase):
    """Tests for the JSONExporter class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a fresh metrics collector for each test
        self.collector = MetricsCollector()
        self.collector.reset()
        
        # Create an exporter
        self.exporter = JSONExporter(self.collector)
        
        # Create some test metrics
        self.collector.create_counter("test_counter", "A test counter")
        self.collector.increment("test_counter", 5)
        
        self.collector.create_gauge("test_gauge", "A test gauge")
        self.collector.set("test_gauge", 10)
        
        self.collector.create_histogram("test_histogram", "A test histogram")
        self.collector.observe("test_histogram", 15)
        self.collector.observe("test_histogram", 25)
        
        self.collector.create_summary("test_summary", "A test summary")
        self.collector.observe("test_summary", 10)
        self.collector.observe("test_summary", 20)
        self.collector.observe("test_summary", 30)
    
    def test_export(self):
        """Test exporting metrics to JSON."""
        # Export metrics
        json_str = self.exporter.export()
        
        # Parse the JSON
        data = json.loads(json_str)
        
        # Check that all metrics are present
        self.assertIn("test_counter", data)
        self.assertIn("test_gauge", data)
        self.assertIn("test_histogram", data)
        self.assertIn("test_summary", data)
        
        # Check counter values
        self.assertEqual(data["test_counter"]["value"], 5)
        
        # Check gauge values
        self.assertEqual(data["test_gauge"]["value"], 10)
        
        # Check histogram values
        self.assertEqual(data["test_histogram"]["stats"]["count"], 2)
        
        # Check summary values
        self.assertEqual(data["test_summary"]["stats"]["count"], 3)


class TestPrometheusExporter(unittest.TestCase):
    """Tests for the PrometheusExporter class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a fresh metrics collector for each test
        self.collector = MetricsCollector()
        self.collector.reset()
        
        # Create an exporter
        self.exporter = PrometheusExporter(self.collector)
        
        # Create some test metrics
        self.collector.create_counter("test_counter", "A test counter")
        self.collector.increment("test_counter", 5)
        
        self.collector.create_gauge("test_gauge", "A test gauge")
        self.collector.set("test_gauge", 10)
        
        self.collector.create_histogram("test_histogram", "A test histogram")
        self.collector.observe("test_histogram", 15)
        self.collector.observe("test_histogram", 25)
        
        self.collector.create_summary("test_summary", "A test summary")
        self.collector.observe("test_summary", 10)
        self.collector.observe("test_summary", 20)
        self.collector.observe("test_summary", 30)
    
    def test_export(self):
        """Test exporting metrics to Prometheus format."""
        # Export metrics
        prometheus_str = self.exporter.export()
        
        # Check that all metrics are present
        self.assertIn("# HELP test_counter", prometheus_str)
        self.assertIn("# TYPE test_counter counter", prometheus_str)
        self.assertIn("test_counter 5", prometheus_str)
        
        self.assertIn("# HELP test_gauge", prometheus_str)
        self.assertIn("# TYPE test_gauge gauge", prometheus_str)
        self.assertIn("test_gauge 10", prometheus_str)
        
        self.assertIn("# HELP test_histogram", prometheus_str)
        self.assertIn("# TYPE test_histogram histogram", prometheus_str)
        self.assertIn("test_histogram_sum", prometheus_str)
        self.assertIn("test_histogram_count 2", prometheus_str)
        
        self.assertIn("# HELP test_summary", prometheus_str)
        self.assertIn("# TYPE test_summary summary", prometheus_str)
        self.assertIn("test_summary_sum", prometheus_str)
        self.assertIn("test_summary_count 3", prometheus_str)


class TestLogExporter(unittest.TestCase):
    """Tests for the LogExporter class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a fresh metrics collector for each test
        self.collector = MetricsCollector()
        self.collector.reset()
        
        # Create a mock logger
        self.mock_logger = MagicMock()
        
        # Create an exporter
        self.exporter = LogExporter(self.collector, logger=self.mock_logger)
        
        # Create some test metrics
        self.collector.create_counter("test_counter", "A test counter")
        self.collector.increment("test_counter", 5)
        
        self.collector.create_gauge("test_gauge", "A test gauge")
        self.collector.set("test_gauge", 10)
        
        self.collector.create_histogram("test_histogram", "A test histogram")
        self.collector.observe("test_histogram", 15)
        self.collector.observe("test_histogram", 25)
        
        self.collector.create_summary("test_summary", "A test summary")
        self.collector.observe("test_summary", 10)
        self.collector.observe("test_summary", 20)
        self.collector.observe("test_summary", 30)
    
    def test_export(self):
        """Test exporting metrics to logs."""
        # Export metrics
        self.exporter.export()
        
        # Check that the logger was called
        self.assertTrue(self.mock_logger.log.called)
        
        # Check that all metrics were logged
        log_calls = [call[0][1] for call in self.mock_logger.log.call_args_list]
        log_text = " ".join(log_calls)
        
        self.assertIn("test_counter", log_text)
        self.assertIn("test_gauge", log_text)
        self.assertIn("test_histogram", log_text)
        self.assertIn("test_summary", log_text)


@pytest.fixture
def metrics_middleware():
    """Create a MetricsMiddleware instance for testing."""
    collector = MetricsCollector()
    collector.reset()
    return MetricsMiddleware(collector)


@pytest.mark.asyncio
@patch("apifrom.monitoring.metrics.MetricsCollector.track_request")
@patch("apifrom.monitoring.metrics.MetricsCollector.track_request_end")
async def test_request_processing(mock_track_end, mock_track, metrics_middleware):
    """Test request processing."""
    # Mock the track_request method to return a timer ID
    mock_track.return_value = "test_timer"
    
    # Create mock request and response objects
    request = MagicMock()
    response = MagicMock()
    response.status_code = 200
    
    # Process a request
    await metrics_middleware.pre_request(request, "/test")
    
    # Check that track_request was called
    mock_track.assert_called_once_with("/test")
    
    # Process a response
    await metrics_middleware.post_request(request, response)
    
    # Check that track_request_end was called
    mock_track_end.assert_called_once_with("test_timer", "/test", 200)


@pytest.mark.asyncio
@patch("apifrom.monitoring.metrics.MetricsCollector.track_request")
@patch("apifrom.monitoring.metrics.MetricsCollector.track_error")
@patch("apifrom.monitoring.metrics.MetricsCollector.track_request_end")
async def test_error_processing(mock_track_end, mock_track_error, mock_track, metrics_middleware):
    """Test error processing."""
    # Mock the track_request method to return a timer ID
    mock_track.return_value = "test_timer"
    
    # Create a mock request object
    request = MagicMock()
    
    # Process a request
    await metrics_middleware.pre_request(request, "/test")
    
    # Check that track_request was called
    mock_track.assert_called_once_with("/test")
    
    # Process an error
    error = ValueError("Test error")
    await metrics_middleware.on_error(request, error, "/test")
    
    # Check that track_error was called
    mock_track_error.assert_called_once_with("ValueError", "/test")
    
    # Check that track_request_end was called
    mock_track_end.assert_called_once_with("test_timer", "/test", 500)


if __name__ == "__main__":
    unittest.main() 