"""
Optimization utilities for APIFromAnything.

This module provides tools for analyzing and optimizing API performance,
including optimization configuration, recommendation generation, and auto-tuning.
"""

import time
import logging
import json
import os
from typing import Dict, List, Optional, Set, Any, Union, Tuple, Callable
from enum import Enum, auto
from datetime import datetime
import threading
import asyncio
import inspect
import re
import sys
import psutil
from pathlib import Path
import functools
import platform

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware.base import BaseMiddleware
from apifrom.performance.profiler import APIProfiler, ProfileReport


# Set up logging
logger = logging.getLogger("apifrom.performance.optimization")


class OptimizationLevel(Enum):
    """
    Optimization level for the APIFromAnything application.
    
    This enum defines the level of optimization to apply
    to the APIFromAnything application.
    """
    NONE = auto()
    MINIMAL = auto()
    BALANCED = auto()
    AGGRESSIVE = auto()
    CUSTOM = auto()


class OptimizationConfig:
    """
    Configuration for optimizing APIFromAnything.
    
    This class defines the configuration for optimizing
    the APIFromAnything application for high-load scenarios.
    """
    
    def __init__(self,
                 level: OptimizationLevel = OptimizationLevel.BALANCED,
                 enable_caching: bool = True,
                 enable_connection_pooling: bool = True,
                 enable_profiling: bool = True,
                 enable_request_coalescing: bool = False,
                 enable_request_throttling: bool = False,
                 enable_auto_tuning: bool = True,
                 enable_eager_loading: bool = False,
                 enable_circuit_breaker: bool = False,
                 slow_response_threshold_ms: int = 500,
                 high_memory_threshold_mb: int = 500,
                 high_cpu_threshold_percent: int = 80,
                 high_error_rate_threshold: float = 0.05,
                 optimization_interval: int = 3600):
        """
        Initialize optimization configuration.
        
        Args:
            level: The optimization level
            enable_caching: Whether to enable caching
            enable_connection_pooling: Whether to enable connection pooling
            enable_profiling: Whether to enable profiling
            enable_request_coalescing: Whether to enable request coalescing
            enable_request_throttling: Whether to enable request throttling
            enable_auto_tuning: Whether to enable auto-tuning
            enable_eager_loading: Whether to enable eager loading
            enable_circuit_breaker: Whether to enable circuit breaker
            slow_response_threshold_ms: The slow response threshold in milliseconds
            high_memory_threshold_mb: The high memory threshold in megabytes
            high_cpu_threshold_percent: The high CPU threshold in percent
            high_error_rate_threshold: The high error rate threshold (0.0 to 1.0)
            optimization_interval: The interval between optimizations in seconds
        """
        self.level = level
        self.enable_caching = enable_caching
        self.enable_connection_pooling = enable_connection_pooling
        self.enable_profiling = enable_profiling
        self.enable_request_coalescing = enable_request_coalescing
        self.enable_request_throttling = enable_request_throttling
        self.enable_auto_tuning = enable_auto_tuning
        self.enable_eager_loading = enable_eager_loading
        self.enable_circuit_breaker = enable_circuit_breaker
        self.slow_response_threshold_ms = slow_response_threshold_ms
        self.high_memory_threshold_mb = high_memory_threshold_mb
        self.high_cpu_threshold_percent = high_cpu_threshold_percent
        self.high_error_rate_threshold = high_error_rate_threshold
        self.optimization_interval = optimization_interval
    
    @classmethod
    def create_minimal(cls) -> 'OptimizationConfig':
        """
        Create a minimal optimization configuration.
        
        These settings are optimized for minimal overhead.
        
        Returns:
            OptimizationConfig instance
        """
        return cls(
            level=OptimizationLevel.MINIMAL,
            enable_caching=True,
            enable_connection_pooling=False,
            enable_profiling=False,
            enable_request_coalescing=False,
            enable_request_throttling=False,
            enable_auto_tuning=False,
            enable_eager_loading=False,
            enable_circuit_breaker=False,
            slow_response_threshold_ms=1000,
            high_memory_threshold_mb=1000,
            high_cpu_threshold_percent=90,
            high_error_rate_threshold=0.1,
            optimization_interval=86400  # 24 hours
        )
    
    @classmethod
    def create_balanced(cls) -> 'OptimizationConfig':
        """
        Create a balanced optimization configuration.
        
        These settings provide a balance between performance and overhead.
        
        Returns:
            OptimizationConfig instance
        """
        return cls(
            level=OptimizationLevel.BALANCED,
            enable_caching=True,
            enable_connection_pooling=True,
            enable_profiling=True,
            enable_request_coalescing=False,
            enable_request_throttling=False,
            enable_auto_tuning=True,
            enable_eager_loading=False,
            enable_circuit_breaker=False,
            slow_response_threshold_ms=500,
            high_memory_threshold_mb=500,
            high_cpu_threshold_percent=80,
            high_error_rate_threshold=0.05,
            optimization_interval=3600  # 1 hour
        )
    
    @classmethod
    def create_aggressive(cls) -> 'OptimizationConfig':
        """
        Create an aggressive optimization configuration.
        
        These settings are optimized for maximum performance.
        
        Returns:
            OptimizationConfig instance
        """
        return cls(
            level=OptimizationLevel.AGGRESSIVE,
            enable_caching=True,
            enable_connection_pooling=True,
            enable_profiling=True,
            enable_request_coalescing=True,
            enable_request_throttling=True,
            enable_auto_tuning=True,
            enable_eager_loading=True,
            enable_circuit_breaker=True,
            slow_response_threshold_ms=200,
            high_memory_threshold_mb=250,
            high_cpu_threshold_percent=70,
            high_error_rate_threshold=0.02,
            optimization_interval=900  # 15 minutes
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary.
        
        Returns:
            A dictionary representation of the configuration
        """
        return {
            "level": self.level.name,
            "enable_caching": self.enable_caching,
            "enable_connection_pooling": self.enable_connection_pooling,
            "enable_profiling": self.enable_profiling,
            "enable_request_coalescing": self.enable_request_coalescing,
            "enable_request_throttling": self.enable_request_throttling,
            "enable_auto_tuning": self.enable_auto_tuning,
            "enable_eager_loading": self.enable_eager_loading,
            "enable_circuit_breaker": self.enable_circuit_breaker,
            "slow_response_threshold_ms": self.slow_response_threshold_ms,
            "high_memory_threshold_mb": self.high_memory_threshold_mb,
            "high_cpu_threshold_percent": self.high_cpu_threshold_percent,
            "high_error_rate_threshold": self.high_error_rate_threshold,
            "optimization_interval": self.optimization_interval,
        }
    
    def to_json(self, pretty: bool = True) -> str:
        """
        Convert the configuration to a JSON string.
        
        Args:
            pretty: Whether to format the JSON with indentation
            
        Returns:
            A JSON string representation of the configuration
        """
        indent = 2 if pretty else None
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, file_path: str) -> None:
        """
        Save the configuration to a file.
        
        Args:
            file_path: The path to save the configuration to
        """
        with open(file_path, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def load(cls, file_path: str) -> 'OptimizationConfig':
        """
        Load configuration from a file.
        
        Args:
            file_path: The path to load the configuration from
            
        Returns:
            OptimizationConfig instance
        """
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        
        # Convert level from string to enum
        if "level" in config_dict:
            config_dict["level"] = OptimizationLevel[config_dict["level"]]
        
        return cls(**config_dict)


class OptimizationRecommendation:
    """
    Represents a performance optimization recommendation.
    
    This class provides methods for generating and applying
    optimization recommendations based on performance data.
    """
    
    def __init__(self,
                 title: str,
                 description: str,
                 action: str,
                 priority: int = 3,  # 1 (highest) to 5 (lowest)
                 affected_endpoints: Optional[List[str]] = None,
                 affected_components: Optional[List[str]] = None,
                 estimated_impact: Optional[str] = None,
                 code_examples: Optional[List[str]] = None):
        """
        Initialize an optimization recommendation.
        
        Args:
            title: The recommendation title
            description: The recommendation description
            action: The recommended action
            priority: The recommendation priority (1-5, 1 is highest)
            affected_endpoints: The affected API endpoints
            affected_components: The affected components
            estimated_impact: The estimated impact of the recommendation
            code_examples: Code examples illustrating the recommendation
        """
        self.title = title
        self.description = description
        self.action = action
        self.priority = priority
        self.affected_endpoints = affected_endpoints or []
        self.affected_components = affected_components or []
        self.estimated_impact = estimated_impact
        self.code_examples = code_examples or []
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the recommendation to a dictionary.
        
        Returns:
            A dictionary representation of the recommendation
        """
        return {
            "title": self.title,
            "description": self.description,
            "action": self.action,
            "priority": self.priority,
            "affected_endpoints": self.affected_endpoints,
            "affected_components": self.affected_components,
            "estimated_impact": self.estimated_impact,
            "code_examples": self.code_examples,
            "created_at": self.created_at.isoformat(),
        }
    
    def to_json(self, pretty: bool = True) -> str:
        """
        Convert the recommendation to a JSON string.
        
        Args:
            pretty: Whether to format the JSON with indentation
            
        Returns:
            A JSON string representation of the recommendation
        """
        indent = 2 if pretty else None
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, file_path: str) -> None:
        """
        Save the recommendation to a file.
        
        Args:
            file_path: The path to save the recommendation to
        """
        with open(file_path, 'w') as f:
            f.write(self.to_json())
    
    def print_summary(self) -> None:
        """
        Print a summary of the recommendation to the console.
        """
        print(f"=== Optimization Recommendation: {self.title} ===")
        print(f"Priority: {self.priority} (1-5, 1 is highest)")
        print(f"Description: {self.description}")
        print(f"Action: {self.action}")
        
        if self.affected_endpoints:
            print("\nAffected Endpoints:")
            for endpoint in self.affected_endpoints:
                print(f"- {endpoint}")
        
        if self.affected_components:
            print("\nAffected Components:")
            for component in self.affected_components:
                print(f"- {component}")
        
        if self.estimated_impact:
            print(f"\nEstimated Impact: {self.estimated_impact}")
        
        if self.code_examples:
            print("\nCode Examples:")
            for i, example in enumerate(self.code_examples):
                print(f"\nExample {i+1}:")
                print(example)


