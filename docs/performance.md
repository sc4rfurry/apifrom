# Performance Optimization in APIFromAnything

This guide covers the performance optimization features available in APIFromAnything and best practices for optimizing your APIs.

## Introduction

APIFromAnything includes comprehensive performance optimization features to help you build fast and efficient APIs. These features include:

- Caching
- Request coalescing
- Batch processing
- Connection pooling
- Profiling
- Auto-tuning

## Async Support in Performance Optimization

As of version 1.0.0, all performance optimization features in APIFromAnything fully support async/await. This allows you to use async functions with all performance optimization features:

```python
from apifrom import API, api
from apifrom.performance import Web
import asyncio

app = API()

@api(route="/products", method="GET")
@Web.optimize(
    cache_ttl=30,  # Cache for 30 seconds
    profile=True,  # Enable profiling
    connection_pool=True,  # Enable connection pooling
    request_coalescing=True,  # Enable request coalescing
    batch_processing=True,  # Enable batch processing
    batch_size=100  # Set batch size
)
async def get_products():
    # Simulate an async database query
    await asyncio.sleep(0.1)
    # Your code here (automatically optimized)
    return {"products": [...]}
```

## Web Decorator for Easy Optimization

The `@Web.optimize` decorator allows you to optimize any API endpoint with a single line of code:

```python
from apifrom import API, api
from apifrom.performance import Web

app = API()

@api(route="/products", method="GET")
@Web.optimize(
    cache_ttl=30,  # Cache for 30 seconds
    profile=True,  # Enable profiling
    connection_pool=True,  # Enable connection pooling
    request_coalescing=True,  # Enable request coalescing
    batch_processing=True,  # Enable batch processing
    batch_size=100  # Set batch size
)
def get_products():
    # Your code here (automatically optimized)
    return {"products": [...]}
```

## Caching

Caching improves performance by storing the results of expensive operations and reusing them:

### Basic Caching

```python
from apifrom import API, api
from apifrom.performance import cache

app = API()

@api(route="/expensive-operation", method="GET")
@cache(ttl=60)  # Cache for 60 seconds
def expensive_operation():
    # Expensive operation
    return {"result": "expensive computation"}
```

### Advanced Caching

```python
from apifrom import API, api
from apifrom.performance import cache
from apifrom.core.request import Request

app = API()

@api(route="/user/{user_id}", method="GET")
@cache(
    ttl=300,  # Cache for 5 minutes
    key_builder=lambda request: f"user:{request.path_params['user_id']}",  # Custom cache key
    storage="redis",  # Use Redis for storage
    redis_url="redis://localhost:6379/0",  # Redis URL
    invalidate_on_update=True,  # Invalidate cache on update
    stale_while_revalidate=True,  # Serve stale data while revalidating
    stale_ttl=3600,  # Stale data TTL in seconds
    vary_by_headers=["Authorization"],  # Vary cache by headers
    vary_by_query_params=["version"],  # Vary cache by query parameters
)
def get_user(request: Request, user_id: int):
    # Expensive database query
    return {"id": user_id, "name": "John Doe"}
```

### Cache Invalidation

```python
from apifrom import API, api
from apifrom.performance import cache, invalidate_cache

app = API()

@api(route="/user/{user_id}", method="GET")
@cache(ttl=300, key_prefix="user")
def get_user(user_id: int):
    # Expensive database query
    return {"id": user_id, "name": "John Doe"}

@api(route="/user/{user_id}", method="PUT")
def update_user(user_id: int, name: str):
    # Update user in database
    
    # Invalidate cache
    invalidate_cache(f"user:user:{user_id}")
    
    return {"id": user_id, "name": name}
```

### Cache Middleware

```python
from apifrom import API
from apifrom.middleware import CacheMiddleware

app = API()

# Add cache middleware
app.add_middleware(
    CacheMiddleware(
        ttl=60,  # Cache TTL in seconds
        max_size=1000,  # Maximum number of cached responses
        key_builder=None,  # Custom function to build cache keys
        storage="memory",  # Storage backend (memory, redis)
        redis_url=None,  # Redis URL (if using redis storage)
        include_query_params=True,  # Include query parameters in cache key
        include_headers=False,  # Include headers in cache key
        cache_control=True,  # Add Cache-Control headers to responses
    )
)
```

