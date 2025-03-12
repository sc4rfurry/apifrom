"""
Example demonstrating deployment to Vercel serverless functions.

This example shows how to create an API with APIFromAnything that can be
deployed to Vercel serverless functions.
"""

from typing import Dict, List
import os
import json

from apifrom import API
from apifrom.decorators.api import api
from apifrom.adapters.vercel import VercelAdapter

# Create an API instance
app = API(
    title="Vercel Serverless API",
    description="An API deployed to Vercel serverless functions",
    version="1.0.0"
)

# In-memory database for demonstration
products = [
    {"id": 1, "name": "Product 1", "price": 19.99, "category": "electronics"},
    {"id": 2, "name": "Product 2", "price": 29.99, "category": "clothing"},
    {"id": 3, "name": "Product 3", "price": 9.99, "category": "books"},
]


@api(app, route="/api", method="GET")
def index() -> Dict:
    """
    Root endpoint that returns API information.
    
    Returns:
        API information
    """
    return {
        "name": app.title,
        "description": app.description,
        "version": app.version,
        "endpoints": [
            "/api",
            "/api/products",
            "/api/products/{product_id}",
            "/api/categories",
        ]
    }


@api(app, route="/api/products", method="GET")
def get_products(category: str = None) -> Dict:
    """
    Get all products, optionally filtered by category.
    
    Args:
        category: Filter by product category
        
    Returns:
        List of products
    """
    if category:
        filtered_products = [p for p in products if p["category"] == category]
        return {"products": filtered_products}
    
    return {"products": products}


@api(app, route="/api/products/{product_id}", method="GET")
def get_product(product_id: int) -> Dict:
    """
    Get a product by ID.
    
    Args:
        product_id: The product ID
        
    Returns:
        Product details
    """
    for product in products:
        if product["id"] == product_id:
            return product
    
    return {"error": "Product not found"}


@api(app, route="/api/categories", method="GET")
def get_categories() -> Dict:
    """
    Get all product categories.
    
    Returns:
        List of categories
    """
    categories = list(set(product["category"] for product in products))
    return {"categories": categories}


# Create a Vercel adapter
vercel_adapter = VercelAdapter(app)

# Export the handler function for Vercel
handler = vercel_adapter.get_handler()


"""
To deploy this API to Vercel, follow these steps:

1. Create a new directory for your Vercel project:
   ```
   mkdir vercel-api
   cd vercel-api
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install apifrom
   ```

3. Create an `api` directory for your serverless functions:
   ```
   mkdir api
   ```

4. Create a file `api/index.py` with the content of this example.

5. Create a `vercel.json` file in the root directory with the following content:
   ```json
   {
     "version": 2,
     "builds": [
       { "src": "api/*.py", "use": "@vercel/python" }
     ],
     "routes": [
       { "src": "/(.*)", "dest": "api/index.py" }
     ]
   }
   ```

6. Initialize a Git repository and commit your files:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   ```

7. Install the Vercel CLI and deploy:
   ```
   npm install -g vercel
   vercel login
   vercel
   ```

8. Your API will be deployed to a URL like `https://your-project-name.vercel.app/api`
"""


# For local development
if __name__ == "__main__":
    # Run the API server
    app.run(host="127.0.0.1", port=8000)
    
    print("\nVercel Serverless API running at http://127.0.0.1:8000")
    print("\nAvailable endpoints:")
    print("  - GET /api: API information")
    print("  - GET /api/products: List all products")
    print("  - GET /api/products/{product_id}: Get a product by ID")
    print("  - GET /api/categories: List all product categories")
    print("\nTo deploy to Vercel, follow the instructions in the comments at the end of this file.") 