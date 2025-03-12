# Environment Configuration and Monitoring

This document provides a summary of the environment configuration and monitoring setup for APIFromAnything.

## Environment Configuration

APIFromAnything now supports environment-specific configuration through a flexible configuration system. This allows you to customize the application for different environments (development, testing, staging, production) and override settings with environment variables.

### Configuration Structure

The configuration system is structured as follows:

1. **Base Configuration**: Common settings shared across all environments
2. **Environment-Specific Configurations**: Settings specific to each environment (development, testing, staging, production)
3. **Environment Variable Overrides**: Settings that can be overridden with environment variables

### Configuration Files

- `apifrom/config.py`: The main configuration module that defines the configuration classes and utilities
- `.env.template`: A template for environment variables that can be used to create environment-specific `.env` files
- `docker/.env.production`: Production-specific environment variables for Docker deployment

### Usage

To use the configuration system in your code:

```python
from apifrom.config import get_config

config = get_config()

# Access configuration values
debug_mode = config.DEBUG
app_name = config.APP_NAME
```

### Environment Types

The following environment types are supported:

- **Development**: For local development with debugging enabled
- **Testing**: For running tests
- **Staging**: For pre-production testing
- **Production**: For production deployment

### Configuration Categories

The configuration system includes settings for:

- **Application**: Name, version, debug mode
- **Server**: Host, port, workers, reload
- **Security**: Secret key, allowed hosts, CORS origins, HTTPS, CSRF, rate limiting
- **Database**: URL, pool size, max overflow, timeout
- **Cache**: URL, TTL
- **Logging**: Level, format, file
- **Monitoring**: Metrics, port
- **Health Check**: Paths
- **Middleware**: List of middleware classes
- **External Services**: Sentry DSN

## Logging

APIFromAnything now includes enhanced logging capabilities through a structured logging system.

### Logging Features

- **Structured JSON Logging**: Logs are output in JSON format for easier parsing and analysis
- **Log Rotation**: Logs are automatically rotated to prevent disk space issues
- **Contextual Logging**: Additional context can be added to log messages
- **Performance Logging**: Decorators for logging function execution time
- **Sentry Integration**: Error tracking with Sentry

### Logging Configuration

Logging is configured in `apifrom/logging_utils.py` and includes:

- **Formatters**: For structured JSON and simple text formats
- **Handlers**: For console and file output
- **Loggers**: For different components of the application

### Usage

To use the logging system in your code:

```python
from apifrom.logging_utils import get_logger, log_execution_time

# Get a logger
logger = get_logger(__name__)

# Log messages
logger.info("This is an info message")
logger.error("This is an error message", extra={"user_id": 123})

# Log execution time
@log_execution_time(level=logging.DEBUG)
async def my_function():
    # Function code here
    pass
```

## Monitoring

APIFromAnything now includes a comprehensive monitoring system based on Prometheus, Grafana, and AlertManager.

### Monitoring Components

- **Prometheus**: For metrics collection and storage
- **Grafana**: For visualization and dashboards
- **AlertManager**: For alert management and notifications

### Metrics

The monitoring system collects various metrics:

- **Request Metrics**: Count, latency, in-progress, errors
- **Database Metrics**: Query latency
- **Cache Metrics**: Hit/miss counts
- **System Metrics**: Version, Python version

### Dashboards

A pre-configured Grafana dashboard is included that provides insights into the performance and health of your API.

### Alerts

Pre-configured alerts notify you when certain conditions are met, such as high latency, error rates, or resource usage.

### Integration

The monitoring system is integrated with the application through a Prometheus middleware and utility classes for tracking custom metrics.

## Docker Compose Setup

The Docker Compose setup includes services for:

- **API**: The main application
- **Database**: PostgreSQL for data storage
- **Redis**: For caching
- **Prometheus**: For metrics collection
- **Grafana**: For visualization
- **AlertManager**: For alert management
- **Nginx**: For reverse proxy

## Getting Started

To get started with the environment configuration and monitoring:

1. Copy `.env.template` to `.env` and customize for your environment
2. Start the Docker Compose stack: `docker-compose up -d`
3. Access the monitoring tools:
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (default credentials: admin/admin)
   - AlertManager: http://localhost:9093

## Best Practices

- Use environment-specific configuration files for different environments
- Override sensitive settings with environment variables
- Monitor both application-level and system-level metrics
- Set up alerts for critical conditions
- Regularly review and adjust alert thresholds
- Implement proper logging alongside metrics for better debugging 