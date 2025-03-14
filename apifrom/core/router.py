"""
Router module for APIFromAnything.

This module defines the Router class that manages the registration and lookup
of API endpoints.
"""

import inspect
import logging
import re
import typing as t
from functools import wraps

from apifrom.utils.type_utils import get_type_hints_with_extras

logger = logging.getLogger(__name__)


class Router:
    """
    Router for managing API endpoints.
    
    This class is responsible for registering and looking up API endpoints.
    It maintains a registry of routes and their associated handlers.
    
    Attributes:
        routes (list): List of registered routes.
    """
    
    def __init__(self):
        """Initialize a new Router instance."""
        self.routes = []
    
    def add_route(
        self,
        handler: t.Callable,
        path: t.Optional[str] = None,
        method: str = "GET",
        name: t.Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Add a route to the router.
        
        Args:
            handler: The function to handle the route.
            path: The URL path for the route. If None, derived from handler name.
            method: The HTTP method for the route.
            name: The name for the route. If None, derived from handler name.
            **kwargs: Additional arguments to associate with the route.
        """
        if path is None:
            # Convert function name to path
            # e.g., get_user -> /get-user
            path = "/" + handler.__name__.replace("_", "-")
        
        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path
        
        # Extract path parameters from function signature
        sig = inspect.signature(handler)
        path_params = {}
        
        for param_name, param in sig.parameters.items():
            # Skip self, cls, and **kwargs
            if param_name in ("self", "cls") or param.kind == param.VAR_KEYWORD:
                continue
            
            # Check if parameter is in path
            if "{" + param_name + "}" in path:
                path_params[param_name] = param
            
            # If not in path and no default, add as query parameter
            # This will be handled by the decorator
        
        if name is None:
            name = handler.__name__
        
        # Get type hints for validation
        type_hints = get_type_hints_with_extras(handler)
        
        # Store route information
        route_info = {
            "handler": handler,
            "path": path,
            "method": method.upper(),
            "name": name,
            "path_params": path_params,
            "type_hints": type_hints,
            **kwargs
        }
        
        self.routes.append(route_info)
        logger.debug(f"Added route: {method.upper()} {path}")
    
    def get_route_by_path(self, path: str, method: str = "GET") -> t.Optional[dict]:
        """
        Get a route by path and method.
        
        Args:
            path: The path to match.
            method: The HTTP method to match.
            
        Returns:
            The route info if found, None otherwise.
        """
        # Normalize method
        method = method.upper()
        
        # First, try exact match
        for route in self.routes:
            if route["path"] == path and route["method"] == method:
                return route
        
        # If no exact match, try pattern matching
        for route in self.routes:
            if route["method"] != method:
                continue
            
            pattern = route["path"]
            pattern = re.sub(r"{([^}]+)}", r"(?P<\1>[^/]+)", pattern)
            pattern = f"^{pattern}$"
            
            match = re.match(pattern, path)
            if match:
                # Extract path parameters
                path_params = match.groupdict()
                
                # Create a copy of the route with the extracted path parameters
                route_copy = route.copy()
                route_copy["path_params"] = path_params
                
                return route_copy
        
        return None
    
    def get_route_handler(self, path: str, method: str = "GET") -> t.Optional[t.Callable]:
        """
        Get a route handler by path and method.
        
        Args:
            path: The path to match.
            method: The HTTP method to match.
            
        Returns:
            The handler function if found, None otherwise.
        """
        route = self.get_route_by_path(path, method)
        if route:
            return route["handler"]
        return None 