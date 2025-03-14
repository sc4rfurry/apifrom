"""
Web Decorator with Performance Optimization Example

This example demonstrates how to use the Web decorator along with performance
optimization features like profiling, caching, connection pooling, request
coalescing, and batch processing.

To run this example:
1. Install the APIFromAnything library
2. Run this script: python web_optimization_example.py
3. Open your browser to http://localhost:8000/dashboard
"""

import asyncio
import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime

from apifrom.core.app import API
from apifrom.decorators.web import Web
from apifrom.server.wsgi import WSGIServer
from apifrom.performance.profiler import APIProfiler, ProfileMiddleware
from apifrom.performance.cache_optimizer import CacheOptimizer, OptimizedCacheMiddleware
from apifrom.performance.connection_pool import ConnectionPool, PoolManager
from apifrom.performance.request_coalescing import coalesce_requests
from apifrom.performance.batch_processing import batch_process, BatchProcessor
from apifrom.performance.optimization import OptimizationAnalyzer, OptimizationConfig, OptimizationLevel

# Create an API app
app = API()

# Set up performance optimization components
profiler = APIProfiler()
cache_optimizer = CacheOptimizer()
pool_manager = PoolManager()
optimization_analyzer = OptimizationAnalyzer(
    config=OptimizationConfig(
        level=OptimizationLevel.BALANCED,
        enable_profiling=True,
        enable_caching=True,
        enable_connection_pooling=True,
        enable_request_coalescing=True,
        enable_batch_processing=True
    )
)

# Add middleware
app.add_middleware(ProfileMiddleware(profiler))
app.add_middleware(OptimizedCacheMiddleware(cache_optimizer))

# Create connection pools
db_pool = pool_manager.create_pool(
    name="database",
    min_size=5,
    max_size=20,
    validate_func=lambda conn: True  # In a real app, this would check if the connection is valid
)

external_api_pool = pool_manager.create_pool(
    name="external_api",
    min_size=2,
    max_size=10
)

# Sample data
products = [
    {"id": 101, "name": "Laptop", "price": 999.99, "category": "Electronics", "in_stock": True},
    {"id": 102, "name": "Smartphone", "price": 499.99, "category": "Electronics", "in_stock": True},
    {"id": 103, "name": "Headphones", "price": 99.99, "category": "Electronics", "in_stock": False},
    {"id": 104, "name": "Monitor", "price": 299.99, "category": "Electronics", "in_stock": True},
    {"id": 105, "name": "Coffee Maker", "price": 79.99, "category": "Appliances", "in_stock": True},
    {"id": 106, "name": "Blender", "price": 49.99, "category": "Appliances", "in_stock": True},
    {"id": 107, "name": "Toaster", "price": 29.99, "category": "Appliances", "in_stock": False},
    {"id": 108, "name": "Desk", "price": 199.99, "category": "Furniture", "in_stock": True},
    {"id": 109, "name": "Chair", "price": 149.99, "category": "Furniture", "in_stock": True},
    {"id": 110, "name": "Bookshelf", "price": 129.99, "category": "Furniture", "in_stock": False},
]

users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin"},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com", "role": "user"},
    {"id": 4, "name": "Diana", "email": "diana@example.com", "role": "manager"},
]

orders = [
    {"id": 1001, "user_id": 1, "products": [101, 104], "total": 1299.98, "status": "completed", "date": "2023-01-15"},
    {"id": 1002, "user_id": 2, "products": [102], "total": 499.99, "status": "shipped", "date": "2023-02-20"},
    {"id": 1003, "user_id": 3, "products": [103, 106], "total": 149.98, "status": "processing", "date": "2023-03-05"},
    {"id": 1004, "user_id": 4, "products": [105, 108, 109], "total": 429.97, "status": "completed", "date": "2023-03-10"},
    {"id": 1005, "user_id": 1, "products": [110], "total": 129.99, "status": "processing", "date": "2023-04-01"},
]

# Simulated database functions
async def db_query(query, delay=0.1):
    """Simulate a database query with a delay."""
    await asyncio.sleep(delay)
    if "products" in query:
        return products
    elif "users" in query:
        return users
    elif "orders" in query:
        return orders
    return []

async def db_get_by_id(collection, id_value, delay=0.05):
    """Simulate getting an item by ID from the database."""
    await asyncio.sleep(delay)
    if collection == "products":
        for product in products:
            if product["id"] == id_value:
                return product
    elif collection == "users":
        for user in users:
            if user["id"] == id_value:
                return user
    elif collection == "orders":
        for order in orders:
            if order["id"] == id_value:
                return order
    return None

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
    elif endpoint == "exchange_rates":
        return {
            "USD": 1.0,
            "EUR": random.uniform(0.9, 1.1),
            "GBP": random.uniform(0.7, 0.9),
            "JPY": random.uniform(100, 150)
        }
    return {}

