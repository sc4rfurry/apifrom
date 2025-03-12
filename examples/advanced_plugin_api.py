"""
Advanced plugin system example using APIFromAnything.

This example demonstrates the enhanced plugin system of the APIFromAnything library,
showcasing features like lifecycle hooks, dependency injection, configuration management,
and event handling.
"""

import logging
import time
from typing import Dict, List, Optional, Any

from apifrom import API, api
from apifrom.plugins.base import (
    Plugin, 
    PluginManager, 
    PluginMetadata, 
    PluginConfig, 
    PluginEvent, 
    PluginPriority,
    PluginHook,
)
from apifrom.core.request import Request
from apifrom.core.response import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create API instance
app = API(
    title="Advanced Plugin API Example",
    description="An API demonstrating the advanced plugin system of APIFromAnything",
    version="1.0.0",
    debug=True
)

# Create a custom hook for the API
request_transformation_hook = app.plugin_manager.register_hook(
    "request_transformation",
    "Transform the request before it is processed by the API"
)

response_transformation_hook = app.plugin_manager.register_hook(
    "response_transformation",
    "Transform the response before it is sent to the client"
)

# Define a base plugin that other plugins can depend on
class LoggingPlugin(Plugin):
    """
    Plugin for logging API requests and responses.
    """
    
    def get_metadata(self) -> PluginMetadata:
        """
        Get the metadata for this plugin.
        
        Returns:
            The plugin metadata
        """
        return PluginMetadata(
            name="logging",
            version="1.0.0",
            description="Logs API requests and responses",
            author="APIFromAnything Team",
            tags=["logging", "utility"]
        )
    
    def get_config(self) -> PluginConfig:
        """
        Get the configuration for this plugin.
        
        Returns:
            The plugin configuration
        """
        return PluginConfig(
            defaults={
                "log_request_headers": True,
                "log_request_body": False,
                "log_response_headers": True,
                "log_response_body": False,
                "log_level": "INFO",
            },
            schema={
                "type": "object",
                "properties": {
                    "log_request_headers": {"type": "boolean"},
                    "log_request_body": {"type": "boolean"},
                    "log_response_headers": {"type": "boolean"},
                    "log_response_body": {"type": "boolean"},
                    "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
                },
            }
        )
    
    def initialize(self, api: API) -> None:
        """
        Initialize the plugin.
        
        Args:
            api: The API instance
        """
        super().initialize(api)
        self.logger.info(f"Initializing {self.metadata.name} plugin")
        
        # Set the log level
        log_level = getattr(logging, self.config.get("log_level", "INFO"))
        self.logger.setLevel(log_level)
    
    async def pre_request(self, request: Request) -> Request:
        """
        Log the request.
        
        Args:
            request: The request object
            
        Returns:
            The request object
        """
        self.logger.info(f"Request: {request.method} {request.path}")
        
        if self.config.get("log_request_headers"):
            self.logger.debug(f"Request headers: {request.headers}")
        
        if self.config.get("log_request_body") and request.body:
            self.logger.debug(f"Request body: {request.body}")
        
        # Store the start time for calculating duration
        request.state.logging_start_time = time.time()
        
        return request
    
    async def post_response(self, response: Response, request: Request) -> Response:
        """
        Log the response.
        
        Args:
            response: The response object
            request: The request object
            
        Returns:
            The response object
        """
        # Calculate the request duration
        start_time = getattr(request.state, "logging_start_time", None)
        duration = time.time() - start_time if start_time else None
        
        self.logger.info(f"Response: {response.status_code} ({duration:.2f}s)")
        
        if self.config.get("log_response_headers"):
            self.logger.debug(f"Response headers: {response.headers}")
        
        if self.config.get("log_response_body") and hasattr(response, "body"):
            self.logger.debug(f"Response body: {response.body}")
        
        return response
    
    async def on_event(self, event: PluginEvent, **kwargs) -> None:
        """
        Handle events.
        
        Args:
            event: The event that occurred
            **kwargs: Additional event data
        """
        self.logger.debug(f"Event: {event.value}")


