"""
Error Handling Example for APIFromAnything.

This example demonstrates how to use the error handling middleware
to properly handle exceptions in API endpoints.
"""

from typing import Dict, List, Optional, Any

from apifrom import API, api
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware import (
    ErrorHandlingMiddleware,
    APIError,
    BadRequestError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
    UnprocessableEntityError,
    TooManyRequestsError
)

# Create an API instance
app = API(
    title="Error Handling Example API",
    description="An example of using error handling middleware in APIFromAnything",
    version="1.0.0"
)

# Add the error handling middleware
app.add_middleware(
    ErrorHandlingMiddleware(
        debug=True,  # Enable debug mode for development
        include_traceback=True,  # Include tracebacks in debug mode
        include_exception_class=True,  # Include exception class names
        log_exceptions=True  # Log exceptions
    )
)

# Simulate a database with users
users_db = [
    {"id": 1, "username": "alice", "email": "alice@example.com", "role": "admin"},
    {"id": 2, "username": "bob", "email": "bob@example.com", "role": "user"},
    {"id": 3, "username": "charlie", "email": "charlie@example.com", "role": "user"}
]


# Example endpoint that might raise different exceptions
@api(route="/users/{user_id}", method="GET")
def get_user(user_id: int) -> Dict[str, Any]:
    """
    Get a user by ID.
    
    Args:
        user_id: The user ID
        
    Returns:
        The user data
        
    Raises:
        NotFoundError: If the user does not exist
    """
    # Validate that the ID is positive
    if user_id <= 0:
        raise BadRequestError(
            message="User ID must be positive",
            error_code="invalid_user_id",
            details={"user_id": user_id}
        )
    
    # Find the user
    for user in users_db:
        if user["id"] == user_id:
            return user
    
    # User not found
    raise NotFoundError(
        message=f"User with ID {user_id} not found",
        error_code="user_not_found",
        details={"user_id": user_id}
    )


# Example endpoint that demonstrates validation errors
@api(route="/users", method="POST")
def create_user(username: str, email: str, role: str = "user") -> Dict[str, Any]:
    """
    Create a new user.
    
    Args:
        username: The username
        email: The email address
        role: The user role (default: "user")
        
    Returns:
        The created user
        
    Raises:
        BadRequestError: If the request data is invalid
        ConflictError: If the username or email already exists
    """
    # Validate the inputs
    validation_errors = {}
    
    if not username:
        validation_errors["username"] = ["Username is required"]
    elif len(username) < 3:
        validation_errors["username"] = ["Username must be at least 3 characters"]
    
    if not email:
        validation_errors["email"] = ["Email is required"]
    elif "@" not in email:
        validation_errors["email"] = ["Invalid email format"]
    
    if role not in ["admin", "user"]:
        validation_errors["role"] = ["Role must be 'admin' or 'user'"]
    
    # If there are validation errors, raise an exception
    if validation_errors:
        raise UnprocessableEntityError(
            message="Validation error",
            error_code="validation_error",
            validation_errors=validation_errors
        )
    
    # Check if the username or email already exists
    for user in users_db:
        if user["username"] == username:
            raise ConflictError(
                message="Username already exists",
                error_code="username_exists",
                details={"username": username}
            )
        if user["email"] == email:
            raise ConflictError(
                message="Email already exists",
                error_code="email_exists",
                details={"email": email}
            )
    
    # Create the user
    user_id = max(user["id"] for user in users_db) + 1
    new_user = {
        "id": user_id,
        "username": username,
        "email": email,
        "role": role
    }
    
    # Add to the database
    users_db.append(new_user)
    
    return new_user


# Example endpoint that demonstrates authorization errors
@api(route="/admin", method="GET")
def admin_endpoint(request: Request) -> Dict[str, Any]:
    """
    Admin-only endpoint.
    
    Returns:
        Admin data
        
    Raises:
        UnauthorizedError: If the user is not authenticated
        ForbiddenError: If the user is not an admin
    """
    # Check if the request has an Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise UnauthorizedError(
            message="Authentication required",
            error_code="authentication_required"
        )
    
    # Simulate authentication (in a real app, you would validate the token)
    # For this example, we'll just check if the header contains a username
    username = None
    for user in users_db:
        if user["username"] in auth_header:
            username = user["username"]
            user_data = user
            break
    
    if not username:
        raise UnauthorizedError(
            message="Invalid authentication",
            error_code="invalid_authentication"
        )
    
    # Check if the user is an admin
    if user_data["role"] != "admin":
        raise ForbiddenError(
            message="Admin access required",
            error_code="admin_required",
            details={"user_role": user_data["role"]}
        )
    
    # Return admin data
    return {
        "message": "Welcome to the admin area",
        "user": user_data
    }


# Example endpoint that demonstrates rate limiting errors
counter = 0
@api(route="/rate-limited", method="GET")
def rate_limited_endpoint() -> Dict[str, Any]:
    """
    Rate-limited endpoint.
    
    Returns:
        A message
        
    Raises:
        TooManyRequestsError: If the rate limit is exceeded
    """
    global counter
    counter += 1
    
    # Simulate rate limiting (every 5 requests)
    if counter % 5 == 0:
        raise TooManyRequestsError(
            message="Rate limit exceeded",
            error_code="rate_limit_exceeded",
            retry_after=30  # Try again after 30 seconds
        )
    
    return {"message": f"Request {counter} succeeded"}


# Example of an endpoint that will raise a standard Python exception
@api(route="/standard-error", method="GET")
def standard_error() -> Dict[str, Any]:
    """
    Endpoint that raises a standard Python exception.
    
    Returns:
        Never returns successfully
        
    Raises:
        ValueError: Always raises a ValueError
    """
    # Raise a standard Python exception
    raise ValueError("This is a demonstration of handling standard Python exceptions")


# Example of an endpoint that will raise a KeyError
@api(route="/key-error", method="GET")
def key_error() -> Dict[str, Any]:
    """
    Endpoint that raises a KeyError.
    
    Returns:
        Never returns successfully
        
    Raises:
        KeyError: Always raises a KeyError
    """
    # This will raise a KeyError
    data = {}
    return {"value": data["non_existent_key"]}


# Example of an endpoint that will raise a custom exception
class CustomApplicationError(Exception):
    """A custom application exception."""
    pass

@api(route="/custom-error", method="GET")
def custom_error() -> Dict[str, Any]:
    """
    Endpoint that raises a custom exception.
    
    Returns:
        Never returns successfully
        
    Raises:
        CustomApplicationError: Always raises a CustomApplicationError
    """
    # Raise a custom exception
    raise CustomApplicationError("This is a custom application exception")


# Add a custom exception handler
custom_handler = app.error_handler.add_exception_handler(
    CustomApplicationError,
    lambda e: Response(
        content={
            "error": {
                "message": str(e),
                "code": "custom_error",
                "status": 500,
                "type": "CustomApplicationError"
            }
        },
        status_code=500,
        headers={"Content-Type": "application/json"}
    )
)


# Run the API server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000) 