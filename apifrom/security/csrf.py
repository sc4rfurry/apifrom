"""
CSRF protection middleware for APIFromAnything.

This module provides middleware for protecting against Cross-Site Request Forgery (CSRF) attacks.
"""

import base64
import hashlib
import hmac
import json
import re
import secrets
import time
from typing import Callable, Dict, List, Optional, Set, Union

from apifrom.core.request import Request
from apifrom.core.response import Response, JSONResponse
from apifrom.middleware.base import BaseMiddleware


class CSRFToken:
    """
    CSRF token generator and validator.
    """
    
    def __init__(
        self,
        secret: Optional[str] = None,
        token_length: int = 32,
        max_age: int = 3600,  # 1 hour
    ):
        """
        Initialize the CSRF token generator.
        
        Args:
            secret: Secret key for token generation (defaults to a random key)
            token_length: Length of the token in bytes
            max_age: Maximum age of tokens in seconds
        """
        self.secret = secret or secrets.token_hex(32)
        self.token_length = token_length
        self.max_age = max_age
    
    def generate_token(self, session_id: Optional[str] = None) -> str:
        """
        Generate a new CSRF token.
        
        Args:
            session_id: Session ID to bind the token to (optional)
            
        Returns:
            A new CSRF token
        """
        # Generate a random token
        random_bytes = secrets.token_bytes(self.token_length)
        random_token = base64.urlsafe_b64encode(random_bytes).decode()
        
        # Add timestamp for expiration
        timestamp = int(time.time())
        
        # Create the token parts
        parts = [random_token, str(timestamp)]
        
        # Add session binding if provided
        if session_id:
            parts.append(session_id)
        
        # Join the parts
        token_data = ":".join(parts)
        
        # Create a signature
        signature = self._create_signature(token_data)
        
        # Return the complete token
        return f"{token_data}:{signature}"
    
    def validate_token(self, token: str, session_id: Optional[str] = None) -> bool:
        """
        Validate a CSRF token.
        
        Args:
            token: The token to validate
            session_id: Session ID to validate against (optional)
            
        Returns:
            True if the token is valid, False otherwise
        """
        try:
            # Split the token into parts
            parts = token.split(":")
            
            # Check if the token has the correct format
            if len(parts) < 3:
                return False
            
            # Extract the parts
            if session_id:
                if len(parts) < 4:
                    return False
                random_token, timestamp_str, token_session_id, signature = parts
                
                # Verify session binding
                if token_session_id != session_id:
                    return False
            else:
                if len(parts) < 3:
                    return False
                random_token, timestamp_str, signature = parts
            
            # Reconstruct the token data for signature verification
            token_data = ":".join(parts[:-1])
            
            # Verify the signature
            expected_signature = self._create_signature(token_data)
            if not hmac.compare_digest(signature, expected_signature):
                return False
            
            # Check if the token has expired
            timestamp = int(timestamp_str)
            current_time = int(time.time())
            if current_time - timestamp > self.max_age:
                return False
            
            return True
        except Exception:
            return False
    
    def _create_signature(self, data: str) -> str:
        """
        Create a signature for the given data.
        
        Args:
            data: The data to sign
            
        Returns:
            The signature
        """
        return hmac.new(
            self.secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()


class CSRFMiddleware(BaseMiddleware):
    """
    Middleware for CSRF protection.
    """
    
    def __init__(
        self,
        secret: Optional[str] = None,
        token_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        cookie_name: str = "csrf_token",
        cookie_path: str = "/",
        cookie_secure: bool = True,
        cookie_http_only: bool = True,
        cookie_same_site: str = "Lax",
        exempt_methods: Optional[Set[str]] = None,
        exempt_routes: Optional[List[str]] = None,
        error_message: str = "CSRF token validation failed",
    ):
        """
        Initialize the CSRF middleware.

        Args:
            secret: Secret key for token generation (defaults to a random key)
            token_name: Name of the token in forms and query parameters
            header_name: Name of the token header
            cookie_name: Name of the token cookie
            cookie_path: Path for the token cookie
            cookie_secure: Whether the cookie should be secure (HTTPS only)
            cookie_http_only: Whether the cookie should be HTTP only
            cookie_same_site: SameSite attribute for the cookie
            exempt_methods: HTTP methods exempt from CSRF protection
            exempt_routes: Routes exempt from CSRF protection
            error_message: Error message for CSRF validation failures
        """
        super().__init__()
        self.secret = secret or secrets.token_hex(32)
        self.token_name = token_name
        self.header_name = header_name
        self.cookie_name = cookie_name
        self.cookie_path = cookie_path
        self.cookie_secure = cookie_secure
        self.cookie_http_only = cookie_http_only
        self.cookie_same_site = cookie_same_site
        self.exempt_methods = exempt_methods or {"GET", "HEAD", "OPTIONS", "TRACE"}
        self.exempt_routes = exempt_routes or []
        self.error_message = error_message
    
    def _is_exempt(self, request: Request) -> bool:
        """
        Check if a request is exempt from CSRF protection.
        
        Args:
            request: The request to check
            
        Returns:
            True if the request is exempt, False otherwise
        """
        # Check if the method is exempt
        if request.method in self.exempt_methods:
            return True
        
        # Check if the route is exempt
        for route in self.exempt_routes:
            if request.path.startswith(route):
                return True
        
        return False
    
    def _get_token_from_request(self, request: Request) -> Optional[str]:
        """
        Get the CSRF token from a request.

        Args:
            request: The request to get the token from

        Returns:
            The CSRF token, or None if not found
        """
        # Try to get the token from the header
        token = request.headers.get(self.header_name)
        if token:
            return token

        # Try to get the token from the form data
        if hasattr(request, "form") and request.form:
            token = request.form.get(self.token_name)
            if token:
                return token

        # Try to get the token from the JSON body
        if hasattr(request, "json") and request.json:
            token = request.json.get(self.token_name)
            if token:
                return token

        # Try to get the token from the query parameters
        if hasattr(request, "query_params") and request.query_params:
            token = request.query_params.get(self.token_name)
            if token:
                return token

        return None
    
    def _get_session_id(self, request: Request) -> Optional[str]:
        """
        Get the session ID from a request.
        
        Args:
            request: The request to get the session ID from
            
        Returns:
            The session ID, or None if not found
        """
        # Default implementation: try to get the session ID from the request state
        return getattr(request.state, "session_id", None)
    
    def _set_csrf_cookie(self, response: Response, token: str) -> None:
        """
        Set the CSRF token cookie on a response.
        
        Args:
            response: The response to set the cookie on
            token: The CSRF token
        """
        cookie_value = f"{self.cookie_name}={token}; Path={self.cookie_path}"
        
        if self.cookie_secure:
            cookie_value += "; Secure"
        
        if self.cookie_http_only:
            cookie_value += "; HttpOnly"
        
        if self.cookie_same_site:
            cookie_value += f"; SameSite={self.cookie_same_site}"
        
        response.headers["Set-Cookie"] = cookie_value
    
    def _generate_token(self, session_id: Optional[str] = None) -> str:
        """
        Generate a new CSRF token.

        Args:
            session_id: The session ID to use for token generation

        Returns:
            The generated token
        """
        # Create a payload with a timestamp and session ID
        payload = {
            "timestamp": int(time.time()),
            "session_id": session_id or "",
            "random": secrets.token_hex(8)
        }
        
        # Convert the payload to a string
        payload_str = json.dumps(payload)
        
        # Create a signature using HMAC-SHA256
        signature = hmac.new(
            self.secret.encode(),
            payload_str.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Combine the payload and signature
        token = f"{base64.urlsafe_b64encode(payload_str.encode()).decode()}.{signature}"
        
        return token
    
    def _validate_token(self, token: str, session_id: Optional[str] = None) -> bool:
        """
        Validate a CSRF token.

        Args:
            token: The token to validate
            session_id: The session ID to validate against

        Returns:
            True if the token is valid, False otherwise
        """
        try:
            # Split the token into payload and signature
            payload_b64, signature = token.split(".")
            
            # Decode the payload
            payload_str = base64.urlsafe_b64decode(payload_b64.encode()).decode()
            payload = json.loads(payload_str)
            
            # Verify the signature
            expected_signature = hmac.new(
                self.secret.encode(),
                payload_str.encode(),
                digestmod=hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return False
            
            # Check if the token has expired (1 hour validity)
            if int(time.time()) - payload["timestamp"] > 3600:
                return False
            
            # If a session ID is provided, check if it matches
            if session_id and payload["session_id"] and payload["session_id"] != session_id:
                return False
            
            return True
        except Exception:
            # Any exception during validation means the token is invalid
            return False
    
    async def process_request(self, request: Request) -> Request:
        """
        Process a request through the CSRF middleware.

        Args:
            request: The request to process

        Returns:
            The processed request
        """
        # Check if the request is exempt from CSRF protection
        if self._is_exempt(request):
            # For GET requests, generate a new token and store it in the request state
            if request.method == "GET":
                # Get the session ID if available
                session_id = self._get_session_id(request)
                
                # Generate a new token
                token = self._generate_token(session_id)
                
                # Store the token in the request state for use in process_response
                request.state.csrf_token = token
                request.state.needs_csrf_cookie = True
            
            # Request is exempt, continue processing
            return request
        
        # Request is not exempt, validate the token
        token = self._get_token_from_request(request)
        session_id = self._get_session_id(request)
        
        if not token or not self._validate_token(token, session_id):
            # Token validation failed, store the error in the request state
            request.state.csrf_error = True
            request.state.csrf_error_message = self.error_message
            return request
        
        # Token validation succeeded, continue processing
        return request
    
    async def process_response(self, response: Response) -> Response:
        """
        Process a response through the CSRF middleware.

        Args:
            response: The response to process

        Returns:
            The processed response
        """
        # If there was a CSRF error, return a 403 Forbidden response
        if hasattr(response.request.state, 'csrf_error') and response.request.state.csrf_error:
            error_response = JSONResponse(
                {"error": response.request.state.csrf_error_message},
                status_code=403
            )
            return error_response
        
        # If a new token was generated, set it in the response cookie
        if hasattr(response.request.state, 'needs_csrf_cookie') and response.request.state.needs_csrf_cookie:
            token = response.request.state.csrf_token
            self._set_csrf_cookie(response, token)
        
        return response


def csrf_exempt(func):
    """
    Decorator to exempt a function from CSRF protection.
    
    Args:
        func: The function to exempt
        
    Returns:
        The decorated function
    """
    func._csrf_exempt = True
    return func 