# Define a plugin that depends on the logging plugin
class MetricsPlugin(Plugin):
    """
    Plugin for collecting API metrics.
    """
    
    def get_metadata(self) -> PluginMetadata:
        """
        Get the metadata for this plugin.
        
        Returns:
            The plugin metadata
        """
        return PluginMetadata(
            name="metrics",
            version="1.0.0",
            description="Collects API metrics",
            author="APIFromAnything Team",
            dependencies=["logging"],
            tags=["metrics", "monitoring"]
        )
    
    def get_config(self) -> PluginConfig:
        """
        Get the configuration for this plugin.
        
        Returns:
            The plugin configuration
        """
        return PluginConfig(
            defaults={
                "collect_request_metrics": True,
                "collect_response_metrics": True,
                "collect_error_metrics": True,
            }
        )
    
    def initialize(self, api: API) -> None:
        """
        Initialize the plugin.
        
        Args:
            api: The API instance
        """
        super().initialize(api)
        self.logger.info(f"Initializing {self.metadata.name} plugin")
        
        # Get the logging plugin
        self.logging_plugin = api.plugin_manager.get_plugin("logging")
        
        # Initialize metrics
        self.request_count = 0
        self.response_count = 0
        self.error_count = 0
        self.response_times = []
    
    async def pre_request(self, request: Request) -> Request:
        """
        Collect request metrics.
        
        Args:
            request: The request object
            
        Returns:
            The request object
        """
        if self.config.get("collect_request_metrics"):
            self.request_count += 1
            self.logger.debug(f"Request count: {self.request_count}")
        
        return request
    
    async def post_response(self, response: Response, request: Request) -> Response:
        """
        Collect response metrics.
        
        Args:
            response: The response object
            request: The request object
            
        Returns:
            The response object
        """
        if self.config.get("collect_response_metrics"):
            self.response_count += 1
            
            # Calculate the request duration
            start_time = getattr(request.state, "logging_start_time", None)
            if start_time:
                duration = time.time() - start_time
                self.response_times.append(duration)
                self.logger.debug(f"Response time: {duration:.2f}s")
        
        return response
    
    async def on_error(self, error: Exception, request: Request) -> Optional[Response]:
        """
        Collect error metrics.
        
        Args:
            error: The error that occurred
            request: The request object
            
        Returns:
            None
        """
        if self.config.get("collect_error_metrics"):
            self.error_count += 1
            self.logger.debug(f"Error count: {self.error_count}")
        
        return None
    
    async def on_event(self, event: PluginEvent, **kwargs) -> None:
        """
        Handle events.
        
        Args:
            event: The event that occurred
            **kwargs: Additional event data
        """
        if event == PluginEvent.SERVER_STOPPING:
            # Log metrics summary when the server is stopping
            self.logger.info("Metrics summary:")
            self.logger.info(f"  Request count: {self.request_count}")
            self.logger.info(f"  Response count: {self.response_count}")
            self.logger.info(f"  Error count: {self.error_count}")
            
            if self.response_times:
                avg_response_time = sum(self.response_times) / len(self.response_times)
                self.logger.info(f"  Average response time: {avg_response_time:.2f}s")


# Define a plugin that uses hooks
class RequestTransformerPlugin(Plugin):
    """
    Plugin for transforming requests and responses.
    """
    
    def get_metadata(self) -> PluginMetadata:
        """
        Get the metadata for this plugin.
        
        Returns:
            The plugin metadata
        """
        return PluginMetadata(
            name="request_transformer",
            version="1.0.0",
            description="Transforms requests and responses",
            author="APIFromAnything Team",
            tags=["transformer", "utility"]
        )
    
    def initialize(self, api: API) -> None:
        """
        Initialize the plugin.
        
        Args:
            api: The API instance
        """
        super().initialize(api)
        self.logger.info(f"Initializing {self.metadata.name} plugin")
        
        # Register hooks
        request_hook = api.plugin_manager.get_hook("request_transformation")
        response_hook = api.plugin_manager.get_hook("response_transformation")
        
        if request_hook:
            self.register_hook(request_hook, self.transform_request, PluginPriority.HIGH.value)
        
        if response_hook:
            self.register_hook(response_hook, self.transform_response, PluginPriority.HIGH.value)
    
    async def transform_request(self, request: Request) -> Request:
        """
        Transform the request.
        
        Args:
            request: The request object
            
        Returns:
            The transformed request object
        """
        # Add a custom header to the request
        request.headers["X-Transformed-By"] = self.metadata.name
        self.logger.debug(f"Transformed request: {request.path}")
        return request
    
    async def transform_response(self, response: Response, request: Request) -> Response:
        """
        Transform the response.
        
        Args:
            response: The response object
            request: The request object
            
        Returns:
            The transformed response object
        """
        # Add a custom header to the response
        response.headers["X-Transformed-By"] = self.metadata.name
        self.logger.debug(f"Transformed response: {request.path}")
        return response
    
    async def pre_request(self, request: Request) -> Request:
        """
        Process the request.
        
        Args:
            request: The request object
            
        Returns:
            The processed request object
        """
        # Call the request transformation hook
        request_hook = self.api.plugin_manager.get_hook("request_transformation")
        if request_hook:
            results = await request_hook(request)
            if results:
                # Use the last result as the transformed request
                return results[-1]
        
        return request
    
    async def post_response(self, response: Response, request: Request) -> Response:
        """
        Process the response.
        
        Args:
            response: The response object
            request: The request object
            
        Returns:
            The processed response object
        """
        # Call the response transformation hook
        response_hook = self.api.plugin_manager.get_hook("response_transformation")
        if response_hook:
            results = await response_hook(response, request)
            if results:
                # Use the last result as the transformed response
                return results[-1]
        
        return response


