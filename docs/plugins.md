# <div align="center">🔌 Plugin System</div>

<div align="center">
  <img src="https://img.shields.io/badge/APIFromAnything-Plugin%20System-blue?style=for-the-badge" alt="Plugin System" />
  <br/>
  <strong>Extend and customize your API with a powerful plugin architecture</strong>
</div>

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-core-components">Core Components</a> •
  <a href="#-plugin-lifecycle">Lifecycle</a> •
  <a href="#-request-response-hooks">Hooks</a> •
  <a href="#-event-system">Events</a> •
  <a href="#-configuration-management">Configuration</a> •
  <a href="#-built-in-plugins">Built-in Plugins</a> •
  <a href="#-examples">Examples</a> •
  <a href="#-best-practices">Best Practices</a>
</p>

---

## 🚀 Overview

APIFromAnything includes a robust and extensible plugin system that allows you to customize and extend the functionality of your API without modifying the core library code. The plugin architecture follows a modular design pattern, enabling seamless integration of custom functionality.

<table>
  <tr>
    <td><b>🧩 Modular Design</b></td>
    <td>Plugins can be developed and distributed independently</td>
  </tr>
  <tr>
    <td><b>🔄 Extensible Architecture</b></td>
    <td>Multiple extension points throughout the request/response lifecycle</td>
  </tr>
  <tr>
    <td><b>🛡️ Robust Isolation</b></td>
    <td>Plugins are isolated to prevent failures from affecting the entire application</td>
  </tr>
  <tr>
    <td><b>⚡ Dynamic Registration</b></td>
    <td>Plugins can be registered, activated, and deactivated at runtime</td>
  </tr>
  <tr>
    <td><b>⚙️ Configurable</b></td>
    <td>Plugins can have their own configuration options with validation</td>
  </tr>
  <tr>
    <td><b>🔗 Dependency Management</b></td>
    <td>Plugins can depend on other plugins with automatic dependency resolution</td>
  </tr>
</table>

## 🧩 Core Components

The plugin system consists of several core components that work together to provide a comprehensive solution.

### Plugin Base Class

The `Plugin` abstract base class defines the interface that all plugins must implement:

<details open>
<summary><b>Basic Plugin Implementation</b></summary>

```python
from apifrom.plugins import Plugin
from apifrom.plugins.base import PluginMetadata, PluginConfig

class MyPlugin(Plugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-plugin",
            version="1.0.0",
            description="My custom plugin",
            author="Your Name",
            dependencies=["logging"],  # Optional dependencies
            tags=["utility"]  # Optional tags
        )
    
    def get_config(self) -> PluginConfig:
        return PluginConfig(
            defaults={
                "option1": "default_value",
                "option2": True
            }
        )
```
</details>

### Plugin Manager

The `PluginManager` class manages the registration and execution of plugins:

<details>
<summary><b>Using the Plugin Manager</b></summary>

```python
from apifrom import API
from apifrom.plugins import Plugin

# The API class has a built-in plugin_manager
app = API(title="My API")

# Create a plugin instance
my_plugin = MyPlugin()

# Register the plugin
app.plugin_manager.register(my_plugin)

# Get a plugin by name
plugin = app.plugin_manager.get_plugin("my-plugin")

# Get plugins by tag
utility_plugins = app.plugin_manager.get_plugins_by_tag("utility")

# Unregister a plugin
app.plugin_manager.unregister("my-plugin")
```
</details>

### Plugin Metadata

The `PluginMetadata` class stores metadata about a plugin:

<details>
<summary><b>Plugin Metadata Fields</b></summary>

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Unique name of the plugin |
| `version` | `str` | Version of the plugin (semantic versioning recommended) |
| `description` | `str` | Description of the plugin's functionality |
| `author` | `str` | Author of the plugin |
| `website` | `str` | Website for the plugin (optional) |
| `license` | `str` | License for the plugin (optional) |
| `dependencies` | `List[str]` | List of plugin names that this plugin depends on |
| `tags` | `List[str]` | List of tags for categorizing the plugin |

</details>

### Plugin Configuration

The `PluginConfig` class manages plugin configuration:

<details>
<summary><b>Plugin Configuration Features</b></summary>

- **Default Values**: Specify default configuration values
- **Schema Validation**: Validate configuration using JSON Schema
- **Configuration Access**: Get and set configuration values
- **Configuration Updates**: Update multiple configuration values at once