## Request Coalescing

Request coalescing combines duplicate concurrent requests into a single backend operation:

```python
from apifrom import API, api
from apifrom.performance import coalesce_requests

app = API()

@api(route="/popular-data", method="GET")
@coalesce_requests(
    ttl=30,  # Cache TTL in seconds
    max_wait_time=0.05,  # Maximum wait time in seconds
    key_builder=lambda request: request.url.path,  # Custom key builder
)
async def get_popular_data():
    """
    This endpoint might receive many identical requests under load.
    With request coalescing, only one database query will be executed
    even if 100 users request this data at the same time.
    """
    # Expensive database query or API call
    return {"data": "expensive computation result"}
```

## Batch Processing

Batch processing improves performance by grouping multiple similar operations:

### Batch Processing Decorator

```python
from apifrom import API, api
from apifrom.performance import batch_process

app = API()

@api(route="/users", method="POST")
@batch_process(
    max_batch_size=100,  # Maximum batch size
    max_wait_time=0.1,  # Maximum wait time in seconds
    key_builder=lambda request: request.url.path,  # Custom key builder
)
async def create_users(user_data_batch):
    """
    This endpoint will collect individual user creation requests and
    process them in batches of up to 100 users or after 0.1 seconds.
    """
    # Bulk insert all users in the batch
    return db.bulk_insert_users(user_data_batch)
```

### Ad-hoc Batch Operations

```python
from apifrom import API, api
from apifrom.performance import BatchProcessor
from typing import List, Dict

app = API()

@api(route="/batch-operations", method="POST")
async def batch_operations(operations: List[Dict]):
    """Process multiple operations in a single request."""

    # Define a function to process each operation
    async def process_operation(op):
        op_type = op["type"]
        if op_type == "create":
            return await db.create_item(op["data"])
        elif op_type == "update":
            return await db.update_item(op["id"], op["data"])
        elif op_type == "delete":
            return await db.delete_item(op["id"])

    # Process all operations in efficient batches
    results = await BatchProcessor.map(
        process_operation,
        operations,
        batch_size=20,  # Process in batches of 20
        worker_count=4,  # Use 4 workers
        timeout=30,  # Timeout after 30 seconds
    )

    return {"results": results}
```

## Connection Pooling

Connection pooling efficiently manages database and external service connections:

```python
from apifrom import API, api
from apifrom.performance import ConnectionPool
import aiohttp

app = API()

# Create a connection pool
http_pool = ConnectionPool(
    factory=lambda: aiohttp.ClientSession(),
    min_size=5,  # Minimum pool size
    max_size=20,  # Maximum pool size
    max_idle_time=60,  # Maximum idle time in seconds
    cleanup_interval=300,  # Cleanup interval in seconds
)

@api(route="/external-api", method="GET")
async def call_external_api(url: str):
    # Get a connection from the pool
    async with http_pool.acquire() as session:
        # Use the connection
        async with session.get(url) as response:
            return await response.json()
```

## Profiling

Profiling helps you identify performance bottlenecks:

### Profiling Decorator

```python
from apifrom import API, api
from apifrom.performance import profile

app = API()

@api(route="/users", method="GET")
@profile(
    enabled=True,  # Enable profiling
    log_level="INFO",  # Log level
    include_memory=True,  # Include memory usage
    include_sql=True,  # Include SQL queries
    include_http=True,  # Include HTTP requests
    threshold=100,  # Log only if execution time exceeds threshold (ms)
)
def get_users():
    # Your code here
    return {"users": [...]}
```

### Profiling Middleware

