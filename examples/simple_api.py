"""
A simple example of using the APIFromAnything library.
"""
from apifrom import APIApp

# Create an API instance
app = APIApp(
    title="Simple API Example",
    description="A simple example of using the APIFromAnything library",
    version="1.0.0"
)

# Define a simple endpoint
@app.api("/hello/{name}")
def hello(name: str, greeting: str = "Hello") -> dict:
    """
    Say hello to someone.
    
    Args:
        name: The name to greet
        greeting: The greeting to use (default: "Hello")
        
    Returns:
        A greeting message
    """
    return {"message": f"{greeting}, {name}!"}

# Define an endpoint with more complex parameters
@app.api("/users", methods=["POST"])
def create_user(name: str, email: str, age: int = None) -> dict:
    """
    Create a new user.
    
    Args:
        name: The user's name
        email: The user's email
        age: The user's age (optional)
        
    Returns:
        The created user
    """
    user = {
        "name": name,
        "email": email,
        "id": 123  # In a real app, this would be generated
    }
    
    if age is not None:
        user["age"] = age
    
    return user

# Define an endpoint with error handling
@app.api("/divide/{a}/{b}")
def divide(a: float, b: float) -> dict:
    """
    Divide two numbers.
    
    Args:
        a: The numerator
        b: The denominator
        
    Returns:
        The result of the division
        
    Raises:
        ValueError: If b is zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    
    return {"result": a / b}

# Run the API server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000) 