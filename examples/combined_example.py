"""
A comprehensive example of using the APIFromAnything library with multiple features.
"""
from typing import Dict, List, Optional
import asyncio

from apifrom import APIApp
from apifrom.middleware import CORSMiddleware, LoggingMiddleware, RateLimitingMiddleware
from apifrom.security import JWTAuth
from apifrom.cache import MemoryCache

# Create an API instance
app = APIApp(
    title="Comprehensive API Example",
    description="A comprehensive example of using the APIFromAnything library",
    version="1.0.0",
    debug=True
)

# Add middleware
app.add_middleware(CORSMiddleware, 
                  allow_origins=["*"],
                  allow_methods=["GET", "POST", "PUT", "DELETE"],
                  allow_headers=["Content-Type", "Authorization"])
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitingMiddleware, 
                  limit=100,
                  period=60)  # 100 requests per minute

# Set up authentication
auth = JWTAuth(secret_key="your-secret-key")

# Set up caching
cache = MemoryCache()

# Simulated database
users = [
    {"id": 1, "username": "user1", "email": "user1@example.com"},
    {"id": 2, "username": "user2", "email": "user2@example.com"},
]

products = [
    {"id": 1, "name": "Product 1", "price": 19.99},
    {"id": 2, "name": "Product 2", "price": 29.99},
    {"id": 3, "name": "Product 3", "price": 39.99},
]

# Basic endpoint
@app.api("/hello/{name}")
def hello(name: str) -> Dict:
    """
    Say hello to someone.
    
    Args:
        name: The name to greet
        
    Returns:
        A greeting message
    """
    return {"message": f"Hello, {name}!"}

# Cached endpoint
@app.api("/products")
@cache.cached(ttl=300)  # Cache for 5 minutes
async def get_products() -> List[Dict]:
    """
    Get all products.
    
    This endpoint is cached for 5 minutes.
    
    Returns:
        A list of products
    """
    # Simulate database query
    await asyncio.sleep(0.5)
    return products

# Protected endpoint
@app.api("/users")
@auth.requires_auth
async def get_users() -> List[Dict]:
    """
    Get all users.
    
    This endpoint requires authentication.
    
    Returns:
        A list of users
    """
    # Simulate database query
    await asyncio.sleep(0.2)
    return users

# Endpoint with path and query parameters
@app.api("/products/{product_id}")
async def get_product(product_id: int, include_details: bool = False) -> Optional[Dict]:
    """
    Get a product by ID.
    
    Args:
        product_id: The ID of the product to retrieve
        include_details: Whether to include additional details
        
    Returns:
        The product if found, None otherwise
    """
    # Simulate database query
    await asyncio.sleep(0.1)
    
    # Find product by ID
    for product in products:
        if product["id"] == product_id:
            result = dict(product)
            
            # Add additional details if requested
            if include_details:
                result["description"] = f"Detailed description for {product['name']}"
                result["stock"] = 100
                result["category"] = "Example Category"
            
            return result
    
    return None

# Run the API server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000) 