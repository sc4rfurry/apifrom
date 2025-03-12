# Advanced Caching in APIFromAnything

This document provides detailed information about the advanced caching features available in APIFromAnything.

## Overview

APIFromAnything provides a sophisticated caching system that allows you to cache API responses with fine-grained control. The advanced caching features include:

- Multiple cache backends (in-memory, Redis, Memcached)
- Distributed caching support
- Tag-based and dependency-based cache invalidation strategies
- Cache control decorators for fine-grained control
- Automatic cache key generation based on request parameters
- Cache headers management

## Cache Backends

### In-Memory Cache

The simplest cache backend that stores cache entries in memory. This is suitable for single-instance applications or development environments.

```python
from apifrom.middleware.cache_advanced import MemoryCacheBackend

cache_backend = MemoryCacheBackend()
```

### Redis Cache

A distributed cache backend that uses Redis as the storage engine. This is suitable for multi-instance applications or production environments.

```python
from apifrom.middleware.cache_advanced import RedisCacheBackend

cache_backend = RedisCacheBackend(
    url="redis://localhost:6379/0",
    prefix="apifrom:"  # Optional prefix for Redis keys
)
```

### Memcached Cache

A distributed cache backend that uses Memcached as the storage engine. This is suitable for multi-instance applications or production environments.

```python
from apifrom.middleware.cache_advanced import MemcachedCacheBackend

cache_backend = MemcachedCacheBackend(
    servers=["localhost:11211"],
    prefix="apifrom:"  # Optional prefix for Memcached keys
)
```

## Cache Invalidation Strategies

### Tag-Based Invalidation

Tag-based invalidation allows you to associate cache entries with one or more tags, and then invalidate all cache entries with a specific tag.

```python
from apifrom.middleware.cache_advanced import TagBasedInvalidation

invalidation_strategy = TagBasedInvalidation(cache_backend)
```

### Dependency-Based Invalidation

Dependency-based invalidation allows you to associate cache entries with one or more dependencies, and then invalidate all cache entries that depend on a specific dependency.

```python
from apifrom.middleware.cache_advanced import DependencyBasedInvalidation

invalidation_strategy = DependencyBasedInvalidation(cache_backend)
```

## Advanced Cache Middleware

The `AdvancedCacheMiddleware` is the main component that integrates the cache backend and invalidation strategy with your API application.

```python
from apifrom.middleware.cache_advanced import AdvancedCacheMiddleware

cache_middleware = AdvancedCacheMiddleware(
    cache_backend=cache_backend,
    invalidation_strategy=invalidation_strategy,
    ttl=60,  # Default TTL of 60 seconds
    key_prefix="cache:",  # Optional prefix for cache keys
    vary_headers=["Accept", "Accept-Language"]  # Headers to include in the cache key
)

app.add_middleware(cache_middleware)
```

## Cache Control Decorators

### Cache Decorator

The `@CacheControl.cache` decorator allows you to enable caching for a specific endpoint with custom options.

```python
from apifrom.middleware.cache_advanced import CacheControl

@api(app)
@CacheControl.cache(
    ttl=60,  # Cache for 60 seconds
    tags=["posts"],  # Associate with tags (for tag-based invalidation)
    dependencies=["posts"]  # Associate with dependencies (for dependency-based invalidation)
)
async def get_posts() -> List[Dict]:
    """Get all posts."""
    return posts_db
```

### No Cache Decorator

The `@CacheControl.no_cache` decorator allows you to disable caching for a specific endpoint.

```python
from apifrom.middleware.cache_advanced import CacheControl

@api(app)
@CacheControl.no_cache
async def get_stats() -> Dict:
    """Get real-time statistics."""
    return {"users": 100, "posts": 200, "comments": 300}
```

### Invalidate Decorator

The `@CacheControl.invalidate` decorator allows you to invalidate cache entries after an endpoint is called.

