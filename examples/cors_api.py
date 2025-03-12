"""
Example demonstrating the CORS middleware.

This example shows how to create an API with CORS support to allow
cross-origin requests from different domains.
"""

from typing import Dict, List

from apifrom import API
from apifrom.decorators.api import api
from apifrom.middleware import CORSMiddleware

# Create the API instance
app = API(
    title="CORS Demo API",
    description="A demonstration of CORS middleware integration",
    version="1.0.0",
    debug=True
)

# Add CORS middleware with various configuration options
app.add_middleware(
    CORSMiddleware(
        # Allow requests from these origins
        allow_origins=["https://example.com", "https://app.example.com"],
        # Allow these HTTP methods
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        # Allow these headers in requests
        allow_headers=["Content-Type", "Authorization", "X-Custom-Header"],
        # Allow credentials (cookies, authorization headers)
        allow_credentials=True,
        # Expose these headers to the browser
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
        # Cache preflight requests for 1 hour (3600 seconds)
        max_age=3600
    )
)

# Alternatively, you can allow all origins with "*"
# app.add_middleware(CORSMiddleware(allow_origins=["*"]))


# Define some API endpoints
@api(app)
def get_users() -> List[Dict]:
    """
    Get a list of users.
    
    Returns:
        A list of user objects
    """
    return [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
        {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
    ]


@api(app)
def get_user(user_id: int) -> Dict:
    """
    Get a user by ID.
    
    Args:
        user_id: The ID of the user to get
        
    Returns:
        The user object
    """
    users = {
        1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
        2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
        3: {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
    }
    
    if user_id not in users:
        raise ValueError(f"User with ID {user_id} not found")
    
    return users[user_id]


@api(app)
def create_user(name: str, email: str) -> Dict:
    """
    Create a new user.
    
    Args:
        name: The name of the user
        email: The email of the user
        
    Returns:
        The created user object
    """
    # In a real application, this would save the user to a database
    return {"id": 4, "name": name, "email": email}


if __name__ == "__main__":
    # Run the API server
    app.run(host="127.0.0.1", port=8000)
    
    print("\nCORS-enabled API running at http://127.0.0.1:8000")
    print("\nTry accessing this API from a different origin to see CORS in action.")
    print("You can use tools like curl or Postman to test CORS headers:")
    print("\ncurl -H \"Origin: https://example.com\" -v http://127.0.0.1:8000/users")
    print("\nOr create a simple HTML page on a different port with JavaScript fetch:")
    print("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CORS Test</title>
    </head>
    <body>
        <h1>CORS Test</h1>
        <button id="fetchButton">Fetch Users</button>
        <pre id="result"></pre>
        
        <script>
            document.getElementById('fetchButton').addEventListener('click', async () => {
                try {
                    const response = await fetch('http://127.0.0.1:8000/users', {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        credentials: 'include'  // Include cookies if needed
                    });
                    
                    const data = await response.json();
                    document.getElementById('result').textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    document.getElementById('result').textContent = 'Error: ' + error.message;
                }
            });
        </script>
    </body>
    </html>
    """) 