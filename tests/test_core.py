"""
Tests for the core functionality of the APIFromAnything library.
"""

import json
import unittest
from typing import Dict, List, Optional
import asyncio
import logging

from apifrom import API, api
from apifrom.core.request import Request
from apifrom.core.response import Response, JSONResponse

logger = logging.getLogger(__name__)

class TestAPI(unittest.TestCase):
    """
    Tests for the API class.
    """
    
    def setUp(self):
        """
        Set up the test environment.
        """
        self.api = API(
            title="Test API",
            description="API for testing",
            version="1.0.0",
            debug=True
        )
    
    def test_api_initialization(self):
        """
        Test API initialization.
        """
        self.assertEqual(self.api.title, "Test API")
        self.assertEqual(self.api.description, "API for testing")
        self.assertEqual(self.api.version, "1.0.0")
        self.assertTrue(self.api.debug)
    
    def test_add_route(self):
        """
        Test adding a route to the API.
        """
        # Define a test handler
        def test_handler(request: Request) -> Response:
            return JSONResponse({"message": "Hello, World!"})
        
        # Add the route
        self.api.add_route("/test", endpoint=test_handler, methods=["GET"])
        
        # Check if the route was added
        route_found = False
        for route in self.api.router.routes:
            if route["path"] == "/test" and route["method"] == "GET" and route["handler"] == test_handler:
                route_found = True
                break
        
        self.assertTrue(route_found, "Route was not added correctly")
    
    def test_api_decorator(self):
        """
        Test the @api decorator.
        """
        # Define a test function
        @api(app=self.api, route="/test-decorator", method="GET")
        def test_function() -> Dict:
            return {"message": "Hello from decorator!"}
        
        # Check if the route was added
        route_found = False
        for route in self.api.router.routes:
            if route["path"] == "/test-decorator" and route["method"] == "GET":
                route_found = True
                break
        
        self.assertTrue(route_found, "Route was not added correctly")
    
    def test_path_parameters(self):
        """
        Test path parameters.
        """
        # Define a test function with path parameters
        @api(app=self.api, route="/users/{user_id}", method="GET")
        def get_user(user_id: int) -> Dict:
            return {"user_id": user_id, "name": f"User {user_id}"}
        
        # Create a mock request
        request = Request(
            method="GET",
            path="/users/123",
            headers={},
            query_params={},
            body=None,
            path_params={"user_id": "123"}
        )
        
        # Get the handler
        handler = self.api.router.get_route_handler("/users/{user_id}", "GET")
        
        # Call the handler
        response = asyncio.run(handler(request))
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.body), {"user_id": 123, "name": "User 123"})
    
    def test_query_parameters(self):
        """
        Test query parameters.
        """
        # Define a test function with query parameters
        @api(app=self.api, route="/search", method="GET")
        def search(query: str, limit: Optional[int] = 10) -> Dict:
            return {"query": query, "limit": limit, "results": []}
        
        # Create a mock request
        request = Request(
            method="GET",
            path="/search",
            headers={},
            query_params={"query": "test", "limit": "20"},
            body=None,
            path_params={}
        )
        
        # Get the handler
        handler = self.api.router.get_route_handler("/search", "GET")
        
        # Call the handler
        response = asyncio.run(handler(request))
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.body), {"query": "test", "limit": 20, "results": []})
    
    def test_request_body(self):
        """
        Test request body.
        """
        # Define a test function with request body
        @api(app=self.api, route="/users", method="POST")
        def create_user(name: str, age: int) -> Dict:
            logger.debug(f"create_user called with name={name}, age={age}")
            return {"name": name, "age": age, "id": 1}
        
        # Create a mock request
        request = Request(
            method="POST",
            path="/users",
            headers={"Content-Type": "application/json"},
            query_params={},
            body=json.dumps({"name": "John", "age": 30}).encode('utf-8'),
            path_params={}
        )
        
        logger.debug(f"Request body: {request._body}")
        logger.debug(f"Request headers: {request.headers}")

        # Get the handler
        handler = self.api.router.get_route_handler("/users", "POST")
        logger.debug(f"Handler: {handler}")

        # Call the handler
        response = asyncio.run(handler(request))
        logger.debug(f"Response: {response}")
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response body: {response.body}")

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.body), {"name": "John", "age": 30, "id": 1})
    
    def test_type_validation(self):
        """
        Test type validation.
        """
        # Define a test function with type validation
        @api(app=self.api, route="/validate", method="POST")
        def validate(name: str, age: int, tags: List[str]) -> Dict:
            return {"name": name, "age": age, "tags": tags}
        
        # Create a mock request with valid data
        valid_request = Request(
            method="POST",
            path="/validate",
            headers={"Content-Type": "application/json"},
            query_params={},
            body=json.dumps({"name": "John", "age": 30, "tags": ["a", "b", "c"]}).encode('utf-8'),
            path_params={}
        )
        
        # Get the handler
        handler = self.api.router.get_route_handler("/validate", "POST")
        
        # Call the handler with valid data
        valid_response = asyncio.run(handler(valid_request))
        
        # Check the response
        self.assertEqual(valid_response.status_code, 200)
        self.assertEqual(json.loads(valid_response.body), {"name": "John", "age": 30, "tags": ["a", "b", "c"]})
        
        # Create a mock request with invalid data (age as string)
        invalid_request = Request(
            method="POST",
            path="/validate",
            headers={"Content-Type": "application/json"},
            query_params={},
            body=json.dumps({"name": "John", "age": "thirty", "tags": ["a", "b", "c"]}).encode('utf-8'),
            path_params={}
        )
        
        # Call the handler with invalid data
        invalid_response = asyncio.run(handler(invalid_request))
        
        # Check the response
        self.assertEqual(invalid_response.status_code, 400)
        error_response = json.loads(invalid_response.body)
        self.assertIn("error", error_response)


if __name__ == "__main__":
    unittest.main() 