class OptimizationAnalyzer:
    """
    Analyzes API performance and generates optimization recommendations.
    
    This class provides tools for analyzing API performance,
    generating optimization recommendations, and applying optimizations.
    """
    
    def __init__(self,
                 config: Optional[OptimizationConfig] = None,
                 profiler: Optional[APIProfiler] = None,
                 output_dir: Optional[str] = None):
        """
        Initialize an optimization analyzer.
        
        Args:
            config: The optimization configuration
            profiler: An existing APIProfiler instance
            output_dir: The directory to save optimization data to
        """
        self.config = config or OptimizationConfig.create_balanced()
        self.profiler = profiler
        self.output_dir = output_dir or os.getcwd()
        self.recommendations = []
        self._lock = threading.Lock()
        self._last_optimization = time.time()
        self._system_stats = {}
        self._api_stats = {}
        self._endpoint_stats = {}
    
    def _get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics.
        
        Returns:
            A dictionary of system statistics
        """
        stats = {}
        
        # Get CPU usage
        stats["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        stats["cpu_count"] = psutil.cpu_count()
        
        # Get memory usage
        memory = psutil.virtual_memory()
        stats["memory_total_mb"] = memory.total / (1024 * 1024)
        stats["memory_available_mb"] = memory.available / (1024 * 1024)
        stats["memory_used_mb"] = memory.used / (1024 * 1024)
        stats["memory_percent"] = memory.percent
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        stats["disk_total_gb"] = disk.total / (1024 * 1024 * 1024)
        stats["disk_used_gb"] = disk.used / (1024 * 1024 * 1024)
        stats["disk_free_gb"] = disk.free / (1024 * 1024 * 1024)
        stats["disk_percent"] = disk.percent
        
        # Get network stats
        net_io = psutil.net_io_counters()
        stats["net_bytes_sent"] = net_io.bytes_sent
        stats["net_bytes_recv"] = net_io.bytes_recv
        stats["net_packets_sent"] = net_io.packets_sent
        stats["net_packets_recv"] = net_io.packets_recv
        
        # Get Python process stats
        process = psutil.Process()
        stats["process_cpu_percent"] = process.cpu_percent(interval=0.1)
        stats["process_memory_mb"] = process.memory_info().rss / (1024 * 1024)
        stats["process_threads"] = process.num_threads()
        stats["process_open_files"] = len(process.open_files())
        stats["process_connections"] = len(process.connections())
        
        return stats
    
    def _analyze_profile_reports(self, reports: List[ProfileReport]) -> List[OptimizationRecommendation]:
        """
        Analyze profile reports and generate optimization recommendations.
        
        Args:
            reports: The profile reports to analyze
            
        Returns:
            A list of optimization recommendations
        """
        recommendations = []
        
        # Sort reports by average response time (descending)
        sorted_reports = sorted(reports, key=lambda r: r.avg_response_time, reverse=True)
        
        # Analyze top 10 slowest endpoints
        for report in sorted_reports[:10]:
            # Check if response time exceeds threshold
            if report.avg_response_time > self.config.slow_response_threshold_ms:
                # Get the report's own recommendations
                report_recommendations = report.get_recommendations()
                
                if report_recommendations:
                    # Create a recommendation from the report's recommendations
                    recommendation = OptimizationRecommendation(
                        title=f"Slow Endpoint: {report.endpoint_name}",
                        description=f"The endpoint {report.endpoint_name} has an average response time of "
                                    f"{report.avg_response_time:.2f} ms, which exceeds the threshold of "
                                    f"{self.config.slow_response_threshold_ms} ms.",
                        action="\n".join(report_recommendations),
                        priority=min(5, max(1, int(report.avg_response_time / self.config.slow_response_threshold_ms))),
                        affected_endpoints=[report.endpoint_name],
                        estimated_impact=f"Reducing response time by "
                                        f"{report.avg_response_time - self.config.slow_response_threshold_ms:.2f} ms "
                                        f"could improve user experience and reduce server load."
                    )
                    recommendations.append(recommendation)
        
        # Check for high p95 response times
        for report in sorted_reports:
            if report.p95_response_time > self.config.slow_response_threshold_ms * 2:
                # Check if we already have a recommendation for this endpoint
                if not any(rec.title == f"High P95 Response Time: {report.endpoint_name}" for rec in recommendations):
                    recommendation = OptimizationRecommendation(
                        title=f"High P95 Response Time: {report.endpoint_name}",
                        description=f"The endpoint {report.endpoint_name} has a 95th percentile response time of "
                                    f"{report.p95_response_time:.2f} ms, which is significantly higher than its "
                                    f"average response time of {report.avg_response_time:.2f} ms.",
                        action="Consider optimizing the worst-case scenarios for this endpoint or implementing "
                                "caching to reduce response time variability.",
                        priority=3,
                        affected_endpoints=[report.endpoint_name],
                        estimated_impact="Reducing response time variability could improve user experience "
                                        "and reduce timeouts."
                    )
                    recommendations.append(recommendation)
        
        # Check for endpoints with high request counts
        sorted_by_requests = sorted(reports, key=lambda r: r.request_count, reverse=True)
        if sorted_by_requests and sorted_by_requests[0].request_count > 1000:
            top_endpoint = sorted_by_requests[0]
            recommendation = OptimizationRecommendation(
                title=f"High Traffic Endpoint: {top_endpoint.endpoint_name}",
                description=f"The endpoint {top_endpoint.endpoint_name} has received {top_endpoint.request_count} "
                            f"requests, which is significantly higher than other endpoints.",
                action="Consider implementing aggressive caching for this endpoint or optimizing its "
                        "performance to reduce server load.",
                priority=2,
                affected_endpoints=[top_endpoint.endpoint_name],
                estimated_impact="Optimizing high-traffic endpoints can significantly reduce overall server load."
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _analyze_system_stats(self) -> List[OptimizationRecommendation]:
        """
        Analyze system statistics and generate optimization recommendations.
        
        Returns:
            A list of optimization recommendations
        """
        recommendations = []
        
        # Check if we have system stats
        if not self._system_stats:
            return recommendations
        
        # Check for high CPU usage
        if self._system_stats.get("cpu_percent", 0) > self.config.high_cpu_threshold_percent:
            recommendation = OptimizationRecommendation(
                title="High CPU Usage",
                description=f"The system CPU usage is {self._system_stats.get('cpu_percent', 0):.2f}%, which "
                            f"exceeds the threshold of {self.config.high_cpu_threshold_percent}%.",
                action="Consider optimizing CPU-intensive operations, implementing caching, or scaling up "
                        "the system to handle the load.",
                priority=1,
                estimated_impact="Reducing CPU usage can improve response times and prevent system overload."
            )
            recommendations.append(recommendation)
        
        # Check for high memory usage
        if self._system_stats.get("memory_percent", 0) > 80:
            recommendation = OptimizationRecommendation(
                title="High Memory Usage",
                description=f"The system memory usage is {self._system_stats.get('memory_percent', 0):.2f}%, "
                            f"which is approaching the maximum capacity.",
                action="Consider optimizing memory-intensive operations, implementing connection pooling, "
                        "or scaling up the system memory to handle the load.",
                priority=1,
                estimated_impact="Reducing memory usage can prevent out-of-memory errors and improve stability."
            )
            recommendations.append(recommendation)
        
        # Check for high process memory usage
        process_memory_mb = self._system_stats.get("process_memory_mb", 0)
        if process_memory_mb > self.config.high_memory_threshold_mb:
            recommendation = OptimizationRecommendation(
                title="High Application Memory Usage",
                description=f"The application is using {process_memory_mb:.2f} MB of memory, which "
                            f"exceeds the threshold of {self.config.high_memory_threshold_mb} MB.",
                action="Consider optimizing memory-intensive operations, implementing connection pooling, "
                        "or scaling up the system memory to handle the load.",
                priority=2,
                estimated_impact="Reducing application memory usage can prevent out-of-memory errors and improve stability."
            )
            recommendations.append(recommendation)
        
        # Check for many open files
        open_files = self._system_stats.get("process_open_files", 0)
        if open_files > 100:
            recommendation = OptimizationRecommendation(
                title="Many Open Files",
                description=f"The application has {open_files} open files, which is unusually high.",
                action="Consider implementing proper resource cleanup, connection pooling, or "
                        "using context managers to ensure resources are released.",
                priority=3,
                estimated_impact="Reducing open files can prevent resource exhaustion and improve stability."
            )
            recommendations.append(recommendation)
        
        # Check for many connections
        connections = self._system_stats.get("process_connections", 0)
        if connections > 50:
            recommendation = OptimizationRecommendation(
                title="Many Open Connections",
                description=f"The application has {connections} open connections, which is unusually high.",
                action="Consider implementing connection pooling or ensuring connections are properly closed.",
                priority=3,
                estimated_impact="Reducing open connections can prevent resource exhaustion and improve stability."
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_general_recommendations(self) -> List[OptimizationRecommendation]:
        """
        Generate general optimization recommendations.
        
        Returns:
            A list of optimization recommendations
        """
        recommendations = []
        
        # Recommend caching if not enabled
        if not self.config.enable_caching:
            recommendation = OptimizationRecommendation(
                title="Enable Response Caching",
                description="Response caching is not enabled, which can lead to unnecessary computation and database queries.",
                action="Consider enabling response caching using the CacheMiddleware or OptimizedCacheMiddleware.",
                priority=3,
                code_examples=[
                    """
