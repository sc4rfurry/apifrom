"""
Trusted Types implementation for APIFromAnything.

This module provides utilities for implementing Trusted Types, a web platform feature
that helps prevent DOM-based Cross-Site Scripting (XSS) attacks by restricting the
strings that can be passed to DOM injection sinks.
"""

from typing import Dict, List, Optional, Union, Callable, Any, Set
import re
import json
import uuid

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware.base import BaseMiddleware


class TrustedTypesPolicy:
    """
    Policy for configuring Trusted Types.
    
    This class represents a Trusted Types policy that can be used to create
    trusted values for various DOM sinks.
    """
    
    def __init__(self, name: str, enforce: bool = True):
        """
        Initialize the Trusted Types policy.
        
        Args:
            name: The name of the policy
            enforce: Whether to enforce the policy
        """
        self.name = name
        self.enforce = enforce
        self.script_handlers: List[Callable[[str], str]] = []
        self.html_handlers: List[Callable[[str], str]] = []
        self.script_url_handlers: List[Callable[[str], str]] = []
        self.url_handlers: List[Callable[[str], str]] = []
    
    def create_script(self, script: str) -> str:
        """
        Create a trusted script.
        
        Args:
            script: The script to create
            
        Returns:
            The trusted script
        """
        for handler in self.script_handlers:
            script = handler(script)
        return script
    
    def create_html(self, html: str) -> str:
        """
        Create trusted HTML.
        
        Args:
            html: The HTML to create
            
        Returns:
            The trusted HTML
        """
        for handler in self.html_handlers:
            html = handler(html)
        return html
    
    def create_script_url(self, url: str) -> str:
        """
        Create a trusted script URL.
        
        Args:
            url: The URL to create
            
        Returns:
            The trusted script URL
        """
        for handler in self.script_url_handlers:
            url = handler(url)
        return url
    
    def create_url(self, url: str) -> str:
        """
        Create a trusted URL.
        
        Args:
            url: The URL to create
            
        Returns:
            The trusted URL
        """
        for handler in self.url_handlers:
            url = handler(url)
        return url
    
    def add_script_handler(self, handler: Callable[[str], str]) -> "TrustedTypesPolicy":
        """
        Add a script handler.
        
        Args:
            handler: The handler function
            
        Returns:
            The policy instance for chaining
        """
        self.script_handlers.append(handler)
        return self
    
    def add_html_handler(self, handler: Callable[[str], str]) -> "TrustedTypesPolicy":
        """
        Add an HTML handler.
        
        Args:
            handler: The handler function
            
        Returns:
            The policy instance for chaining
        """
        self.html_handlers.append(handler)
        return self
    
    def add_script_url_handler(self, handler: Callable[[str], str]) -> "TrustedTypesPolicy":
        """
        Add a script URL handler.
        
        Args:
            handler: The handler function
            
        Returns:
            The policy instance for chaining
        """
        self.script_url_handlers.append(handler)
        return self
    
    def add_url_handler(self, handler: Callable[[str], str]) -> "TrustedTypesPolicy":
        """
        Add a URL handler.
        
        Args:
            handler: The handler function
            
        Returns:
            The policy instance for chaining
        """
        self.url_handlers.append(handler)
        return self
    
    def to_js(self) -> str:
        """
        Convert the policy to JavaScript code.
        
        Returns:
            JavaScript code for creating the policy
        """
        js_code = f"""
        if (window.trustedTypes && window.trustedTypes.createPolicy) {{
            window.trustedTypes.createPolicy('{self.name}', {{
                createHTML: function(s) {{ return s; }},
                createScript: function(s) {{ return s; }},
                createScriptURL: function(s) {{ return s; }},
            }});
        }}
        """
        return js_code


