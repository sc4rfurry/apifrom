"""
Core application container for APIFromAnything.

This module defines the main API class that serves as the container for all
registered endpoints, middleware, and configuration.
"""

import inspect
import logging
import typing as t
from functools import partial

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route

from apifrom.core.router import Router
from apifrom.middleware.base import BaseMiddleware
from apifrom.core.response import JSONResponse, Response
from apifrom.core.request import Request
from apifrom.docs.openapi import OpenAPIGenerator, OpenAPIConfig
from apifrom.docs.swagger_ui import SwaggerUI, SwaggerUIConfig

logger = logging.getLogger(__name__)


class API:
    """
    Main application container for APIFromAnything.
    
    This class serves as the central registry for all API endpoints, middleware,
    and configuration. It provides methods for registering endpoints, middleware,
    and starting the server.
    
    Attributes:
        router (Router): The router instance for managing routes.
        middleware (list): List of middleware instances.
        debug (bool): Whether to run in debug mode.
        title (str): The title of the API.
        description (str): The description of the API.
        version (str): The version of the API.
        docs_url (str): The URL for the API documentation.
    """
    
    # Class variable to store the current instance
    _current_instance = None
    
    def __init__(
        self,
        debug: bool = False,
        title: str = "APIFromAnything API",
        description: str = "API created with APIFromAnything",
        version: str = "1.0.0",
        docs_url: str = "/docs",
        openapi_config: OpenAPIConfig | None = None,
        swagger_ui_config: SwaggerUIConfig | None = None,
        enable_docs: bool = True,
    ):
        """
        Initialize a new API instance.
        
        Args:
            debug: Whether to run in debug mode.
            title: The title of the API.
            description: The description of the API.
            version: The version of the API.
            docs_url: The URL for the API documentation.
            openapi_config: Configuration for OpenAPI documentation.
            swagger_ui_config: Configuration for Swagger UI.
            enable_docs: Whether to enable API documentation.
        """
        self.router = Router()
        self.middleware = []
        self.debug = debug
        self.title = title
        self.description = description
        self.version = version
        self.docs_url = docs_url
        self.enable_docs = enable_docs
        self._app = None
        
        # Initialize OpenAPI configuration
        self.openapi_config = openapi_config or OpenAPIConfig(
            title=title,
            description=description,
            version=version
        )
        
        # Initialize Swagger UI configuration
        self.swagger_ui_config = swagger_ui_config or SwaggerUIConfig()
        
        # Register built-in middleware
        # self.add_middleware(SomeBuiltInMiddleware())
        
        # Set this instance as the current instance
        API._current_instance = self
        
        logger.info(f"Initialized API: {title} v{version}")
    
    @classmethod
    def _get_current_instance(cls):
        """
        Get the current API instance.
        
        Returns:
            The current API instance, or None if no instance has been created.
        """
        return cls._current_instance
    
    def add_middleware(self, middleware: BaseMiddleware) -> None:
        """
        Add middleware to the API.
        
        Args:
            middleware: The middleware instance to add.
        """
        self.middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__class__.__name__}")
    
    def register_endpoint(
        self,
        handler: t.Callable,
        route: str,
        method: str = "GET",
        name: str | None = None,
        **kwargs
    ) -> None:
        """
        Register an endpoint with the API.
        
        Args:
            handler: The handler function for the endpoint.
            route: The route for the endpoint.
            method: The HTTP method for the endpoint.
            name: The name of the endpoint.
            **kwargs: Additional arguments to pass to the router.
        """
        self.router.add_route(
            handler=handler,
            path=route,
            method=method,
            name=name,
            **kwargs
        )
        logger.debug(f"Registered endpoint: {method} {route}")
    
    def add_route(
        self,
        path: str,
        endpoint: t.Callable | None = None,
        methods: t.Union[t.List[str], str, None] = None,
        name: str | None = None,
        include_in_schema: bool = True,
        **kwargs
    ):
        """
        Add a route to the API.
        
        This method can be used as a decorator or called directly.
        
        Args:
            path: The path for the route.
            endpoint: The endpoint function.
            methods: The HTTP methods for the route.
            name: The name for the route.
            include_in_schema: Whether to include the route in the OpenAPI schema.
            **kwargs: Additional arguments to pass to the router.
        
        Returns:
            The endpoint function if used as a decorator, or None if called directly.
        """
        if endpoint is None:
            # Used as a decorator
            def decorator(func):
                method = methods[0] if isinstance(methods, list) and methods else methods or "GET"
                self.router.add_route(
                    handler=func,
                    path=path,
                    method=method,
                    name=name or func.__name__,
                    include_in_schema=include_in_schema,
                    **kwargs
                )
                return func
            return decorator
        
        # Called directly
        method = methods[0] if isinstance(methods, list) and methods else methods or "GET"
        self.router.add_route(
            handler=endpoint,
            path=path,
            method=method,
            name=name or endpoint.__name__,
            include_in_schema=include_in_schema,
            **kwargs
        )
    
    def add_routes(self, routes: t.List[t.Callable]) -> None:
        """
        Add multiple routes to the API.
        
        This method adds multiple routes to the API at once. The routes should be
        functions decorated with the @api decorator.
        
        Args:
            routes: A list of functions decorated with the @api decorator.
        """
        for route in routes:
            # The @api decorator stores the original function on the wrapper
            if hasattr(route, "__original_func__"):
                # The route is already registered by the @api decorator
                pass
            else:
                # Register the route directly
                self.router.add_route(
                    handler=route,
                    path=f"/{route.__name__}",
                    method="GET",
                    name=route.__name__
                )
    
    def _build_app(self) -> Starlette:
        """
        Build the Starlette application.
        
        Returns:
            The Starlette application instance.
        """
        routes = []
        
        # Convert router routes to Starlette routes
        for route_info in self.router.routes:
            handler = route_info["handler"]
            path = route_info["path"]
            method = route_info["method"]
            name = route_info["name"]
            
            # Create Starlette route
            route = Route(
                path,
                endpoint=handler,
                methods=[method],
                name=name,
            )
            routes.append(route)
        
        # Add documentation routes if enabled
        if self.enable_docs:
            # Create OpenAPI generator
            openapi_generator = OpenAPIGenerator(
                title=self.title,
                description=self.description,
                version=self.version,
                router=self.router,
                config=self.openapi_config
            )
            
            # Create Swagger UI
            swagger_ui = SwaggerUI(
                openapi_generator=openapi_generator,
                url_prefix=self.docs_url,
                config=self.swagger_ui_config
            )
            
            # Add Swagger UI routes
            routes.extend(swagger_ui.setup_routes())
        
        # Create Starlette app
        app = Starlette(
            debug=self.debug,
            routes=routes,
        )
        
        # Add middleware to the app
        for mw in reversed(self.middleware):
            mw.app = app
            app = mw
        
        return app
    
    def run(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        **kwargs
    ) -> None:
        """
        Run the API server.
        
        Args:
            host: The host to bind to.
            port: The port to bind to.
            **kwargs: Additional arguments to pass to uvicorn.run.
        """
        if not self._app:
            self._app = self._build_app()
        
        logger.info(f"Starting API server at http://{host}:{port}")
        uvicorn.run(
            self._app,
            host=host,
            port=port,
            **kwargs
        )
    
    def __call__(self, scope, receive, send):
        """
        ASGI callable.
        
        This method allows the API instance to be used as an ASGI application.
        
        Args:
            scope: The ASGI scope.
            receive: The ASGI receive function.
            send: The ASGI send function.
        """
        if not self._app:
            self._app = self._build_app()
        
        return self._app(scope, receive, send)
    
    async def process_request(self, request: Request) -> Response:
        """
        Process a request and return a response.
        
        This method is used by adapters to process requests without going through
        the ASGI interface.
        
        Args:
            request: The request to process.
            
        Returns:
            The response to the request.
        """
        # Find the matching route
        route_info = self.router.get_route_by_path(request.path, request.method)
        
        if not route_info:
            # Return 404 if no route is found
            logger.error(f"No route found for {request.method} {request.path}")
            return Response(
                content={"error": "Not Found"},
                status_code=404
            )
        
        # Get the handler
        handler = route_info["handler"]
        
        # Extract path parameters
        path_params = route_info.get("path_params", {})
        
        # Set path parameters on the request
        request.path_params = path_params
        
        # Call the handler
        try:
            logger.debug(f"Calling handler {handler.__name__} for {request.method} {request.path}")
            response = handler(request)
            
            # Handle async handlers
            if inspect.iscoroutine(response):
                logger.debug(f"Handler {handler.__name__} returned a coroutine, awaiting it")
                response = await response
                
            logger.debug(f"Handler {handler.__name__} returned {response}")
            return response
        except Exception as e:
            # Return 500 if an error occurs
            logger.error(f"Error calling handler {handler.__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                content={"error": str(e)},
                status_code=500
            ) 