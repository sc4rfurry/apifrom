"""
CSRF protection example using APIFromAnything.

This example demonstrates how to use the CSRF protection middleware to protect
an API created with the APIFromAnything library against CSRF attacks.
"""

import logging
from typing import Dict, List, Optional

from apifrom import API, api
from apifrom.security import CSRFMiddleware, csrf_exempt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create API instance
app = API(
    title="CSRF Protected API Example",
    description="An API with CSRF protection created with APIFromAnything",
    version="1.0.0",
    debug=True
)

# Add CSRF middleware
csrf_middleware = CSRFMiddleware(
    secret="your-csrf-secret-key",  # Use a secure random key in production
    exempt_routes=["/api/public"],  # Routes exempt from CSRF protection
)
app.add_middleware(csrf_middleware)

# Simulated database
items_db = [
    {"id": 1, "name": "Item 1", "description": "Description for Item 1"},
    {"id": 2, "name": "Item 2", "description": "Description for Item 2"},
    {"id": 3, "name": "Item 3", "description": "Description for Item 3"},
]


# Public endpoint (no CSRF protection needed)
@api(route="/api/public/items", method="GET")
def get_public_items() -> List[Dict]:
    """
    Get all items (public endpoint).
    
    This endpoint is exempt from CSRF protection because it's under /api/public.
    
    Returns:
        A list of items
    """
    logger.info("Fetching public items")
    return items_db


# Protected endpoint (requires CSRF token)
@api(route="/api/items", method="GET")
def get_items() -> List[Dict]:
    """
    Get all items (protected endpoint).
    
    This endpoint is protected by CSRF, but since it's a GET request,
    it's automatically exempt and will include a CSRF token in the response.
    
    Returns:
        A list of items
    """
    logger.info("Fetching items")
    return items_db


# Protected endpoint (requires CSRF token)
@api(route="/api/items/{item_id}", method="GET")
def get_item(item_id: int) -> Dict:
    """
    Get an item by ID (protected endpoint).
    
    This endpoint is protected by CSRF, but since it's a GET request,
    it's automatically exempt and will include a CSRF token in the response.
    
    Args:
        item_id: The ID of the item to retrieve
        
    Returns:
        An item
    """
    logger.info(f"Fetching item {item_id}")
    
    for item in items_db:
        if item["id"] == item_id:
            return item
    
    return {"error": "Item not found"}


# Protected endpoint (requires CSRF token)
@api(route="/api/items", method="POST")
def create_item(name: str, description: str, csrf_token: str) -> Dict:
    """
    Create a new item (protected endpoint).
    
    This endpoint is protected by CSRF and requires a valid CSRF token.
    
    Args:
        name: The name of the item
        description: The description of the item
        csrf_token: The CSRF token
        
    Returns:
        The created item
    """
    logger.info(f"Creating new item: {name}")
    
    item_id = max(item["id"] for item in items_db) + 1
    new_item = {"id": item_id, "name": name, "description": description}
    items_db.append(new_item)
    
    return new_item


# Protected endpoint (requires CSRF token)
@api(route="/api/items/{item_id}", method="PUT")
def update_item(item_id: int, name: Optional[str] = None, description: Optional[str] = None, csrf_token: str = None) -> Dict:
    """
    Update an item (protected endpoint).
    
    This endpoint is protected by CSRF and requires a valid CSRF token.
    
    Args:
        item_id: The ID of the item to update
        name: The new name of the item (optional)
        description: The new description of the item (optional)
        csrf_token: The CSRF token
        
    Returns:
        The updated item
    """
    logger.info(f"Updating item {item_id}")
    
    for item in items_db:
        if item["id"] == item_id:
            if name is not None:
                item["name"] = name
            if description is not None:
                item["description"] = description
            return item
    
    return {"error": "Item not found"}