from apifrom import API
from apifrom.middleware import CacheMiddleware
from apifrom.performance.cache_optimizer import OptimizedCacheMiddleware

# Create an API instance
app = API(
    title="My API",
    description="My API Description",
    version="1.0.0"
)

# Add cache middleware
app.add_middleware(CacheMiddleware(ttl=60))  # Cache for 60 seconds

# Or use optimized cache middleware for high-load scenarios
from apifrom.middleware.cache_advanced import RedisCacheBackend
cache_backend = RedisCacheBackend(url="redis://localhost:6379/0")
app.add_middleware(OptimizedCacheMiddleware(
    cache_backend=cache_backend,
    ttl=60,
    auto_tune_interval=3600  # Auto-tune every hour
))
"""
                ],
                estimated_impact="Enabling caching can significantly reduce response times and server load for read-heavy operations."
            )
            recommendations.append(recommendation)
        
        # Recommend connection pooling if not enabled
        if not self.config.enable_connection_pooling:
            recommendation = OptimizationRecommendation(
                title="Enable Connection Pooling",
                description="Connection pooling is not enabled, which can lead to resource exhaustion and slow response times.",
                action="Consider enabling connection pooling using the ConnectionPoolMiddleware.",
                priority=3,
                code_examples=[
                    """
from apifrom import API
from apifrom.performance.connection_pool import ConnectionPoolMiddleware