# Define API endpoints with Web decorator and performance optimizations
@app.api("/")
@Web(title="API Dashboard", description="Performance-optimized API with Web interface")
async def index(request):
    """Return a list of available endpoints."""
    return {
        "endpoints": [
            {"path": "/", "description": "This index page"},
            {"path": "/dashboard", "description": "System dashboard with performance metrics"},
            {"path": "/products", "description": "List of products (cached)"},
            {"path": "/users", "description": "List of users (with connection pooling)"},
            {"path": "/orders", "description": "List of orders (with request coalescing)"},
            {"path": "/weather", "description": "Current weather (with request coalescing)"},
            {"path": "/exchange-rates", "description": "Current exchange rates (with connection pooling)"},
            {"path": "/batch/products", "description": "Create products in batch"},
            {"path": "/batch/operations", "description": "Perform batch operations"},
            {"path": "/performance", "description": "Performance metrics and recommendations"},
        ]
    }

@app.api("/dashboard")
@Web(
    title="System Dashboard",
    description="Overview of system performance and data",
    theme="dark"
)
async def dashboard(request):
    """Return a dashboard with system overview and performance metrics."""
    # Get data for the dashboard (using various optimization techniques)
    products_data = await get_products(request)
    users_data = await get_users(request)
    orders_data = await get_orders(request)
    weather_data = await get_weather(request)
    exchange_rates = await get_exchange_rates(request)
    
    # Get performance metrics
    profile_data = profiler.get_endpoint_stats()
    cache_stats = cache_optimizer.get_stats()
    pool_stats = pool_manager.get_stats()
    
    # Calculate some statistics
    total_products = len(products_data)
    products_in_stock = len([p for p in products_data if p.get("in_stock", False)])
    total_users = len(users_data)
    total_orders = len(orders_data)
    completed_orders = len([o for o in orders_data if o.get("status") == "completed"])
    total_sales = sum(o.get("total", 0) for o in orders_data)
    
    return {
        "system_status": "healthy",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_products": total_products,
            "products_in_stock": products_in_stock,
            "total_users": total_users,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "total_sales": round(total_sales, 2)
        },
        "weather": weather_data,
        "exchange_rates": exchange_rates,
        "performance": {
            "average_response_time": profiler.get_average_response_time(),
            "requests_per_minute": profiler.get_requests_per_minute(),
            "cache_hit_rate": cache_stats.get("hit_rate", 0),
            "connection_pool_utilization": pool_stats.get("utilization", 0),
            "endpoint_performance": profile_data
        },
        "recent_data": {
            "products": products_data[:3],
            "users": users_data[:3],
            "orders": orders_data[:3]
        }
    }

@app.api("/products")
@Web(title="Products", description="List of all products", theme="default")
@profiler.profile_endpoint
@cache_optimizer.optimize(ttl=60)  # Cache for 60 seconds
async def get_products(request):
    """Return a list of products (cached)."""
    # This would normally be a database query, but we're using a simulated delay
    # The cache will prevent this delay on subsequent requests
    await asyncio.sleep(0.2)
    return products

@app.api("/users")
@Web(title="Users", description="List of all users", theme="light")
@profiler.profile_endpoint
async def get_users(request):
    """Return a list of users (with connection pooling)."""
    # Use connection pooling for database access
    async with db_pool.acquire() as connection:
        # Simulate a database query using the connection
        return await db_query("SELECT * FROM users", delay=0.1)

@app.api("/orders")
@Web(title="Orders", description="List of all orders")
@profiler.profile_endpoint
@coalesce_requests(window_time=0.5)  # Coalesce requests within 0.5 seconds
async def get_orders(request):
    """Return a list of orders (with request coalescing)."""
    # This endpoint might receive many concurrent requests
    # Request coalescing will ensure only one database query is made
    return await db_query("SELECT * FROM orders", delay=0.3)

@app.api("/weather")
@Web(title="Weather", description="Current weather information")
@profiler.profile_endpoint
@coalesce_requests(window_time=1.0, max_requests=20)  # Coalesce up to 20 requests within 1 second
async def get_weather(request):
    """Return current weather information (with request coalescing)."""
    # External API calls are expensive, so we coalesce requests
    async with external_api_pool.acquire() as connection:
        return await external_api_call("weather")

