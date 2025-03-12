from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

# Define a simple endpoint
async def hello(request):
    name = request.path_params.get("name", "World")
    return JSONResponse({"message": f"Hello, {name}!"})

# Create routes
routes = [
    Route("/hello/{name:str}", hello),
    Route("/hello", hello)
]

# Create a simple API
app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    print("Starting server on http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001) 