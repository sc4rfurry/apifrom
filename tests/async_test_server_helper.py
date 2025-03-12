"""
Helper module for async test server functionality.
This module provides a refactored AsyncTestServer class that uses factory methods
instead of constructors to avoid pytest collection issues and properly handles async operations.
"""
import threading
import time
import asyncio
from typing import Optional, Any, Dict, Callable, Awaitable

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
            
        async def handle_request(self, *args, **kwargs):
            pass

    class uvicorn:
        @staticmethod
        def run(*args, **kwargs):
            pass


class AsyncTestServer:
    """
    An async-compatible test server for integration testing.
    This class uses factory methods instead of constructors to avoid pytest collection issues
    and properly handles async operations.
    """
    
    @classmethod
    def create(cls, api_instance: API, host: str = "127.0.0.1", port: int = 8888):
        """
        Create a new AsyncTestServer instance.
        
        Args:
            api_instance: The API instance to serve
            host: The host to bind to
            port: The port to bind to
            
        Returns:
            A new AsyncTestServer instance
        """
        server = cls.__new__(cls)
        server.api = api_instance
        server.host = host
        server.port = port
        server.server_thread = None
        server.is_running = False
        server.loop = asyncio.new_event_loop()
        return server
    
    async def start(self):
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
        await asyncio.sleep(0.5)
    
    async def stop(self):
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
        asyncio.set_event_loop(self.loop)
        self.api.run(host=self.host, port=self.port)
    
    async def __aenter__(self):
        """
        Start the server when entering an async context.
        """
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Stop the server when exiting an async context.
        """
        await self.stop()
        
    async def request(self, method: str, path: str, query_params: Optional[Dict] = None, 
                     headers: Optional[Dict] = None, body: Optional[Any] = None):
        """
        Make a request to the server.
        
        Args:
            method: The HTTP method
            path: The request path
            query_params: Query parameters
            headers: Request headers
            body: Request body
            
        Returns:
            The response from the server
        """
        # Create a request object
        request = {
            "method": method,
            "path": path,
            "query_params": query_params or {},
            "headers": headers or {},
            "body": body
        }
        
        # Handle the request
        return await self.api.handle_request(request) 