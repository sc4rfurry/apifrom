# Security Guide for APIFromAnything

This guide covers the security features available in APIFromAnything and best practices for securing your APIs.

## Authentication Methods

APIFromAnything provides several built-in authentication methods:

### JWT Authentication

JSON Web Tokens (JWT) provide a stateless authentication mechanism:

```python
from apifrom import API, api
from apifrom.security import jwt_required

# Create an API instance
app = API()

# JWT configuration
JWT_SECRET = "your-secret-key"
JWT_ALGORITHM = "HS256"

@api(route="/protected", method="GET")
@jwt_required(
    secret=JWT_SECRET,
    algorithm=JWT_ALGORITHM,
    token_location="header",  # Where to look for the token (header, query, cookie)
    header_name="Authorization",  # Header name
    header_type="Bearer",  # Header type
    verify_exp=True,  # Verify token expiration
    verify_aud=False,  # Verify audience
    verify_iss=False,  # Verify issuer
    verify_sub=False,  # Verify subject
    verify_jti=False,  # Verify JWT ID
    verify_at_hash=False,  # Verify access token hash
)
def protected_endpoint(request):
    # Access JWT payload
    jwt_payload = request.state.jwt_payload
    user_id = jwt_payload.get("sub")
    
    return {"message": f"Hello, user {user_id}!"}
```

#### Generating JWT Tokens

```python
from apifrom.security import create_jwt_token

# Generate a JWT token
token = create_jwt_token(
    payload={"sub": "user123", "role": "admin"},
    secret="your-secret-key",
    algorithm="HS256",
    expires_delta=3600,  # Token expiration in seconds
)

print(f"JWT Token: {token}")
```

### API Key Authentication

API keys provide a simple authentication mechanism:

```python
from apifrom import API, api
from apifrom.security import api_key_required

# Create an API instance
app = API()

# API key configuration
API_KEYS = {
    "api-key-1": ["read"],
    "api-key-2": ["read", "write"],
}

@api(route="/api-key-protected", method="GET")
@api_key_required(
    api_keys=API_KEYS,
    scopes=["read"],  # Required scopes
    header_name="X-API-Key",  # Header name
    query_param_name=None,  # Query parameter name (if used)
    cookie_name=None,  # Cookie name (if used)
)
def api_key_protected_endpoint(request):
    # Access API key
    api_key = request.state.api_key
    
    return {"message": f"Hello, API key {api_key}!"}
```

### Basic Authentication

Basic authentication uses username and password:

```python
from apifrom import API, api
from apifrom.security import basic_auth_required

# Create an API instance
app = API()

# Basic auth configuration
CREDENTIALS = {
    "user1": "password1",
    "user2": "password2",
}

@api(route="/basic-auth-protected", method="GET")
@basic_auth_required(
    credentials=CREDENTIALS,
    realm="My API",  # Realm for WWW-Authenticate header
)
def basic_auth_protected_endpoint(request):
    # Access username
    username = request.state.username
    
    return {"message": f"Hello, {username}!"}
```

### OAuth2 Authentication

OAuth2 provides a more complex authentication mechanism:

```python
from apifrom import API, api
from apifrom.security import oauth2_required

# Create an API instance
app = API()

# OAuth2 configuration
OAUTH2_CONFIG = {
    "token_url": "https://auth.example.com/token",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "scopes": ["read", "write"],
}

@api(route="/oauth2-protected", method="GET")
@oauth2_required(
    config=OAUTH2_CONFIG,
    scopes=["read"],  # Required scopes
)
def oauth2_protected_endpoint(request):
    # Access OAuth2 token
    token = request.state.oauth2_token
    
    return {"message": "Hello, OAuth2 user!"}
```

### Multiple Authentication Methods

You can combine multiple authentication methods:

```python
from apifrom import API, api
from apifrom.security import multi_auth_required, jwt_required, api_key_required

# Create an API instance
app = API()

# Authentication configurations
JWT_CONFIG = {"secret": "your-secret-key", "algorithm": "HS256"}
API_KEY_CONFIG = {"api_keys": {"api-key-1": ["read"]}}

@api(route="/multi-auth-protected", method="GET")
@multi_auth_required(
    auth_methods=[
        jwt_required(**JWT_CONFIG),
        api_key_required(**API_KEY_CONFIG),
    ],
    require_all=False,  # If True, all methods must pass; if False, any method can pass
)
def multi_auth_protected_endpoint(request):
    # Check which authentication method passed
    if hasattr(request.state, "jwt_payload"):
        user_id = request.state.jwt_payload.get("sub")
        return {"message": f"Hello, JWT user {user_id}!"}
    elif hasattr(request.state, "api_key"):
        api_key = request.state.api_key
        return {"message": f"Hello, API key {api_key}!"}
    
    return {"message": "Hello, authenticated user!"}
```

## Security Middleware

APIFromAnything provides several security middleware components:

### CORS Middleware

Cross-Origin Resource Sharing (CORS) controls which domains can access your API:

```python
from apifrom import API
from apifrom.middleware import CORSMiddleware

# Create an API instance
app = API()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware(
        allow_origins=["https://example.com", "https://app.example.com"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Custom-Header"],
        allow_credentials=True,
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
)
```

### CSRF Middleware

Cross-Site Request Forgery (CSRF) protection:

```python
from apifrom import API
from apifrom.middleware import CSRFMiddleware

# Create an API instance
app = API()

# Add CSRF middleware
app.add_middleware(
    CSRFMiddleware(
        secret="your-csrf-secret",
        cookie_name="csrf_token",
        header_name="X-CSRF-Token",
        secure=True,  # Only send cookie over HTTPS
        samesite="strict",  # Cookie same-site policy
        methods=["POST", "PUT", "DELETE", "PATCH"],  # Methods to protect
    )
)
```