# Protected endpoint (requires CSRF token)
@api(route="/api/items/{item_id}", method="DELETE")
def delete_item(item_id: int, csrf_token: str) -> Dict:
    """
    Delete an item (protected endpoint).
    
    This endpoint is protected by CSRF and requires a valid CSRF token.
    
    Args:
        item_id: The ID of the item to delete
        csrf_token: The CSRF token
        
    Returns:
        A success message
    """
    logger.info(f"Deleting item {item_id}")
    
    global items_db
    for i, item in enumerate(items_db):
        if item["id"] == item_id:
            del items_db[i]
            return {"message": f"Item with ID {item_id} deleted successfully"}
    
    return {"error": "Item not found"}


# Explicitly exempt endpoint from CSRF protection
@api(route="/api/webhook", method="POST")
@csrf_exempt
def webhook_handler(payload: Dict) -> Dict:
    """
    Handle webhook (exempt from CSRF protection).
    
    This endpoint is explicitly exempt from CSRF protection using the
    @csrf_exempt decorator, even though it's a POST request.
    
    Args:
        payload: The webhook payload
        
    Returns:
        A success message
    """
    logger.info(f"Received webhook: {payload}")
    return {"message": "Webhook received successfully"}


# HTML page with a form that includes the CSRF token
@api(route="/form", method="GET")
def get_form() -> str:
    """
    Get an HTML form that includes the CSRF token.
    
    This endpoint returns an HTML page with a form that includes the CSRF token.
    The token is automatically included in the response as a cookie.
    
    Returns:
        An HTML page
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CSRF Protection Example</title>
        <script>
            // Function to get the CSRF token from the cookie
            function getCSRFToken() {
                const cookies = document.cookie.split(';');
                for (let cookie of cookies) {
                    const [name, value] = cookie.trim().split('=');
                    if (name === 'csrf_token') {
                        return value;
                    }
                }
                return '';
            }
            
            // Function to submit the form
            async function submitForm() {
                const name = document.getElementById('name').value;
                const description = document.getElementById('description').value;
                const csrfToken = getCSRFToken();
                
                try {
                    const response = await fetch('/api/items', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': csrfToken
                        },
                        body: JSON.stringify({
                            name,
                            description,
                            csrf_token: csrfToken
                        })
                    });
                    
                    const result = await response.json();
                    document.getElementById('result').textContent = JSON.stringify(result, null, 2);
                } catch (error) {
                    document.getElementById('result').textContent = 'Error: ' + error.message;
                }
            }
        </script>
    </head>
    <body>
        <h1>Create a New Item</h1>
        <form id="itemForm" onsubmit="event.preventDefault(); submitForm();">
            <div>
                <label for="name">Name:</label>
                <input type="text" id="name" name="name" required>
            </div>
            <div>
                <label for="description">Description:</label>
                <textarea id="description" name="description" required></textarea>
            </div>
            <div>
                <button type="submit">Create Item</button>
            </div>
        </form>
        <h2>Result:</h2>
        <pre id="result"></pre>
        
        <h2>All Items:</h2>
        <div id="items"></div>
        <script>
            // Fetch and display all items
            async function fetchItems() {
                try {
                    const response = await fetch('/api/items');
                    const items = await response.json();
                    
                    const itemsContainer = document.getElementById('items');
                    itemsContainer.innerHTML = '';
                    
                    items.forEach(item => {
                        const itemElement = document.createElement('div');
                        itemElement.innerHTML = `
                            <h3>${item.name}</h3>
                            <p>${item.description}</p>
                            <button onclick="deleteItem(${item.id})">Delete</button>
                        `;
                        itemsContainer.appendChild(itemElement);
                    });
                } catch (error) {
                    console.error('Error fetching items:', error);
                }
            }
            
            // Delete an item
            async function deleteItem(id) {
                const csrfToken = getCSRFToken();
                
                try {
                    const response = await fetch(`/api/items/${id}`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRF-Token': csrfToken
                        },
                        body: JSON.stringify({
                            csrf_token: csrfToken
                        })
                    });
                    
                    const result = await response.json();
                    document.getElementById('result').textContent = JSON.stringify(result, null, 2);
                    
                    // Refresh the items list
                    fetchItems();
                } catch (error) {
                    document.getElementById('result').textContent = 'Error: ' + error.message;
                }
            }
            
            // Initial fetch
            fetchItems();
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    # Run the API server
    app.run(host="0.0.0.0", port=8007) 