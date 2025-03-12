"""
Example demonstrating the Web decorator for API optimization.

This example demonstrates how to use the Web decorator to optimize API endpoints
with minimal code changes, enabling caching, profiling, and connection pooling.
"""

import time
import random
from typing import Dict, List, Optional, Any

from apifrom import API
from apifrom.decorators.api import api
from apifrom.performance.optimization import Web
from apifrom.middleware import CORSMiddleware
from apifrom.middleware import MemoryCacheBackend
from apifrom.performance.profiler import ProfileMiddleware
from apifrom.performance.cache_optimizer import OptimizedCacheMiddleware


# Create a simple API
app = API(
    title="Web Optimized API",
    description="A simple API demonstrating the Web decorator for optimization",
    version="1.0.0",
    debug=True
)

# Add middleware for CORS
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

# Add middleware for profiling
profile_middleware = ProfileMiddleware(output_dir="./profiles")
app.add_middleware(profile_middleware)

# Add middleware for caching
cache_backend = MemoryCacheBackend()
cache_middleware = OptimizedCacheMiddleware(cache_backend=cache_backend)
app.add_middleware(cache_middleware)


# Define endpoints

# Standard endpoint without optimization
@api(app, route="/products", method="GET")
def get_products() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get a list of products.
    
    Returns:
        A dictionary containing a list of products
    """
    # Simulate database access (slow operation)
    time.sleep(0.5)
    
    # Generate some random products
    products = []
    for i in range(10):
        products.append({
            "id": i,
            "name": f"Product {i}",
            "price": round(random.uniform(10, 100), 2),
            "description": f"This is product {i}"
        })
    
    return {"products": products}


# Optimized endpoint using the Web decorator
@api(app, route="/products/optimized", method="GET")
@Web.optimize(
    cache_ttl=30,  # Cache for 30 seconds
    profile=True,  # Enable profiling
    connection_pool=True,  # Enable connection pooling (if available)
    auto_tune=True  # Enable auto-tuning
)
def get_optimized_products() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get a list of products (optimized version).
    
    Returns:
        A dictionary containing a list of products
    """
    # Simulate database access (slow operation)
    time.sleep(0.5)
    
    # Generate some random products
    products = []
    for i in range(10):
        products.append({
            "id": i,
            "name": f"Product {i}",
            "price": round(random.uniform(10, 100), 2),
            "description": f"This is product {i}"
        })
    
    return {"products": products}


# Endpoint for a single product (with adaptive caching)
@api(app, route="/products/{product_id}", method="GET")
@Web.optimize(
    cache_ttl=60,  # Cache for 60 seconds
    profile=True
)
def get_product(product_id: int) -> Dict[str, Any]:
    """
    Get a single product by ID.
    
    Args:
        product_id: The product ID
        
    Returns:
        A dictionary containing the product details
    """
    # Simulate database access (slow operation)
    time.sleep(0.2)
    
    # Generate a product based on the ID
    return {
        "product": {
            "id": product_id,
            "name": f"Product {product_id}",
            "price": round(random.uniform(10, 100), 2),
            "description": f"This is product {product_id}",
            "details": {
                "manufacturer": "ACME Corp",
                "sku": f"SKU-{product_id:04d}",
                "weight": round(random.uniform(0.1, 5.0), 2),
                "dimensions": {
                    "width": round(random.uniform(5, 30), 1),
                    "height": round(random.uniform(5, 30), 1),
                    "depth": round(random.uniform(5, 30), 1)
                }
            }
        }
    }


# Profile data endpoint
@api(app, route="/profile-data", method="GET")
def get_profile_data() -> Dict[str, Any]:
    """
    Get profiling data for all endpoints.
    
    Returns:
        Profiling data
    """
    reports = profile_middleware.get_all_reports()
    
    return {
        "timestamp": time.time(),
        "reports": [report.to_dict() for report in reports]
    }


