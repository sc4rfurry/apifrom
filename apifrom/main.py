"""
Main module for APIFromAnything.

This module contains the main application factory and health check endpoints.
"""

import logging
import platform
import sys
from typing import Dict, List, Optional, Type, Union

from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from apifrom.config import get_config, configure_logging
from apifrom.monitoring import setup_monitoring

# Set up logger
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Configure logging
configure_logging()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        The configured FastAPI application.
    """
    # Create FastAPI app
    app = FastAPI(
        title=config.APP_NAME,
        version=config.VERSION,
        debug=config.DEBUG,
        docs_url="/docs" if config.DEBUG else None,
        redoc_url="/redoc" if config.DEBUG else None,
    )

    # Set up monitoring
    system_info = {
        "version": config.VERSION,
        "python_version": platform.python_version(),
    }
    setup_monitoring(app, system_info)

    # Register health check endpoints
    @app.get(config.HEALTH_CHECK_PATH)
    async def health_check():
        """
        Simple health check endpoint.

        Returns:
            Dict with status information.
        """
        logger.info(f"Health check requested at {config.HEALTH_CHECK_PATH}")
        return {"status": "ok", "version": config.VERSION}

    @app.get(config.DETAILED_HEALTH_CHECK_PATH)
    async def detailed_health_check():
        """
        Detailed health check endpoint.

        Returns:
            Dict with detailed status information.
        """
        logger.info(f"Detailed health check requested at {config.DETAILED_HEALTH_CHECK_PATH}")
        return {
            "status": "ok",
            "version": config.VERSION,
            "environment": config.ENVIRONMENT.value,
            "python_version": platform.python_version(),
            "system": platform.system(),
            "dependencies": {
                "fastapi": "0.95.0",  # Replace with actual version
                "uvicorn": "0.21.1",  # Replace with actual version
            }
        }

    # Load middleware from configuration
    for middleware_class_path in config.MIDDLEWARE:
        try:
            module_path, class_name = middleware_class_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            middleware_class = getattr(module, class_name)
            app.add_middleware(middleware_class)
            logger.info(f"Loaded middleware: {middleware_class_path}")
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load middleware {middleware_class_path}: {str(e)}")

    logger.info(f"Application {config.APP_NAME} v{config.VERSION} started in {config.ENVIRONMENT.value} mode")
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "apifrom.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.RELOAD,
        workers=config.WORKERS,
        log_level=config.LOG_LEVEL.lower(),
    ) 