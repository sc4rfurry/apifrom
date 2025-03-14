# APIFromAnything Documentation

<div align="center">
  <img src="https://img.shields.io/badge/APIFromAnything-Transform%20Python%20Functions%20to%20APIs-blue?style=for-the-badge&logo=python" alt="APIFromAnything" />
  <br/>
  <strong>Transform any Python function into a production-ready REST API endpoint in seconds</strong>
</div>

Welcome to the official documentation for **APIFromAnything**, a powerful Python library designed to transform ordinary Python functions into fully-functional REST API endpoints using a decorator-based approach.

## Version 1.0.0 - Production Ready

APIFromAnything is now production-ready with version 1.0.0! This release includes:

- Comprehensive test suite with high code coverage
- Production-grade security features
- Performance optimizations for high-traffic scenarios
- Detailed documentation and examples
- Support for multiple deployment environments
- Full async/await support throughout the codebase

## Overview

APIFromAnything is designed to be robust, extensible, and high-performance, with features like automatic routing, input validation, output serialization, error handling, and documentation generation. It's perfect for quickly creating APIs from existing code, building microservices, or developing serverless functions.

```python
from apifrom import API, api

app = API(title="My API")

@api(route="/hello/{name}")
def hello(name: str, greeting: str = "Hello") -> dict:
    """Say hello to someone."""
    return {"message": f"{greeting}, {name}!"}

# That's it! You now have a fully functioning API endpoint
```

## Key Features

- **🧩 Simple Decorator API**: Transform any Python function into an API endpoint with a single decorator
- **🔍 Type-Based Validation**: Automatic request validation based on Python type hints
- **🔄 Automatic Serialization**: Convert Python objects to JSON responses automatically
- **🛣️ Path & Query Parameters**: Support for path and query parameters with automatic type conversion
- **⚡ Asynchronous Support**: First-class support for async/await functions
- **🔌 Middleware System**: Extensible middleware system for request/response processing
- **🔒 Security Features**: Built-in support for JWT, API key, Basic auth, OAuth2, CORS, CSRF, security headers, and more
- **📚 OpenAPI Documentation**: Automatic generation of OpenAPI/Swagger documentation
- **📊 Monitoring & Metrics**: Track API performance and usage with comprehensive metrics collection
- **🚀 Performance Optimization**: Tools for profiling, caching, connection pooling, and batch processing
- **☁️ Serverless Ready**: Deploy to AWS Lambda, Google Cloud Functions, Azure Functions, Vercel, and Netlify
- **🔌 Plugin System**: Extend and customize functionality with a powerful plugin architecture

## Documentation Structure

This documentation is organized into the following sections:

- **[Getting Started](getting_started.md)**: Quick start guide and basic concepts
- **[Core Concepts](core_concepts.md)**: Detailed explanation of the core concepts and components
- **[API Reference](api_reference.md)**: Comprehensive reference for all modules and functions
- **[Middleware](middleware.md)**: Guide to using and creating middleware components
- **[Security](security.md)**: Detailed information about security features
- **[Performance](performance.md)**: Performance optimization techniques
- **[Plugins](plugins.md)**: Guide to using and creating plugins
- **[Advanced Caching](advanced_caching.md)**: Advanced caching strategies
- **[Serverless](serverless.md)**: Deploying to serverless environments
- **[Deployment](deployment.md)**: General deployment guidelines
- **[Testing](testing.md)**: Testing your APIs
- **[Troubleshooting](troubleshooting.md)**: Common issues and solutions
- **[Contributing](contributing.md)**: Guidelines for contributing to the project
- **[Examples](examples.md)**: Comprehensive examples demonstrating various features

## Installation

```bash
# Basic installation
pip install apifrom

# With all optional dependencies
pip install "apifrom[all]"
```

## Quick Links

- [GitHub Repository](https://github.com/sc4rfurry/apifrom)
- [PyPI Package](https://pypi.org/project/apifrom/)
- [Issue Tracker](https://github.com/sc4rfurry/apifrom/issues)
- [Changelog](https://github.com/sc4rfurry/apifrom/blob/main/CHANGELOG.md)

## License

APIFromAnything is licensed under the MIT License. See the [LICENSE](https://github.com/apifrom/apifrom/blob/main/LICENSE) file for details. 

```{toctree}
:maxdepth: 2
:caption: Contents:

contents
getting_started
core_concepts
api_reference
autoapi/index
middleware
security
performance
testing
deployment
deployment_guide
serverless
advanced_caching
plugins
production_checklist
troubleshooting
migration_guide
monitoring
environment_and_monitoring
production_readiness
github_deployment
examples
contributing
contributing_to_docs
requirements
```