class TrustedTypesMiddleware(BaseMiddleware):
    """
    Middleware for adding Trusted Types headers and scripts to responses.
    
    This middleware adds the Content-Security-Policy header with the
    require-trusted-types-for directive to enforce Trusted Types for script
    execution, and injects a script to create Trusted Types policies.
    """
    
    def __init__(
        self,
        policies: Optional[List[TrustedTypesPolicy]] = None,
        require_for_script: bool = True,
        allow_duplicates: bool = False,
        report_only: bool = False,
        report_uri: Optional[str] = None,
        exempt_paths: Optional[List[str]] = None,
    ):
        """
        Initialize the Trusted Types middleware.
        
        Args:
            policies: List of Trusted Types policies to create
            require_for_script: Whether to require Trusted Types for script execution
            allow_duplicates: Whether to allow duplicate policy names
            report_only: Whether to use report-only mode
            report_uri: URI to report violations to
            exempt_paths: Paths exempt from Trusted Types
        """
        super().__init__()
        self.policies = policies or []
        self.require_for_script = require_for_script
        self.allow_duplicates = allow_duplicates
        self.report_only = report_only
        self.report_uri = report_uri
        self.exempt_paths = exempt_paths or []
    
    def _is_exempt(self, request: Request) -> bool:
        """
        Check if a request is exempt from Trusted Types.
        
        Args:
            request: The request to check
            
        Returns:
            True if the request is exempt, False otherwise
        """
        for path in self.exempt_paths:
            if request.path.startswith(path):
                return True
        
        return False
    
    def _get_csp_header_name(self) -> str:
        """
        Get the CSP header name based on the mode.
        
        Returns:
            The CSP header name
        """
        if self.report_only:
            return "Content-Security-Policy-Report-Only"
        return "Content-Security-Policy"
    
    def _get_csp_header_value(self) -> str:
        """
        Get the CSP header value for Trusted Types.
        
        Returns:
            The CSP header value
        """
        directives = []
        
        if self.require_for_script:
            directives.append("require-trusted-types-for 'script'")
        
        policy_names = [policy.name for policy in self.policies if policy.enforce]
        if policy_names:
            if self.allow_duplicates:
                directives.append(f"trusted-types {' '.join(policy_names)} 'allow-duplicates'")
            else:
                directives.append(f"trusted-types {' '.join(policy_names)}")
        
        if self.report_uri:
            directives.append(f"report-uri {self.report_uri}")
        
        return "; ".join(directives)
    
    def _generate_policy_script(self) -> str:
        """
        Generate a script to create Trusted Types policies.
        
        Returns:
            A script element with the policy creation code
        """
        policy_scripts = [policy.to_js() for policy in self.policies]
        script = f"""
        <script>
        // Trusted Types policies
        (function() {{
            {' '.join(policy_scripts)}
        }})();
        </script>
        """
        return script
    
    def _inject_policy_script(self, response: Union[str, Response]) -> Union[str, Response]:
        """
        Inject the policy script into HTML content.
        
        Args:
            response: The response or HTML content to modify
            
        Returns:
            The modified response or HTML content
        """
        # Handle string input (for tests)
        if isinstance(response, str):
            html_content = response
            script = self._generate_policy_script()
            insert_pos = html_content.find("</head>")
            if insert_pos != -1:
                html_content = html_content[:insert_pos] + script + html_content[insert_pos:]
            return html_content
        
        # Handle Response object
        if hasattr(response, "headers") and hasattr(response, "body"):
            # Check if the response is HTML
            content_type = response.headers.get("Content-Type", "")
            if "text/html" in content_type:
                # Get the HTML content
                html_content = response.body
                if isinstance(html_content, bytes):
                    html_content = html_content.decode("utf-8")
                
                # Inject the policy script
                script = self._generate_policy_script()
                insert_pos = html_content.find("</head>")
                if insert_pos != -1:
                    html_content = html_content[:insert_pos] + script + html_content[insert_pos:]
                
                # Update the response body
                if isinstance(response.body, bytes):
                    response.body = html_content.encode("utf-8")
                else:
                    response.body = html_content
        
        return response
    
    async def process_request(self, request: Request) -> Request:
        """
        Process a request through the Trusted Types middleware.
        
        Args:
            request: The request to process
            
        Returns:
            The processed request
        """
        # This middleware doesn't modify the request, just passes it through
        return request
    
    async def process_response(self, response: Response) -> Response:
        """
        Process a response through the Trusted Types middleware.
        
        Args:
            response: The response to process
            
        Returns:
            The processed response
        """
        # Check if the request is exempt
        if self._is_exempt(response.request):
            return response

        # Add the CSP header for Trusted Types
        header_name = self._get_csp_header_name()
        header_value = self._get_csp_header_value()
        response.headers[header_name] = header_value

        # Inject the policy script if the response is HTML
        response = self._inject_policy_script(response)
        
        return response


