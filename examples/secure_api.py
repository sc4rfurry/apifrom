"""
Secure API example using APIFromAnything.

This example demonstrates how to use the security features of the APIFromAnything
library to secure API endpoints with various authentication methods.
"""

import datetime
import logging
import time
from typing import Dict, List

import jwt

from apifrom import API, api
from apifrom.security import (
    jwt_required,
    api_key_required,
    basic_auth_required,
    oauth2_required,
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create API instance
app = API(
    title="Secure API Example",
    description="A secure API created with APIFromAnything",
    version="1.0.0",
    debug=True
)

# JWT configuration
JWT_SECRET = "my-secure-jwt-secret"
JWT_ALGORITHM = "HS256"

# API keys
API_KEYS = {
    "api-key-1": ["read"],
    "api-key-2": ["read", "write"],
}

# Basic auth credentials
BASIC_AUTH_CREDENTIALS = {
    "admin": "password",
    "user": "password",
}


# Public endpoint (no authentication required)
@api(route="/public")
def public_endpoint() -> Dict[str, str]:
    """
    Public endpoint that doesn't require authentication.
    
    Returns:
        A message
    """
    return {"message": "This is a public endpoint"}


# JWT-protected endpoint
@api(route="/jwt-protected")
@jwt_required(secret=JWT_SECRET, algorithm=JWT_ALGORITHM)
def jwt_protected_endpoint(request) -> Dict[str, any]:
    """
    JWT-protected endpoint.
    
    This endpoint requires a valid JWT token.
    
    Args:
        request: The request object
        
    Returns:
        The JWT payload
    """
    # The JWT payload is available in request.state.jwt_payload
    return {
        "message": "This endpoint is protected by JWT",
        "payload": request.state.jwt_payload,
    }


# API key-protected endpoint
@api(route="/api-key-protected")
@api_key_required(api_keys=API_KEYS)
def api_key_protected_endpoint(request) -> Dict[str, str]:
    """
    API key-protected endpoint.
    
    This endpoint requires a valid API key.
    
    Args:
        request: The request object
        
    Returns:
        A message
    """
    # The API key is available in request.state.api_key
    return {
        "message": "This endpoint is protected by API key",
        "api_key": request.state.api_key,
    }


# API key-protected endpoint with scope
@api(route="/api-key-write")
@api_key_required(api_keys=API_KEYS, scopes=["write"])
def api_key_write_endpoint(request) -> Dict[str, str]:
    """
    API key-protected endpoint with write scope.
    
    This endpoint requires a valid API key with the "write" scope.
    
    Args:
        request: The request object
        
    Returns:
        A message
    """
    return {
        "message": "This endpoint is protected by API key with write scope",
        "api_key": request.state.api_key,
    }


# Basic auth-protected endpoint
@api(route="/basic-auth-protected")
@basic_auth_required(credentials=BASIC_AUTH_CREDENTIALS)
def basic_auth_protected_endpoint(request) -> Dict[str, str]:
    """
    Basic auth-protected endpoint.
    
    This endpoint requires valid Basic auth credentials.
    
    Args:
        request: The request object
        
    Returns:
        A message
    """
    # The username is available in request.state.username
    return {
        "message": "This endpoint is protected by Basic auth",
        "username": request.state.username,
    }


# OAuth2-protected endpoint
@api(route="/oauth2-protected")
@oauth2_required(scopes=["read"])
def oauth2_protected_endpoint(request) -> Dict[str, str]:
    """
    OAuth2-protected endpoint.
    
    This endpoint requires a valid OAuth2 token.
    
    Args:
        request: The request object
        
    Returns:
        A message
    """
    # The OAuth2 token is available in request.state.oauth2_token
    return {
        "message": "This endpoint is protected by OAuth2",
        "token": request.state.oauth2_token,
    }


# Endpoint to generate a JWT token for testing
@api(route="/generate-token", method="POST")
def generate_token(username: str, role: str = "user") -> Dict[str, str]:
    """
    Generate a JWT token for testing.
    
    Args:
        username: The username to include in the token
        role: The role to include in the token
        
    Returns:
        The generated token
    """
    # Create the JWT payload
    payload = {
        "sub": username,
        "role": role,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    
    # Generate the JWT token
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {"token": token}


if __name__ == "__main__":
    # Run the API server
    app.run(host="0.0.0.0", port=8002) 