# Define a plugin that listens for events
class EventListenerPlugin(Plugin):
    """
    Plugin for listening to events.
    """
    
    def get_metadata(self) -> PluginMetadata:
        """
        Get the metadata for this plugin.
        
        Returns:
            The plugin metadata
        """
        return PluginMetadata(
            name="event_listener",
            version="1.0.0",
            description="Listens for events",
            author="APIFromAnything Team",
            tags=["events", "utility"]
        )
    
    def initialize(self, api: API) -> None:
        """
        Initialize the plugin.
        
        Args:
            api: The API instance
        """
        super().initialize(api)
        self.logger.info(f"Initializing {self.metadata.name} plugin")
        
        # Register as a listener for all events
        for event in PluginEvent:
            api.plugin_manager.register_event_listener(self, event)
        
        # Initialize event counters
        self.event_counts = {event: 0 for event in PluginEvent}
    
    async def on_event(self, event: PluginEvent, **kwargs) -> None:
        """
        Handle events.
        
        Args:
            event: The event that occurred
            **kwargs: Additional event data
        """
        self.event_counts[event] += 1
        self.logger.debug(f"Event: {event.value} (count: {self.event_counts[event]})")
        
        if event == PluginEvent.SERVER_STOPPING:
            # Log event summary when the server is stopping
            self.logger.info("Event summary:")
            for event_type, count in self.event_counts.items():
                self.logger.info(f"  {event_type.value}: {count}")


# Register the plugins
app.plugin_manager.register(LoggingPlugin())
app.plugin_manager.register(MetricsPlugin())
app.plugin_manager.register(RequestTransformerPlugin())
app.plugin_manager.register(EventListenerPlugin())

# Configure the logging plugin
logging_plugin = app.plugin_manager.get_plugin("logging")
logging_plugin.config.update({
    "log_request_body": True,
    "log_response_body": True,
})

# Simulated database
items_db = [
    {"id": 1, "name": "Item 1", "description": "Description for Item 1"},
    {"id": 2, "name": "Item 2", "description": "Description for Item 2"},
    {"id": 3, "name": "Item 3", "description": "Description for Item 3"},
]


@api(route="/items", method="GET")
def get_items() -> List[Dict]:
    """
    Get all items.
    
    Returns:
        A list of items
    """
    logger.info("Fetching items")
    return items_db


@api(route="/items/{item_id}", method="GET")
def get_item(item_id: int) -> Dict:
    """
    Get an item by ID.
    
    Args:
        item_id: The ID of the item to retrieve
        
    Returns:
        An item
    """
    logger.info(f"Fetching item {item_id}")
    
    for item in items_db:
        if item["id"] == item_id:
            return item
    
    return {"error": "Item not found"}


@api(route="/items", method="POST")
def create_item(name: str, description: str) -> Dict:
    """
    Create a new item.
    
    Args:
        name: The name of the item
        description: The description of the item
        
    Returns:
        The created item
    """
    logger.info(f"Creating new item: {name}")
    
    item_id = max(item["id"] for item in items_db) + 1
    new_item = {"id": item_id, "name": name, "description": description}
    items_db.append(new_item)
    
    return new_item