### Security Headers Middleware

Add security headers to responses:

```python
from apifrom import API
from apifrom.middleware import SecurityHeadersMiddleware

# Create an API instance
app = API()

# Add security headers middleware
app.add_middleware(
    SecurityHeadersMiddleware(
        # Content Security Policy
        csp={
            "default-src": ["'self'"],
            "script-src": ["'self'", "https://cdn.example.com"],
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:"],
            "font-src": ["'self'", "https://fonts.googleapis.com"],
            "connect-src": ["'self'", "https://api.example.com"],
            "object-src": ["'none'"],
            "frame-ancestors": ["'none'"],
            "upgrade-insecure-requests": True,
            "block-all-mixed-content": True,
        },
        # HTTP Strict Transport Security
        hsts={
            "max-age": 31536000,  # 1 year
            "includeSubDomains": True,
            "preload": True,
        },
        # X-Content-Type-Options
        x_content_type_options="nosniff",
        # X-Frame-Options
        x_frame_options="DENY",
        # X-XSS-Protection
        x_xss_protection="1; mode=block",
        # Referrer-Policy
        referrer_policy="strict-origin-when-cross-origin",
        # Permissions-Policy
        permissions_policy={
            "geolocation": ["self"],
            "microphone": [],
            "camera": [],
            "payment": [],
        },
    )
)
```

### Rate Limiting Middleware

Protect against abuse with rate limiting:

```python
from apifrom import API
from apifrom.middleware import RateLimitMiddleware

# Create an API instance
app = API()

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware(
        limit=100,  # Maximum requests
        window=60,  # Time window in seconds
        key_func=lambda request: request.client.host,  # Function to extract the client key
        storage="memory",  # Storage backend (memory, redis)
        redis_url=None,  # Redis URL (if using redis storage)
        headers=True,  # Add rate limit headers to responses
    )
)
```

## Input Validation

APIFromAnything automatically validates input types:

```python
from apifrom import API, api
from pydantic import BaseModel, Field, EmailStr, validator

# Create an API instance
app = API()

# Define a Pydantic model for validation
class User(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    age: int = Field(..., ge=18, le=120)
    password: str = Field(..., min_length=8)
    
    # Custom validator
    @validator("password")
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

@api(route="/users", method="POST")
def create_user(user: User) -> dict:
    """Create a new user."""
    # Password is automatically validated
    return {"id": 123, **user.dict(exclude={"password"})}
```

## SQL Injection Prevention

APIFromAnything helps prevent SQL injection:

```python
from apifrom import API, api
from apifrom.database import Database

# Create an API instance
app = API()

# Create a database connection
db = Database("sqlite:///app.db")

@api(route="/users/{user_id}", method="GET")
def get_user(user_id: int) -> dict:
    """Get a user by ID."""
    # Parameters are automatically sanitized
    user = db.query("SELECT * FROM users WHERE id = ?", [user_id])
    return user
```

## Best Practices

### 1. Use HTTPS

Always use HTTPS in production:

```python
from apifrom import API

app = API()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=443,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem",
    )
```

### 2. Store Secrets Securely

Use environment variables or a secure vault for secrets:

```python
import os
from apifrom import API, api
from apifrom.security import jwt_required

# Create an API instance
app = API()

# Get secrets from environment variables
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

@api(route="/protected", method="GET")
@jwt_required(secret=JWT_SECRET, algorithm=JWT_ALGORITHM)
def protected_endpoint(request):
    return {"message": "Protected endpoint"}
```

### 3. Implement Proper Error Handling

Don't expose sensitive information in error messages:

```python
from apifrom import API, api
from apifrom.middleware import ErrorHandlingMiddleware

# Create an API instance
app = API()

# Add error handling middleware
app.add_middleware(
    ErrorHandlingMiddleware(
        debug=False,  # Don't include debug information in production
        include_traceback=False,  # Don't include tracebacks in error responses
        log_exceptions=True,  # Log exceptions to the console
    )
)
```

### 4. Implement Proper Logging

Log security events:

```python
import logging
from apifrom import API, api
from apifrom.security import jwt_required

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="security.log",
)
logger = logging.getLogger("security")

# Create an API instance
app = API()

@api(route="/protected", method="GET")
@jwt_required(secret="your-secret-key", algorithm="HS256")
def protected_endpoint(request):
    # Log access
    logger.info(
        f"Access to protected endpoint: user={request.state.jwt_payload.get('sub')}, "
        f"ip={request.client.host}"
    )
    return {"message": "Protected endpoint"}
```

### 5. Implement Proper Access Control

Use role-based access control:

```python
from apifrom import API, api
from apifrom.security import jwt_required

# Create an API instance
app = API()

def has_role(request, role):
    """Check if the user has the required role."""
    jwt_payload = request.state.jwt_payload
    user_roles = jwt_payload.get("roles", [])
    return role in user_roles

@api(route="/admin", method="GET")
@jwt_required(secret="your-secret-key", algorithm="HS256")
def admin_endpoint(request):
    # Check if the user has the admin role
    if not has_role(request, "admin"):
        return {"error": "Forbidden"}, 403
    
    return {"message": "Admin endpoint"}
```

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Implement proper authentication
- [ ] Implement proper authorization
- [ ] Validate all input
- [ ] Sanitize all output
- [ ] Implement proper error handling
- [ ] Implement proper logging
- [ ] Implement rate limiting
- [ ] Implement CORS
- [ ] Implement CSRF protection
- [ ] Implement security headers
- [ ] Store secrets securely
- [ ] Keep dependencies up to date
- [ ] Perform security audits
- [ ] Have a security incident response plan

## Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [JWT.io](https://jwt.io/)
- [API Security Best Practices](https://github.com/shieldfy/API-Security-Checklist) 