```python
from apifrom.middleware.cache_advanced import CacheControl

@api(app)
@CacheControl.invalidate(["posts", "post:{post_id}"])
async def update_post(post_id: int, title: str = None, content: str = None) -> Dict:
    """Update a post."""
    # Update the post in the database
    return {"message": "Post updated"}
```

## Advanced Usage Examples

### Blog API with Dependency-Based Invalidation

```python
from apifrom import API, api
from apifrom.middleware.cache_advanced import (
    AdvancedCacheMiddleware,
    RedisCacheBackend,
    DependencyBasedInvalidation,
    CacheControl
)
from typing import Dict, List
import asyncio

# Create an API instance
app = API(title="Blog API")

# Create a Redis cache backend
try:
    cache_backend = RedisCacheBackend(url="redis://localhost:6379/0")
except ImportError:
    from apifrom.middleware.cache_advanced import MemoryCacheBackend
    cache_backend = MemoryCacheBackend()

# Create a dependency-based invalidation strategy
invalidation_strategy = DependencyBasedInvalidation(cache_backend)

# Add advanced cache middleware
app.add_middleware(
    AdvancedCacheMiddleware(
        cache_backend=cache_backend,
        invalidation_strategy=invalidation_strategy,
        ttl=60
    )
)

# In-memory database for demonstration
posts_db = [
    {"id": 1, "title": "First Post", "content": "This is the first post"},
    {"id": 2, "title": "Second Post", "content": "This is the second post"},
]

# API endpoints
@api(app)
@CacheControl.cache(ttl=30, dependencies=["posts"])
async def get_posts() -> List[Dict]:
    """Get all posts."""
    return posts_db

@api(app)
@CacheControl.cache(ttl=60, dependencies=["posts", "post:{post_id}"])
async def get_post(post_id: int) -> Dict:
    """Get a post by ID."""
    for post in posts_db:
        if post["id"] == post_id:
            return post
    return {"error": "Post not found"}

@api(app)
@CacheControl.invalidate(["posts"])
async def create_post(title: str, content: str) -> Dict:
    """Create a new post."""
    post_id = max(post["id"] for post in posts_db) + 1
    new_post = {"id": post_id, "title": title, "content": content}
    posts_db.append(new_post)
    return {"message": "Post created", "post": new_post}

@api(app)
@CacheControl.invalidate(["posts", "post:{post_id}"])
async def update_post(post_id: int, title: str = None, content: str = None) -> Dict:
    """Update a post."""
    for post in posts_db:
        if post["id"] == post_id:
            if title is not None:
                post["title"] = title
            if content is not None:
                post["content"] = content
            return {"message": "Post updated", "post": post}
    return {"error": "Post not found"}

@api(app)
@CacheControl.invalidate(["posts", "post:{post_id}"])
async def delete_post(post_id: int) -> Dict:
    """Delete a post."""
    for i, post in enumerate(posts_db):
        if post["id"] == post_id:
            del posts_db[i]
            return {"message": "Post deleted"}
    return {"error": "Post not found"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### E-commerce API with Tag-Based Invalidation

```python
from apifrom import API, api
from apifrom.middleware.cache_advanced import (
    AdvancedCacheMiddleware,
    MemcachedCacheBackend,
    TagBasedInvalidation,
    CacheControl
)
from typing import Dict, List
import asyncio

# Create an API instance
app = API(title="E-commerce API")

# Create a Memcached cache backend
try:
    cache_backend = MemcachedCacheBackend(servers=["localhost:11211"])
except ImportError:
    from apifrom.middleware.cache_advanced import MemoryCacheBackend
    cache_backend = MemoryCacheBackend()

# Create a tag-based invalidation strategy
invalidation_strategy = TagBasedInvalidation(cache_backend)

# Add advanced cache middleware
app.add_middleware(
    AdvancedCacheMiddleware(
        cache_backend=cache_backend,
        invalidation_strategy=invalidation_strategy,
        ttl=60
    )
)

