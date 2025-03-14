"""
Web decorator for the APIFromAnything library.

This module provides the Web decorator, which enhances API endpoints with
automatic HTML rendering capabilities, making them more user-friendly
when accessed directly from a web browser.
"""
import json
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Union

from apifrom.core.response import Response
from apifrom.core.app import API


class Web:
    """
    Decorator that enhances API endpoints with HTML rendering capabilities.
    
    When an endpoint decorated with @Web is accessed with an Accept header
    that includes 'text/html' (e.g., from a web browser), the response
    will be rendered as HTML. Otherwise, the response will be returned
    as JSON (the default API behavior).
    
    This makes API endpoints more user-friendly when accessed directly
    from a web browser, while maintaining their programmatic API functionality.
    
    Attributes:
        title (str): The title to display in the HTML page
        description (str): A description of the endpoint to display in the HTML
        theme (str): The theme to use for styling ('default', 'dark', 'light')
        template (str): Optional path to a custom HTML template
    
    Example:
        ```python
        from apifrom.core.app import API
        from apifrom.decorators.web import Web
        
        app = API()
        
        @app.api('/users')
        @Web(title="Users API", description="Get a list of users")
        def get_users(request):
            return [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Charlie"}
            ]
        ```
    """
    
    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        theme: str = "default",
        template: Optional[str] = None
    ):
        """
        Initialize the Web decorator.
        
        Args:
            title: The title to display in the HTML page
            description: A description of the endpoint to display in the HTML
            theme: The theme to use for styling ('default', 'dark', 'light')
            template: Optional path to a custom HTML template
        """
        self.title = title or "API Endpoint"
        self.description = description or ""
        self.theme = theme
        self.template = template
    
    def __call__(self, func: Callable) -> Callable:
        """
        Apply the decorator to the function.
        
        Args:
            func: The function to decorate
            
        Returns:
            The decorated function
        """
        is_coroutine = inspect.iscoroutinefunction(func)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Call the original function
            result = await func(*args, **kwargs)
            
            # If the result is already a Response, return it
            if isinstance(result, Response):
                return result
            
            # Check if the first argument is a request
            request = args[0] if args else None
            
            # If the request has an Accept header that includes text/html,
            # render the result as HTML
            if request and hasattr(request, 'headers') and 'accept' in request.headers:
                accept = request.headers['accept'].lower()
                if 'text/html' in accept:
                    html = self._render_html(result)
                    return Response(
                        content=html,
                        content_type="text/html",
                        status_code=200
                    )
            
            # Otherwise, return the result as is
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Call the original function
            result = func(*args, **kwargs)
            
            # If the result is already a Response, return it
            if isinstance(result, Response):
                return result
            
            # Check if the first argument is a request
            request = args[0] if args else None
            
            # If the request has an Accept header that includes text/html,
            # render the result as HTML
            if request and hasattr(request, 'headers') and 'accept' in request.headers:
                accept = request.headers['accept'].lower()
                if 'text/html' in accept:
                    html = self._render_html(result)
                    return Response(
                        content=html,
                        content_type="text/html",
                        status_code=200
                    )
            
            # Otherwise, return the result as is
            return result
        
        return async_wrapper if is_coroutine else sync_wrapper
    
    def _render_html(self, data: Any) -> str:
        """
        Render the data as HTML.
        
        Args:
            data: The data to render
            
        Returns:
            The HTML representation of the data
        """
        if self.template:
            return self._render_with_template(data)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.title}</title>
            <style>
                {self._get_theme_styles()}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{self.title}</h1>
                <p>{self.description}</p>
                <div class="content">
        """
        
        if isinstance(data, dict):
            html += self._render_dict(data)
        elif isinstance(data, list):
            html += self._render_list(data)
        else:
            html += f"<pre>{self._format_value(data)}</pre>"
        
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _render_dict(self, data: Dict) -> str:
        """
        Render a dictionary as HTML.
        
        Args:
            data: The dictionary to render
            
        Returns:
            The HTML representation of the dictionary
        """
        html = "<table class='data-table'>"
        html += "<tr><th>Key</th><th>Value</th></tr>"
        
        for key, value in data.items():
            html += f"<tr><td>{key}</td><td>{self._format_value(value)}</td></tr>"
        
        html += "</table>"
        return html
    
    def _render_list(self, data: List) -> str:
        """
        Render a list as HTML.
        
        Args:
            data: The list to render
            
        Returns:
            The HTML representation of the list
        """
        # If the list is empty, render an empty list
        if not data:
            return "<p>Empty list</p>"
        
        # If the list contains dictionaries, render a table
        if all(isinstance(item, dict) for item in data):
            # Get all unique keys from all dictionaries
            keys = set()
            for item in data:
                keys.update(item.keys())
            keys = sorted(keys)
            
            html = "<table class='data-table'>"
            html += "<tr>"
            for key in keys:
                html += f"<th>{key}</th>"
            html += "</tr>"
            
            for item in data:
                html += "<tr>"
                for key in keys:
                    value = item.get(key, "")
                    html += f"<td>{self._format_value(value)}</td>"
                html += "</tr>"
            
            html += "</table>"
            return html
        
        # Otherwise, render a simple list
        html = "<ul>"
        for item in data:
            html += f"<li>{self._format_value(item)}</li>"
        html += "</ul>"
        return html
    
    def _format_value(self, value: Any) -> str:
        """
        Format a value for HTML display.
        
        Args:
            value: The value to format
            
        Returns:
            The formatted value
        """
        if isinstance(value, dict):
            return self._render_dict(value)
        elif isinstance(value, list):
            return self._render_list(value)
        elif value is None:
            return "<em>null</em>"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return str(value)
    
    def _render_with_template(self, data: Any) -> str:
        """
        Render the data using a custom template.
        
        Args:
            data: The data to render
            
        Returns:
            The HTML representation of the data using the template
        """
        try:
            import jinja2
            
            # Load the template
            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader("./"),
                autoescape=jinja2.select_autoescape(['html', 'xml'])
            )
            template = env.get_template(self.template)
            
            # Render the template with the data
            return template.render(
                title=self.title,
                description=self.description,
                data=data
            )
        except ImportError:
            # If jinja2 is not installed, fall back to the default rendering
            return self._render_html(data)
        except jinja2.exceptions.TemplateNotFound:
            # If the template is not found, fall back to the default rendering
            return self._render_html(data)
    
    def _get_theme_styles(self) -> str:
        """
        Get the CSS styles for the current theme.
        
        Returns:
            The CSS styles for the theme
        """
        # Base styles for all themes
        base_styles = """
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                margin-top: 0;
            }
            .content {
                margin-top: 20px;
            }
            .data-table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            .data-table th, .data-table td {
                padding: 8px 12px;
                text-align: left;
                border: 1px solid;
            }
            .data-table th {
                font-weight: bold;
            }
            ul {
                margin: 0;
                padding-left: 20px;
            }
        """
        
        # Theme-specific styles
        if self.theme == "dark":
            theme_styles = """
                body {
                    background-color: #1e1e1e;
                    color: #f0f0f0;
                }
                .data-table th, .data-table td {
                    border-color: #444;
                }
                .data-table th {
                    background-color: #333;
                }
                .data-table tr:nth-child(even) {
                    background-color: #2a2a2a;
                }
                a {
                    color: #4da6ff;
                }
            """
        elif self.theme == "light":
            theme_styles = """
                body {
                    background-color: #ffffff;
                    color: #333333;
                }
                .data-table th, .data-table td {
                    border-color: #ddd;
                }
                .data-table th {
                    background-color: #f5f5f5;
                }
                .data-table tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                a {
                    color: #0066cc;
                }
            """
        else:  # default theme
            theme_styles = """
                body {
                    background-color: #f8f9fa;
                    color: #212529;
                }
                .data-table th, .data-table td {
                    border-color: #dee2e6;
                }
                .data-table th {
                    background-color: #e9ecef;
                }
                .data-table tr:nth-child(even) {
                    background-color: #f2f2f2;
                }
                a {
                    color: #007bff;
                }
            """
        
        return base_styles + theme_styles 

app = API() 