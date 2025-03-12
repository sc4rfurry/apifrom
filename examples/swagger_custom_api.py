"""
Example demonstrating the customized Swagger UI integration.

This example shows how to create an API with fully customized Swagger UI documentation
with advanced styling options.
"""

from typing import Dict, List, Optional
import random

from apifrom import API
from apifrom.decorators.api import api
from apifrom.docs.openapi import OpenAPIConfig
from apifrom.docs.swagger_ui import SwaggerUIConfig
from apifrom.middleware import CORSMiddleware

# Create an API with custom documentation configuration
openapi_config = OpenAPIConfig(
    title="Advanced Swagger UI Demo API",
    description="""
    This API demonstrates the advanced customization options available for Swagger UI in APIFromAnything.
    
    ## Features
    - Custom theme and styling
    - Advanced navigation options
    - Custom operation displays
    - Responsive design
    
    Try out the different operations below to see the documentation in action!
    """,
    version="1.2.0",
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "API Support",
        "url": "https://example.com/support",
        "email": "support@example.com"
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
    },
    servers=[
        {"url": "https://api.example.com/v1", "description": "Production server"},
        {"url": "https://staging-api.example.com/v1", "description": "Staging server"},
        {"url": "http://localhost:8005", "description": "Local development server"}
    ],
    external_docs={
        "description": "Find more info here",
        "url": "https://example.com/docs"
    },
    tags=[
        {
            "name": "users",
            "description": "Operations related to users"
        },
        {
            "name": "products",
            "description": "Operations related to products"
        }
    ]
)

# Create custom Swagger UI configuration
swagger_ui_config = SwaggerUIConfig(
    theme="material",  # Other options: "default", "muted", "outline", "flattop"
    deep_linking=True,
    display_operation_id=True,
    default_models_expand_depth=2,
    default_model_expand_depth=3,
    display_request_duration=True,
    doc_expansion="list",  # Other options: "full", "none"
    filter=True,
    max_displayed_tags=None,
    operations_sorter="alpha",  # Other options: "method"
    show_extensions=True,
    show_common_extensions=True,
    tag_sorter="alpha",
    use_unicode_characters=True,
    persist_authorization=True,
    syntax_highlight="monokai"  # Other options: "agate", "arta", "nord", "obsidian"
)

# Create the API instance with custom documentation
app = API(
    title="Advanced Swagger UI Demo API",
    description="A demonstration of custom Swagger UI integration",
    version="1.2.0",
    docs_url="/api-docs",
    debug=True,
    openapi_config=openapi_config,
    swagger_ui_config=swagger_ui_config
)

# Add CORS middleware
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

# Sample data
users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin"},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com", "role": "user"}
]

products = [
    {"id": 1, "name": "Laptop", "price": 999.99, "in_stock": True},
    {"id": 2, "name": "Smartphone", "price": 699.99, "in_stock": True},
    {"id": 3, "name": "Headphones", "price": 149.99, "in_stock": False}
]


# User endpoints
@api(app, route="/users", method="GET", tags=["users"])
def get_users(limit: int = 10, role: Optional[str] = None) -> List[Dict]:
    """
    Get a list of users.
    
    Args:
        limit: Maximum number of users to return
        role: Filter users by role (admin, user)
        
    Returns:
        A list of user objects
    """
    filtered_users = users
    if role:
        filtered_users = [u for u in users if u["role"] == role]
    return filtered_users[:limit]


@api(app, route="/users/{user_id}", method="GET", tags=["users"])
def get_user(user_id: int) -> Dict:
    """
    Get a user by ID.
    
    Args:
        user_id: The ID of the user to retrieve
        
    Returns:
        A user object
        
    Raises:
        404: If the user is not found
    """
    for user in users:
        if user["id"] == user_id:
            return user
    return {"error": "User not found"}, 404


@api(app, route="/users", method="POST", tags=["users"])
def create_user(name: str, email: str, role: str = "user") -> Dict:
    """
    Create a new user.
    
    Args:
        name: The name of the user
        email: The email of the user
        role: The role of the user (default: user)
        
    Returns:
        The created user object
    """
    user_id = max(u["id"] for u in users) + 1
    new_user = {"id": user_id, "name": name, "email": email, "role": role}
    users.append(new_user)
    return new_user


# Product endpoints
@api(app, route="/products", method="GET", tags=["products"])
def get_products(in_stock: Optional[bool] = None) -> List[Dict]:
    """
    Get a list of products.
    
    Args:
        in_stock: Filter products by availability
        
    Returns:
        A list of product objects
    """
    filtered_products = products
    if in_stock is not None:
        filtered_products = [p for p in products if p["in_stock"] == in_stock]
    return filtered_products


@api(app, route="/products/{product_id}", method="GET", tags=["products"])
def get_product(product_id: int) -> Dict:
    """
    Get a product by ID.
    
    Args:
        product_id: The ID of the product to retrieve
        
    Returns:
        A product object
        
    Raises:
        404: If the product is not found
    """
    for product in products:
        if product["id"] == product_id:
            return product
    return {"error": "Product not found"}, 404


@api(app, route="/products/random", method="GET", tags=["products"])
def get_random_product() -> Dict:
    """
    Get a random product.
    
    Returns:
        A randomly selected product
    """
    return random.choice(products)


if __name__ == "__main__":
    # Run the API server
    app.run(host="0.0.0.0", port=8005) 