# Cache stats endpoint
@api(app, route="/cache-stats", method="GET")
def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Cache statistics
    """
    return {
        "timestamp": time.time(),
        "stats": cache_middleware.get_analytics().to_dict()
    }


# Index page with instructions
@api(app, route="/", method="GET")
def index() -> str:
    """
    Index page with instructions.
    
    Returns:
        HTML page with instructions
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Web Optimization Demo</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1, h2 {
                color: #333;
            }
            pre {
                background-color: #f4f4f4;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                overflow-x: auto;
            }
            .endpoint {
                margin-bottom: 20px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            .endpoint h3 {
                margin-top: 0;
            }
            .btn {
                display: inline-block;
                padding: 8px 16px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin-right: 10px;
                margin-bottom: 10px;
            }
            .results {
                margin-top: 20px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
                display: none;
            }
        </style>
    </head>
    <body>
        <h1>Web Optimization Demo</h1>
        <p>
            This demo shows how to use the <code>@Web.optimize</code> decorator to optimize API endpoints.
            The decorator enables caching, profiling, and connection pooling with minimal code changes.
        </p>
        
        <div class="endpoint">
            <h3>Standard Endpoint (Non-optimized)</h3>
            <p>First, make several requests to the standard endpoint:</p>
            <a href="/products" class="btn" target="_blank">Get Products</a>
            <p>This endpoint doesn't use any optimization techniques and will be slow on each request.</p>
        </div>
        
        <div class="endpoint">
            <h3>Optimized Endpoint</h3>
            <p>Now, make several requests to the optimized endpoint:</p>
            <a href="/products/optimized" class="btn" target="_blank">Get Optimized Products</a>
            <p>
                This endpoint uses the <code>@Web.optimize</code> decorator with caching.
                The first request will be slow, but subsequent requests will be much faster
                due to caching (for 30 seconds).
            </p>
        </div>
        
        <div class="endpoint">
            <h3>Single Product Endpoint (Parameterized)</h3>
            <p>Try the single product endpoint with different IDs:</p>
            <a href="/products/1" class="btn" target="_blank">Product 1</a>
            <a href="/products/2" class="btn" target="_blank">Product 2</a>
            <a href="/products/3" class="btn" target="_blank">Product 3</a>
            <p>
                This endpoint demonstrates how the <code>@Web.optimize</code> decorator works with
                parameterized routes. Each product ID has its own cache entry.
            </p>
        </div>
        
        <div class="endpoint">
            <h3>Analytics</h3>
            <p>After making several requests, check the profiling and cache statistics:</p>
            <a href="/profile-data" class="btn" target="_blank">Profile Data</a>
            <a href="/cache-stats" class="btn" target="_blank">Cache Stats</a>
            <p>
                These endpoints show the performance metrics collected by the profiling middleware
                and the cache statistics, demonstrating the benefits of the optimizations.
            </p>
        </div>
        
        <h2>Code Example</h2>
        <p>Here's how to use the <code>@Web.optimize</code> decorator:</p>
        <pre>
from apifrom import API
from apifrom.decorators.api import api
from apifrom.performance.optimization import Web

# Create API
app = API(title="Optimized API", version="1.0.0")

# Standard endpoint
@api(app, route="/products", method="GET")
def get_products():
    # Slow operation...
    return {"products": [...]}

# Optimized endpoint
@api(app, route="/products/optimized", method="GET")
@Web.optimize(
    cache_ttl=30,  # Cache for 30 seconds
    profile=True,  # Enable profiling
    connection_pool=True,  # Enable connection pooling
    auto_tune=True  # Enable auto-tuning
)
def get_optimized_products():
    # Same slow operation, but now optimized...
    return {"products": [...]}
        </pre>
        
        <script>
            document.addEventListener("DOMContentLoaded", function() {
                // Add event listeners for buttons
                document.querySelectorAll(".btn").forEach(function(btn) {
                    btn.addEventListener("click", function(e) {
                        e.preventDefault();
                        
                        const url = this.getAttribute("href");
                        const resultDiv = document.querySelector(".results");
                        
                        // Show loading
                        if (!resultDiv) {
                            const newResultDiv = document.createElement("div");
                            newResultDiv.className = "results";
                            newResultDiv.style.display = "block";
                            newResultDiv.innerHTML = "Loading...";
                            this.parentNode.appendChild(newResultDiv);
                        } else {
                            resultDiv.style.display = "block";
                            resultDiv.innerHTML = "Loading...";
                        }
                        
                        // Fetch the data
                        const startTime = performance.now();
                        fetch(url)
                            .then(response => response.json())
                            .then(data => {
                                const endTime = performance.now();
                                const duration = (endTime - startTime).toFixed(2);
                                
                                // Display the results
                                const resultDiv = this.parentNode.querySelector(".results");
                                resultDiv.innerHTML = `
                                    <strong>Response Time:</strong> ${duration}ms
                                    <pre>${JSON.stringify(data, null, 2)}</pre>
                                `;
                            })
                            .catch(error => {
                                const resultDiv = this.parentNode.querySelector(".results");
                                resultDiv.innerHTML = `<strong>Error:</strong> ${error}`;
                            });
                    });
                });
            });
        </script>
    </body>
    </html>
    """


# Run the API if executed directly
if __name__ == "__main__":
    import os
    
    # Create the profiles directory if it doesn't exist
    os.makedirs("./profiles", exist_ok=True)
    
    # Run the API
    app.run(host="127.0.0.1", port=8000)
    
    print("\nWeb Optimized API running at http://127.0.0.1:8000")
    print("Available endpoints:")
    print("  GET /: Index page with instructions")
    print("  GET /products: Get products (standard endpoint)")
    print("  GET /products/optimized: Get products (optimized endpoint)")
    print("  GET /products/{product_id}: Get a single product")
    print("  GET /profile-data: Get profiling data")
    print("  GET /cache-stats: Get cache statistics")
    
    print("\nOpen http://127.0.0.1:8000/ in your browser to see the demo.") 