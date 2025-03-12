"""An example of using the performance optimization features of the APIFromAnything library."""
import time
import asyncio
from typing import List, Dict, Any

from apifrom import API, api
from apifrom.performance import Web
from apifrom.performance.profiler import APIProfiler
from apifrom.performance.cache_optimizer import CacheOptimizer
from apifrom.performance.connection_pool import ConnectionPool
from apifrom.performance.request_coalescing import coalesce_requests
from apifrom.performance.batch_processing import batch_process, BatchProcessor

# Create an API instance
app = API(
    title="Performance Optimization Example",
    description="An example of using the performance optimization features of the APIFromAnything library",
    version="1.0.0"
)

# Create a profiler for the API
profiler = APIProfiler()

# Create a cache optimizer
cache_optimizer = CacheOptimizer()

# Create a connection pool
connection_pool = ConnectionPool()

# Simulated database for demonstration
users_db = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
]

# Simulated expensive operation
def expensive_operation(delay=0.5):
    """Simulate an expensive operation."""
    time.sleep(delay)
    return {"result": "Expensive operation completed"}

# Example 1: Using the Web decorator for comprehensive optimization
@api(route="/optimized", method="GET")
@Web.optimize(
    cache_ttl=30,  # Cache for 30 seconds
    profile=True,  # Enable profiling
    connection_pool=True,  # Enable connection pooling
    request_coalescing=True,  # Enable request coalescing
    batch_processing=True  # Enable batch processing
)
def optimized_endpoint(param: str = "default"):
    """
    An endpoint optimized with the Web decorator.
    
    Args:
        param: A parameter to vary the response
        
    Returns:
        The result of the operation
    """
    # This operation will be optimized with caching, profiling, etc.
    result = expensive_operation(0.2)
    result["param"] = param
    return result

# Example 2: Using individual optimization components
@api(route="/users/{user_id}", method="GET")
@profiler.profile_endpoint
@cache_optimizer.optimize
@connection_pool.with_connection
def get_user(user_id: int):
    """
    Get a user by ID with performance optimizations.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        The user data
    """
    # Simulate database lookup
    time.sleep(0.1)
    
    for user in users_db:
        if user["id"] == user_id:
            return user
    
    return {"error": "User not found"}

# Example 3: Request coalescing for high-traffic endpoints
@api(route="/popular-data", method="GET")
@coalesce_requests(window_time=0.5, max_requests=10)
async def get_popular_data():
    """
    Get popular data with request coalescing.
    
    This endpoint might receive many identical requests under load.
    With request coalescing, only one database query will be executed
    even if multiple users request this data at the same time.
    
    Returns:
        The popular data
    """
    # Simulate an expensive database query
    await asyncio.sleep(0.5)
    return {"data": "Popular data that many users request simultaneously"}

# Example 4: Batch processing for bulk operations
@api(route="/users/batch", method="POST")
@batch_process(batch_size=10, max_wait_time=0.5)
def create_users_batch(users_batch: List[Dict[str, Any]]):
    """
    Create multiple users in a batch.
    
    Args:
        users_batch: A list of user data to create
        
    Returns:
        The created users
    """
    # Simulate batch database insert
    time.sleep(0.3)
    
    # Process the batch
    created_users = []
    for i, user_data in enumerate(users_batch):
        user = {
            "id": len(users_db) + i + 1,
            "name": user_data.get("name", "Unknown"),
            "email": user_data.get("email", "unknown@example.com")
        }
        created_users.append(user)
    
    # In a real app, we would add these to the database
    # users_db.extend(created_users)
    
    return created_users

# Example 5: Ad-hoc batch operations
@api(route="/batch-operations", method="POST")
async def batch_operations(operations: List[Dict[str, Any]]):
    """
    Process multiple operations in a single request.
    
    Args:
        operations: A list of operations to perform
        
    Returns:
        The results of the operations
    """
    # Define a function to process each operation
    async def process_operation(op):
        op_type = op.get("type")
        
        if op_type == "get_user":
            user_id = op.get("user_id")
            # Simulate database lookup
            await asyncio.sleep(0.1)
            for user in users_db:
                if user["id"] == user_id:
                    return {"type": "get_user", "result": user}
            return {"type": "get_user", "error": "User not found"}
        
        elif op_type == "create_user":
            user_data = op.get("data", {})
            # Simulate database insert
            await asyncio.sleep(0.2)
            user = {
                "id": len(users_db) + 1,
                "name": user_data.get("name", "Unknown"),
                "email": user_data.get("email", "unknown@example.com")
            }
            return {"type": "create_user", "result": user}
        
        else:
            return {"type": "unknown", "error": "Unknown operation type"}
    
    # Process all operations in efficient batches
    results = await BatchProcessor.map(
        process_operation,
        operations,
        batch_size=5,
        worker_count=3
    )
    
    return {"results": results}

# Example 6: Performance metrics endpoint
@api(route="/metrics", method="GET")
def get_metrics():
    """
    Get performance metrics for the API.
    
    Returns:
        Performance metrics
    """
    metrics = {
        "profiler": {
            endpoint: {
                "call_count": data["call_count"],
                "avg_response_time": sum(data["response_times"]) / len(data["response_times"]) if data["response_times"] else 0,
                "max_response_time": max(data["response_times"]) if data["response_times"] else 0,
                "min_response_time": min(data["response_times"]) if data["response_times"] else 0
            }
            for endpoint, data in profiler.profile_data.items()
        },
        "cache": {
            "size": len(cache_optimizer.cache),
            "keys": list(cache_optimizer.cache.keys())
        },
        "connection_pool": {
            "connections": connection_pool.connections
        }
    }
    
    return metrics

# Run the API server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
