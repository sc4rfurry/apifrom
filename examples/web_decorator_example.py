"""
Web Decorator Example

This example demonstrates how to use the Web decorator to create API endpoints
that can be accessed both programmatically and through a web browser.

To run this example:
1. Install the APIFromAnything library
2. Run this script: python web_decorator_example.py
3. Open your browser to http://localhost:8000/users
4. Try the same endpoint programmatically:
   curl -H "Accept: application/json" http://localhost:8000/users
"""

from apifrom.core.app import API
from apifrom.decorators.web import Web
from apifrom.server.wsgi import WSGIServer

# Create an API app
app = API()

# Sample data
users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin"},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com", "role": "user"},
    {"id": 4, "name": "Diana", "email": "diana@example.com", "role": "manager"},
]

products = [
    {"id": 101, "name": "Laptop", "price": 999.99, "in_stock": True},
    {"id": 102, "name": "Smartphone", "price": 499.99, "in_stock": True},
    {"id": 103, "name": "Headphones", "price": 99.99, "in_stock": False},
    {"id": 104, "name": "Monitor", "price": 299.99, "in_stock": True},
]

# Define API endpoints with Web decorator
@app.api("/")
@Web(title="API Index", description="Available endpoints in this API")
def index(request):
    """Return a list of available endpoints."""
    return {
        "endpoints": [
            {"path": "/", "description": "This index page"},
            {"path": "/users", "description": "List of users"},
            {"path": "/products", "description": "List of products"},
            {"path": "/user/{id}", "description": "Get user by ID"},
            {"path": "/product/{id}", "description": "Get product by ID"},
            {"path": "/dashboard", "description": "Dashboard with multiple data types"},
        ]
    }

@app.api("/users")
@Web(title="Users API", description="List of all users in the system")
def get_users(request):
    """Return a list of users."""
    return users

@app.api("/products")
@Web(title="Products API", description="List of all products in the system", theme="dark")
def get_products(request):
    """Return a list of products."""
    return products

@app.api("/user/{id}")
@Web(title="User Details", description="Detailed information about a user")
def get_user(request, id):
    """Return a user by ID."""
    user_id = int(id)
    for user in users:
        if user["id"] == user_id:
            return user
    return {"error": "User not found"}

@app.api("/product/{id}")
@Web(title="Product Details", description="Detailed information about a product", theme="light")
def get_product(request, id):
    """Return a product by ID."""
    product_id = int(id)
    for product in products:
        if product["id"] == product_id:
            return product
    return {"error": "Product not found"}

@app.api("/dashboard")
@Web(title="Dashboard", description="System overview dashboard")
def dashboard(request):
    """Return a dashboard with various data types."""
    return {
        "system_status": "healthy",
        "active_users": len([u for u in users if u["role"] != "inactive"]),
        "products_in_stock": len([p for p in products if p["in_stock"]]),
        "recent_users": users[:2],
        "popular_products": products[:2],
        "stats": {
            "total_users": len(users),
            "total_products": len(products),
            "average_price": sum(p["price"] for p in products) / len(products),
        }
    }

if __name__ == "__main__":
    # Start the server
    print("Starting server on http://localhost:8000")
    print("Try these endpoints in your browser:")
    print("  - http://localhost:8000/")
    print("  - http://localhost:8000/users")
    print("  - http://localhost:8000/products (dark theme)")
    print("  - http://localhost:8000/user/1")
    print("  - http://localhost:8000/product/101 (light theme)")
    print("  - http://localhost:8000/dashboard")
    print("\nOr programmatically:")
    print("  curl -H \"Accept: application/json\" http://localhost:8000/users")
    
    server = WSGIServer(app, host="localhost", port=8000)
    server.start() 