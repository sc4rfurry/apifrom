"""APIFromAnything module for generating APIs from Python functions."""

from typing import Dict, Any, Optional, Union, List, Callable
import inspect


class APIFromAnything:
    """Core class for transforming Python functions into REST API endpoints.
    
    The APIFromAnything class provides functionality to automatically generate
    REST API endpoints from existing Python functions using type hints for
    validation and documentation.
    
    Attributes:
        config (Dict[str, Any]): Configuration dictionary for customizing API behavior.
        routes (Dict[str, Dict]): Dictionary mapping routes to handler configurations.
        middleware (List[Callable]): List of middleware functions to apply to requests.
        
    Examples:
        Basic usage:
        
        >>> from apifrom import APIFromAnything
        >>> api = APIFromAnything()
        >>> 
        >>> @api.route("/hello/{name}")
        >>> def hello(name: str, greeting: str = "Hello") -> Dict[str, str]:
        >>>     return {"message": f"{greeting}, {name}!"}
        >>> 
        >>> # Start the API server
        >>> api.serve(host="localhost", port=8000)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the API generator.
        
        Args:
            config (Dict[str, Any], optional): Configuration options for the API.
                Includes settings for authentication, rate limiting, CORS, etc.
                Defaults to None.
                
        Note:
            If config is None, default configuration values will be used.
        """
        self.config = config or {}
        self.routes = {}
        self.middleware = []
        self._initialize_defaults()
        
    def _initialize_defaults(self) -> None:
        """Set up default configuration values.
        
        This internal method initializes default values for various configuration
        settings if they aren't explicitly provided in the config dictionary.
        """
        defaults = {
            "cors": {"enabled": False},
            "authentication": {"enabled": False, "type": None},
            "rate_limiting": {"enabled": False, "limit": 100, "period": 60},
            "documentation": {"enabled": True, "title": "API Documentation"},
            "logging": {"level": "INFO", "format": "standard"}
        }
        
        for key, default_value in defaults.items():
            if key not in self.config:
                self.config[key] = default_value
        
    def generate_api(self, source: Union[Callable, object, str]) -> Dict[str, Any]:
        """Generate API from the provided source.
        
        Analyzes the provided source (function, class, or module) and generates
        API route configurations based on the source's structure and type hints.
        
        Args:
            source: The source to generate API endpoints from. Can be:
                - A function: Creates a single endpoint
                - A class: Creates endpoints for each public method
                - A module: Creates endpoints for all functions and classes
                - A string: Path to a Python file to analyze
                
        Returns:
            Dict[str, Any]: A dictionary containing the generated API configuration.
            
        Raises:
            TypeError: If the source type is not supported.
            ValueError: If the source cannot be parsed or contains invalid types.
            
        Examples:
            Generate API from a function:
            
            >>> def user_info(user_id: int) -> Dict[str, Any]:
            >>>     return {"id": user_id, "name": f"User {user_id}"}
            >>> 
            >>> api = APIFromAnything()
            >>> api_config = api.generate_api(user_info)
        """
        result = {"endpoints": [], "schemas": {}}
        
        if callable(source) and not inspect.isclass(source):
            # Handle function
            endpoint = self._analyze_function(source)
            result["endpoints"].append(endpoint)
        elif inspect.isclass(source):
            # Handle class
            for name, method in inspect.getmembers(source, predicate=inspect.isfunction):
                if not name.startswith('_'):  # Skip private methods
                    endpoint = self._analyze_function(method)
                    result["endpoints"].append(endpoint)
        elif isinstance(source, str):
            # Handle file path
            pass  # Implementation would load and analyze the Python file
        else:
            raise TypeError(f"Unsupported source type: {type(source)}")
            
        return result
        
    def _analyze_function(self, func: Callable) -> Dict[str, Any]:
        """Analyze a function and create an API endpoint configuration.
        
        Args:
            func: The function to analyze.
            
        Returns:
            Dict[str, Any]: Endpoint configuration dictionary.
        """
        signature = inspect.signature(func)
        doc = inspect.getdoc(func) or ""
        
        endpoint = {
            "name": func.__name__,
            "path": f"/{func.__name__}",
            "method": "GET",
            "description": doc,
            "parameters": [],
            "response": None
        }
        
        # Analyze parameters
        for name, param in signature.parameters.items():
            if name == "self":
                continue
                
            parameter = {
                "name": name,
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "any",
                "required": param.default == inspect.Parameter.empty,
                "default": None if param.default == inspect.Parameter.empty else param.default
            }
            endpoint["parameters"].append(parameter)
            
        # Analyze return type
        if signature.return_annotation != inspect.Signature.empty:
            endpoint["response"] = str(signature.return_annotation)
            
        return endpoint
        
    def export_api(self, format: str = 'openapi') -> Dict[str, Any]:
        """Export the generated API in the specified format.
        
        Args:
            format (str, optional): The format to export the API in.
                Supported formats include:
                - 'openapi': OpenAPI/Swagger specification
                - 'raml': RAML specification
                - 'postman': Postman collection
                Defaults to 'openapi'.
                
        Returns:
            Dict[str, Any]: The API specification in the requested format.
            
        Raises:
            ValueError: If the requested format is not supported.
            
        Examples:
            Export as OpenAPI specification:
            
            >>> api = APIFromAnything()
            >>> # ... add routes
            >>> openapi_spec = api.export_api(format='openapi')
            >>> with open('openapi.json', 'w') as f:
            >>>     json.dump(openapi_spec, f)
        """
        if format.lower() not in ['openapi', 'raml', 'postman']:
            raise ValueError(f"Unsupported export format: {format}")
            
        # Implementation would convert the internal route representations
        # to the specified format
        
        result = {
            "format": format,
            "specification": {},
            "version": "1.0.0"
        }
        
        return result
        
    def route(self, path: str, methods: List[str] = None, **options) -> Callable:
        """Decorator for registering routes with the API.
        
        Args:
            path (str): URL path pattern for the route.
            methods (List[str], optional): HTTP methods supported by this route.
                Defaults to ["GET"].
            **options: Additional route options like rate limiting, auth requirements.
            
        Returns:
            Callable: Decorator function that registers the decorated function.
            
        Examples:
            >>> api = APIFromAnything()
            >>> 
            >>> @api.route("/users/{user_id}", methods=["GET"])
            >>> def get_user(user_id: int) -> Dict[str, Any]:
            >>>     return {"id": user_id, "name": f"User {user_id}"}
        """
        methods = methods or ["GET"]
        
        def decorator(func):
            endpoint = self._analyze_function(func)
            endpoint["path"] = path
            endpoint["method"] = methods
            endpoint["options"] = options
            
            self.routes[path] = {
                "handler": func,
                "config": endpoint
            }
            
            return func
            
        return decorator
        
    def add_middleware(self, middleware_func: Callable) -> None:
        """Add middleware to the API request processing pipeline.
        
        Args:
            middleware_func (Callable): Middleware function to add.
                The function should accept (request, next_handler) parameters.
                
        Examples:
            >>> api = APIFromAnything()
            >>> 
            >>> @api.add_middleware
            >>> async def logging_middleware(request, next_handler):
            >>>     print(f"Request to {request.path}")
            >>>     response = await next_handler(request)
            >>>     print(f"Response status: {response.status}")
            >>>     return response
        """
        self.middleware.append(middleware_func)
        
    def serve(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """Start the API server.
        
        Args:
            host (str, optional): Host address to bind the server to.
                Defaults to "127.0.0.1".
            port (int, optional): Port number to listen on.
                Defaults to 8000.
                
        Examples:
            >>> api = APIFromAnything()
            >>> # ... configure routes
            >>> api.serve(host="0.0.0.0", port=5000)
        """
        print(f"Starting API server on http://{host}:{port}")
        # Implementation would start a web server using the configured routes
