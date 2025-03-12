"""
An example of using the security features of the APIFromAnything library.
"""
import os
import time
import uuid
from typing import Dict, List, Optional

from apifrom import APIApp
from apifrom.security import JWTAuth, APIKeyAuth, BasicAuth
from apifrom.middleware import (
    CSRFMiddleware,
    CORSMiddleware,
    SecurityHeadersMiddleware,
    RateLimitingMiddleware
)

# Create an API instance
app = APIApp(
    title="Security Example",
    description="An example of using the security features of the APIFromAnything library",
    version="1.0.0"
)

# Generate a secret key for JWT
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-here")

# Set up authentication
jwt_auth = JWTAuth(secret_key=JWT_SECRET)
api_key_auth = APIKeyAuth(
    api_keys={
        "api-key-1": {"scopes": ["read"]},
        "api-key-2": {"scopes": ["read", "write"]},
    }
)
basic_auth = BasicAuth(
    users={
        "admin": {"password": "admin123", "scopes": ["admin"]},
        "user": {"password": "user123", "scopes": ["user"]},
    }
)

# Add security middleware
app.add_middleware(CORSMiddleware, 
                  allow_origins=["https://example.com"],
                  allow_methods=["GET", "POST", "PUT", "DELETE"],
                  allow_headers=["Content-Type", "Authorization"])

app.add_middleware(CSRFMiddleware, 
                  secret=JWT_SECRET,
                  cookie_name="csrf_token",
                  header_name="X-CSRF-Token")

app.add_middleware(SecurityHeadersMiddleware,
                  content_security_policy={
                      "default-src": ["'self'"],
                      "script-src": ["'self'", "https://cdn.example.com"],
                      "style-src": ["'self'", "https://cdn.example.com"],
                      "img-src": ["'self'", "data:", "https://cdn.example.com"],
                  },
                  xss_protection=True,
                  frame_options="DENY",
                  content_type_options="nosniff",
                  hsts=True)

app.add_middleware(RateLimitingMiddleware,
                  limit=100,
                  period=60,  # 100 requests per minute
                  key_func=lambda request: request.client.host)

# Simulated user database
users = {
    "user1": {"id": "user1", "username": "user1", "password": "password1"},
    "user2": {"id": "user2", "username": "user2", "password": "password2"},
}

# Simulated token database
tokens = {}

# Public endpoint
@app.api("/public")
def public_endpoint() -> Dict:
    """
    A public endpoint that doesn't require authentication.
    
    Returns:
        A message
    """
    return {"message": "This is a public endpoint"}

# JWT protected endpoint
@app.api("/jwt-protected")
@jwt_auth.requires_auth
def jwt_protected_endpoint(request) -> Dict:
    """
    A protected endpoint that requires JWT authentication.
    
    Returns:
        Information about the authenticated user
    """
    return {
        "message": "This is a JWT protected endpoint",
        "user": request.state.jwt_payload.get("sub"),
        "authenticated": True
    }

# API key protected endpoint
@app.api("/api-key-protected")
@api_key_auth.requires_auth
def api_key_protected_endpoint(request) -> Dict:
    """
    A protected endpoint that requires API key authentication.
    
    Returns:
        Information about the API key
    """
    return {
        "message": "This is an API key protected endpoint",
        "api_key": request.state.api_key,
        "scopes": request.state.scopes,
        "authenticated": True
    }

# Basic auth protected endpoint
@app.api("/basic-auth-protected")
@basic_auth.requires_auth
def basic_auth_protected_endpoint(request) -> Dict:
    """
    A protected endpoint that requires basic authentication.
    
    Returns:
        Information about the authenticated user
    """
    return {
        "message": "This is a basic auth protected endpoint",
        "user": request.state.user,
        "scopes": request.state.scopes,
        "authenticated": True
    }

# Login endpoint to get JWT token
@app.api("/login", methods=["POST"])
def login(username: str, password: str) -> Dict:
    """
    Login to get a JWT token.
    
    Args:
        username: The username
        password: The password
        
    Returns:
        A JWT token if authentication is successful
    """
    # Check if user exists and password is correct
    user = users.get(username)
    if not user or user["password"] != password:
        return {"error": "Invalid username or password"}, 401
    
    # Generate token
    token = jwt_auth.create_token(
        payload={
            "sub": username,
            "exp": int(time.time()) + 3600,  # 1 hour expiration
            "iat": int(time.time()),
            "jti": str(uuid.uuid4())
        }
    )
    
    # Store token
    tokens[token] = username
    
    return {"token": token, "token_type": "bearer", "expires_in": 3600}

# Logout endpoint
@app.api("/logout", methods=["POST"])
@jwt_auth.requires_auth
def logout(request) -> Dict:
    """
    Logout to invalidate the JWT token.
    
    Returns:
        A success message
    """
    # Get token from authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        
        # Remove token from storage
        if token in tokens:
            del tokens[token]
    
    return {"message": "Logged out successfully"}

# CSRF protected endpoint
@app.api("/csrf-protected", methods=["POST"])
def csrf_protected_endpoint(request) -> Dict:
    """
    A CSRF protected endpoint.
    
    Returns:
        A success message
    """
    return {"message": "CSRF protection passed"}

# Run the API server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000) 