</details>

## 🔄 Plugin Lifecycle

Plugins go through several lifecycle stages, each with specific hooks that can be implemented:

<div align="center">
  <img src="https://img.shields.io/badge/Registration-➡️-blue" alt="Registration" />
  <img src="https://img.shields.io/badge/Initialization-➡️-green" alt="Initialization" />
  <img src="https://img.shields.io/badge/Activation-➡️-yellow" alt="Activation" />
  <img src="https://img.shields.io/badge/Deactivation-➡️-orange" alt="Deactivation" />
  <img src="https://img.shields.io/badge/Shutdown-red" alt="Shutdown" />
</div>

<details>
<summary><b>Implementing Lifecycle Methods</b></summary>

```python
class MyPlugin(Plugin):
    def initialize(self, api: API) -> None:
        """Called when the plugin is registered with the API."""
        super().initialize(api)
        self.logger.info(f"Initializing {self.metadata.name} plugin")
        # Initialize resources, connect to databases, etc.
    
    def activate(self) -> None:
        """Called when the plugin is activated."""
        super().activate()
        self.logger.info(f"Activating {self.metadata.name} plugin")
        # Start background tasks, etc.
    
    def deactivate(self) -> None:
        """Called when the plugin is deactivated."""
        super().deactivate()
        self.logger.info(f"Deactivating {self.metadata.name} plugin")
        # Stop background tasks, etc.
    
    def shutdown(self) -> None:
        """Called when the API is shutting down."""
        self.logger.info(f"Shutting down {self.metadata.name} plugin")
        # Release resources, close connections, etc.
```
</details>

### Lifecycle States

The `PluginState` enum defines the possible states for plugins:

| State | Description |
|-------|-------------|
| `REGISTERED` | The plugin is registered but not initialized |
| `INITIALIZED` | The plugin is initialized but not active |
| `ACTIVE` | The plugin is active and processing requests |
| `DISABLED` | The plugin is disabled and not processing requests |
| `ERROR` | The plugin encountered an error |

## 🔄 Request/Response Hooks

Plugins can process requests and responses by implementing the following hooks:

<details open>
<summary><b>Request/Response Hook Implementation</b></summary>

```python
class MyPlugin(Plugin):
    async def pre_request(self, request: Request) -> Request:
        """Process a request before it is handled by the API."""
        self.logger.info(f"Processing request: {request.method} {request.path}")
        # Modify the request if needed
        return request
    
    async def post_response(self, response: Response, request: Request) -> Response:
        """Process a response after it is generated by the API."""
        self.logger.info(f"Processing response: {response.status_code}")
        # Modify the response if needed
        return response
    
    async def on_error(self, error: Exception, request: Request) -> Optional[Response]:
        """Handle an error that occurred during request processing."""
        self.logger.error(f"Error processing request: {error}")
        # Return a custom response or None to let the API handle the error
        return None
```
</details>

### Request Processing Flow

<div align="center">
  <table>
    <tr>
      <td align="center">Client Request</td>
      <td align="center">→</td>
      <td align="center"><code>pre_request</code> hooks</td>
      <td align="center">→</td>
      <td align="center">API Handler</td>
      <td align="center">→</td>
      <td align="center"><code>post_response</code> hooks</td>
      <td align="center">→</td>
      <td align="center">Client Response</td>
    </tr>
  </table>
</div>

## 📢 Event System

Plugins can react to events emitted by the plugin system through the `on_event` method:

<details>
<summary><b>Event Handling Implementation</b></summary>

```python
from apifrom.plugins.base import PluginEvent

class MyPlugin(Plugin):
    async def on_event(self, event: PluginEvent, **kwargs) -> None:
        """Handle an event emitted by the plugin system."""
        if event == PluginEvent.SERVER_STARTING:
            self.logger.info("Server is starting")
        elif event == PluginEvent.SERVER_STOPPING:
            self.logger.info("Server is stopping")
        elif event == PluginEvent.REQUEST_RECEIVED:
            request = kwargs.get("request")
            self.logger.info(f"Request received: {request.method} {request.path}")
        elif event == PluginEvent.RESPONSE_SENT:
            response = kwargs.get("response")
            self.logger.info(f"Response sent: {response.status_code}")
```
</details>

### Available Events