# Create an API instance
app = API(
    title="My API",
    description="My API Description",
    version="1.0.0"
)

# Add connection pool middleware
app.add_middleware(ConnectionPoolMiddleware(
    database_url="postgresql+asyncpg://user:password@localhost/dbname",
    redis_url="redis://localhost:6379/0"
))
"""
                ],
                estimated_impact="Enabling connection pooling can reduce connection overhead and improve response times."
            )
            recommendations.append(recommendation)
        
        # Recommend profiling if not enabled
        if not self.config.enable_profiling:
            recommendation = OptimizationRecommendation(
                title="Enable API Profiling",
                description="API profiling is not enabled, which makes it difficult to identify performance bottlenecks.",
                action="Consider enabling API profiling using the ProfileMiddleware.",
                priority=4,
                code_examples=[
                    """
from apifrom import API
from apifrom.performance.profiler import ProfileMiddleware

# Create an API instance
app = API(
    title="My API",
    description="My API Description",
    version="1.0.0"
)

# Add profile middleware
app.add_middleware(ProfileMiddleware(
    output_dir="./profiles",
    save_interval=3600  # Save profiles every hour
))
"""
                ],
                estimated_impact="Enabling profiling can help identify performance bottlenecks and optimize API performance."
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_code_specific_recommendations(self) -> List[OptimizationRecommendation]:
        """
        Generate code-specific optimization recommendations.
        
        This method analyzes the codebase to find potential performance issues.
        
        Returns:
            A list of optimization recommendations
        """
        recommendations = []
        
        # This is a placeholder for code-specific recommendations
        # In a real implementation, you would analyze the codebase to find potential performance issues
        # and generate recommendations for each issue found
        
        return recommendations
    
    def analyze(self) -> List[OptimizationRecommendation]:
        """
        Analyze API performance and generate optimization recommendations.
        
        Returns:
            A list of optimization recommendations
        """
        # Check if we should optimize
        if time.time() - self._last_optimization < self.config.optimization_interval:
            return self.recommendations
        
        # Get system stats
        self._system_stats = self._get_system_stats()
        
        # Initialize recommendations
        recommendations = []
        
        # Analyze profile reports if available
        if self.profiler:
            reports = self.profiler.get_all_reports()
            recommendations.extend(self._analyze_profile_reports(reports))
        
        # Analyze system stats
        recommendations.extend(self._analyze_system_stats())
        
        # Generate general recommendations
        recommendations.extend(self._generate_general_recommendations())
        
        # Generate code-specific recommendations
        recommendations.extend(self._generate_code_specific_recommendations())
        
        # Sort recommendations by priority
        recommendations.sort(key=lambda r: r.priority)
        
        # Update recommendations
        with self._lock:
            self.recommendations = recommendations
            self._last_optimization = time.time()
        
        # Save recommendations if output directory is set
        if self.output_dir:
            self._save_recommendations()
        
        return recommendations
    
    def get_recommendations(self) -> List[OptimizationRecommendation]:
        """
        Get optimization recommendations.
        
        Returns:
            A list of optimization recommendations
        """
        return self.recommendations
    
    def _save_recommendations(self) -> None:
        """
        Save optimization recommendations to files.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save system stats
        system_stats_path = os.path.join(self.output_dir, f"system_stats_{timestamp}.json")
        with open(system_stats_path, 'w') as f:
            json.dump(self._system_stats, f, indent=2)
        
        # Save recommendations
        recommendations_path = os.path.join(self.output_dir, f"recommendations_{timestamp}.json")
        recommendations_data = [rec.to_dict() for rec in self.recommendations]
        with open(recommendations_path, 'w') as f:
            json.dump(recommendations_data, f, indent=2)
        
        # Save a summary file
        summary_path = os.path.join(self.output_dir, f"optimization_summary_{timestamp}.txt")
        with open(summary_path, 'w') as f:
            f.write(f"Optimization Summary ({timestamp})\n")
            f.write(f"='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='='\n\n")
            
            f.write("System Statistics:\n")
            f.write(f"- CPU Usage: {self._system_stats.get('cpu_percent', 0):.2f}%\n")
            f.write(f"- Memory Usage: {self._system_stats.get('memory_percent', 0):.2f}%\n")
            f.write(f"- Process Memory: {self._system_stats.get('process_memory_mb', 0):.2f} MB\n")
            f.write(f"- Open Files: {self._system_stats.get('process_open_files', 0)}\n")
            f.write(f"- Open Connections: {self._system_stats.get('process_connections', 0)}\n\n")
            
            f.write("Recommendations:\n")
            for i, rec in enumerate(self.recommendations):
                f.write(f"{i+1}. {rec.title} (Priority: {rec.priority})\n")
                f.write(f"   Description: {rec.description}\n")
                f.write(f"   Action: {rec.action}\n")
                if rec.estimated_impact:
                    f.write(f"   Estimated Impact: {rec.estimated_impact}\n")
                f.write("\n")
    
    def print_summary(self) -> None:
        """
        Print a summary of the optimization analysis to the console.
        """
        if not self._system_stats:
            print("No system statistics available. Run analyze() first.")
            return
        
        if not self.recommendations:
            print("No recommendations available. Run analyze() first.")
            return
        
        print("=== Optimization Analysis Summary ===")
        print("\nSystem Statistics:")
        print(f"- CPU Usage: {self._system_stats.get('cpu_percent', 0):.2f}%")
        print(f"- Memory Usage: {self._system_stats.get('memory_percent', 0):.2f}%")
        print(f"- Process Memory: {self._system_stats.get('process_memory_mb', 0):.2f} MB")
        print(f"- Open Files: {self._system_stats.get('process_open_files', 0)}")
        print(f"- Open Connections: {self._system_stats.get('process_connections', 0)}")
        
        print("\nTop Recommendations:")
        for i, rec in enumerate(self.recommendations[:5]):
            print(f"\n{i+1}. {rec.title} (Priority: {rec.priority})")
            print(f"   Description: {rec.description}")
            print(f"   Action: {rec.action}")
            if rec.estimated_impact:
                print(f"   Estimated Impact: {rec.estimated_impact}")
        
        if len(self.recommendations) > 5:
            print(f"\n... and {len(self.recommendations) - 5} more recommendations.")
    
    def get_optimization_config(self) -> OptimizationConfig:
        """
        Get the optimization configuration.
        
        Returns:
            The optimization configuration
        """
        return self.config
    
    def set_optimization_config(self, config: OptimizationConfig) -> None:
        """
        Set the optimization configuration.
        
        Args:
            config: The optimization configuration
        """
        self.config = config


