"""
A simple example of using the APIFromAnything library.
"""
import logging
import asyncio
from apifrom import API
from apifrom.core.request import Request
from apifrom.core.response import JSONResponse

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create an API instance
app = API(
    title="Simple API Example",
    description="A simple example of using the APIFromAnything library",
    version="1.0.0",
    debug=True,
    enable_docs=False  # Disable documentation to avoid Swagger UI issues
)

# Define a simple endpoint
@app.add_route("/hello/{name}")
def hello(request: Request):
    """
    Say hello to someone.
    
    Args:
        request: The request object
        
    Returns:
        A greeting message
    """
    logger.debug(f"Request: {request}")
    logger.debug(f"Path params: {request.path_params}")
    
    name = request.path_params.get("name", "world")
    greeting = request.query_params.get("greeting", "Hello")
    
    response = JSONResponse({"message": f"{greeting}, {name}!"})
    return response.to_starlette_response()

# Define an endpoint with more complex parameters
@app.add_route("/users", methods=["POST"])
async def create_user(request: Request):
    """
    Create a new user.
    
    Args:
        request: The request object
        
    Returns:
        The created user
    """
    logger.debug(f"Request: {request}")
    
    data = await request.json()
    logger.debug(f"JSON data: {data}")
    
    name = data.get("name")
    email = data.get("email")
    age = data.get("age")
    
    if not name or not email:
        response = JSONResponse({"error": "Name and email are required"}, status_code=400)
        return response.to_starlette_response()
    
    user = {
        "name": name,
        "email": email,
        "id": 123  # In a real app, this would be generated
    }
    
    if age is not None:
        user["age"] = age
    
    response = JSONResponse(user)
    return response.to_starlette_response()

# Define an endpoint with error handling
@app.add_route("/divide/{a}/{b}")
def divide(request: Request):
    """
    Divide two numbers.
    
    Args:
        request: The request object
        
    Returns:
        The result of the division
    """
    logger.debug(f"Request: {request}")
    logger.debug(f"Path params: {request.path_params}")
    
    try:
        a = float(request.path_params.get("a", 0))
        b = float(request.path_params.get("b", 1))
        
        if b == 0:
            response = JSONResponse({"error": "Cannot divide by zero"}, status_code=400)
            return response.to_starlette_response()
        
        response = JSONResponse({"result": a / b})
        return response.to_starlette_response()
    except Exception as e:
        logger.exception("Error in divide endpoint")
        response = JSONResponse({"error": str(e)}, status_code=500)
        return response.to_starlette_response()

# Run the API server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000) 