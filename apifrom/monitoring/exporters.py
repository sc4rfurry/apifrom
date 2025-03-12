"""
Exporters for metrics data in APIFromAnything.

This module provides exporters for converting metrics data to various formats
and integrating with popular monitoring systems like Prometheus, Grafana, etc.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union

from apifrom.monitoring.metrics import MetricsCollector, Metric, MetricType


class MetricsExporter(ABC):
    """Base class for all metrics exporters."""
    
    def __init__(self, collector: Optional[MetricsCollector] = None):
        """Initialize the exporter with a metrics collector."""
        self.collector = collector or MetricsCollector()
    
    @abstractmethod
    def export(self, **kwargs) -> Any:
        """Export metrics in the specific format."""
        pass


class JSONExporter(MetricsExporter):
    """Exports metrics data in JSON format."""
    
    def export(self, pretty: bool = False) -> str:
        """
        Export metrics as JSON.
        
        Args:
            pretty: Whether to format the JSON with indentation for readability.
            
        Returns:
            JSON string representation of the metrics.
        """
        metrics = self.collector.get_all_metrics()
        result = {}
        
        for name, metric in metrics.items():
            metric_data = {
                "name": metric.name,
                "type": metric.type.value,
                "description": metric.description,
                "labels": metric.labels,
            }
            
            if metric.type == MetricType.COUNTER or metric.type == MetricType.GAUGE:
                metric_data["value"] = metric.value
            elif metric.type == MetricType.HISTOGRAM:
                metric_data["buckets"] = metric.get_histogram_buckets()
                metric_data["stats"] = metric.get_stats()
            elif metric.type == MetricType.SUMMARY:
                metric_data["quantiles"] = metric.get_summary_quantiles()
                metric_data["stats"] = metric.get_stats()
                
            result[name] = metric_data
            
        indent = 2 if pretty else None
        return json.dumps(result, indent=indent)
    
    def export_to_file(self, file_path: str, pretty: bool = True) -> None:
        """
        Export metrics to a JSON file.
        
        Args:
            file_path: Path to the output file.
            pretty: Whether to format the JSON with indentation for readability.
        """
        with open(file_path, 'w') as f:
            f.write(self.export(pretty=pretty))


class PrometheusExporter(MetricsExporter):
    """Exports metrics in Prometheus text format."""
    
    def export(self, **kwargs) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            String in Prometheus exposition format.
        """
        metrics = self.collector.get_all_metrics()
        lines = []
        
        for name, metric in metrics.items():
            # Add metric metadata (HELP and TYPE)
            lines.append(f"# HELP {name} {metric.description}")
            lines.append(f"# TYPE {name} {metric.type.value}")
            
            if metric.type == MetricType.COUNTER or metric.type == MetricType.GAUGE:
                # Format labels if present
                labels_str = self._format_labels(metric.labels)
                lines.append(f"{name}{labels_str} {metric.value}")
                
            elif metric.type == MetricType.HISTOGRAM:
                # Add bucket entries
                buckets = metric.get_histogram_buckets()
                stats = metric.get_stats()
                
                for bucket, count in buckets.items():
                    labels = dict(metric.labels)
                    labels["le"] = str(bucket)
                    labels_str = self._format_labels(labels)
                    lines.append(f"{name}_bucket{labels_str} {count}")
                
                # Add sum and count
                labels_str = self._format_labels(metric.labels)
                lines.append(f"{name}_sum{labels_str} {stats['sum']}")
                lines.append(f"{name}_count{labels_str} {stats['count']}")
                
            elif metric.type == MetricType.SUMMARY:
                # Add quantile entries
                quantiles = metric.get_summary_quantiles()
                stats = metric.get_stats()
                
                for quantile, value in quantiles.items():
                    labels = dict(metric.labels)
                    labels["quantile"] = str(quantile)
                    labels_str = self._format_labels(labels)
                    lines.append(f"{name}{labels_str} {value}")
                
                # Add sum and count
                labels_str = self._format_labels(metric.labels)
                lines.append(f"{name}_sum{labels_str} {stats['sum']}")
                lines.append(f"{name}_count{labels_str} {stats['count']}")
        
        return "\n".join(lines)
    
    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus exposition format."""
        if not labels:
            return ""
            
        label_parts = [f'{k}="{v}"' for k, v in labels.items()]
        return "{" + ",".join(label_parts) + "}"
    
    def export_to_file(self, file_path: str) -> None:
        """
        Export metrics to a file in Prometheus text format.
        
        Args:
            file_path: Path to the output file.
        """
        with open(file_path, 'w') as f:
            f.write(self.export())
    
    def serve_metrics(self, host: str = "localhost", port: int = 8000, endpoint: str = "/metrics") -> None:
        """
        Start a simple HTTP server to expose metrics for Prometheus scraping.
        
        Args:
            host: Host to bind the server to.
            port: Port to listen on.
            endpoint: URL endpoint for metrics.
        """
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        metrics_exporter = self
        
        class PrometheusHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == endpoint:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; version=0.0.4")
                    self.end_headers()
                    self.wfile.write(metrics_exporter.export().encode())
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Not Found")
        
        server = HTTPServer((host, port), PrometheusHandler)
        print(f"Starting Prometheus metrics server on http://{host}:{port}{endpoint}")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


class LogExporter(MetricsExporter):
    """Exports metrics to Python's logging system."""
    
    def __init__(self, collector: Optional[MetricsCollector] = None, 
                 logger: Optional[logging.Logger] = None,
                 level: int = logging.INFO):
        """
        Initialize the log exporter.
        
        Args:
            collector: Metrics collector to export from.
            logger: Logger to use for logging metrics.
            level: Logging level to use.
        """
        super().__init__(collector)
        self.logger = logger or logging.getLogger("apifrom.metrics")
        self.level = level
    
    def export(self, include_details: bool = False, **kwargs) -> None:
        """
        Export metrics to logs.
        
        Args:
            include_details: Whether to include detailed metrics information.
        """
        metrics = self.collector.get_all_metrics()
        
        self.logger.log(self.level, f"APIFromAnything Metrics Report - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        for name, metric in metrics.items():
            if metric.type == MetricType.COUNTER or metric.type == MetricType.GAUGE:
                self.logger.log(self.level, f"{name} ({metric.type.value}): {metric.value} {metric.labels}")
                
            elif metric.type == MetricType.HISTOGRAM:
                stats = metric.get_stats()
                self.logger.log(self.level, f"{name} ({metric.type.value}): count={stats['count']}, "
                               f"min={stats['min']:.2f}, max={stats['max']:.2f}, "
                               f"mean={stats['mean']:.2f}, median={stats['median']:.2f} {metric.labels}")
                
            elif metric.type == MetricType.SUMMARY:
                stats = metric.get_stats()
                self.logger.log(self.level, f"{name} ({metric.type.value}): count={stats['count']}, "
                               f"min={stats['min']:.2f}, max={stats['max']:.2f}, "
                               f"mean={stats['mean']:.2f} {metric.labels}")
    
    def export_periodic(self, interval_seconds: int = 60, include_details: bool = False) -> None:
        """
        Start a background thread to periodically export metrics to logs.
        
        Args:
            interval_seconds: Interval between exports in seconds.
            include_details: Whether to include detailed metrics information.
        """
        import threading
        
        def _export_loop():
            while True:
                self.export(include_details=include_details)
                time.sleep(interval_seconds)
        
        thread = threading.Thread(target=_export_loop, daemon=True)
        thread.start()
        
        return thread 