"""
Configuration module for APIFromAnything.

This module provides configuration classes and utilities for different environments.
"""

import enum
import logging
import logging.config
import os
from typing import Any, Dict, List, Optional, Type, Union

from apifrom.logging_utils import configure_logging_dict, setup_sentry


class Environment(enum.Enum):
    """Environment types for the application."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class BaseConfig:
    """Base configuration class with common settings."""
    
    # Application settings
    APP_NAME = "APIFromAnything"
    VERSION = "1.0.0"
    DEBUG = False
    
    # Server settings
    HOST = "127.0.0.1"
    PORT = 8000
    WORKERS = 1
    RELOAD = False
    
    # Security settings
    SECRET_KEY = "insecure-secret-key-change-in-production"
    ALLOWED_HOSTS = ["*"]
    CORS_ORIGINS = ["*"]
    HTTPS_ENABLED = False
    CSRF_PROTECTION = False
    RATE_LIMITING_ENABLED = False
    RATE_LIMIT = "100/minute"
    
    # Database settings
    DATABASE_URL = "sqlite:///./app.db"
    DB_POOL_SIZE = 5
    DB_MAX_OVERFLOW = 10
    DB_TIMEOUT = 30
    
    # Cache settings
    CACHE_URL = "memory://"
    CACHE_TTL = 300  # seconds
    
    # Logging settings
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "simple"  # "simple" or "structured"
    LOG_FILE = None
    
    # Monitoring settings
    METRICS_ENABLED = False
    METRICS_PORT = 9090
    
    # Health check settings
    HEALTH_CHECK_PATH = "/health"
    DETAILED_HEALTH_CHECK_PATH = "/health/detailed"
    
    # Middleware settings
    MIDDLEWARE = [
        "apifrom.middleware.logging.LoggingMiddleware",
        "apifrom.middleware.cors.CORSMiddleware",
    ]
    
    # External services
    SENTRY_DSN = None


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""
    
    DEBUG = True
    RELOAD = True
    LOG_LEVEL = "DEBUG"
    METRICS_ENABLED = True


class TestingConfig(BaseConfig):
    """Testing environment configuration."""
    
    DEBUG = True
    DATABASE_URL = "sqlite:///./test.db"
    LOG_LEVEL = "DEBUG"
    LOG_FILE = None
    METRICS_ENABLED = False


class StagingConfig(BaseConfig):
    """Staging environment configuration."""
    
    HOST = "0.0.0.0"
    WORKERS = 2
    HTTPS_ENABLED = True
    CORS_ORIGINS = ["https://staging.example.com"]
    ALLOWED_HOSTS = ["staging.example.com", "api.staging.example.com"]
    LOG_FORMAT = "structured"
    LOG_FILE = "/var/log/apifrom/app.log"
    METRICS_ENABLED = True
    RATE_LIMITING_ENABLED = True
    
    # Additional middleware for staging
    MIDDLEWARE = BaseConfig.MIDDLEWARE + [
        "apifrom.middleware.security.SecurityMiddleware",
    ]


class ProductionConfig(BaseConfig):
    """Production environment configuration."""
    
    HOST = "0.0.0.0"
    WORKERS = 4
    HTTPS_ENABLED = True
    CORS_ORIGINS = ["https://example.com"]
    ALLOWED_HOSTS = ["example.com", "api.example.com"]
    CSRF_PROTECTION = True
    RATE_LIMITING_ENABLED = True
    LOG_FORMAT = "structured"
    LOG_FILE = "/var/log/apifrom/app.log"
    METRICS_ENABLED = True
    
    # Additional middleware for production
    MIDDLEWARE = BaseConfig.MIDDLEWARE + [
        "apifrom.middleware.security.SecurityMiddleware",
        "apifrom.middleware.rate_limiting.RateLimitingMiddleware",
    ]


# Map environment types to configuration classes
CONFIG_MAPPING = {
    Environment.DEVELOPMENT: DevelopmentConfig,
    Environment.TESTING: TestingConfig,
    Environment.STAGING: StagingConfig,
    Environment.PRODUCTION: ProductionConfig,
}


def get_config() -> BaseConfig:
    """
    Get the configuration for the current environment.
    
    Returns:
        The configuration instance for the current environment.
    """
    # Get environment from environment variable
    env_name = os.getenv("ENVIRONMENT", "development").lower()
    
    try:
        env = Environment(env_name)
    except ValueError:
        logging.warning(f"Invalid environment: {env_name}. Using development.")
        env = Environment.DEVELOPMENT
    
    # Get configuration class for the environment
    config_class = CONFIG_MAPPING[env]
    
    # Create configuration instance
    config = config_class()
    
    # Override configuration from environment variables
    for key in dir(config):
        if key.isupper():
            env_value = os.getenv(key)
            if env_value is not None:
                # Convert environment variable to the appropriate type
                attr_value = getattr(config, key)
                if isinstance(attr_value, bool):
                    setattr(config, key, env_value.lower() in ("true", "1", "yes"))
                elif isinstance(attr_value, int):
                    setattr(config, key, int(env_value))
                elif isinstance(attr_value, float):
                    setattr(config, key, float(env_value))
                elif isinstance(attr_value, list):
                    setattr(config, key, env_value.split(","))
                else:
                    setattr(config, key, env_value)
    
    return config


def configure_logging() -> None:
    """Configure logging for the application."""
    config = get_config()
    
    # Configure logging
    logging_config = configure_logging_dict(
        log_level=config.LOG_LEVEL,
        log_format=config.LOG_FORMAT,
        log_file=config.LOG_FILE,
    )
    logging.config.dictConfig(logging_config)
    
    # Set up Sentry if configured
    if config.SENTRY_DSN:
        setup_sentry(
            dsn=config.SENTRY_DSN,
            environment=config.ENVIRONMENT.value,
            release=config.VERSION,
        ) 