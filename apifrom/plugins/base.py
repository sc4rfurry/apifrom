"""
Base plugin module for APIFromAnything.

This module provides the base classes and interfaces for creating plugins
for the APIFromAnything library. The plugin system is designed to be robust,
dynamic, and feature-rich, allowing for extensive customization and extension
of the core functionality.
"""

import abc
import inspect
import logging
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, TypeVar, Generic

from apifrom.core.app import API
from apifrom.core.request import Request
from apifrom.core.response import Response


class PluginPriority(Enum):
    """
    Priority levels for plugins.
    
    This enum defines the priority levels for plugins, which determine the order
    in which plugins are executed. Higher priority plugins are executed first.
    """
    HIGHEST = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    LOWEST = 0


class PluginState(Enum):
    """
    States for plugins.
    
    This enum defines the possible states for plugins, which are used to track
    the lifecycle of a plugin.
    """
    REGISTERED = "registered"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


class PluginEvent(Enum):
    """
    Events that can be emitted by the plugin system.
    
    This enum defines the events that can be emitted by the plugin system,
    which plugins can listen for and respond to.
    """
    PLUGIN_REGISTERED = "plugin_registered"
    PLUGIN_INITIALIZED = "plugin_initialized"
    PLUGIN_ACTIVATED = "plugin_activated"
    PLUGIN_DISABLED = "plugin_disabled"
    PLUGIN_ERROR = "plugin_error"
    SERVER_STARTING = "server_starting"
    SERVER_STARTED = "server_started"
    SERVER_STOPPING = "server_stopping"
    SERVER_STOPPED = "server_stopped"
    REQUEST_RECEIVED = "request_received"
    RESPONSE_SENT = "response_sent"
    ERROR_OCCURRED = "error_occurred"


class PluginDependencyError(Exception):
    """
    Exception raised when a plugin dependency cannot be satisfied.
    """
    pass


class PluginConfigurationError(Exception):
    """
    Exception raised when a plugin configuration is invalid.
    """
    pass


class PluginLifecycleError(Exception):
    """
    Exception raised when a plugin lifecycle operation fails.
    """
    pass


T = TypeVar('T')


class PluginHook(Generic[T]):
    """
    A hook that plugins can register callbacks for.
    
    This class provides a way for plugins to register callbacks for specific
    hooks in the API lifecycle, allowing them to extend or modify the behavior
    of the API at various points.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize the plugin hook.
        
        Args:
            name: The name of the hook
            description: A description of the hook
        """
        self.name = name
        self.description = description
        self.callbacks: List[Tuple[Callable[..., T], int]] = []
    
    def register(self, callback: Callable[..., T], priority: int = PluginPriority.NORMAL.value) -> None:
        """
        Register a callback for this hook.
        
        Args:
            callback: The callback function
            priority: The priority of the callback (higher priority callbacks are executed first)
        """
        self.callbacks.append((callback, priority))
        self.callbacks.sort(key=lambda x: x[1], reverse=True)
    
    def unregister(self, callback: Callable[..., T]) -> None:
        """
        Unregister a callback from this hook.
        
        Args:
            callback: The callback function to unregister
        """
        self.callbacks = [(cb, priority) for cb, priority in self.callbacks if cb != callback]
    
    async def __call__(self, *args, **kwargs) -> List[T]:
        """
        Call all registered callbacks with the given arguments.
        
        Args:
            *args: Positional arguments to pass to the callbacks
            **kwargs: Keyword arguments to pass to the callbacks
            
        Returns:
            A list of the results from all callbacks
        """
        results = []
        for callback, _ in self.callbacks:
            if inspect.iscoroutinefunction(callback):
                result = await callback(*args, **kwargs)
            else:
                result = callback(*args, **kwargs)
            results.append(result)
        return results


