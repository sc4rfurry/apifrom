"""
Logging plugin for APIFromAnything.

This module provides a plugin for logging requests and responses.
"""

import json
import logging
import time
from typing import Dict, Optional

from apifrom.core.app import API
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.plugins.base import Plugin


class LoggingPlugin(Plugin):
    """
    Plugin for logging requests and responses.
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        level: int = logging.INFO,
        log_request_body: bool = False,
        log_response_body: bool = False,
        log_headers: bool = False,
        exclude_paths: list = None,
        exclude_methods: list = None,
    ):
        """
        Initialize the logging plugin.
        
        Args:
            logger: The logger to use (defaults to a new logger)
            level: The logging level
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            log_headers: Whether to log headers
            exclude_paths: Paths to exclude from logging
            exclude_methods: HTTP methods to exclude from logging
        """
        self._name = "logging"
        self.logger = logger or logging.getLogger("apifrom.plugins.logging")
        self.level = level
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.log_headers = log_headers
        self.exclude_paths = exclude_paths or []
        self.exclude_methods = exclude_methods or []
    
    @property
    def name(self) -> str:
        """
        Get the name of the plugin.
        
        Returns:
            The name of the plugin
        """
        return self._name
    
    @property
    def description(self) -> str:
        """
        Get the description of the plugin.
        
        Returns:
            The description of the plugin
        """
        return "Logs requests and responses"
    
    def initialize(self, api: API) -> None:
        """
        Initialize the plugin.
        
        Args:
            api: The API instance
        """
        self.logger.info(f"Initializing {self.name} plugin")
    
    def pre_request(self, request: Request) -> Request:
        """
        Log the request.
        
        Args:
            request: The request object
            
        Returns:
            The request object
        """
        # Skip excluded paths and methods
        if request.path in self.exclude_paths or request.method in self.exclude_methods:
            return request
        
        # Store the start time for calculating duration
        request.state.logging_start_time = time.time()
        
        # Log the request
        log_data = {
            "request": {
                "method": request.method,
                "path": request.path,
                "query_params": request.query_params,
                "client_ip": request.client_ip,
            }
        }
        
        if self.log_headers:
            log_data["request"]["headers"] = dict(request.headers)
        
        if self.log_request_body and request.body:
            try:
                log_data["request"]["body"] = request.json()
            except Exception:
                log_data["request"]["body"] = str(request.body)
        
        self.logger.log(self.level, f"Request: {json.dumps(log_data)}")
        
        return request
    
    def post_response(self, response: Response, request: Request) -> Response:
        """
        Log the response.
        
        Args:
            response: The response object
            request: The request object
            
        Returns:
            The response object
        """
        # Skip excluded paths and methods
        if request.path in self.exclude_paths or request.method in self.exclude_methods:
            return response
        
        # Calculate the request duration
        start_time = getattr(request.state, "logging_start_time", None)
        duration = time.time() - start_time if start_time else None
        
        # Log the response
        log_data = {
            "response": {
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2) if duration else None,
            }
        }
        
        if self.log_headers:
            log_data["response"]["headers"] = dict(response.headers)
        
        if self.log_response_body:
            try:
                log_data["response"]["body"] = response.body
            except Exception:
                log_data["response"]["body"] = str(response.body)
        
        self.logger.log(self.level, f"Response: {json.dumps(log_data)}")
        
        return response
    
    def on_error(self, error: Exception, request: Request) -> Optional[Response]:
        """
        Log an error.
        
        Args:
            error: The error that occurred
            request: The request object
            
        Returns:
            None
        """
        # Skip excluded paths and methods
        if request.path in self.exclude_paths or request.method in self.exclude_methods:
            return None
        
        # Calculate the request duration
        start_time = getattr(request.state, "logging_start_time", None)
        duration = time.time() - start_time if start_time else None
        
        # Log the error
        log_data = {
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "request": {
                    "method": request.method,
                    "path": request.path,
                },
                "duration_ms": round(duration * 1000, 2) if duration else None,
            }
        }
        
        self.logger.error(f"Error: {json.dumps(log_data)}")
        
        return None
    
    def on_startup(self) -> None:
        """
        Log server startup.
        """
        self.logger.info("API server starting up")
    
    def on_shutdown(self) -> None:
        """
        Log server shutdown.
        """
        self.logger.info("API server shutting down") 