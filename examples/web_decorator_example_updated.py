"""
An example of using the web decorator in the APIFromAnything library.
This demonstrates how to create HTML endpoints with the web decorator.
"""
import asyncio
from typing import Dict, List, Optional

from apifrom import API
from apifrom.middleware import CORSMiddleware

# Create an API instance
app = API(
    title="Web Decorator Example",
    description="An example of using the web decorator in the APIFromAnything library",
    version="1.0.0"
)

# Add middleware
app.add_middleware(CORSMiddleware, 
                  allow_origins=["*"],
                  allow_methods=["GET", "POST"],
                  allow_headers=["Content-Type"])

# Simulated database
products = [
    {"id": 1, "name": "Product 1", "price": 19.99, "category": "Electronics"},
    {"id": 2, "name": "Product 2", "price": 29.99, "category": "Clothing"},
    {"id": 3, "name": "Product 3", "price": 39.99, "category": "Home"},
    {"id": 4, "name": "Product 4", "price": 49.99, "category": "Electronics"},
    {"id": 5, "name": "Product 5", "price": 59.99, "category": "Clothing"},
]

# Basic web endpoint
@app.web("/")
def index():
    """
    Render the home page.
    
    Returns:
        HTML content for the home page
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>APIFromAnything Web Example</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            h1 {
                color: #333;
            }
            nav {
                margin-bottom: 20px;
            }
            nav a {
                margin-right: 15px;
                color: #0066cc;
                text-decoration: none;
            }
            nav a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to APIFromAnything Web Example</h1>
            <nav>
                <a href="/">Home</a>
                <a href="/products">Products</a>
                <a href="/about">About</a>
                <a href="/contact">Contact</a>
            </nav>
            <p>
                This example demonstrates how to use the web decorator to create HTML endpoints.
            </p>
            <p>
                The web decorator allows you to return HTML content directly from your endpoint functions.
            </p>
        </div>
    </body>
    </html>
    """

# Web endpoint with dynamic content
@app.web("/products")
async def products_page():
    """
    Render the products page.
    
    Returns:
        HTML content for the products page
    """
    # Simulate database query
    await asyncio.sleep(0.1)
    
    # Generate HTML for products
    products_html = ""
    for product in products:
        products_html += f"""
        <div class="product">
            <h3>{product['name']}</h3>
            <p>Price: ${product['price']}</p>
            <p>Category: {product['category']}</p>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Products - APIFromAnything Web Example</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
            }}
            h1 {{
                color: #333;
            }}
            nav {{
                margin-bottom: 20px;
            }}
            nav a {{
                margin-right: 15px;
                color: #0066cc;
                text-decoration: none;
            }}
            nav a:hover {{
                text-decoration: underline;
            }}
            .product {{
                border: 1px solid #ddd;
                padding: 15px;
                margin-bottom: 15px;
                border-radius: 5px;
            }}
            .product h3 {{
                margin-top: 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Products</h1>
            <nav>
                <a href="/">Home</a>
                <a href="/products">Products</a>
                <a href="/about">About</a>
                <a href="/contact">Contact</a>
            </nav>
            <div class="products">
                {products_html}
            </div>
        </div>
    </body>
    </html>
    """

