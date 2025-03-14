# 🚀 APIFromAnything

<div align="center">

[![PyPI version](https://img.shields.io/badge/pypi-v1.0.0-blue.svg)](https://pypi.org/project/apifrom/)
[![Documentation Status](https://readthedocs.org/projects/apifrom/badge/?version=latest)](https://apifrom.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://pypi.org/project/apifrom/)

**Transform Python functions into powerful API endpoints with minimal code changes**

[Documentation](https://apifrom.readthedocs.io/) | [Quick Start](#-quick-start) | [Examples](#-examples) | [Contributing](#-contributing)

![CodeQL](https://github.com/sc4rfurry/apifrom/workflows/CodeQL/badge.svg)
![Dependency Review](https://github.com/sc4rfurry/apifrom/workflows/Dependency%20Review/badge.svg)

</div>

## 🔍 Overview

APIFromAnything is a powerful Python framework that transforms regular Python functions into fully-featured API endpoints with minimal code changes. It's designed to simplify API development while providing enterprise-grade features like middleware support, security, performance optimizations, and monitoring.

Whether you're building a simple microservice or a complex API backend, APIFromAnything provides the tools you need to get up and running quickly without sacrificing flexibility or performance.

## ✨ Key Features

### Core Functionality
- **🔄 Simple API Creation**: Transform any Python function into an API endpoint with a single decorator
- **⚡ Full Async Support**: Native support for async/await throughout the entire framework
- **🧩 Extensible Architecture**: Modular design allows for easy customization and extension

### Middleware & Processing
- **🔄 Middleware System**: Comprehensive middleware architecture for request/response processing
- **🔄 Request/Response Hooks**: Customize request handling and response generation
- **📦 Content Negotiation**: Automatic content type negotiation and serialization

### Security Features
- **🔒 Authentication**: JWT, API key, Basic auth, OAuth2 support built-in
- **🛡️ Protection**: CORS, CSRF, XSS protection mechanisms
- **🔐 Security Headers**: CSP, HSTS, and other security headers
- **🔍 Rate Limiting**: Configurable rate limiting to prevent abuse

### Performance Optimizations
- **⚡ Caching**: Multi-level caching system (memory, Redis, file)
- **🔌 Connection Pooling**: Efficient database and HTTP connection management
- **🔄 Request Coalescing**: Combine duplicate requests to reduce load
- **📦 Batch Processing**: Process multiple requests efficiently

### Documentation & Monitoring
- **📚 API Docs**: Automatic OpenAPI documentation generation
- **📊 Metrics**: Built-in metrics collection with Prometheus integration
- **📈 Monitoring**: Grafana dashboards for visualization
- **🚨 Alerting**: Pre-configured alerts for common issues

## 📥 Installation

### Using pip (Recommended)

```bash
pip install apifrom
```

### Using Poetry

```bash
poetry add apifrom
```

### From Source

```bash
git clone https://github.com/sc4rfurry/apifrom.git
cd apifrom
pip install -e .
```

## 🚀 Quick Start

### Basic API

```python
from apifrom import API

app = API()

@app.api("/hello/{name}")
def hello(name: str):
    return {"message": f"Hello, {name}!"}

if __name__ == "__main__":
    app.run()
```

### Async API

```python
from apifrom import API

app = API()

@app.api("/hello/{name}")
async def hello(name: str):
    # Async operations can be performed here
    return {"message": f"Hello, {name}!"}

if __name__ == "__main__":
    app.run()
```

### With Middleware

```python
from apifrom import API
from apifrom.middleware import CORSMiddleware, LoggingMiddleware

app = API()

# Add middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_middleware(LoggingMiddleware)

@app.api("/hello/{name}")
async def hello(name: str):
    return {"message": f"Hello, {name}!"}

if __name__ == "__main__":
    app.run()
```

## 📝 Examples

### RESTful API

```python
from apifrom import API
from apifrom.security import JWTAuth

app = API()
auth = JWTAuth(secret_key="your-secret-key")

# User database (in-memory for example)
users = {}

@app.api("/users", methods=["POST"])
async def create_user(username: str, email: str, password: str):
    user_id = len(users) + 1
    users[user_id] = {"id": user_id, "username": username, "email": email}
    return {"id": user_id, "username": username, "email": email}

@app.api("/users/{user_id}", methods=["GET"])
@auth.requires_auth
async def get_user(user_id: int):
    if user_id not in users:
        return {"error": "User not found"}, 404
    return users[user_id]

@app.api("/users", methods=["GET"])
@auth.requires_auth
async def list_users():
    return list(users.values())

if __name__ == "__main__":
    app.run()
```

### With Caching

```python
from apifrom import API
from apifrom.cache import MemoryCache

app = API()
cache = MemoryCache()

@app.api("/expensive-operation")
@cache.cached(ttl=300)  # Cache for 5 minutes
async def expensive_operation():
    # Simulate expensive operation
    import time
    time.sleep(2)
    return {"result": "This was expensive to calculate"}

if __name__ == "__main__":
    app.run()
```

### With Database

```python
from apifrom import API
from apifrom.db import Database

app = API()
db = Database("sqlite:///app.db")

@app.api("/posts", methods=["GET"])
async def get_posts():
    async with db.connection() as conn:
        posts = await conn.fetch("SELECT * FROM posts")
    return {"posts": posts}

@app.api("/posts", methods=["POST"])
async def create_post(title: str, content: str):
    async with db.connection() as conn:
        post_id = await conn.execute(
            "INSERT INTO posts (title, content) VALUES (?, ?)",
            title, content
        )
    return {"id": post_id, "title": title, "content": content}

if __name__ == "__main__":
    app.run()
```

### Example Directory

The project includes a comprehensive set of examples in the `examples/` directory:

| Example | Description |
|---------|-------------|
| `simple_api.py` | Basic API with simple endpoints |
| `async_api.py` | Demonstrates async/await functionality |
| `combined_example.py` | Comprehensive example with multiple features |
| `security_api.py` | Shows various security features |
| `web_decorator_example_updated.py` | Demonstrates the web decorator for HTML endpoints |
| `database_api.py` | Database integration example |
| `cached_api.py` | Caching implementation |
| `cors_api.py` | CORS middleware usage |
| `csrf_protected_api.py` | CSRF protection |
| `rate_limited_api.py` | Rate limiting functionality |
| `monitoring_api.py` | Metrics and monitoring |
| `serverless_api.py` | Serverless deployment |
| `vercel_serverless_api.py` | Vercel-specific deployment |
| `netlify_functions_api.py` | Netlify-specific deployment |
| `file_upload_api.py` | File upload handling |
| `error_handling_api.py` | Error handling and validation |
| `pagination_api.py` | Pagination implementation |
| `batch_processing_api.py` | Batch processing for performance |
| `advanced_caching_api.py` | Advanced caching strategies |
| `plugin_api.py` | Plugin system usage |
| `advanced_plugin_api.py` | Advanced plugin development |

To run any example:

```bash
# Navigate to the examples directory
cd examples

# Run an example
python simple_api.py
```

## 🏗️ Architecture

APIFromAnything follows a modular architecture designed for flexibility and extensibility:

```
┌─────────────────────────────────────────────────────────┐
│                      APIFromAnything                     │
├─────────────┬─────────────┬───────────────┬─────────────┤
│   Routing   │  Middleware │   Security    │ Performance │
├─────────────┼─────────────┼───────────────┼─────────────┤
│ HTTP Server │   Database  │ Documentation │  Monitoring │
└─────────────┴─────────────┴───────────────┴─────────────┘
```

- **Core**: The central component that manages the application lifecycle
- **Routing**: Maps URLs to handler functions
- **Middleware**: Processes requests and responses
- **Security**: Handles authentication, authorization, and protection
- **Performance**: Optimizes API performance
- **HTTP Server**: Manages HTTP connections
- **Database**: Provides database connectivity
- **Documentation**: Generates API documentation
- **Monitoring**: Collects and exposes metrics

## 🔄 Middleware

APIFromAnything includes a comprehensive middleware system:

| Middleware | Description |
|------------|-------------|
| `CORSMiddleware` | Handles Cross-Origin Resource Sharing |
| `CSRFMiddleware` | Protects against Cross-Site Request Forgery |
| `SecurityHeadersMiddleware` | Adds security headers to responses |
| `RateLimitingMiddleware` | Limits request rates |
| `CacheMiddleware` | Caches responses |
| `LoggingMiddleware` | Logs requests and responses |
| `CompressionMiddleware` | Compresses response data |
| `AuthenticationMiddleware` | Handles authentication |

Example:

```python
from apifrom import API
from apifrom.middleware import CORSMiddleware, SecurityHeadersMiddleware

app = API()
app.add_middleware(CORSMiddleware, allow_origins=["https://example.com"])
app.add_middleware(SecurityHeadersMiddleware)
```

## 🔒 Security

APIFromAnything provides comprehensive security features:

### Authentication

```python
from apifrom import API
from apifrom.security import JWTAuth

app = API()
auth = JWTAuth(secret_key="your-secret-key")

@app.api("/protected")
@auth.requires_auth
async def protected():
    return {"message": "This is protected"}
```

### CORS Protection

```python
from apifrom import API
from apifrom.middleware import CORSMiddleware

app = API()
app.add_middleware(CORSMiddleware, 
                  allow_origins=["https://example.com"],
                  allow_methods=["GET", "POST"],
                  allow_headers=["Content-Type", "Authorization"])
```

### Rate Limiting

```python
from apifrom import API
from apifrom.middleware import RateLimitingMiddleware

app = API()
app.add_middleware(RateLimitingMiddleware, 
                  limit=100,
                  period=60,  # 100 requests per minute
                  key_func=lambda request: request.client.host)
```

## ⚡ Performance

APIFromAnything includes several performance optimization features:

### Caching

```python
from apifrom import API
from apifrom.cache import RedisCache

app = API()
cache = RedisCache(url="redis://localhost:6379/0")

@app.api("/expensive-operation")
@cache.cached(ttl=300)  # Cache for 5 minutes
async def expensive_operation():
    # Expensive operation here
    return {"result": "Expensive calculation"}
```

### Connection Pooling

```python
from apifrom import API
from apifrom.db import Database

app = API()
db = Database("postgresql://user:password@localhost/db",
             min_size=5,
             max_size=20)

@app.api("/users")
async def get_users():
    async with db.connection() as conn:
        # Connection is taken from the pool
        users = await conn.fetch("SELECT * FROM users")
    # Connection is returned to the pool
    return {"users": users}
```

### Request Coalescing

```python
from apifrom import API
from apifrom.performance import coalesce_requests

app = API()

@app.api("/data/{id}")
@coalesce_requests
async def get_data(id: str):
    # If multiple requests for the same ID arrive simultaneously,
    # only one database query will be executed
    # and the result will be shared among all requests
    return {"data": f"Data for {id}"}
```

## 📊 Monitoring

APIFromAnything includes built-in monitoring capabilities:

### Prometheus Metrics

```python
from apifrom import API
from apifrom.monitoring import setup_monitoring

app = API()
setup_monitoring(app)

# Metrics will be available at /metrics
```

### Custom Metrics

```python
from apifrom import API
from apifrom.monitoring import Counter, Histogram

app = API()

# Define custom metrics
request_counter = Counter("app_requests_total", "Total requests")
request_latency = Histogram("app_request_latency_seconds", "Request latency")

@app.api("/hello")
async def hello():
    # Increment counter
    request_counter.inc()
    
    # Measure latency
    with request_latency.time():
        # Your code here
        return {"message": "Hello, World!"}
```

## 🚀 Deployment

### GitHub Actions

This project includes GitHub Actions workflows for continuous integration and deployment:

- **Python Package**: Tests the code and publishes the package to PyPI when a new tag is pushed
- **Documentation**: Builds and deploys the documentation to GitHub Pages
- **ReadTheDocs**: Triggers a build on ReadTheDocs when documentation files are updated

To set up these workflows:

1. Push your code to a GitHub repository
2. Set up the necessary secrets in your repository settings:
   - `PYPI_API_TOKEN`: API token for publishing to PyPI

For detailed instructions, see the [GitHub and ReadTheDocs Deployment Guide](https://apifrom.readthedocs.io/en/latest/github_deployment/).

### Serverless

#### AWS Lambda

```python
# handler.py
from apifrom import API
from apifrom.adapters import LambdaAdapter

app = API()

@app.api("/hello/{name}")
async def hello(name: str):
    return {"message": f"Hello, {name}!"}

# Lambda handler
handler = LambdaAdapter(app).handler
```

#### Vercel

```python
# api/index.py
from apifrom import API
from apifrom.adapters import VercelAdapter

app = API()

@app.api("/hello/{name}")
async def hello(name: str):
    return {"message": f"Hello, {name}!"}

# Vercel handler
handler = VercelAdapter(app).handler
```

## 📚 Documentation

For full documentation, visit [apifrom.readthedocs.io](https://apifrom.readthedocs.io/en/latest/).

The documentation includes:

- **Getting Started Guide**: Quick introduction to APIFromAnything
- **Core Concepts**: Detailed explanation of the framework's architecture
- **API Reference**: Complete reference for all classes and functions
- **Middleware Guide**: How to use and create middleware
- **Security Guide**: How to secure your API
- **Performance Guide**: How to optimize your API's performance
- **Deployment Guide**: How to deploy your API to various platforms
- **Examples**: Comprehensive examples for common use cases

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/sc4rfurry/apifrom.git
cd apifrom

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Code Style

We use [Black](https://github.com/psf/black) for code formatting and [isort](https://github.com/PyCQA/isort) for import sorting:

```bash
# Format code
black .

# Sort imports
isort .
```

### Testing

We use [pytest](https://docs.pytest.org/) for testing:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=apifrom

# Run specific tests
pytest tests/test_api.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <p>Made with ❤️ by the sc4rfurry</p>
  <p>
    <a href="https://github.com/sc4rfurry/apifrom">GitHub</a> •
    <a href="https://pypi.org/project/apifrom/">PyPI</a> •
    <a href="https://apifrom.readthedocs.io/en/latest/">Documentation</a>
  </p>
</div>
