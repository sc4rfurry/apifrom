"""
Tests for the security functionality of the APIFromAnything library.
"""

import base64
import json
import unittest
from typing import Dict

import jwt

from apifrom import API, api
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.security import jwt_required, api_key_required, basic_auth_required


class TestSecurity(unittest.TestCase):
    """
    Tests for the security functionality.
    """
    
    def setUp(self):
        """
        Set up the test environment.
        """
        self.api = API(
            title="Test API",
            description="API for testing security",
            version="1.0.0",
            debug=True
        )
        
        # JWT configuration
        self.jwt_secret = "test-secret"
        self.jwt_algorithm = "HS256"
        
        # API keys
        self.api_keys = {
            "test-key": ["read"],
            "admin-key": ["read", "write"],
        }
        
        # Basic auth credentials
        self.basic_auth_credentials = {
            "user": "password",
            "admin": "admin-password",
        }
    
    def test_jwt_authentication(self):
        """
        Test JWT authentication.
        """
        # Define a JWT-protected endpoint
        @api(route="/jwt-protected", method="GET")
        @jwt_required(secret=self.jwt_secret, algorithm=self.jwt_algorithm)
        async def jwt_protected_endpoint(request: Request) -> Dict:
            return {"user": request.state.jwt_payload.get("sub")}
        
        # Create a valid JWT token
        payload = {"sub": "test-user", "role": "user"}
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        # Create a mock request with a valid token
        valid_request = Request(
            method="GET",
            path="/jwt-protected",
            headers={"Authorization": f"Bearer {token}"},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Get the handler
        handler = self.api.router.get_route_handler("/jwt-protected", "GET")
        
        # Call the handler with a valid token
        import asyncio
        valid_response = asyncio.run(handler(valid_request))
        
        # Check the response
        self.assertEqual(valid_response.status_code, 200)
        self.assertEqual(json.loads(valid_response.body), {"user": "test-user"})
        
        # Create a mock request with an invalid token
        invalid_request = Request(
            method="GET",
            path="/jwt-protected",
            headers={"Authorization": "Bearer invalid-token"},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Call the handler with an invalid token
        invalid_response = asyncio.run(handler(invalid_request))
        
        # Check the response
        self.assertEqual(invalid_response.status_code, 401)
        self.assertIn("error", json.loads(invalid_response.body))
    
    def test_api_key_authentication(self):
        """
        Test API key authentication.
        """
        # Define an API key-protected endpoint
        @api(route="/api-key-protected", method="GET")
        @api_key_required(api_keys=self.api_keys)
        async def api_key_protected_endpoint(request: Request) -> Dict:
            return {"api_key": request.state.api_key}
        
        # Create a mock request with a valid API key
        valid_request = Request(
            method="GET",
            path="/api-key-protected",
            headers={"X-API-Key": "test-key"},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Get the handler
        handler = self.api.router.get_route_handler("/api-key-protected", "GET")
        
        # Call the handler with a valid API key
        import asyncio
        valid_response = asyncio.run(handler(valid_request))
        
        # Check the response
        self.assertEqual(valid_response.status_code, 200)
        self.assertEqual(json.loads(valid_response.body), {"api_key": "test-key"})
        
        # Create a mock request with an invalid API key
        invalid_request = Request(
            method="GET",
            path="/api-key-protected",
            headers={"X-API-Key": "invalid-key"},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Call the handler with an invalid API key
        invalid_response = asyncio.run(handler(invalid_request))
        
        # Check the response
        self.assertEqual(invalid_response.status_code, 401)
        self.assertIn("error", json.loads(invalid_response.body))
    
    def test_api_key_scopes(self):
        """
        Test API key scopes.
        """
        # Define an API key-protected endpoint with scope
        @api(route="/api-key-write", method="GET")
        @api_key_required(api_keys=self.api_keys, scopes=["write"])
        async def api_key_write_endpoint(request: Request) -> Dict:
            return {"api_key": request.state.api_key}
        
        # Create a mock request with a valid API key that has the required scope
        valid_request = Request(
            method="GET",
            path="/api-key-write",
            headers={"X-API-Key": "admin-key"},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Get the handler
        handler = self.api.router.get_route_handler("/api-key-write", "GET")
        
        # Call the handler with a valid API key
        import asyncio
        valid_response = asyncio.run(handler(valid_request))
        
        # Check the response
        self.assertEqual(valid_response.status_code, 200)
        self.assertEqual(json.loads(valid_response.body), {"api_key": "admin-key"})
        
        # Create a mock request with a valid API key that doesn't have the required scope
        invalid_scope_request = Request(
            method="GET",
            path="/api-key-write",
            headers={"X-API-Key": "test-key"},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Call the handler with an API key that doesn't have the required scope
        invalid_scope_response = asyncio.run(handler(invalid_scope_request))
        
        # Check the response
        self.assertEqual(invalid_scope_response.status_code, 403)
        self.assertIn("error", json.loads(invalid_scope_response.body))
    
    def test_basic_auth_authentication(self):
        """
        Test Basic auth authentication.
        """
        # Define a Basic auth-protected endpoint
        @api(route="/basic-auth-protected", method="GET")
        @basic_auth_required(credentials=self.basic_auth_credentials)
        async def basic_auth_protected_endpoint(request: Request) -> Dict:
            return {"username": request.state.username}
        
        # Create a mock request with valid Basic auth credentials
        credentials = base64.b64encode(b"user:password").decode("utf-8")
        valid_request = Request(
            method="GET",
            path="/basic-auth-protected",
            headers={"Authorization": f"Basic {credentials}"},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Get the handler
        handler = self.api.router.get_route_handler("/basic-auth-protected", "GET")
        
        # Call the handler with valid credentials
        import asyncio
        valid_response = asyncio.run(handler(valid_request))
        
        # Check the response
        self.assertEqual(valid_response.status_code, 200)
        self.assertEqual(json.loads(valid_response.body), {"username": "user"})
        
        # Create a mock request with invalid Basic auth credentials
        invalid_credentials = base64.b64encode(b"user:wrong-password").decode("utf-8")
        invalid_request = Request(
            method="GET",
            path="/basic-auth-protected",
            headers={"Authorization": f"Basic {invalid_credentials}"},
            query_params={},
            body=None,
            path_params={},
            client_ip="127.0.0.1"
        )
        
        # Call the handler with invalid credentials
        invalid_response = asyncio.run(handler(invalid_request))
        
        # Check the response
        self.assertEqual(invalid_response.status_code, 401)
        self.assertIn("error", json.loads(invalid_response.body))


if __name__ == "__main__":
    unittest.main() 