@app.api("/exchange-rates")
@Web(title="Exchange Rates", description="Current exchange rates")
@profiler.profile_endpoint
@cache_optimizer.optimize(ttl=300)  # Cache for 5 minutes
async def get_exchange_rates(request):
    """Return current exchange rates (cached and with connection pooling)."""
    # Use connection pooling for external API access
    async with external_api_pool.acquire() as connection:
        return await external_api_call("exchange_rates")

@app.api("/batch/products", method="POST")
@Web(title="Batch Product Creation", description="Create multiple products in a single request")
@profiler.profile_endpoint
@batch_process(batch_size=10, max_wait_time=0.5)
async def create_products_batch(products_batch: List[Dict[str, Any]]):
    """Create multiple products in a batch."""
    # In a real application, this would insert the products into a database
    # For this example, we'll just simulate a delay and return the created products
    await asyncio.sleep(0.3)
    
    created_products = []
    for product_data in products_batch:
        # Generate a new product ID
        product_id = max(p["id"] for p in products) + 1
        
        # Create the new product
        new_product = {
            "id": product_id,
            "name": product_data.get("name", "Unknown"),
            "price": product_data.get("price", 0.0),
            "category": product_data.get("category", "Uncategorized"),
            "in_stock": product_data.get("in_stock", True)
        }
        
        # Add to our products list (in a real app, this would be a database insert)
        products.append(new_product)
        created_products.append(new_product)
    
    return {
        "success": True,
        "message": f"Created {len(created_products)} products",
        "products": created_products
    }

@app.api("/batch/operations", method="POST")
@Web(title="Batch Operations", description="Perform multiple operations in a single request")
@profiler.profile_endpoint
async def batch_operations(operations: List[Dict[str, Any]]):
    """Process multiple operations in a single request."""
    
    # Define a function to process each operation
    async def process_operation(op):
        op_type = op.get("type")
        
        if op_type == "get_product":
            return await db_get_by_id("products", op.get("id"))
        
        elif op_type == "get_user":
            return await db_get_by_id("users", op.get("id"))
        
        elif op_type == "get_order":
            return await db_get_by_id("orders", op.get("id"))
        
        elif op_type == "create_product":
            # Generate a new product ID
            product_id = max(p["id"] for p in products) + 1
            
            # Create the new product
            new_product = {
                "id": product_id,
                "name": op.get("data", {}).get("name", "Unknown"),
                "price": op.get("data", {}).get("price", 0.0),
                "category": op.get("data", {}).get("category", "Uncategorized"),
                "in_stock": op.get("data", {}).get("in_stock", True)
            }
            
            # Add to our products list
            products.append(new_product)
            return new_product
        
        else:
            return {"error": f"Unknown operation type: {op_type}"}
    
    # Process all operations in efficient batches
    results = await BatchProcessor.map(
        process_operation,
        operations,
        batch_size=5,
        worker_count=3
    )
    
    return {
        "success": True,
        "message": f"Processed {len(results)} operations",
        "results": results
    }

@app.api("/performance")
@Web(title="Performance Metrics", description="System performance metrics and optimization recommendations")
async def performance_metrics(request):
    """Return performance metrics and optimization recommendations."""
    # Get performance data
    profile_data = profiler.get_endpoint_stats()
    cache_stats = cache_optimizer.get_stats()
    pool_stats = pool_manager.get_stats()
    
    # Generate optimization recommendations
    recommendations = optimization_analyzer.analyze(
        profile_data=profile_data,
        cache_stats=cache_stats,
        pool_stats=pool_stats
    )
    
    return {
        "metrics": {
            "endpoints": profile_data,
            "cache": cache_stats,
            "connection_pools": pool_stats,
            "system": {
                "uptime": profiler.get_uptime(),
                "total_requests": profiler.get_total_requests(),
                "average_response_time": profiler.get_average_response_time(),
                "requests_per_minute": profiler.get_requests_per_minute(),
                "error_rate": profiler.get_error_rate()
            }
        },
        "recommendations": recommendations,
        "optimization_config": optimization_analyzer.config.to_dict()
    }

if __name__ == "__main__":
    # Start the server
    print("Starting server on http://localhost:8000")
    print("Try these endpoints in your browser:")
    print("  - http://localhost:8000/")
    print("  - http://localhost:8000/dashboard (dark theme)")
    print("  - http://localhost:8000/products")
    print("  - http://localhost:8000/users (light theme)")
    print("  - http://localhost:8000/orders")
    print("  - http://localhost:8000/weather")
    print("  - http://localhost:8000/exchange-rates")
    print("  - http://localhost:8000/performance")
    
    server = WSGIServer(app, host="localhost", port=8000)
    server.start() 