class Web:
    """
    Decorator for optimizing web endpoints.
    
    This decorator applies various optimizations to web endpoints,
    such as caching, profiling, and auto-tuning.
    """
    
    @staticmethod
    def optimize(
        cache_ttl: Optional[int] = None,
        profile: bool = True,
        connection_pool: bool = True,
        auto_tune: bool = True,
        request_coalescing: bool = False,
        coalescing_ttl: int = 30,
        batch_processing: bool = False,
        batch_size: int = 100,
        request_throttling: bool = False,
        eager_loading: bool = False,
        circuit_breaker: bool = False
    ) -> Callable:
        """
        Decorator for optimizing web endpoints.
        
        Args:
            cache_ttl: The cache TTL in seconds (None for no caching)
            profile: Whether to profile the endpoint
            connection_pool: Whether to use connection pooling
            auto_tune: Whether to auto-tune the endpoint
            request_coalescing: Whether to coalesce duplicate requests
            coalescing_ttl: The time-to-live for coalesced requests in seconds
            batch_processing: Whether to enable batch processing
            batch_size: The maximum batch size for batch processing
            request_throttling: Whether to throttle excessive requests
            eager_loading: Whether to eagerly load related resources
            circuit_breaker: Whether to use a circuit breaker
            
        Returns:
            A decorated function
        """
        def decorator(func):
            # Mark the function with optimization metadata
            func.__optimization__ = {
                "cache_ttl": cache_ttl,
                "profile": profile,
                "connection_pool": connection_pool,
                "auto_tune": auto_tune,
                "request_coalescing": request_coalescing,
                "coalescing_ttl": coalescing_ttl,
                "batch_processing": batch_processing,
                "batch_size": batch_size,
                "request_throttling": request_throttling,
                "eager_loading": eager_loading,
                "circuit_breaker": circuit_breaker,
            }
            
            # Apply request coalescing if enabled
            if request_coalescing:
                # Use the coalesce_requests decorator
                from apifrom.performance.request_coalescing import coalesce_requests
                func = coalesce_requests(ttl=coalescing_ttl)(func)
            
            # Apply batch processing if enabled
            if batch_processing:
                # Use the batch_process decorator
                from apifrom.performance.batch_processing import batch_process
                
                # Define a function to process batches
                async def process_batch(batch):
                    # Batch is a list of (args, kwargs) tuples
                    results = []
                    for args, kwargs in batch:
                        # Call the original function with the arguments
                        result = await func(*args, **kwargs)
                        results.append(result)
                    return results
                
                func = batch_process(
                    process_func=process_batch,
                    max_batch_size=batch_size
                )(func)
            
            # Continue with the normal decorator chain
            return func
        
        return decorator
    
    @staticmethod
    def is_optimized(func: Callable) -> bool:
        """
        Check if a function is optimized.
        
        Args:
            func: The function to check
            
        Returns:
            True if the function is optimized, False otherwise
        """
        return hasattr(func, "__optimization__")
    
    @staticmethod
    def get_optimization_config(func: Callable) -> Dict[str, Any]:
        """
        Get the optimization configuration for a function.
        
        Args:
            func: The function to get the configuration for
            
        Returns:
            The optimization configuration dictionary, or an empty dictionary if not optimized
        """
        return getattr(func, "__optimization__", {})
    
    @staticmethod
    def create_default_web_optimization():
        """
        Create a default web optimization decorator.
        
        Returns:
            A default web optimization decorator with balanced settings
        """
        return Web.optimize(
            cache_ttl=60,
            profile=True,
            connection_pool=True,
            auto_tune=True,
            request_coalescing=False,
            batch_processing=False,
        ) 