"""
Response module for APIFromAnything.

This module defines the Response class and related utilities for handling
HTTP responses.
"""

import json
import logging
import typing as t
from http import HTTPStatus

from starlette.responses import Response as StarletteResponse
from starlette.responses import JSONResponse as StarletteJSONResponse

logger = logging.getLogger(__name__)


class Response:
    """
    Response class for APIFromAnything.
    
    This class represents an HTTP response and provides methods for setting
    response data, status code, and headers.
    
    Attributes:
        content: The response content.
        status_code: The HTTP status code.
        headers: HTTP headers.
        content_type: The content type of the response.
    """
    
    def __init__(
        self,
        content: t.Any = None,
        status_code: int = 200,
        headers: t.Optional[t.Dict[str, str]] = None,
        content_type: str = "application/json"
    ):
        """
        Initialize a new Response instance.
        
        Args:
            content: The response content.
            status_code: The HTTP status code.
            headers: HTTP headers.
            content_type: The content type of the response.
        """
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}
        self.content_type = content_type
    
    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> 'Response':
        """
        Create a Response instance from a dictionary.
        
        Args:
            data: The dictionary containing response data.
            
        Returns:
            A new Response instance.
        """
        content = data.get('content')
        status_code = data.get('status_code', 200)
        headers = data.get('headers', {})
        content_type = data.get('content_type', 'application/json')
        
        if content_type == 'application/json':
            return JSONResponse(content=content, status_code=status_code, headers=headers)
        elif content_type == 'text/html':
            return HTMLResponse(content=content, status_code=status_code, headers=headers)
        elif content_type == 'text/plain':
            return TextResponse(content=content, status_code=status_code, headers=headers)
        else:
            return cls(content=content, status_code=status_code, headers=headers, content_type=content_type)
    
    def to_dict(self) -> t.Dict[str, t.Any]:
        """
        Convert the response to a dictionary.
        
        Returns:
            A dictionary representation of the response.
        """
        return {
            'content': self.content,
            'status_code': self.status_code,
            'headers': self.headers,
            'content_type': self.content_type
        }
    
    def set_cookie(
        self,
        key: str,
        value: str = "",
        max_age: t.Optional[int] = None,
        expires: t.Optional[int] = None,
        path: str = "/",
        domain: t.Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: str = "lax"
    ) -> None:
        """
        Set a cookie in the response.
        
        Args:
            key: The cookie name.
            value: The cookie value.
            max_age: The maximum age of the cookie in seconds.
            expires: The expiration time of the cookie as a UNIX timestamp.
            path: The path for which the cookie is valid.
            domain: The domain for which the cookie is valid.
            secure: Whether the cookie should only be sent over HTTPS.
            httponly: Whether the cookie should be accessible only via HTTP.
            samesite: The SameSite attribute of the cookie.
        """
        self.headers.setdefault("set-cookie", [])
        cookie = f"{key}={value}"
        
        if max_age is not None:
            cookie += f"; Max-Age={max_age}"
        if expires is not None:
            cookie += f"; Expires={expires}"
        if path:
            cookie += f"; Path={path}"
        if domain:
            cookie += f"; Domain={domain}"
        if secure:
            cookie += "; Secure"
        if httponly:
            cookie += "; HttpOnly"
        if samesite:
            cookie += f"; SameSite={samesite}"
        
        self.headers["set-cookie"].append(cookie)
    
    def to_starlette_response(self) -> StarletteResponse:
        """
        Convert to a Starlette response.
        
        Returns:
            A Starlette response.
        """
        if self.content_type == "application/json":
            return StarletteJSONResponse(
                content=self.content,
                status_code=self.status_code,
                headers=self.headers
            )
        else:
            return StarletteResponse(
                content=self.content,
                status_code=self.status_code,
                headers=self.headers,
                media_type=self.content_type
            )


class JSONResponse(Response):
    """
    JSON response for APIFromAnything.
    
    This class represents an HTTP response with JSON content.
    """
    
    def __init__(
        self,
        content: t.Any = None,
        status_code: int = 200,
        headers: t.Optional[t.Dict[str, str]] = None
    ):
        """
        Initialize a new JSONResponse instance.
        
        Args:
            content: The response content.
            status_code: The HTTP status code.
            headers: HTTP headers.
        """
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            content_type="application/json"
        )
    
    @property
    def body(self) -> bytes:
        """
        Get the response body as bytes.
        
        Returns:
            The response body as bytes.
        """
        return json.dumps(self.content).encode("utf-8") if self.content is not None else b""


class HTMLResponse(Response):
    """
    HTML response for APIFromAnything.
    
    This class represents an HTTP response with HTML content.
    """
    
    def __init__(
        self,
        content: str = "",
        status_code: int = 200,
        headers: t.Optional[t.Dict[str, str]] = None
    ):
        """
        Initialize a new HTMLResponse instance.
        
        Args:
            content: The HTML content.
            status_code: The HTTP status code.
            headers: HTTP headers.
        """
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            content_type="text/html"
        )


class TextResponse(Response):
    """
    Text response for APIFromAnything.
    
    This class represents an HTTP response with plain text content.
    """
    
    def __init__(
        self,
        content: str = "",
        status_code: int = 200,
        headers: t.Optional[t.Dict[str, str]] = None
    ):
        """
        Initialize a new TextResponse instance.
        
        Args:
            content: The text content.
            status_code: The HTTP status code.
            headers: HTTP headers.
        """
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            content_type="text/plain"
        )


class RedirectResponse(Response):
    """
    Redirect response for APIFromAnything.
    
    This class represents an HTTP redirect response.
    """
    
    def __init__(
        self,
        url: str,
        status_code: int = 302,
        headers: t.Optional[t.Dict[str, str]] = None
    ):
        """
        Initialize a new RedirectResponse instance.
        
        Args:
            url: The URL to redirect to.
            status_code: The HTTP status code.
            headers: HTTP headers.
        """
        headers = headers or {}
        headers["location"] = url
        
        super().__init__(
            content="",
            status_code=status_code,
            headers=headers,
            content_type="text/plain"
        )


class ErrorResponse(JSONResponse):
    """
    Error response for APIFromAnything.
    
    This class represents an HTTP error response with JSON content.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: t.Optional[str] = None,
        details: t.Optional[t.Dict] = None,
        headers: t.Optional[t.Dict[str, str]] = None
    ):
        """
        Initialize a new ErrorResponse instance.
        
        Args:
            message: The error message.
            status_code: The HTTP status code.
            error_code: An optional error code.
            details: Additional error details.
            headers: HTTP headers.
        """
        content = {
            "error": {
                "message": message,
                "status_code": status_code
            }
        }
        
        if error_code:
            content["error"]["code"] = error_code
        
        if details:
            content["error"]["details"] = details
        
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers
        ) 