<table>
  <tr>
    <th>Category</th>
    <th>Event</th>
    <th>Description</th>
  </tr>
  <tr>
    <td rowspan="5"><b>Plugin Lifecycle</b></td>
    <td><code>PLUGIN_REGISTERED</code></td>
    <td>A plugin has been registered</td>
  </tr>
  <tr>
    <td><code>PLUGIN_INITIALIZED</code></td>
    <td>A plugin has been initialized</td>
  </tr>
  <tr>
    <td><code>PLUGIN_ACTIVATED</code></td>
    <td>A plugin has been activated</td>
  </tr>
  <tr>
    <td><code>PLUGIN_DISABLED</code></td>
    <td>A plugin has been disabled</td>
  </tr>
  <tr>
    <td><code>PLUGIN_ERROR</code></td>
    <td>An error occurred in a plugin</td>
  </tr>
  <tr>
    <td rowspan="4"><b>Server Lifecycle</b></td>
    <td><code>SERVER_STARTING</code></td>
    <td>The server is starting</td>
  </tr>
  <tr>
    <td><code>SERVER_STARTED</code></td>
    <td>The server has started</td>
  </tr>
  <tr>
    <td><code>SERVER_STOPPING</code></td>
    <td>The server is stopping</td>
  </tr>
  <tr>
    <td><code>SERVER_STOPPED</code></td>
    <td>The server has stopped</td>
  </tr>
  <tr>
    <td rowspan="3"><b>Request/Response</b></td>
    <td><code>REQUEST_RECEIVED</code></td>
    <td>A request has been received</td>
  </tr>
  <tr>
    <td><code>RESPONSE_SENT</code></td>
    <td>A response has been sent</td>
  </tr>
  <tr>
    <td><code>ERROR_OCCURRED</code></td>
    <td>An error occurred during request processing</td>
  </tr>
</table>

## 🪝 Hook System

The hook system allows plugins to register callbacks for specific hooks, providing a more flexible way to extend functionality:

<details>
<summary><b>Using the Hook System</b></summary>

```python
class MyPlugin(Plugin):
    def initialize(self, api: API) -> None:
        super().initialize(api)
        
        # Get or register a hook
        request_transformation_hook = api.plugin_manager.register_hook(
            "request_transformation",
            "Transform the request before it is processed by the API"
        )
        
        # Register a callback for the hook
        self.register_hook(
            request_transformation_hook,
            self.transform_request,
            priority=75  # Higher priority callbacks are executed first
        )
    
    def transform_request(self, request: Request) -> Request:
        """Transform the request."""
        # Modify the request
        return request
    
    def shutdown(self) -> None:
        # Unregister the callback when the plugin is shut down
        request_transformation_hook = self.api.plugin_manager.get_hook("request_transformation")
        if request_transformation_hook:
            self.unregister_hook(request_transformation_hook, self.transform_request)
```
</details>

### Hook Priority

Hooks can be registered with a priority level to control the order of execution:

<table>
  <tr>
    <th>Priority</th>
    <th>Value</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><code>HIGHEST</code></td>
    <td>100</td>
    <td>Executed first</td>
  </tr>
  <tr>
    <td><code>HIGH</code></td>
    <td>75</td>
    <td>Executed after HIGHEST</td>
  </tr>
  <tr>
    <td><code>NORMAL</code></td>
    <td>50</td>
    <td>Default priority</td>
  </tr>
  <tr>
    <td><code>LOW</code></td>
    <td>25</td>
    <td>Executed after NORMAL</td>
  </tr>
  <tr>
    <td><code>LOWEST</code></td>
    <td>0</td>
    <td>Executed last</td>
  </tr>
</table>

## ⚙️ Configuration Management

Plugins can have their own configuration options with default values and validation:

<details>
<summary><b>Plugin Configuration Implementation</b></summary>

```python
class MyPlugin(Plugin):
    def get_config(self) -> PluginConfig:
        return PluginConfig(
            defaults={
                "option1": "default_value",
                "option2": True
            },
            schema={
                "type": "object",
                "properties": {
                    "option1": {"type": "string"},
                    "option2": {"type": "boolean"}
                }
            }
        )
    
    def initialize(self, api: API) -> None:
        super().initialize(api)
        
        # Access configuration options
        option1 = self.config.get("option1")
        option2 = self.config.get("option2")
        
        self.logger.info(f"Configuration: option1={option1}, option2={option2}")
        
        # Update configuration options
        self.config.set("option1", "new_value")
        
        # Validate configuration
        if not self.config.validate():
            self.logger.error("Invalid configuration")
```
</details>

