import sys
sys.path.append('.')

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

# Define a simple endpoint
@pytest.mark.asyncio
async def test_endpoint(request):
    """Test that a simple endpoint works."""
    response = JSONResponse({"message": "Hello, World!"})
    assert response.status_code == 200
    assert b'"message":"Hello, World!"' in response.body
    return response

# This is just an example app, not part of the tests
def create_example_app():
    # Create routes
    routes = [
        Route("/test", test_endpoint)
    ]

    # Create a simple API
    return Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    app = create_example_app()
    print("Starting server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000) 