# In-memory database for demonstration
products_db = [
    {"id": 1, "name": "Product 1", "price": 10.0, "category_id": 1},
    {"id": 2, "name": "Product 2", "price": 20.0, "category_id": 1},
    {"id": 3, "name": "Product 3", "price": 30.0, "category_id": 2},
]

categories_db = [
    {"id": 1, "name": "Category 1"},
    {"id": 2, "name": "Category 2"},
]

# API endpoints
@api(app)
@CacheControl.cache(ttl=30, tags=["products"])
async def get_products() -> List[Dict]:
    """Get all products."""
    return products_db

@api(app)
@CacheControl.cache(ttl=60, tags=["products", "product:{product_id}"])
async def get_product(product_id: int) -> Dict:
    """Get a product by ID."""
    for product in products_db:
        if product["id"] == product_id:
            return product
    return {"error": "Product not found"}

@api(app)
@CacheControl.cache(ttl=30, tags=["categories"])
async def get_categories() -> List[Dict]:
    """Get all categories."""
    return categories_db

@api(app)
@CacheControl.cache(ttl=60, tags=["categories", "category:{category_id}"])
async def get_category(category_id: int) -> Dict:
    """Get a category by ID."""
    for category in categories_db:
        if category["id"] == category_id:
            return category
    return {"error": "Category not found"}

@api(app)
@CacheControl.cache(ttl=30, tags=["products", "category:{category_id}"])
async def get_products_by_category(category_id: int) -> List[Dict]:
    """Get products by category."""
    category_products = []
    for product in products_db:
        if product["category_id"] == category_id:
            category_products.append(product)
    return category_products

@api(app)
@CacheControl.invalidate(["products", "product:{product_id}"])
async def update_product(product_id: int, name: str = None, price: float = None) -> Dict:
    """Update a product."""
    for product in products_db:
        if product["id"] == product_id:
            if name is not None:
                product["name"] = name
            if price is not None:
                product["price"] = price
            return {"message": "Product updated", "product": product}
    return {"error": "Product not found"}

@api(app)
@CacheControl.invalidate(["categories", "category:{category_id}"])
async def update_category(category_id: int, name: str = None) -> Dict:
    """Update a category."""
    for category in categories_db:
        if category["id"] == category_id:
            if name is not None:
                category["name"] = name
            return {"message": "Category updated", "category": category}
    return {"error": "Category not found"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## Performance Considerations

### Cache Key Generation

The cache key is generated based on the request method, path, query parameters, and vary headers. This ensures that different requests get different cache entries.

### Cache Invalidation

Cache invalidation is a critical aspect of caching. The advanced caching system provides two invalidation strategies:

- **Tag-based invalidation**: Associate cache entries with tags and invalidate all entries with a specific tag.
- **Dependency-based invalidation**: Associate cache entries with dependencies and invalidate all entries that depend on a specific dependency.

### Distributed Caching

For multi-instance applications, it's recommended to use a distributed cache backend like Redis or Memcached. This ensures that all instances share the same cache and invalidation events.

## Best Practices

1. **Use appropriate TTLs**: Set appropriate time-to-live (TTL) values for your cache entries based on how frequently the data changes.

2. **Choose the right invalidation strategy**: Use tag-based invalidation for simple scenarios and dependency-based invalidation for more complex scenarios.

3. **Be careful with cache keys**: Ensure that your cache keys are unique for different requests but consistent for the same request.

4. **Monitor cache performance**: Keep an eye on cache hit rates and invalidation events to ensure your caching strategy is effective.

5. **Test cache invalidation**: Thoroughly test your cache invalidation logic to ensure that stale data is not served to users.

6. **Consider cache stampede**: Implement mechanisms to prevent cache stampede (many concurrent requests trying to rebuild the cache at the same time).

7. **Use vary headers wisely**: Include only the headers that affect the response content in the vary headers list.

## Conclusion

The advanced caching system in APIFromAnything provides a powerful and flexible way to improve the performance of your API. By using the appropriate cache backend, invalidation strategy, and cache control decorators, you can achieve significant performance improvements while maintaining data consistency. 