### Configuration Methods

<table>
  <tr>
    <th>Method</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><code>get(key, default=None)</code></td>
    <td>Get a configuration value</td>
  </tr>
  <tr>
    <td><code>set(key, value)</code></td>
    <td>Set a configuration value</td>
  </tr>
  <tr>
    <td><code>update(values)</code></td>
    <td>Update multiple configuration values</td>
  </tr>
  <tr>
    <td><code>validate()</code></td>
    <td>Validate the configuration against the schema</td>
  </tr>
</table>

## 📦 Built-in Plugins

APIFromAnything includes several built-in plugins that provide common functionality:

### LoggingPlugin

The `LoggingPlugin` logs requests and responses:

<details>
<summary><b>Using the LoggingPlugin</b></summary>

```python
from apifrom import API
from apifrom.plugins import LoggingPlugin

app = API(title="My API")

# Create and register a logging plugin
logging_plugin = LoggingPlugin(
    log_request_body=True,
    log_response_body=True,
    log_headers=True,
    exclude_paths=["/health"],
    exclude_methods=["OPTIONS"]
)
app.plugin_manager.register(logging_plugin)
```
</details>

<details>
<summary><b>LoggingPlugin Configuration Options</b></summary>

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `log_request_body` | `bool` | `False` | Whether to log request bodies |
| `log_response_body` | `bool` | `False` | Whether to log response bodies |
| `log_headers` | `bool` | `False` | Whether to log headers |
| `exclude_paths` | `List[str]` | `[]` | Paths to exclude from logging |
| `exclude_methods` | `List[str]` | `[]` | HTTP methods to exclude from logging |
| `level` | `int` | `logging.INFO` | The logging level |

</details>

## 🔍 Examples

### Basic Plugin Example

<details open>
<summary><b>Timing Plugin</b></summary>

```python
import time
from typing import Optional

from apifrom import API, api, Plugin
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.plugins.base import PluginMetadata, PluginConfig

class TimingPlugin(Plugin):
    """
    Plugin for measuring request execution time.
    """
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="timing",
            version="1.0.0",
            description="Measures request execution time",
            author="Your Name",
            tags=["utility", "performance"]
        )
    
    def get_config(self) -> PluginConfig:
        return PluginConfig(
            defaults={
                "add_header": True,
                "log_timing": True
            }
        )
    
    async def pre_request(self, request: Request) -> Request:
        # Store the start time
        request.state.timing_start_time = time.time()
        return request
    
    async def post_response(self, response: Response, request: Request) -> Response:
        # Calculate the execution time
        start_time = getattr(request.state, "timing_start_time", None)
        if start_time:
            execution_time = time.time() - start_time
            
            # Add timing header to the response
            if self.config.get("add_header"):
                response.headers["X-Execution-Time"] = f"{execution_time:.4f}s"
            
            # Log the timing information
            if self.config.get("log_timing"):
                self.logger.info(f"Request to {request.path} took {execution_time:.4f} seconds")
        
        return response

# Create an API instance
app = API(title="Timing Plugin Example")

# Register the timing plugin
timing_plugin = TimingPlugin()
app.plugin_manager.register(timing_plugin)

# Define an API endpoint
@api(route="/test")
def test_endpoint():
    """Test endpoint that simulates a delay."""
    time.sleep(0.5)
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```
</details>

### Plugin with Dependencies

<details>
<summary><b>Metrics Plugin (depends on Timing Plugin)</b></summary>

```python
class MetricsPlugin(Plugin):
    """
    Plugin for collecting API metrics.
    """
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="metrics",
            version="1.0.0",
            description="Collects API metrics",
            author="Your Name",
            dependencies=["timing"],  # This plugin depends on the timing plugin
            tags=["utility", "monitoring"]
        )
    
    def initialize(self, api: API) -> None:
        super().initialize(api)
        
        # Get the timing plugin
        self.timing_plugin = api.plugin_manager.get_plugin("timing")
        
        # Initialize metrics
        self.request_count = 0
        self.response_count = 0
        self.error_count = 0
        self.response_times = []
    
    async def pre_request(self, request: Request) -> Request:
        self.request_count += 1
        return request
    
    async def post_response(self, response: Response, request: Request) -> Response:
        self.response_count += 1
        
        # Get the execution time from the timing plugin
        start_time = getattr(request.state, "timing_start_time", None)
        if start_time:
            execution_time = time.time() - start_time
            self.response_times.append(execution_time)
        
        return response
    
    async def on_error(self, error: Exception, request: Request) -> Optional[Response]:
        self.error_count += 1
        return None
```
</details>

