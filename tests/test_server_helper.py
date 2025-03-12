"""
Helper module for test server functionality.
This module provides a refactored TestServer class that uses factory methods
instead of constructors to avoid pytest collection issues.
"""
import threading
import time
from typing import Optional, Any, Dict, Callable

try:
    from apifrom.core.api import API
    import uvicorn
except ImportError:
    # Mock classes for testing
    class API:
        def __init__(self, *args, **kwargs):
            self.routes = {}
            
        def run(self, *args, **kwargs):
            pass

    class uvicorn:
        @staticmethod
        def run(*args, **kwargs):
            pass


class TestServer:
    """
    A test server for integration testing.
    This class uses factory methods instead of constructors to avoid pytest collection issues.
    """
    
    @classmethod
    def create(cls, api_instance: API, host: str = "127.0.0.1", port: int = 8888):
        """
        Create a new TestServer instance.
        
        Args:
            api_instance: The API instance to serve
            host: The host to bind to
            port: The port to bind to
            
        Returns:
            A new TestServer instance
        """
        server = cls.__new__(cls)
        server.api = api_instance
        server.host = host
        server.port = port
        server.server_thread = None
        server.is_running = False
        return server
    
    def start(self):
        """
        Start the test server in a background thread.
        """
        if self.is_running:
            return
            
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.is_running = True
        
        # Wait for the server to start
        time.sleep(0.5)
    
    def stop(self):
        """
        Stop the test server.
        """
        if not self.is_running:
            return
            
        self.is_running = False
        if self.server_thread:
            self.server_thread.join(timeout=1.0)
            self.server_thread = None
    
    def _run_server(self):
        """
        Run the server in the current thread.
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