# Web endpoint with path parameter
@app.web("/products/{product_id}")
async def product_detail(product_id: int):
    """
    Render the product detail page.
    
    Args:
        product_id: The ID of the product to display
        
    Returns:
        HTML content for the product detail page
    """
    # Simulate database query
    await asyncio.sleep(0.1)
    
    # Find product by ID
    product = None
    for p in products:
        if p["id"] == product_id:
            product = p
            break
    
    if not product:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Product Not Found - APIFromAnything Web Example</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    line-height: 1.6;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                }
                h1 {
                    color: #333;
                }
                nav {
                    margin-bottom: 20px;
                }
                nav a {
                    margin-right: 15px;
                    color: #0066cc;
                    text-decoration: none;
                }
                nav a:hover {
                    text-decoration: underline;
                }
                .error {
                    color: red;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Product Not Found</h1>
                <nav>
                    <a href="/">Home</a>
                    <a href="/products">Products</a>
                    <a href="/about">About</a>
                    <a href="/contact">Contact</a>
                </nav>
                <p class="error">
                    The product with ID {product_id} was not found.
                </p>
                <p>
                    <a href="/products">Back to Products</a>
                </p>
            </div>
        </body>
        </html>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{product['name']} - APIFromAnything Web Example</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
            }}
            h1 {{
                color: #333;
            }}
            nav {{
                margin-bottom: 20px;
            }}
            nav a {{
                margin-right: 15px;
                color: #0066cc;
                text-decoration: none;
            }}
            nav a:hover {{
                text-decoration: underline;
            }}
            .product-detail {{
                border: 1px solid #ddd;
                padding: 20px;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{product['name']}</h1>
            <nav>
                <a href="/">Home</a>
                <a href="/products">Products</a>
                <a href="/about">About</a>
                <a href="/contact">Contact</a>
            </nav>
            <div class="product-detail">
                <h2>{product['name']}</h2>
                <p><strong>Price:</strong> ${product['price']}</p>
                <p><strong>Category:</strong> {product['category']}</p>
                <p><strong>ID:</strong> {product['id']}</p>
            </div>
            <p>
                <a href="/products">Back to Products</a>
            </p>
        </div>
    </body>
    </html>
    """

# Simple about page
@app.web("/about")
def about():
    """
    Render the about page.
    
    Returns:
        HTML content for the about page
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>About - APIFromAnything Web Example</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            h1 {
                color: #333;
            }
            nav {
                margin-bottom: 20px;
            }
            nav a {
                margin-right: 15px;
                color: #0066cc;
                text-decoration: none;
            }
            nav a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>About</h1>
            <nav>
                <a href="/">Home</a>
                <a href="/products">Products</a>
                <a href="/about">About</a>
                <a href="/contact">Contact</a>
            </nav>
            <p>
                APIFromAnything is a powerful Python framework that transforms regular Python functions into fully-featured API endpoints with minimal code changes.
            </p>
            <p>
                The web decorator allows you to create HTML endpoints directly from your Python functions, making it easy to build simple web applications.
            </p>
        </div>
    </body>
    </html>
    """

# Contact page with form
@app.web("/contact", methods=["GET", "POST"])
async def contact(request):
    """
    Render the contact page and handle form submission.
    
    Args:
        request: The request object
        
    Returns:
        HTML content for the contact page
    """
    message = ""
    
    # Handle form submission
    if request.method == "POST":
        form_data = await request.form()
        name = form_data.get("name", "")
        email = form_data.get("email", "")
        message_text = form_data.get("message", "")
        
        # Simulate sending email
        await asyncio.sleep(0.5)
        
        message = f"Thank you, {name}! Your message has been sent."
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Contact - APIFromAnything Web Example</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
            }}
            h1 {{
                color: #333;
            }}
            nav {{
                margin-bottom: 20px;
            }}
            nav a {{
                margin-right: 15px;
                color: #0066cc;
                text-decoration: none;
            }}
            nav a:hover {{
                text-decoration: underline;
            }}
            form {{
                margin-top: 20px;
            }}
            .form-group {{
                margin-bottom: 15px;
            }}
            label {{
                display: block;
                margin-bottom: 5px;
            }}
            input, textarea {{
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            button {{
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
            }}
            .message {{
                color: green;
                margin-bottom: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Contact</h1>
            <nav>
                <a href="/">Home</a>
                <a href="/products">Products</a>
                <a href="/about">About</a>
                <a href="/contact">Contact</a>
            </nav>
            
            {f'<p class="message">{message}</p>' if message else ''}
            
            <form method="post" action="/contact">
                <div class="form-group">
                    <label for="name">Name:</label>
                    <input type="text" id="name" name="name" required>
                </div>
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="message">Message:</label>
                    <textarea id="message" name="message" rows="5" required></textarea>
                </div>
                <button type="submit">Send Message</button>
            </form>
        </div>
    </body>
    </html>
    """

# Run the API server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000) 