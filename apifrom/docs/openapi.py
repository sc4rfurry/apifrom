"""
OpenAPI documentation generator for APIFromAnything.

This module provides functionality to generate OpenAPI/Swagger documentation
for APIs created with the APIFromAnything library. It supports comprehensive
customization options and follows the OpenAPI 3.0 specification.
"""

import inspect
import json
import re
from typing import Any, Dict, List, Optional, Type, Union, get_type_hints, Callable

from apifrom.core.router import Router
from apifrom.utils.type_utils import (
    get_args,
    get_origin,
    is_optional_type,
    extract_optional_type,
    is_list_type,
    is_dict_type,
    is_union_type,
    get_union_types,
)


class OpenAPIConfig:
    """
    Configuration for OpenAPI documentation generation.
    
    This class provides configuration options for customizing the
    OpenAPI documentation generation process.
    """
    
    def __init__(
        self,
        title: str,
        description: str,
        version: str,
        terms_of_service: Optional[str] = None,
        contact: Optional[Dict[str, str]] = None,
        license_info: Optional[Dict[str, str]] = None,
        servers: Optional[List[Dict[str, str]]] = None,
        external_docs: Optional[Dict[str, str]] = None,
        tags: Optional[List[Dict[str, Any]]] = None,
        security: Optional[List[Dict[str, List[str]]]] = None,
        components: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the OpenAPI configuration.
        
        Args:
            title: The title of the API
            description: The description of the API
            version: The version of the API
            terms_of_service: URL to the terms of service
            contact: Contact information (name, url, email)
            license_info: License information (name, url)
            servers: Server information (url, description, variables)
            external_docs: External documentation (description, url)
            tags: API tags with descriptions
            security: Global security requirements
            components: Pre-defined components (schemas, responses, parameters, etc.)
        """
        self.title = title
        self.description = description
        self.version = version
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license_info = license_info
        self.servers = servers or [{"url": "/"}]
        self.external_docs = external_docs
        self.tags = tags or []
        self.security = security
        self.components = components or {}


class OpenAPIGenerator:
    """
    Generator for OpenAPI documentation.
    
    This class generates OpenAPI/Swagger documentation for APIs created with
    the APIFromAnything library, with extensive customization options.
    """
    
    def __init__(
        self,
        title: str,
        description: str,
        version: str,
        router: Router,
        config: Optional[OpenAPIConfig] = None,
    ):
        """
        Initialize the OpenAPI generator.
        
        Args:
            title: The title of the API
            description: The description of the API
            version: The version of the API
            router: The router instance containing the API routes
            config: Additional configuration options
        """
        self.router = router
        self.config = config or OpenAPIConfig(title, description, version)
        self.custom_schemas: Dict[str, Dict[str, Any]] = {}
        self.custom_responses: Dict[str, Dict[str, Any]] = {}
        self.custom_parameters: Dict[str, Dict[str, Any]] = {}
        self.custom_examples: Dict[str, Dict[str, Any]] = {}
        self.custom_request_bodies: Dict[str, Dict[str, Any]] = {}
        self.custom_headers: Dict[str, Dict[str, Any]] = {}
        self.custom_security_schemes: Dict[str, Dict[str, Any]] = {}
        self.custom_links: Dict[str, Dict[str, Any]] = {}
        self.custom_callbacks: Dict[str, Dict[str, Any]] = {}
    
    def generate(self) -> Dict[str, Any]:
        """
        Generate the OpenAPI documentation.
        
        Returns:
            The OpenAPI documentation as a dictionary
        """
        openapi_doc = {
            "openapi": "3.0.0",
            "info": self._generate_info(),
            "servers": self.config.servers,
            "paths": self._generate_paths(),
            "components": self._generate_components(),
        }
        
        # Add tags if defined
        if self.config.tags:
            openapi_doc["tags"] = self.config.tags
        
        # Add external docs if defined
        if self.config.external_docs:
            openapi_doc["externalDocs"] = self.config.external_docs
        
        # Add global security requirements if defined
        if self.config.security:
            openapi_doc["security"] = self.config.security
        
        return openapi_doc
    
    def _generate_info(self) -> Dict[str, Any]:
        """
        Generate the info section of the OpenAPI documentation.
        
        Returns:
            The info section as a dictionary
        """
        info = {
            "title": self.config.title,
            "description": self.config.description,
            "version": self.config.version,
        }
        
        # Add terms of service if defined
        if self.config.terms_of_service:
            info["termsOfService"] = self.config.terms_of_service
        
        # Add contact information if defined
        if self.config.contact:
            info["contact"] = self.config.contact
        
        # Add license information if defined
        if self.config.license_info:
            info["license"] = self.config.license_info
        
        return info
    
    def _generate_paths(self) -> Dict[str, Any]:
        """
        Generate the paths section of the OpenAPI documentation.
        
        Returns:
            The paths section as a dictionary
        """
        paths = {}
        
        for route_path, route_info in self.router.routes.items():
            path_item = {}
            
            for method, handler_info in route_info.items():
                handler = handler_info["handler"]
                operation = self._generate_operation(handler, method, route_path)
                
                # Add security requirements if applicable
                security_requirements = self._get_security_requirements(handler)
                if security_requirements:
                    operation["security"] = security_requirements
                
                path_item[method.lower()] = operation
            
            # Convert path parameters from {param} to {param} format if needed
            openapi_path = route_path
            
            paths[openapi_path] = path_item
        
        return paths
    
    def _generate_operation(self, handler, method: str, path: str) -> Dict[str, Any]:
        """
        Generate an operation object for the OpenAPI documentation.
        
        Args:
            handler: The handler function
            method: The HTTP method
            path: The route path
            
        Returns:
            The operation object as a dictionary
        """
        # Get function signature and docstring
        signature = inspect.signature(handler)
        docstring = inspect.getdoc(handler) or ""
        
        # Parse docstring to get description and parameter/return descriptions
        description, param_docs, return_doc, metadata = self._parse_docstring(docstring)
        
        # Get type hints
        type_hints = get_type_hints(handler)
        
        # Extract path parameters from the path
        path_params = re.findall(r'{([^}]+)}', path)
        
        # Generate parameters
        parameters = []
        request_body = None
        
        # Add path parameters first
        for param_name in path_params:
            param_type = type_hints.get(param_name, str)
            param_description = param_docs.get(param_name, "")
            
            parameter = {
                "name": param_name,
                "in": "path",
                "description": param_description,
                "required": True,
                "schema": self._get_schema_for_type(param_type),
            }
            
            parameters.append(parameter)
        
        # Add other parameters
        for param_name, param in signature.parameters.items():
            # Skip 'self' parameter for class methods
            if param_name == "self":
                continue
                
            # Skip 'request' parameter as it's handled internally
            if param_name == "request":
                continue
            
            # Skip path parameters as they're already added
            if param_name in path_params:
                continue
            
            # Get parameter type
            param_type = type_hints.get(param_name, Any)
            
            # Get parameter description from docstring
            param_description = param_docs.get(param_name, "")
            
            # For POST, PUT, PATCH methods, use request body for parameters
            if method.upper() in ["POST", "PUT", "PATCH"] and param_name not in ["path", "query"]:
                if not request_body:
                    request_body = {
                        "description": "Request body",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": [],
                                }
                            }
                        }
                    }
                
                # Add property to request body
                schema = request_body["content"]["application/json"]["schema"]
                schema["properties"][param_name] = self._get_schema_for_type(param_type)
                
                # If parameter has no default value, it's required
                if param.default == inspect.Parameter.empty:
                    schema["required"].append(param_name)
            else:
                # Add as query parameter
                parameter = {
                    "name": param_name,
                    "in": "query",
                    "description": param_description,
                    "schema": self._get_schema_for_type(param_type),
                }
                
                # If parameter has no default value, it's required
                if param.default == inspect.Parameter.empty and not is_optional_type(param_type):
                    parameter["required"] = True
                
                # Add examples if available
                if f"{param_name}_example" in metadata:
                    parameter["example"] = metadata[f"{param_name}_example"]
                
                parameters.append(parameter)
        
        # Generate responses
        responses = {
            "200": {
                "description": return_doc or "Successful response",
                "content": {
                    "application/json": {
                        "schema": self._get_schema_for_type(type_hints.get("return", Any)),
                    }
                }
            },
            "400": {
                "description": "Bad request",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "error": {"type": "string"},
                            }
                        }
                    }
                }
            },
            "500": {
                "description": "Internal server error",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "error": {"type": "string"},
                            }
                        }
                    }
                }
            }
        }
        
        # Add custom responses from metadata
        if "responses" in metadata:
            for status_code, response_info in metadata["responses"].items():
                responses[str(status_code)] = response_info
        
        # Build operation object
        operation = {
            "summary": metadata.get("summary", self._get_summary(handler.__name__, description)),
            "description": description,
            "parameters": parameters,
            "responses": responses,
        }
        
        # Add operation ID if available
        if "operationId" in metadata:
            operation["operationId"] = metadata["operationId"]
        else:
            operation["operationId"] = handler.__name__
        
        # Add tags if available
        if "tags" in metadata:
            operation["tags"] = metadata["tags"]
        
        # Add deprecated flag if available
        if "deprecated" in metadata:
            operation["deprecated"] = metadata["deprecated"]
        
        # Add external docs if available
        if "externalDocs" in metadata:
            operation["externalDocs"] = metadata["externalDocs"]
        
        # Add request body if present
        if request_body:
            # Add examples if available
            if "requestBodyExample" in metadata:
                request_body["content"]["application/json"]["example"] = metadata["requestBodyExample"]
            
            operation["requestBody"] = request_body
        
        # Add callbacks if available
        if "callbacks" in metadata:
            operation["callbacks"] = metadata["callbacks"]
        
        return operation
    
    def _get_summary(self, function_name: str, description: str) -> str:
        """
        Generate a summary for an operation.
        
        Args:
            function_name: The name of the function
            description: The description from the docstring
            
        Returns:
            A summary string
        """
        # If description is available, use the first line
        if description:
            first_line = description.split("\n")[0].strip()
            if first_line:
                return first_line
        
        # Otherwise, generate a summary from the function name
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', function_name)
        return " ".join(word.capitalize() for word in words)
    
    def _parse_docstring(self, docstring: str) -> tuple:
        """
        Parse a docstring to extract description and parameter/return descriptions.
        
        Args:
            docstring: The docstring to parse
            
        Returns:
            A tuple containing (description, parameter_docs, return_doc, metadata)
        """
        if not docstring:
            return "", {}, "", {}
        
        # Extract OpenAPI metadata from docstring
        metadata = {}
        docstring_lines = docstring.split("\n")
        cleaned_lines = []
        
        i = 0
        while i < len(docstring_lines):
            line = docstring_lines[i].strip()
            
            # Check for OpenAPI metadata
            if line.startswith("@openapi"):
                # Extract the metadata key and value
                metadata_match = re.match(r'@openapi\s+(\w+):\s*(.*)', line)
                if metadata_match:
                    key, value = metadata_match.groups()
                    
                    # Handle multi-line values
                    if value.endswith("\\"):
                        value = value[:-1]
                        j = i + 1
                        while j < len(docstring_lines) and (docstring_lines[j].strip().startswith("@") or not docstring_lines[j].strip()):
                            value += " " + docstring_lines[j].strip()
                            j += 1
                        i = j - 1
                    
                    # Try to parse as JSON if possible
                    try:
                        metadata[key] = json.loads(value)
                    except json.JSONDecodeError:
                        metadata[key] = value
            else:
                cleaned_lines.append(line)
            
            i += 1
        
        # Reconstruct docstring without metadata
        cleaned_docstring = "\n".join(cleaned_lines)
        
        # Split docstring into sections
        sections = re.split(r'\n\s*(?:Args|Returns):\s*\n', cleaned_docstring)
        
        # Extract description
        description = sections[0].strip()
        
        # Extract parameter descriptions
        param_docs = {}
        if len(sections) > 1 and "Args:" in cleaned_docstring:
            args_section = sections[1].strip()
            param_matches = re.findall(r'(\w+):\s*(.*?)(?=\n\s*\w+:|$)', args_section, re.DOTALL)
            for param_name, param_desc in param_matches:
                param_docs[param_name] = param_desc.strip()
        
        # Extract return description
        return_doc = ""
        if "Returns:" in cleaned_docstring:
            returns_section = cleaned_docstring.split("Returns:")[1].strip()
            return_doc = returns_section
        
        return description, param_docs, return_doc, metadata
    
    def _get_schema_for_type(self, type_hint: Type) -> Dict[str, Any]:
        """
        Generate a JSON Schema for a Python type.
        
        Args:
            type_hint: The Python type
            
        Returns:
            A JSON Schema as a dictionary
        """
        # Handle None/NoneType
        if type_hint is type(None):
            return {"type": "null"}
        
        # Handle Any
        if type_hint is Any:
            return {}
        
        # Handle Optional types
        if is_optional_type(type_hint):
            inner_type = extract_optional_type(type_hint)
            schema = self._get_schema_for_type(inner_type)
            schema["nullable"] = True
            return schema
        
        # Handle Union types
        if is_union_type(type_hint):
            union_types = get_union_types(type_hint)
            # If one of the union types is None, treat it as an optional type
            if type(None) in union_types:
                non_none_types = [t for t in union_types if t is not type(None)]
                if len(non_none_types) == 1:
                    schema = self._get_schema_for_type(non_none_types[0])
                    schema["nullable"] = True
                    return schema
            
            # Otherwise, use oneOf for the union
            return {
                "oneOf": [self._get_schema_for_type(t) for t in union_types if t is not type(None)]
            }
        
        # Handle List types
        if is_list_type(type_hint):
            item_type = get_args(type_hint)[0] if get_args(type_hint) else Any
            return {
                "type": "array",
                "items": self._get_schema_for_type(item_type)
            }
        
        # Handle Dict types
        if is_dict_type(type_hint):
            args = get_args(type_hint)
            if args:
                key_type, value_type = args
                # Only support string keys in JSON
                if key_type is not str:
                    key_type = str
                return {
                    "type": "object",
                    "additionalProperties": self._get_schema_for_type(value_type)
                }
            return {"type": "object"}
        
        # Handle primitive types
        if type_hint is str:
            return {"type": "string"}
        elif type_hint is int:
            return {"type": "integer"}
        elif type_hint is float:
            return {"type": "number"}
        elif type_hint is bool:
            return {"type": "boolean"}
        
        # Handle custom classes (as objects)
        if hasattr(type_hint, "__annotations__"):
            # Check if we have a registered schema for this type
            type_name = getattr(type_hint, "__name__", str(type_hint))
            if type_name in self.custom_schemas:
                return {"$ref": f"#/components/schemas/{type_name}"}
            
            properties = {}
            required = []
            
            for attr_name, attr_type in type_hint.__annotations__.items():
                properties[attr_name] = self._get_schema_for_type(attr_type)
                # Assume all attributes are required for now
                required.append(attr_name)
            
            # Register the schema for future reference
            self.custom_schemas[type_name] = {
                "type": "object",
                "properties": properties,
                "required": required
            }
            
            return {"$ref": f"#/components/schemas/{type_name}"}
        
        # Default to object for unknown types
        return {"type": "object"}
    
    def _generate_components(self) -> Dict[str, Any]:
        """
        Generate the components section of the OpenAPI documentation.
        
        Returns:
            The components section as a dictionary
        """
        components = {}
        
        # Add schemas
        if self.custom_schemas:
            components["schemas"] = self.custom_schemas
        
        # Add responses
        if self.custom_responses:
            components["responses"] = self.custom_responses
        
        # Add parameters
        if self.custom_parameters:
            components["parameters"] = self.custom_parameters
        
        # Add examples
        if self.custom_examples:
            components["examples"] = self.custom_examples
        
        # Add request bodies
        if self.custom_request_bodies:
            components["requestBodies"] = self.custom_request_bodies
        
        # Add headers
        if self.custom_headers:
            components["headers"] = self.custom_headers
        
        # Add security schemes
        security_schemes = self._generate_security_schemes()
        if security_schemes:
            components["securitySchemes"] = security_schemes
        
        # Add links
        if self.custom_links:
            components["links"] = self.custom_links
        
        # Add callbacks
        if self.custom_callbacks:
            components["callbacks"] = self.custom_callbacks
        
        # Merge with pre-defined components
        if self.config.components:
            for component_type, component_values in self.config.components.items():
                if component_type not in components:
                    components[component_type] = {}
                components[component_type].update(component_values)
        
        return components
    
    def _generate_security_schemes(self) -> Dict[str, Any]:
        """
        Generate the security schemes section of the OpenAPI documentation.
        
        Returns:
            The security schemes section as a dictionary
        """
        security_schemes = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            },
            "apiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            },
            "basicAuth": {
                "type": "http",
                "scheme": "basic"
            },
            "oauth2Auth": {
                "type": "oauth2",
                "flows": {
                    "implicit": {
                        "authorizationUrl": "https://example.com/oauth/authorize",
                        "scopes": {
                            "read": "Read access",
                            "write": "Write access"
                        }
                    }
                }
            }
        }
        
        # Merge with custom security schemes
        security_schemes.update(self.custom_security_schemes)
        
        return security_schemes
    
    def _get_security_requirements(self, handler) -> List[Dict[str, List[str]]]:
        """
        Get security requirements for a handler.
        
        Args:
            handler: The handler function
            
        Returns:
            A list of security requirement objects
        """
        # Check if handler has security decorators
        security_requirements = []
        
        # Unwrap the handler to get the original function
        original_handler = handler
        while hasattr(original_handler, "__wrapped__"):
            original_handler = original_handler.__wrapped__
            
            # Check for JWT authentication
            if hasattr(original_handler, "_jwt_required"):
                security_requirements.append({"bearerAuth": []})
            
            # Check for API key authentication
            if hasattr(original_handler, "_api_key_required"):
                scopes = getattr(original_handler, "_api_key_scopes", [])
                security_requirements.append({"apiKeyAuth": scopes})
            
            # Check for Basic authentication
            if hasattr(original_handler, "_basic_auth_required"):
                security_requirements.append({"basicAuth": []})
            
            # Check for OAuth2 authentication
            if hasattr(original_handler, "_oauth2_required"):
                scopes = getattr(original_handler, "_oauth2_scopes", [])
                security_requirements.append({"oauth2Auth": scopes})
        
        return security_requirements
    
    def register_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """
        Register a custom schema.
        
        Args:
            name: The name of the schema
            schema: The schema definition
        """
        self.custom_schemas[name] = schema
    
    def register_response(self, name: str, response: Dict[str, Any]) -> None:
        """
        Register a custom response.
        
        Args:
            name: The name of the response
            response: The response definition
        """
        self.custom_responses[name] = response
    
    def register_parameter(self, name: str, parameter: Dict[str, Any]) -> None:
        """
        Register a custom parameter.
        
        Args:
            name: The name of the parameter
            parameter: The parameter definition
        """
        self.custom_parameters[name] = parameter
    
    def register_example(self, name: str, example: Dict[str, Any]) -> None:
        """
        Register a custom example.
        
        Args:
            name: The name of the example
            example: The example definition
        """
        self.custom_examples[name] = example
    
    def register_request_body(self, name: str, request_body: Dict[str, Any]) -> None:
        """
        Register a custom request body.
        
        Args:
            name: The name of the request body
            request_body: The request body definition
        """
        self.custom_request_bodies[name] = request_body
    
    def register_header(self, name: str, header: Dict[str, Any]) -> None:
        """
        Register a custom header.
        
        Args:
            name: The name of the header
            header: The header definition
        """
        self.custom_headers[name] = header
    
    def register_security_scheme(self, name: str, security_scheme: Dict[str, Any]) -> None:
        """
        Register a custom security scheme.
        
        Args:
            name: The name of the security scheme
            security_scheme: The security scheme definition
        """
        self.custom_security_schemes[name] = security_scheme
    
    def register_link(self, name: str, link: Dict[str, Any]) -> None:
        """
        Register a custom link.
        
        Args:
            name: The name of the link
            link: The link definition
        """
        self.custom_links[name] = link
    
    def register_callback(self, name: str, callback: Dict[str, Any]) -> None:
        """
        Register a custom callback.
        
        Args:
            name: The name of the callback
            callback: The callback definition
        """
        self.custom_callbacks[name] = callback
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert the OpenAPI documentation to JSON.
        
        Args:
            indent: The indentation level for the JSON output
            
        Returns:
            The OpenAPI documentation as a JSON string
        """
        return json.dumps(self.generate(), indent=indent)
    
    def to_yaml(self) -> str:
        """
        Convert the OpenAPI documentation to YAML.
        
        Returns:
            The OpenAPI documentation as a YAML string
        """
        try:
            import yaml
            return yaml.dump(self.generate(), sort_keys=False)
        except ImportError:
            raise ImportError("PyYAML is required for YAML output. Install it with 'pip install pyyaml'.")


def openapi_metadata(
    summary: Optional[str] = None,
    description: Optional[str] = None,
    operation_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    deprecated: Optional[bool] = None,
    external_docs: Optional[Dict[str, str]] = None,
    responses: Optional[Dict[str, Dict[str, Any]]] = None,
    parameters: Optional[List[Dict[str, Any]]] = None,
    request_body: Optional[Dict[str, Any]] = None,
    callbacks: Optional[Dict[str, Dict[str, Any]]] = None,
    security: Optional[List[Dict[str, List[str]]]] = None,
) -> Callable:
    """
    Decorator to add OpenAPI metadata to a function.
    
    Args:
        summary: A short summary of what the operation does
        description: A verbose explanation of the operation behavior
        operation_id: Unique string used to identify the operation
        tags: A list of tags for API documentation control
        deprecated: Declares this operation to be deprecated
        external_docs: Additional external documentation
        responses: The responses the API will return
        parameters: Additional parameters that are not part of the function signature
        request_body: The request body information
        callbacks: The callbacks that can be expected from the operation
        security: The security requirements for the operation
        
    Returns:
        The decorated function
    """
    def decorator(func):
        # Store metadata in function attributes
        if summary:
            func._openapi_summary = summary
        if description:
            func._openapi_description = description
        if operation_id:
            func._openapi_operation_id = operation_id
        if tags:
            func._openapi_tags = tags
        if deprecated is not None:
            func._openapi_deprecated = deprecated
        if external_docs:
            func._openapi_external_docs = external_docs
        if responses:
            func._openapi_responses = responses
        if parameters:
            func._openapi_parameters = parameters
        if request_body:
            func._openapi_request_body = request_body
        if callbacks:
            func._openapi_callbacks = callbacks
        if security:
            func._openapi_security = security
        
        return func
    
    return decorator 