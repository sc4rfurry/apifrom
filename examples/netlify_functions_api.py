"""
Example demonstrating deployment to Netlify Functions.

This example shows how to create an API with APIFromAnything that can be
deployed to Netlify Functions.
"""

from typing import Dict, List
import os
import json

from apifrom import API
from apifrom.decorators.api import api
from apifrom.adapters.netlify import NetlifyAdapter

# Create an API instance
app = API(
    title="Netlify Functions API",
    description="An API deployed to Netlify Functions",
    version="1.0.0"
)

# In-memory database for demonstration
todos = [
    {"id": 1, "title": "Learn APIFromAnything", "completed": True},
    {"id": 2, "title": "Build a serverless API", "completed": False},
    {"id": 3, "title": "Deploy to Netlify", "completed": False},
]


@api(app, route="/.netlify/functions/api", method="GET")
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
            "/.netlify/functions/api",
            "/.netlify/functions/api/todos",
            "/.netlify/functions/api/todos/{todo_id}",
        ]
    }


@api(app, route="/.netlify/functions/api/todos", method="GET")
def get_todos(completed: bool = None) -> Dict:
    """
    Get all todos, optionally filtered by completion status.
    
    Args:
        completed: Filter by completion status
        
    Returns:
        List of todos
    """
    if completed is not None:
        filtered_todos = [t for t in todos if t["completed"] == completed]
        return {"todos": filtered_todos}
    
    return {"todos": todos}


@api(app, route="/.netlify/functions/api/todos/{todo_id}", method="GET")
def get_todo(todo_id: int) -> Dict:
    """
    Get a todo by ID.
    
    Args:
        todo_id: The todo ID
        
    Returns:
        Todo details
    """
    for todo in todos:
        if todo["id"] == todo_id:
            return todo
    
    return {"error": "Todo not found"}


@api(app, route="/.netlify/functions/api/todos", method="POST")
def create_todo(title: str) -> Dict:
    """
    Create a new todo.
    
    Args:
        title: The todo title
        
    Returns:
        Created todo
    """
    # Generate a new ID
    new_id = max(todo["id"] for todo in todos) + 1
    
    # Create the new todo
    new_todo = {
        "id": new_id,
        "title": title,
        "completed": False
    }
    
    # Add it to the database
    todos.append(new_todo)
    
    return new_todo


@api(app, route="/.netlify/functions/api/todos/{todo_id}", method="PUT")
def update_todo(todo_id: int, title: str = None, completed: bool = None) -> Dict:
    """
    Update a todo.
    
    Args:
        todo_id: The todo ID
        title: The new title (optional)
        completed: The new completion status (optional)
        
    Returns:
        Updated todo
    """
    for todo in todos:
        if todo["id"] == todo_id:
            if title is not None:
                todo["title"] = title
            if completed is not None:
                todo["completed"] = completed
            return todo
    
    return {"error": "Todo not found"}


@api(app, route="/.netlify/functions/api/todos/{todo_id}", method="DELETE")
def delete_todo(todo_id: int) -> Dict:
    """
    Delete a todo.
    
    Args:
        todo_id: The todo ID
        
    Returns:
        Deletion status
    """
    global todos
    initial_count = len(todos)
    todos = [todo for todo in todos if todo["id"] != todo_id]
    
    if len(todos) < initial_count:
        return {"message": f"Todo {todo_id} deleted successfully"}
    
    return {"error": "Todo not found"}


# Create a Netlify adapter
netlify_adapter = NetlifyAdapter(app)

# Export the handler function for Netlify Functions
def handler(event, context):
    """
    Netlify Functions handler.
    
    Args:
        event: The Netlify event object
        context: The Netlify context object
        
    Returns:
        Response object
    """
    return netlify_adapter.handle(event, context)


"""
To deploy this API to Netlify Functions, follow these steps:

1. Create a new directory for your Netlify project:
   ```
   mkdir netlify-api
   cd netlify-api
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install apifrom
   ```

3. Create a `netlify.toml` file in the root directory with the following content:
   ```toml
   [build]
     functions = "functions"
     publish = "public"

   [[redirects]]
     from = "/api/*"
     to = "/.netlify/functions/api/:splat"
     status = 200
   ```

4. Create a `functions` directory for your serverless functions:
   ```
   mkdir functions
   ```

5. Create a file `functions/api.py` with the content of this example.

6. Create a `requirements.txt` file in the root directory with the following content:
   ```
   apifrom
   ```

7. Create a simple `public/index.html` file:
   ```html
   <!DOCTYPE html>
   <html>
   <head>
     <title>Netlify Functions API</title>
   </head>
   <body>
     <h1>Netlify Functions API</h1>
     <p>Visit <a href="/api">/api</a> to access the API.</p>
   </body>
   </html>
   ```

8. Initialize a Git repository and commit your files:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   ```

9. Create a new site on Netlify and deploy:
   ```
   npm install -g netlify-cli
   netlify login
   netlify init
   netlify deploy --prod
   ```

10. Your API will be deployed to a URL like `https://your-site-name.netlify.app/api`
"""


# For local development
if __name__ == "__main__":
    # Run the API server
    app.run(host="127.0.0.1", port=8000)
    
    print("\nNetlify Functions API running at http://127.0.0.1:8000")
    print("\nAvailable endpoints:")
    print("  - GET /.netlify/functions/api: API information")
    print("  - GET /.netlify/functions/api/todos: List all todos")
    print("  - GET /.netlify/functions/api/todos/{todo_id}: Get a todo by ID")
    print("  - POST /.netlify/functions/api/todos: Create a new todo")
    print("  - PUT /.netlify/functions/api/todos/{todo_id}: Update a todo")
    print("  - DELETE /.netlify/functions/api/todos/{todo_id}: Delete a todo")
    print("\nTo deploy to Netlify, follow the instructions in the comments at the end of this file.") 