class PluginMetadata:
    """
    Metadata for a plugin.
    
    This class stores metadata about a plugin, such as its name, version,
    description, and dependencies.
    """
    
    def __init__(
        self,
        name: str,
        version: str,
        description: str = "",
        author: str = "",
        website: str = "",
        license: str = "",
        dependencies: List[str] = None,
        tags: List[str] = None,
    ):
        """
        Initialize the plugin metadata.
        
        Args:
            name: The name of the plugin
            version: The version of the plugin
            description: A description of the plugin
            author: The author of the plugin
            website: The website of the plugin
            license: The license of the plugin
            dependencies: A list of plugin names that this plugin depends on
            tags: A list of tags for the plugin
        """
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.website = website
        self.license = license
        self.dependencies = dependencies or []
        self.tags = tags or []
        self.id = str(uuid.uuid4())
        self.created_at = time.time()


class PluginConfig:
    """
    Configuration for a plugin.
    
    This class stores configuration options for a plugin, which can be set
    by the user and accessed by the plugin.
    """
    
    def __init__(self, defaults: Dict[str, Any] = None, schema: Dict[str, Any] = None):
        """
        Initialize the plugin configuration.
        
        Args:
            defaults: Default values for configuration options
            schema: JSON Schema for validating configuration options
        """
        self.defaults = defaults or {}
        self.schema = schema or {}
        self.values = self.defaults.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key
            default: The default value to return if the key is not found
            
        Returns:
            The configuration value
        """
        return self.values.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key
            value: The configuration value
        """
        self.values[key] = value
    
    def update(self, values: Dict[str, Any]) -> None:
        """
        Update multiple configuration values.
        
        Args:
            values: A dictionary of configuration values to update
        """
        self.values.update(values)
    
    def validate(self) -> bool:
        """
        Validate the configuration against the schema.
        
        Returns:
            True if the configuration is valid, False otherwise
        """
        if not self.schema:
            return True
        
        try:
            import jsonschema
            jsonschema.validate(instance=self.values, schema=self.schema)
            return True
        except ImportError:
            # If jsonschema is not available, we can't validate
            return True
        except jsonschema.exceptions.ValidationError:
            return False


class Plugin(abc.ABC):
    """
    Base class for all plugins.
    
    This class defines the interface that all plugins must implement, providing
    hooks for various stages of the API lifecycle.
    """
    
    def __init__(self):
        """
        Initialize the plugin.
        """
        self._metadata = self.get_metadata()
        self._config = self.get_config()
        self._state = PluginState.REGISTERED
        self._api = None
        self._logger = logging.getLogger(f"apifrom.plugins.{self._metadata.name}")
    
    @abc.abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """
        Get the metadata for this plugin.
        
        Returns:
            The plugin metadata
        """
        pass
    
    def get_config(self) -> PluginConfig:
        """
        Get the configuration for this plugin.
        
        Returns:
            The plugin configuration
        """
        return PluginConfig()
    
    @property
    def metadata(self) -> PluginMetadata:
        """
        Get the metadata for this plugin.
        
        Returns:
            The plugin metadata
        """
        return self._metadata
    
    @property
    def config(self) -> PluginConfig:
        """
        Get the configuration for this plugin.
        
        Returns:
            The plugin configuration
        """
        return self._config
    
    @property
    def state(self) -> PluginState:
        """
        Get the state of this plugin.
        
        Returns:
            The plugin state
        """
        return self._state
    
    @property
    def api(self) -> Optional[API]:
        """
        Get the API instance that this plugin is registered with.
        
        Returns:
            The API instance, or None if the plugin is not registered
        """
        return self._api
    
    @property
    def logger(self) -> logging.Logger:
        """
        Get the logger for this plugin.
        
        Returns:
            The plugin logger
        """
        return self._logger
    
    def initialize(self, api: API) -> None:
        """
        Initialize the plugin.
        
        This method is called when the plugin is registered with the API.
        
        Args:
            api: The API instance
        """
        self._api = api
        self._state = PluginState.INITIALIZED
    
    def activate(self) -> None:
        """
        Activate the plugin.
        
        This method is called when the plugin is activated.
        """
        self._state = PluginState.ACTIVE
    
    def deactivate(self) -> None:
        """
        Deactivate the plugin.
        
        This method is called when the plugin is deactivated.
        """
        self._state = PluginState.DISABLED
    
    def shutdown(self) -> None:
        """
        Shutdown the plugin.
        
        This method is called when the API is shutting down.
        """
        pass
    
    async def pre_request(self, request: Request) -> Request:
        """
        Process a request before it is handled by the API.
        
        Args:
            request: The request object
            
        Returns:
            The processed request object
        """
        return request
    
    async def post_response(self, response: Response, request: Request) -> Response:
        """
        Process a response after it is generated by the API.
        
        Args:
            response: The response object
            request: The request object
            
        Returns:
            The processed response object
        """
        return response
    
    async def on_error(self, error: Exception, request: Request) -> Optional[Response]:
        """
        Handle an error that occurred during request processing.
        
        Args:
            error: The error that occurred
            request: The request object
            
        Returns:
            A response object, or None to let the API handle the error
        """
        return None
    
    async def on_event(self, event: PluginEvent, **kwargs) -> None:
        """
        Handle an event emitted by the plugin system.
        
        Args:
            event: The event that occurred
            **kwargs: Additional event data
        """
        pass
    
    def register_hook(self, hook: PluginHook, callback: Callable, priority: int = PluginPriority.NORMAL.value) -> None:
        """
        Register a callback for a hook.
        
        Args:
            hook: The hook to register for
            callback: The callback function
            priority: The priority of the callback
        """
        hook.register(callback, priority)
    
    def unregister_hook(self, hook: PluginHook, callback: Callable) -> None:
        """
        Unregister a callback from a hook.
        
        Args:
            hook: The hook to unregister from
            callback: The callback function
        """
        hook.unregister(callback)
    
    def __str__(self) -> str:
        """
        Get a string representation of the plugin.
        
        Returns:
            A string representation of the plugin
        """
        return f"{self._metadata.name} v{self._metadata.version} ({self._state.value})"


