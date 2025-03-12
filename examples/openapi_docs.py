"""
OpenAPI documentation example using APIFromAnything.

This example demonstrates how to generate OpenAPI/Swagger documentation
for an API created with the APIFromAnything library.
"""

import logging
import os
from typing import Dict, List, Optional

from apifrom import API, api
from apifrom.docs.openapi import OpenAPIGenerator
from apifrom.security import jwt_required

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create API instance
app = API(
    title="Pet Store API",
    description="A sample Pet Store API created with APIFromAnything",
    version="1.0.0",
    debug=True
)

# JWT configuration
JWT_SECRET = "my-secure-jwt-secret"
JWT_ALGORITHM = "HS256"

# In-memory database
pets_db = [
    {"id": 1, "name": "Fluffy", "species": "cat", "age": 3},
    {"id": 2, "name": "Rex", "species": "dog", "age": 5},
    {"id": 3, "name": "Bubbles", "species": "fish", "age": 1},
]


@api(route="/pets", method="GET")
def get_pets(species: Optional[str] = None) -> List[Dict]:
    """
    Get all pets or filter by species.
    
    Args:
        species: Filter pets by species (optional)
        
    Returns:
        A list of pet objects
    """
    if species:
        return [pet for pet in pets_db if pet["species"] == species]
    return pets_db


@api(route="/pets/{pet_id}", method="GET")
def get_pet(pet_id: int) -> Dict:
    """
    Get a pet by ID.
    
    Args:
        pet_id: The ID of the pet to retrieve
        
    Returns:
        A pet object
    """
    for pet in pets_db:
        if pet["id"] == pet_id:
            return pet
    return {"error": "Pet not found"}


@api(route="/pets", method="POST")
@jwt_required(secret=JWT_SECRET, algorithm=JWT_ALGORITHM)
def create_pet(name: str, species: str, age: int) -> Dict:
    """
    Create a new pet.
    
    This endpoint requires JWT authentication.
    
    Args:
        name: The name of the pet
        species: The species of the pet
        age: The age of the pet
        
    Returns:
        The created pet object
    """
    pet_id = max(pet["id"] for pet in pets_db) + 1
    new_pet = {"id": pet_id, "name": name, "species": species, "age": age}
    pets_db.append(new_pet)
    return new_pet


@api(route="/pets/{pet_id}", method="PUT")
@jwt_required(secret=JWT_SECRET, algorithm=JWT_ALGORITHM)
def update_pet(pet_id: int, name: Optional[str] = None, species: Optional[str] = None, age: Optional[int] = None) -> Dict:
    """
    Update an existing pet.
    
    This endpoint requires JWT authentication.
    
    Args:
        pet_id: The ID of the pet to update
        name: The new name of the pet (optional)
        species: The new species of the pet (optional)
        age: The new age of the pet (optional)
        
    Returns:
        The updated pet object
    """
    for pet in pets_db:
        if pet["id"] == pet_id:
            if name:
                pet["name"] = name
            if species:
                pet["species"] = species
            if age:
                pet["age"] = age
            return pet
    return {"error": "Pet not found"}


@api(route="/pets/{pet_id}", method="DELETE")
@jwt_required(secret=JWT_SECRET, algorithm=JWT_ALGORITHM)
def delete_pet(pet_id: int) -> Dict:
    """
    Delete a pet.
    
    This endpoint requires JWT authentication.
    
    Args:
        pet_id: The ID of the pet to delete
        
    Returns:
        A success message
    """
    global pets_db
    for i, pet in enumerate(pets_db):
        if pet["id"] == pet_id:
            del pets_db[i]
            return {"message": f"Pet with ID {pet_id} deleted successfully"}
    return {"error": "Pet not found"}


@api(route="/docs/openapi.json", method="GET")
def get_openapi_json() -> Dict:
    """
    Get the OpenAPI documentation in JSON format.
    
    Returns:
        The OpenAPI documentation as a JSON object
    """
    generator = OpenAPIGenerator(
        title=app.title,
        description=app.description,
        version=app.version,
        router=app.router
    )
    return generator.generate()


@api(route="/docs/openapi.yaml", method="GET")
def get_openapi_yaml() -> str:
    """
    Get the OpenAPI documentation in YAML format.
    
    Returns:
        The OpenAPI documentation as a YAML string
    """
    generator = OpenAPIGenerator(
        title=app.title,
        description=app.description,
        version=app.version,
        router=app.router
    )
    return generator.to_yaml()


# Create a simple HTML page to serve Swagger UI
@api(route="/docs", method="GET")
def get_swagger_ui() -> str:
    """
    Get the Swagger UI HTML page.
    
    Returns:
        The Swagger UI HTML page
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Swagger UI</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.0.0/swagger-ui.css">
        <style>
            html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
            *, *:before, *:after { box-sizing: inherit; }
            body { margin: 0; background: #fafafa; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5.0.0/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {
                window.ui = SwaggerUIBundle({
                    url: "/docs/openapi.json",
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout"
                });
            };
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    # Run the API server
    app.run(host="0.0.0.0", port=8003) 