```python
from apifrom import API
from apifrom.middleware import ProfileMiddleware

app = API()

# Add profiling middleware
app.add_middleware(
    ProfileMiddleware(
        enabled=True,  # Enable profiling
        log_level="INFO",  # Log level
        include_memory=True,  # Include memory usage
        include_sql=True,  # Include SQL queries
        include_http=True,  # Include HTTP requests
        threshold=100,  # Log only if execution time exceeds threshold (ms)
    )
)
```

### Accessing Profiling Data

```python
from apifrom.performance import Profiler

# Get profiling data
profiling_data = Profiler.get_data()

# Print profiling data
for endpoint, data in profiling_data.items():
    print(f"Endpoint: {endpoint}")
    print(f"Average response time: {data['avg_response_time']} ms")
    print(f"Min response time: {data['min_response_time']} ms")
    print(f"Max response time: {data['max_response_time']} ms")
    print(f"Request count: {data['request_count']}")
    print(f"Error count: {data['error_count']}")
    print(f"Error rate: {data['error_rate']}%")
    print(f"Memory usage: {data['memory_usage']} MB")
    print(f"SQL queries: {data['sql_queries']}")
    print(f"HTTP requests: {data['http_requests']}")
```

## Auto-Tuning

Auto-tuning automatically adjusts performance parameters based on real-time metrics:

```python
from apifrom import API, api
from apifrom.performance import auto_tune

app = API()

@api(route="/users", method="GET")
@auto_tune(
    enabled=True,  # Enable auto-tuning
    cache_ttl_range=(10, 3600),  # Cache TTL range in seconds
    batch_size_range=(10, 1000),  # Batch size range
    connection_pool_size_range=(5, 100),  # Connection pool size range
    target_response_time=100,  # Target response time in ms
    adjustment_interval=300,  # Adjustment interval in seconds
    learning_rate=0.1,  # Learning rate
)
def get_users():
    # Your code here
    return {"users": [...]}
```

## Asynchronous Programming

Asynchronous programming improves performance by allowing your API to handle multiple requests concurrently:

```python
from apifrom import API, api
import asyncio

app = API()

@api(route="/users", method="GET")
async def get_users():
    # Simulate an asynchronous database query
    await asyncio.sleep(0.1)
    return {"users": [...]}

@api(route="/products", method="GET")
async def get_products():
    # Simulate an asynchronous database query
    await asyncio.sleep(0.1)
    return {"products": [...]}

@api(route="/dashboard", method="GET")
async def get_dashboard():
    # Fetch users and products concurrently
    users_task = asyncio.create_task(get_users())
    products_task = asyncio.create_task(get_products())
    
    # Wait for both tasks to complete
    users, products = await asyncio.gather(users_task, products_task)
    
    return {
        "users": users["users"],
        "products": products["products"]
    }
```

## Performance Best Practices

### 1. Use Caching

Cache expensive operations:

```python
from apifrom import API, api
from apifrom.performance import cache

app = API()

@api(route="/expensive-operation", method="GET")
@cache(ttl=60)  # Cache for 60 seconds
def expensive_operation():
    # Expensive operation
    return {"result": "expensive computation"}
```

### 2. Use Asynchronous Programming

Use asynchronous programming for I/O-bound operations:

```python
from apifrom import API, api
import asyncio

app = API()

@api(route="/users", method="GET")
async def get_users():
    # Asynchronous database query
    await asyncio.sleep(0.1)
    return {"users": [...]}
```

### 3. Use Connection Pooling

Use connection pooling for database and external service connections:

```python
from apifrom import API, api
from apifrom.performance import ConnectionPool
import aiohttp

app = API()

# Create a connection pool
http_pool = ConnectionPool(
    factory=lambda: aiohttp.ClientSession(),
    min_size=5,
    max_size=20
)

@api(route="/external-api", method="GET")
async def call_external_api(url: str):
    # Get a connection from the pool
    async with http_pool.acquire() as session:
        # Use the connection
        async with session.get(url) as response:
            return await response.json()
```

### 4. Use Batch Processing

Use batch processing for multiple similar operations:

```python
from apifrom import API, api
from apifrom.performance import batch_process

app = API()

@api(route="/users", method="POST")
@batch_process(max_batch_size=100, max_wait_time=0.1)
async def create_users(user_data_batch):
    # Bulk insert all users in the batch
    return db.bulk_insert_users(user_data_batch)
```

### 5. Use Request Coalescing

Use request coalescing for popular endpoints:

```python
from apifrom import API, api
from apifrom.performance import coalesce_requests

app = API()

@api(route="/popular-data", method="GET")
@coalesce_requests(ttl=30, max_wait_time=0.05)
async def get_popular_data():
    # Expensive database query or API call
    return {"data": "expensive computation result"}
```

### 6. Use Profiling

Use profiling to identify performance bottlenecks:

```python
from apifrom import API, api
from apifrom.performance import profile

app = API()

@api(route="/users", method="GET")
@profile(enabled=True)
def get_users():
    # Your code here
    return {"users": [...]}
```

### 7. Use Pagination

Use pagination for large result sets:

```python
from apifrom import API, api
from typing import List, Dict, Optional

app = API()

@api(route="/users", method="GET")
def get_users(page: int = 1, limit: int = 10) -> Dict:
    """Get a paginated list of users."""
    # Calculate offset
    offset = (page - 1) * limit
    
    # Get users from database with pagination
    users = db.get_users(offset=offset, limit=limit)
    total = db.count_users()
    
    return {
        "users": users,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }
```

### 8. Use Compression

Use compression to reduce response size:

```python
from apifrom import API
from apifrom.middleware import CompressionMiddleware

app = API()

# Add compression middleware
app.add_middleware(
    CompressionMiddleware(
        minimum_size=1000,  # Minimum response size to compress
        level=9,  # Compression level (1-9)
        algorithms=["gzip", "deflate", "br"],  # Supported compression algorithms
    )
)
```

### 9. Use Database Optimization

Optimize database queries:

```python
from apifrom import API, api
from apifrom.database import Database

app = API()

# Create a database connection
db = Database("sqlite:///app.db")

@api(route="/users", method="GET")
def get_users():
    # Use optimized query with selected fields
    users = db.query(
        "SELECT id, name, email FROM users LIMIT 10",
        use_cache=True,  # Use query cache
        cache_ttl=60,  # Cache TTL in seconds
    )
    return {"users": users}
```

### 10. Use the Web Decorator

Use the Web decorator for easy optimization:

```python
from apifrom import API, api
from apifrom.performance import Web

app = API()

@api(route="/products", method="GET")
@Web.optimize(
    cache_ttl=30,
    profile=True,
    connection_pool=True,
    request_coalescing=True,
    batch_processing=True,
    batch_size=100
)
def get_products():
    # Your code here (automatically optimized)
    return {"products": [...]}
```

## Performance Monitoring

APIFromAnything includes tools for monitoring performance:

### Metrics Collection

```python
from apifrom import API, api
from apifrom.monitoring import MetricsCollector, MetricsMiddleware, PrometheusExporter

# Create an API instance
app = API()

# Create a metrics collector
metrics = MetricsCollector()

# Register the metrics middleware
app.add_middleware(MetricsMiddleware(collector=metrics))

# Create a Prometheus exporter
prometheus_exporter = PrometheusExporter(collector=metrics)

# Define a metrics endpoint
@api(route="/metrics", method="GET")
def metrics():
    """Return Prometheus metrics."""
    return prometheus_exporter.export()
```

### Available Metrics

APIFromAnything collects various metrics:

- **Request Counts**: Total requests processed
- **Response Times**: Distribution of response times
- **Status Codes**: Count of responses by status code
- **Endpoint Usage**: Most frequently called endpoints
- **Error Rates**: Percentage of requests that result in errors
- **Custom Metrics**: Define your own metrics to track

## Conclusion

APIFromAnything provides comprehensive performance optimization features to help you build fast and efficient APIs. By using these features and following best practices, you can ensure that your APIs perform well under load and provide a good user experience. 