### Advanced Plugin Example

<details>
<summary><b>Authentication Plugin</b></summary>

```python
import jwt
from typing import Optional, Dict, Any

from apifrom import API, api, Plugin
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.plugins.base import PluginMetadata, PluginConfig

class AuthPlugin(Plugin):
    """
    Plugin for JWT authentication.
    """
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="auth",
            version="1.0.0",
            description="JWT authentication plugin",
            author="Your Name",
            tags=["security", "authentication"]
        )
    
    def get_config(self) -> PluginConfig:
        return PluginConfig(
            defaults={
                "secret_key": "your-secret-key",
                "algorithm": "HS256",
                "token_prefix": "Bearer",
                "exclude_paths": ["/login", "/public"]
            }
        )
    
    async def pre_request(self, request: Request) -> Request:
        # Skip authentication for excluded paths
        if any(request.path.startswith(path) for path in self.config.get("exclude_paths", [])):
            return request
        
        # Get the authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise ValueError("Missing Authorization header")
        
        # Extract the token
        token_prefix = self.config.get("token_prefix")
        if token_prefix and auth_header.startswith(token_prefix):
            token = auth_header[len(token_prefix):].strip()
        else:
            token = auth_header
        
        # Verify the token
        try:
            payload = jwt.decode(
                token,
                self.config.get("secret_key"),
                algorithms=[self.config.get("algorithm")]
            )
            
            # Store the payload in the request state
            request.state.user = payload
            
        except jwt.PyJWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
        
        return request
```
</details>

## 🏆 Best Practices

When creating plugins, follow these best practices to ensure robustness and maintainability:

<table>
  <tr>
    <th>Practice</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><b>Single Responsibility</b></td>
    <td>Each plugin should have a single, well-defined responsibility</td>
  </tr>
  <tr>
    <td><b>Error Handling</b></td>
    <td>Catch and log exceptions to prevent them from affecting the entire application</td>
  </tr>
  <tr>
    <td><b>Resource Management</b></td>
    <td>Properly initialize and clean up resources in the appropriate lifecycle methods</td>
  </tr>
  <tr>
    <td><b>Logging</b></td>
    <td>Use the plugin's logger for consistent logging</td>
  </tr>
  <tr>
    <td><b>Dependency Management</b></td>
    <td>Clearly specify dependencies and ensure your plugin works correctly with them</td>
  </tr>
  <tr>
    <td><b>Documentation</b></td>
    <td>Document your plugin's functionality, configuration options, and usage</td>
  </tr>
  <tr>
    <td><b>Testing</b></td>
    <td>Write comprehensive tests for your plugin</td>
  </tr>
</table>

### Error Handling

<details>
<summary><b>Robust Error Handling Example</b></summary>

```python
async def pre_request(self, request: Request) -> Request:
    try:
        # Process the request
        result = await self.process_request(request)
        return result
    except Exception as e:
        # Log the error
        self.logger.error(f"Error processing request: {e}", exc_info=True)
        # Don't propagate the error, return the original request
        return request
```
</details>

### Resource Management

<details>
<summary><b>Proper Resource Management Example</b></summary>

```python
def initialize(self, api: API) -> None:
    super().initialize(api)
    # Initialize resources
    self.connection_pool = self.create_connection_pool()
    self.background_task = asyncio.create_task(self.background_worker())

def shutdown(self) -> None:
    # Clean up resources
    if hasattr(self, 'background_task'):
        self.background_task.cancel()
    if hasattr(self, 'connection_pool'):
        self.connection_pool.close()
```
</details>

## 🔗 Related Documentation

- [API Reference](api_reference.md#plugin-system) - Detailed API reference for the plugin system
- [Examples](examples.md#plugin-examples) - More examples of using plugins
- [Getting Started](getting_started.md#plugin-system) - Introduction to the plugin system

## 🤝 Contributing

We welcome contributions to the plugin system! If you have ideas for new features or improvements, please open an issue or submit a pull request.

---

<div align="center">
  <p>
    <a href="../README.md">
      <img src="https://img.shields.io/badge/Back%20to%20README-blue?style=for-the-badge" alt="Back to README" />
    </a>
  </p>
</div> 