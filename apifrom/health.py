"""
Health check module for APIFromAnything.

This module provides health check endpoints and utilities to monitor the health
of the application and its dependencies.
"""

import os
import time
import platform
import psutil
from typing import Dict, Any, Optional
import asyncio

# Global variable to track application start time
START_TIME = time.time()

async def check_database_connection(db_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Check the database connection health.
    
    Args:
        db_url: Optional database URL to check
        
    Returns:
        Dict with database health status
    """
    # This is a placeholder. In a real application, you would check your actual database
    # For example, with SQLAlchemy:
    # from sqlalchemy import create_engine
    # engine = create_engine(db_url)
    # try:
    #     with engine.connect() as conn:
    #         conn.execute("SELECT 1")
    #     return {"status": "healthy", "latency_ms": latency}
    # except Exception as e:
    #     return {"status": "unhealthy", "error": str(e)}
    
    await asyncio.sleep(0.01)  # Simulate a database check
    return {
        "status": "healthy",
        "latency_ms": 10,
        "connection_pool": {
            "used": 0,
            "available": 10,
            "max": 10
        }
    }

async def check_redis_connection(redis_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Check the Redis connection health.
    
    Args:
        redis_url: Optional Redis URL to check
        
    Returns:
        Dict with Redis health status
    """
    # This is a placeholder. In a real application, you would check your actual Redis
    # For example, with aioredis:
    # import aioredis
    # redis = await aioredis.create_redis_pool(redis_url)
    # try:
    #     await redis.ping()
    #     return {"status": "healthy", "latency_ms": latency}
    # except Exception as e:
    #     return {"status": "unhealthy", "error": str(e)}
    # finally:
    #     redis.close()
    #     await redis.wait_closed()
    
    await asyncio.sleep(0.01)  # Simulate a Redis check
    return {
        "status": "healthy",
        "latency_ms": 5
    }

async def get_system_health() -> Dict[str, Any]:
    """
    Get system health metrics.
    
    Returns:
        Dict with system health metrics
    """
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "cpu": {
            "percent": cpu_percent,
            "cores": psutil.cpu_count()
        },
        "memory": {
            "total_mb": memory.total / (1024 * 1024),
            "available_mb": memory.available / (1024 * 1024),
            "percent": memory.percent
        },
        "disk": {
            "total_gb": disk.total / (1024 * 1024 * 1024),
            "free_gb": disk.free / (1024 * 1024 * 1024),
            "percent": disk.percent
        }
    }

async def get_application_health() -> Dict[str, Any]:
    """
    Get application health metrics.
    
    Returns:
        Dict with application health metrics
    """
    uptime_seconds = time.time() - START_TIME
    
    return {
        "status": "healthy",
        "version": os.environ.get("APP_VERSION", "1.0.0"),
        "uptime_seconds": uptime_seconds,
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": platform.python_version()
    }

async def get_complete_health_check() -> Dict[str, Any]:
    """
    Get a complete health check of the application and its dependencies.
    
    Returns:
        Dict with complete health check information
    """
    # Run all health checks concurrently
    app_health, system_health, db_health, redis_health = await asyncio.gather(
        get_application_health(),
        get_system_health(),
        check_database_connection(),
        check_redis_connection()
    )
    
    # Determine overall status
    overall_status = "healthy"
    if db_health["status"] != "healthy" or redis_health["status"] != "healthy":
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "application": app_health,
        "system": system_health,
        "database": db_health,
        "redis": redis_health
    }

async def get_simple_health_check() -> Dict[str, str]:
    """
    Get a simple health check response.
    
    Returns:
        Dict with simple health status
    """
    return {"status": "healthy"} 