class TrustedTypesBuilder:
    """
    Helper class for building Trusted Types policies.
    """
    
    @staticmethod
    def create_default_policy() -> TrustedTypesPolicy:
        """
        Create a default Trusted Types policy.
        
        Returns:
            A default Trusted Types policy
        """
        policy = TrustedTypesPolicy(name="default")
        
        # Add a script handler that validates JavaScript syntax
        def validate_script(script: str) -> str:
            # This is a simple validation that checks for common XSS patterns
            # In a real application, you would use a more robust validation
            if "<script" in script.lower() or "javascript:" in script.lower():
                raise ValueError("Potential XSS attack detected in script")
            return script
        
        # Add an HTML handler that sanitizes HTML
        def sanitize_html(html: str) -> str:
            # This is a simple sanitization that removes script tags
            # In a real application, you would use a more robust sanitizer
            # Use a safer approach to remove script tags
            try:
                # Try to use a proper HTML parser if available
                from html.parser import HTMLParser
                from io import StringIO
                
                class ScriptFilter(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.result = StringIO()
                        self.skip_content = False
                        
                    def handle_starttag(self, tag, attrs):
                        if tag.lower() == 'script':
                            self.skip_content = True
                        else:
                            # Filter out javascript: attributes
                            filtered_attrs = []
                            for name, value in attrs:
                                if value and ('javascript:' not in value.lower()):
                                    filtered_attrs.append((name, value))
                            
                            if filtered_attrs:
                                attr_str = ' ' + ' '.join(f'{name}="{value}"' for name, value in filtered_attrs)
                            else:
                                attr_str = ''
                            
                            self.result.write(f"<{tag}{attr_str}>")
                    
                    def handle_endtag(self, tag):
                        if tag.lower() == 'script':
                            self.skip_content = False
                        else:
                            self.result.write(f"</{tag}>")
                    
                    def handle_data(self, data):
                        if not self.skip_content:
                            self.result.write(data)
                
                parser = ScriptFilter()
                parser.feed(html)
                return parser.result.getvalue()
                
            except (ImportError, Exception):
                # Fallback to regex if HTML parser is not available or fails
                # This is still not perfect but better than the previous regex
                # First remove script tags and their content
                html = re.sub(r'<\s*script\b[^>]*>.*?<\s*/\s*script\s*>', '', html, flags=re.IGNORECASE | re.DOTALL)
                # Then remove any remaining javascript: protocol handlers
                html = re.sub(r'(javascript|vbscript|data):', 'blocked:', html, flags=re.IGNORECASE)
                # Remove event handlers
                html = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
                return html
        
        # Add a URL handler that validates URLs
        def validate_url(url: str) -> str:
            # This is a simple validation that checks for common XSS patterns
            # In a real application, you would use a more robust validation
            if "javascript:" in url.lower():
                raise ValueError("Potential XSS attack detected in URL")
            return url
        
        policy.add_script_handler(validate_script)
        policy.add_html_handler(sanitize_html)
        policy.add_url_handler(validate_url)
        policy.add_script_url_handler(validate_url)
        
        return policy
    
    @staticmethod
    def create_escape_policy() -> TrustedTypesPolicy:
        """
        Create a Trusted Types policy that escapes HTML.
        
        Returns:
            A Trusted Types policy that escapes HTML
        """
        policy = TrustedTypesPolicy(name="escape")
        
        # Add an HTML handler that escapes HTML
        def escape_html(html: str) -> str:
            return html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")
        
        policy.add_html_handler(escape_html)
        
        return policy
    
    @staticmethod
    def create_sanitize_policy() -> TrustedTypesPolicy:
        """
        Create a Trusted Types policy that sanitizes HTML.
        
        Returns:
            A Trusted Types policy that sanitizes HTML
        """
        policy = TrustedTypesPolicy(name="sanitize")
        
        # Add an HTML handler that sanitizes HTML
        def sanitize_html(html: str) -> str:
            # This is a simple sanitization that removes script tags
            # In a real application, you would use a more robust sanitizer
            # Use a safer approach to remove script tags
            try:
                # Try to use a proper HTML parser if available
                from html.parser import HTMLParser
                from io import StringIO
                
                class ScriptFilter(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.result = StringIO()
                        self.skip_content = False
                        
                    def handle_starttag(self, tag, attrs):
                        if tag.lower() == 'script':
                            self.skip_content = True
                        else:
                            # Filter out javascript: attributes
                            filtered_attrs = []
                            for name, value in attrs:
                                if value and ('javascript:' not in value.lower()):
                                    filtered_attrs.append((name, value))
                            
                            if filtered_attrs:
                                attr_str = ' ' + ' '.join(f'{name}="{value}"' for name, value in filtered_attrs)
                            else:
                                attr_str = ''
                            
                            self.result.write(f"<{tag}{attr_str}>")
                    
                    def handle_endtag(self, tag):
                        if tag.lower() == 'script':
                            self.skip_content = False
                        else:
                            self.result.write(f"</{tag}>")
                    
                    def handle_data(self, data):
                        if not self.skip_content:
                            self.result.write(data)
                
                parser = ScriptFilter()
                parser.feed(html)
                return parser.result.getvalue()
                
            except (ImportError, Exception):
                # Fallback to regex if HTML parser is not available or fails
                # This is still not perfect but better than the previous regex
                # First remove script tags and their content
                html = re.sub(r'<\s*script\b[^>]*>.*?<\s*/\s*script\s*>', '', html, flags=re.IGNORECASE | re.DOTALL)
                # Then remove any remaining javascript: protocol handlers
                html = re.sub(r'(javascript|vbscript|data):', 'blocked:', html, flags=re.IGNORECASE)
                # Remove event handlers
                html = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
                return html
        
        policy.add_html_handler(sanitize_html)
        
        return policy
    
    @staticmethod
    def create_url_policy() -> TrustedTypesPolicy:
        """
        Create a Trusted Types policy for URLs.
        
        Returns:
            A Trusted Types policy for URLs
        """
        policy = TrustedTypesPolicy(name="url")
        
        # Add a URL handler that validates URLs
        def validate_url(url: str) -> str:
            # This is a simple validation that checks for common XSS patterns
            # In a real application, you would use a more robust validation
            if "javascript:" in url.lower():
                raise ValueError("Potential XSS attack detected in URL")
            return url
        
        policy.add_url_handler(validate_url)
        policy.add_script_url_handler(validate_url)
        
        return policy


class TrustedTypesViolationReporter:
    """
    Reporter for Trusted Types violations.
    
    This class provides utilities for handling Trusted Types violation reports.
    """
    
    def __init__(self, report_uri: str, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Initialize the Trusted Types violation reporter.
        
        Args:
            report_uri: The URI to send violation reports to
            callback: A callback function to handle violation reports
        """
        self.report_uri = report_uri
        self.callback = callback
    
    async def handle_report(self, report: Dict[str, Any]) -> None:
        """
        Handle a Trusted Types violation report.
        
        Args:
            report: The violation report
        """
        if self.callback:
            await self.callback(report)
    
    def get_report_uri(self) -> str:
        """
        Get the report URI.
        
        Returns:
            The report URI
        """
        return self.report_uri 