@api(route="/items/{item_id}", method="PUT")
def update_item(item_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Dict:
    """
    Update an item.
    
    Args:
        item_id: The ID of the item to update
        name: The new name of the item (optional)
        description: The new description of the item (optional)
        
    Returns:
        The updated item
    """
    logger.info(f"Updating item {item_id}")
    
    for item in items_db:
        if item["id"] == item_id:
            if name is not None:
                item["name"] = name
            if description is not None:
                item["description"] = description
            return item
    
    return {"error": "Item not found"}


@api(route="/items/{item_id}", method="DELETE")
def delete_item(item_id: int) -> Dict:
    """
    Delete an item.
    
    Args:
        item_id: The ID of the item to delete
        
    Returns:
        A success message
    """
    logger.info(f"Deleting item {item_id}")
    
    global items_db
    for i, item in enumerate(items_db):
        if item["id"] == item_id:
            del items_db[i]
            return {"message": f"Item with ID {item_id} deleted successfully"}
    
    return {"error": "Item not found"}


@api(route="/error", method="GET")
def trigger_error() -> Dict:
    """
    Trigger an error.
    
    This endpoint intentionally raises an exception to demonstrate error handling.
    
    Returns:
        Never returns normally
    """
    logger.info("Triggering an error")
    raise ValueError("This is a test error")


@api(route="/plugins", method="GET")
def get_plugins() -> List[Dict]:
    """
    Get information about all registered plugins.
    
    Returns:
        A list of plugin information
    """
    logger.info("Fetching plugins")
    
    plugins = []
    for plugin in app.plugin_manager.plugins.values():
        plugins.append({
            "name": plugin.metadata.name,
            "version": plugin.metadata.version,
            "description": plugin.metadata.description,
            "author": plugin.metadata.author,
            "state": plugin.state.value,
            "dependencies": plugin.metadata.dependencies,
            "tags": plugin.metadata.tags,
        })
    
    return plugins


@api(route="/plugins/{plugin_name}/config", method="GET")
def get_plugin_config(plugin_name: str) -> Dict:
    """
    Get the configuration of a plugin.
    
    Args:
        plugin_name: The name of the plugin
        
    Returns:
        The plugin configuration
    """
    logger.info(f"Fetching configuration for plugin {plugin_name}")
    
    try:
        plugin = app.plugin_manager.get_plugin(plugin_name)
        return plugin.config.values
    except ValueError:
        return {"error": f"Plugin '{plugin_name}' not found"}


@api(route="/plugins/{plugin_name}/config", method="PUT")
def update_plugin_config(plugin_name: str, config: Dict[str, Any]) -> Dict:
    """
    Update the configuration of a plugin.
    
    Args:
        plugin_name: The name of the plugin
        config: The new configuration values
        
    Returns:
        The updated plugin configuration
    """
    logger.info(f"Updating configuration for plugin {plugin_name}")
    
    try:
        plugin = app.plugin_manager.get_plugin(plugin_name)
        plugin.config.update(config)
        
        if not plugin.config.validate():
            return {"error": "Invalid configuration"}
        
        return plugin.config.values
    except ValueError:
        return {"error": f"Plugin '{plugin_name}' not found"}


@api(route="/metrics", method="GET")
def get_metrics() -> Dict:
    """
    Get metrics collected by the metrics plugin.
    
    Returns:
        The collected metrics
    """
    logger.info("Fetching metrics")
    
    try:
        metrics_plugin = app.plugin_manager.get_plugin("metrics")
        
        response_times = metrics_plugin.response_times
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "request_count": metrics_plugin.request_count,
            "response_count": metrics_plugin.response_count,
            "error_count": metrics_plugin.error_count,
            "average_response_time": avg_response_time,
        }
    except ValueError:
        return {"error": "Metrics plugin not found"}


@api(route="/events", method="GET")
def get_events() -> Dict:
    """
    Get event counts collected by the event listener plugin.
    
    Returns:
        The event counts
    """
    logger.info("Fetching event counts")
    
    try:
        event_listener_plugin = app.plugin_manager.get_plugin("event_listener")
        
        return {
            event.value: count
            for event, count in event_listener_plugin.event_counts.items()
        }
    except ValueError:
        return {"error": "Event listener plugin not found"}


if __name__ == "__main__":
    # Run the API server
    app.run(host="0.0.0.0", port=8009) 