class PluginManager:
    """
    Manager for plugins.
    
    This class manages the registration and execution of plugins, providing
    a robust and dynamic plugin system for extending the functionality of
    the API.
    """
    
    def __init__(self):
        """
        Initialize the plugin manager.
        """
        self.plugins: Dict[str, Plugin] = {}
        self.api: Optional[API] = None
        self.hooks: Dict[str, PluginHook] = {}
        self.event_listeners: Dict[PluginEvent, List[Tuple[Plugin, int]]] = {
            event: [] for event in PluginEvent
        }
        self.logger = logging.getLogger("apifrom.plugins")
    
    def register_plugin(self, plugin: Plugin) -> None:
        """
        Register a plugin with the manager.
        
        Args:
            plugin: The plugin to register
            
        Raises:
            PluginDependencyError: If a plugin dependency cannot be satisfied
            PluginConfigurationError: If the plugin configuration is invalid
        """
        # Check if the plugin is already registered
        if plugin.metadata.name in self.plugins:
            raise ValueError(f"Plugin with name '{plugin.metadata.name}' is already registered")
        
        # Check plugin dependencies
        for dependency in plugin.metadata.dependencies:
            if dependency not in self.plugins:
                raise PluginDependencyError(f"Plugin '{plugin.metadata.name}' depends on '{dependency}', which is not registered")
        
        # Validate plugin configuration
        if not plugin.config.validate():
            raise PluginConfigurationError(f"Plugin '{plugin.metadata.name}' has invalid configuration")
        
        # Register the plugin
        self.plugins[plugin.metadata.name] = plugin
        
        # Initialize the plugin if the API is available
        if self.api:
            try:
                plugin.initialize(self.api)
                plugin.activate()
                self.logger.info(f"Plugin '{plugin.metadata.name}' registered and activated")
            except Exception as e:
                plugin._state = PluginState.ERROR
                self.logger.error(f"Failed to initialize plugin '{plugin.metadata.name}': {e}")
                raise PluginLifecycleError(f"Failed to initialize plugin '{plugin.metadata.name}': {e}") from e
        
        # Emit plugin registered event
        self.emit_event(PluginEvent.PLUGIN_REGISTERED, plugin=plugin)
    
    def register(self, plugin: Plugin) -> None:
        """
        Register a plugin with the manager (alias for register_plugin).
        
        Args:
            plugin: The plugin to register
        """
        self.register_plugin(plugin)
    
    def unregister_plugin(self, plugin_name: str) -> None:
        """
        Unregister a plugin from the manager.
        
        Args:
            plugin_name: The name of the plugin to unregister
            
        Raises:
            ValueError: If the plugin is not registered
            PluginDependencyError: If other plugins depend on this plugin
        """
        # Check if the plugin is registered
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin with name '{plugin_name}' is not registered")
        
        # Check if other plugins depend on this plugin
        for other_plugin in self.plugins.values():
            if plugin_name in other_plugin.metadata.dependencies:
                raise PluginDependencyError(f"Cannot unregister plugin '{plugin_name}' because plugin '{other_plugin.metadata.name}' depends on it")
        
        # Get the plugin
        plugin = self.plugins[plugin_name]
        
        # Deactivate and shutdown the plugin
        try:
            plugin.deactivate()
            plugin.shutdown()
            self.logger.info(f"Plugin '{plugin_name}' deactivated and unregistered")
        except Exception as e:
            self.logger.error(f"Failed to deactivate plugin '{plugin_name}': {e}")
        
        # Remove the plugin
        del self.plugins[plugin_name]
        
        # Emit plugin disabled event
        self.emit_event(PluginEvent.PLUGIN_DISABLED, plugin=plugin)
    
    def unregister(self, plugin_name: str) -> None:
        """
        Unregister a plugin from the manager (alias for unregister_plugin).
        
        Args:
            plugin_name: The name of the plugin to unregister
        """
        self.unregister_plugin(plugin_name)
    
    def get_plugin(self, plugin_name: str) -> Plugin:
        """
        Get a plugin by name.
        
        Args:
            plugin_name: The name of the plugin
            
        Returns:
            The plugin instance
            
        Raises:
            ValueError: If the plugin is not registered
        """
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin with name '{plugin_name}' is not registered")
        
        return self.plugins[plugin_name]
    
    def get_plugins_by_tag(self, tag: str) -> List[Plugin]:
        """
        Get plugins by tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            A list of plugins with the specified tag
        """
        return [plugin for plugin in self.plugins.values() if tag in plugin.metadata.tags]
    
    def get_plugins_by_state(self, state: PluginState) -> List[Plugin]:
        """
        Get plugins by state.
        
        Args:
            state: The state to filter by
            
        Returns:
            A list of plugins in the specified state
        """
        return [plugin for plugin in self.plugins.values() if plugin.state == state]
    
    def initialize(self, api: API) -> None:
        """
        Initialize the plugin manager with an API instance.
        
        Args:
            api: The API instance
        """
        self.api = api
        
        # Initialize all registered plugins
        for plugin_name, plugin in list(self.plugins.items()):
            try:
                plugin.initialize(api)
                plugin.activate()
                self.logger.info(f"Plugin '{plugin_name}' initialized and activated")
                self.emit_event(PluginEvent.PLUGIN_INITIALIZED, plugin=plugin)
                self.emit_event(PluginEvent.PLUGIN_ACTIVATED, plugin=plugin)
            except Exception as e:
                plugin._state = PluginState.ERROR
                self.logger.error(f"Failed to initialize plugin '{plugin_name}': {e}")
                self.emit_event(PluginEvent.PLUGIN_ERROR, plugin=plugin, error=e)
    
    def register_hook(self, name: str, description: str = "") -> PluginHook:
        """
        Register a new hook.
        
        Args:
            name: The name of the hook
            description: A description of the hook
            
        Returns:
            The hook instance
        """
        if name in self.hooks:
            return self.hooks[name]
        
        hook = PluginHook(name, description)
        self.hooks[name] = hook
        return hook
    
    def get_hook(self, name: str) -> Optional[PluginHook]:
        """
        Get a hook by name.
        
        Args:
            name: The name of the hook
            
        Returns:
            The hook instance, or None if not found
        """
        return self.hooks.get(name)
    
    def register_event_listener(self, plugin: Plugin, event: PluginEvent, priority: int = PluginPriority.NORMAL.value) -> None:
        """
        Register a plugin as a listener for an event.
        
        Args:
            plugin: The plugin to register
            event: The event to listen for
            priority: The priority of the listener
        """
        self.event_listeners[event].append((plugin, priority))
        self.event_listeners[event].sort(key=lambda x: x[1], reverse=True)
    
    def unregister_event_listener(self, plugin: Plugin, event: PluginEvent) -> None:
        """
        Unregister a plugin as a listener for an event.
        
        Args:
            plugin: The plugin to unregister
            event: The event to stop listening for
        """
        self.event_listeners[event] = [(p, priority) for p, priority in self.event_listeners[event] if p != plugin]
    
    def emit_event(self, event: PluginEvent, **kwargs) -> None:
        """
        Emit an event to all registered listeners.
        
        Args:
            event: The event to emit
            **kwargs: Additional event data
        """
        for plugin, _ in self.event_listeners[event]:
            if plugin.state == PluginState.ACTIVE:
                try:
                    plugin.on_event(event, **kwargs)
                except Exception as e:
                    self.logger.error(f"Error in plugin '{plugin.metadata.name}' while handling event '{event.value}': {e}")
    
    async def pre_request(self, request: Request) -> Request:
        """
        Process a request through all active plugins.
        
        Args:
            request: The request object
            
        Returns:
            The processed request object
        """
        # Emit request received event
        self.emit_event(PluginEvent.REQUEST_RECEIVED, request=request)
        
        # Process the request through all active plugins
        for plugin in self.get_plugins_by_state(PluginState.ACTIVE):
            try:
                request = await plugin.pre_request(request)
            except Exception as e:
                self.logger.error(f"Error in plugin '{plugin.metadata.name}' pre_request: {e}")
                self.emit_event(PluginEvent.ERROR_OCCURRED, plugin=plugin, error=e, request=request)
        
        return request
    
    async def post_response(self, response: Response, request: Request) -> Response:
        """
        Process a response through all active plugins.
        
        Args:
            response: The response object
            request: The request object
            
        Returns:
            The processed response object
        """
        # Process the response through all active plugins
        for plugin in reversed(self.get_plugins_by_state(PluginState.ACTIVE)):
            try:
                response = await plugin.post_response(response, request)
            except Exception as e:
                self.logger.error(f"Error in plugin '{plugin.metadata.name}' post_response: {e}")
                self.emit_event(PluginEvent.ERROR_OCCURRED, plugin=plugin, error=e, request=request, response=response)
        
        # Emit response sent event
        self.emit_event(PluginEvent.RESPONSE_SENT, response=response, request=request)
        
        return response
    
    async def on_error(self, error: Exception, request: Request) -> Optional[Response]:
        """
        Handle an error through all active plugins.
        
        Args:
            error: The error that occurred
            request: The request object
            
        Returns:
            A response object, or None if no plugin handled the error
        """
        # Emit error occurred event
        self.emit_event(PluginEvent.ERROR_OCCURRED, error=error, request=request)
        
        # Handle the error through all active plugins
        for plugin in self.get_plugins_by_state(PluginState.ACTIVE):
            try:
                response = await plugin.on_error(error, request)
                if response is not None:
                    return response
            except Exception as e:
                self.logger.error(f"Error in plugin '{plugin.metadata.name}' on_error: {e}")
        
        return None
    
    def on_startup(self) -> None:
        """
        Call the on_startup method of all active plugins.
        """
        # Emit server starting event
        self.emit_event(PluginEvent.SERVER_STARTING)
    
    def on_shutdown(self) -> None:
        """
        Call the on_shutdown method of all active plugins.
        """
        # Emit server stopping event
        self.emit_event(PluginEvent.SERVER_STOPPING)
        
        # Shutdown all plugins
        for plugin in self.plugins.values():
            try:
                plugin.shutdown()
            except Exception as e:
                self.logger.error(f"Error in plugin '{plugin.metadata.name}' shutdown: {e}")
        
        # Emit server stopped event
        self.emit_event(PluginEvent.SERVER_STOPPED)
    
    def __len__(self) -> int:
        """
        Get the number of registered plugins.
        
        Returns:
            The number of registered plugins
        """
        return len(self.plugins)
    
    def __contains__(self, plugin_name: str) -> bool:
        """
        Check if a plugin is registered.
        
        Args:
            plugin_name: The name of the plugin
            
        Returns:
            True if the plugin is registered, False otherwise
        """
        return plugin_name in self.plugins
    
    def __iter__(self):
        """
        Iterate over all registered plugins.
        
        Returns:
            An iterator over all registered plugins
        """
        return iter(self.plugins.values()) 