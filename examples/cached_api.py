"""
Caching example using APIFromAnything.

This example demonstrates how to use the caching middleware to improve
the performance of an API created with the APIFromAnything library.
"""

import asyncio
import logging
import random
import time
from typing import Dict, List

from apifrom import API, api
from apifrom.middleware import CacheMiddleware, CacheControl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create API instance
app = API(
    title="Cached API Example",
    description="An API with caching created with APIFromAnything",
    version="1.0.0",
    debug=True
)

# Add cache middleware
cache_middleware = CacheMiddleware(
    ttl=30,  # Cache for 30 seconds
    methods=["GET"],  # Only cache GET requests
    exclude_routes=["/no-cache"],  # Don't cache these routes
    vary_headers=["Accept-Language"],  # Vary cache by these headers
)
app.add_middleware(cache_middleware)

# Simulated database
products_db = [
    {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
    {"id": 2, "name": "Smartphone", "price": 699.99, "category": "Electronics"},
    {"id": 3, "name": "Headphones", "price": 149.99, "category": "Electronics"},
    {"id": 4, "name": "Coffee Maker", "price": 89.99, "category": "Kitchen"},
    {"id": 5, "name": "Blender", "price": 49.99, "category": "Kitchen"},
]


@api(route="/products", method="GET")
def get_products() -> List[Dict]:
    """
    Get all products.
    
    This endpoint is cached for 30 seconds.
    
    Returns:
        A list of product objects
    """
    # Simulate a slow database query
    logger.info("Fetching products from database...")
    time.sleep(1)  # Simulate 1 second delay
    
    return products_db


@api(route="/products/{product_id}", method="GET")
@CacheControl.cache(ttl=60)  # Override default TTL to 60 seconds
def get_product(product_id: int) -> Dict:
    """
    Get a product by ID.
    
    This endpoint is cached for 60 seconds (overridden TTL).
    
    Args:
        product_id: The ID of the product to retrieve
        
    Returns:
        A product object
    """
    # Simulate a slow database query
    logger.info(f"Fetching product {product_id} from database...")
    time.sleep(0.5)  # Simulate 0.5 second delay
    
    for product in products_db:
        if product["id"] == product_id:
            return product
    
    return {"error": "Product not found"}


@api(route="/products/category/{category}", method="GET")
def get_products_by_category(category: str) -> List[Dict]:
    """
    Get products by category.
    
    This endpoint is cached with the default TTL.
    
    Args:
        category: The category to filter by
        
    Returns:
        A list of product objects
    """
    # Simulate a slow database query
    logger.info(f"Fetching products in category {category} from database...")
    time.sleep(0.8)  # Simulate 0.8 second delay
    
    return [product for product in products_db if product["category"] == category]


@api(route="/no-cache/random", method="GET")
@CacheControl.no_cache
def get_random_number() -> Dict:
    """
    Get a random number.
    
    This endpoint is explicitly not cached.
    
    Returns:
        A random number
    """
    logger.info("Generating random number...")
    return {"random": random.randint(1, 100)}


@api(route="/products", method="POST")
def create_product(name: str, price: float, category: str) -> Dict:
    """
    Create a new product.
    
    POST requests are not cached by default.
    
    Args:
        name: The name of the product
        price: The price of the product
        category: The category of the product
        
    Returns:
        The created product object
    """
    # Simulate a slow database operation
    logger.info("Creating new product in database...")
    time.sleep(0.5)  # Simulate 0.5 second delay
    
    product_id = max(product["id"] for product in products_db) + 1
    new_product = {"id": product_id, "name": name, "price": price, "category": category}
    products_db.append(new_product)
    
    # Clear cache for related endpoints
    cache_middleware.cache.delete("apifrom-cache:GET:/products")
    cache_middleware.cache.delete(f"apifrom-cache:GET:/products/category/{category}")
    
    return new_product


@api(route="/async/products", method="GET")
async def get_products_async() -> List[Dict]:
    """
    Get all products asynchronously.
    
    This endpoint is cached with the default TTL.
    
    Returns:
        A list of product objects
    """
    # Simulate a slow async database query
    logger.info("Fetching products from database asynchronously...")
    await asyncio.sleep(1)  # Simulate 1 second delay
    
    return products_db


@api(route="/cache/clear", method="POST")
def clear_cache() -> Dict:
    """
    Clear the entire cache.
    
    Returns:
        A success message
    """
    logger.info("Clearing cache...")
    cache_middleware.cache.clear()
    return {"message": "Cache cleared successfully"}


if __name__ == "__main__":
    # Run the API server
    app.run(host="0.0.0.0", port=8004) 