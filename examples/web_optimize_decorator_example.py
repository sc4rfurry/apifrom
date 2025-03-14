"""
WebOptimize Decorator Example

This example demonstrates how to use the WebOptimize decorator to create API endpoints
that are both web-friendly and performance-optimized.

To run this example:
1. Install the APIFromAnything library
2. Run this script: python web_optimize_decorator_example.py
3. Open your browser to http://localhost:8000/dashboard
"""

import asyncio
import time
import random
from typing import List, Dict, Any
from datetime import datetime

from apifrom.core.app import API
from apifrom.decorators.web_optimize import WebOptimize
from apifrom.server.wsgi import WSGIServer

# Create an API app
app = API()

# Create connection pools
db_pool = WebOptimize.create_pool("database", min_size=5, max_size=20)
external_api_pool = WebOptimize.create_pool("external_api", min_size=2, max_size=10)

# Sample data
products = [
    {"id": 101, "name": "Laptop", "price": 999.99, "category": "Electronics", "in_stock": True},
    {"id": 102, "name": "Smartphone", "price": 499.99, "category": "Electronics", "in_stock": True},
    {"id": 103, "name": "Headphones", "price": 99.99, "category": "Electronics", "in_stock": False},
    {"id": 104, "name": "Monitor", "price": 299.99, "category": "Electronics", "in_stock": True},
    {"id": 105, "name": "Coffee Maker", "price": 79.99, "category": "Appliances", "in_stock": True},
]

users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin"},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com", "role": "user"},
]

# Simulated database and API functions
async def db_query(query, delay=0.1):
    """Simulate a database query with a delay."""
    await asyncio.sleep(delay)
    if "products" in query:
        return products
    elif "users" in query:
        return users
    return []

async def external_api_call(endpoint, delay=0.2):
    """Simulate an external API call with a delay."""
    await asyncio.sleep(delay)
    if endpoint == "weather":
        return {
            "temperature": random.randint(60, 85),
            "condition": random.choice(["Sunny", "Cloudy", "Rainy", "Partly Cloudy"]),
            "humidity": random.randint(30, 90),
            "wind_speed": random.randint(0, 20)
        }
    return {}

# Define API endpoints with WebOptimize decorator
@app.api("/")
@WebOptimize(
    title="API Index",
    description="WebOptimize decorator example",
    enable_profiling=True,
    enable_caching=True,
    cache_ttl=30
)
async def index(request):
    """Return a list of available endpoints."""
    return {
        "endpoints": [
            {"path": "/", "description": "This index page"},
            {"path": "/dashboard", "description": "System dashboard"},
            {"path": "/products", "description": "List of products (cached)"},
            {"path": "/users", "description": "List of users (with connection pooling)"},
            {"path": "/weather", "description": "Current weather (with request coalescing)"},
            {"path": "/batch", "description": "Batch processing example"},
            {"path": "/metrics", "description": "Performance metrics"},
        ]
    }

@app.api("/dashboard")
@WebOptimize(
    title="System Dashboard",
    description="Overview of system performance and data",
    theme="dark",
    enable_profiling=True,
    enable_caching=True,
    cache_ttl=10
)
async def dashboard(request):
    """Return a dashboard with system overview and performance metrics."""
    # Get data for the dashboard
    products_data = await get_products(request)
    users_data = await get_users(request)
    weather_data = await get_weather(request)
    
    # Get performance metrics
    metrics = WebOptimize.get_performance_metrics()
    
    return {
        "system_status": "healthy",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_products": len(products_data),
            "products_in_stock": len([p for p in products_data if p.get("in_stock", False)]),
            "total_users": len(users_data),
        },
        "weather": weather_data,
        "performance": {
            "average_response_time": metrics["profiler"]["average_response_time"],
            "requests_per_minute": metrics["profiler"]["requests_per_minute"],
            "cache_hit_rate": metrics["cache"].get("hit_rate", 0),
            "connection_pool_utilization": metrics["connection_pools"].get("utilization", 0),
        },
        "recent_data": {
            "products": products_data[:3],
            "users": users_data[:3],
        }
    }

@app.api("/products")
@WebOptimize(
    title="Products",
    description="List of all products",
    theme="default",
    enable_profiling=True,
    enable_caching=True,
    cache_ttl=60
)
async def get_products(request):
    """Return a list of products (cached)."""
    # This would normally be a database query, but we're using a simulated delay
    # The cache will prevent this delay on subsequent requests
    await asyncio.sleep(0.2)
    return products

@app.api("/users")
@WebOptimize(
    title="Users",
    description="List of all users",
    theme="light",
    enable_profiling=True,
    enable_connection_pooling=True,
    pool_name="database"
)
async def get_users(request):
    """Return a list of users (with connection pooling)."""
    # Use connection pooling for database access
    async with db_pool.acquire() as connection:
        # Simulate a database query using the connection
        return await db_query("SELECT * FROM users", delay=0.1)

@app.api("/weather")
@WebOptimize(
    title="Weather",
    description="Current weather information",
    enable_profiling=True,
    enable_request_coalescing=True,
    coalesce_window_time=1.0,
    coalesce_max_requests=20
)
async def get_weather(request):
    """Return current weather information (with request coalescing)."""
    # External API calls are expensive, so we coalesce requests
    async with external_api_pool.acquire() as connection:
        return await external_api_call("weather")

@app.api("/batch", method="POST")
@WebOptimize(
    title="Batch Processing",
    description="Process multiple items in a batch",
    enable_profiling=True,
    enable_batch_processing=True,
    batch_size=10,
    batch_wait_time=0.5
)
async def batch_process_items(items: List[Dict[str, Any]]):
    """Process multiple items in a batch."""
    # In a real application, this would process the items in a batch
    # For this example, we'll just simulate a delay and return the processed items
    await asyncio.sleep(0.3)
    
    processed_items = []
    for item in items:
        # Process the item (in this case, just add a timestamp)
        processed_item = item.copy()
        processed_item["processed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        processed_items.append(processed_item)
    
    return {
        "success": True,
        "message": f"Processed {len(processed_items)} items",
        "items": processed_items
    }

@app.api("/metrics")
@WebOptimize(
    title="Performance Metrics",
    description="System performance metrics",
    theme="dark",
    enable_profiling=True,
    enable_caching=True,
    cache_ttl=5
)
async def metrics(request):
    """Return performance metrics."""
    return WebOptimize.get_performance_metrics()

if __name__ == "__main__":
    # Start the server
    print("Starting server on http://localhost:8000")
    print("Try these endpoints in your browser:")
    print("  - http://localhost:8000/")
    print("  - http://localhost:8000/dashboard (dark theme)")
    print("  - http://localhost:8000/products")
    print("  - http://localhost:8000/users (light theme)")
    print("  - http://localhost:8000/weather")
    print("  - http://localhost:8000/metrics")
    
    server = WSGIServer(app, host="localhost", port=8000)
    server.start() 