"""
Security headers for APIFromAnything.

This module provides middleware and utilities for adding security headers to API responses,
including Content Security Policy (CSP), X-XSS-Protection, and other security headers
to protect against various web vulnerabilities.
"""

import re
import uuid
from typing import Callable, Dict, List, Optional, Set, Union, Any

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware.base import BaseMiddleware


class CSPDirective:
    """
    Content Security Policy directive builder.
    
    This class provides a fluent interface for building CSP directives.
    """
    
    def __init__(self, name: str):
        """
        Initialize the CSP directive.
        
        Args:
            name: The name of the directive (e.g., 'default-src', 'script-src')
        """
        self.name = name
        self.values: Set[str] = set()
        self._nonce: Optional[str] = None
    
    def allow_self(self) -> 'CSPDirective':
        """
        Allow content from the same origin.
        
        Returns:
            The CSP directive instance for method chaining
        """
        self.values.add("'self'")
        return self
    
    def allow_none(self) -> 'CSPDirective':
        """
        Disallow content from any source.
        
        Returns:
            The CSP directive instance for method chaining
        """
        self.values.add("'none'")
        return self
    
    def allow_unsafe_inline(self) -> 'CSPDirective':
        """
        Allow inline content (not recommended for production).
        
        Returns:
            The CSP directive instance for method chaining
        """
        self.values.add("'unsafe-inline'")
        return self
    
    def allow_unsafe_eval(self) -> 'CSPDirective':
        """
        Allow eval() and similar functions (not recommended for production).
        
        Returns:
            The CSP directive instance for method chaining
        """
        self.values.add("'unsafe-eval'")
        return self
    
    def allow_strict_dynamic(self) -> 'CSPDirective':
        """
        Allow scripts with the correct nonce to load additional scripts.
        
        Returns:
            The CSP directive instance for method chaining
        """
        self.values.add("'strict-dynamic'")
        return self
    
    def allow_sources(self, *sources: str) -> 'CSPDirective':
        """
        Allow content from specific sources.
        
        Args:
            *sources: The sources to allow (e.g., 'https://example.com', '*.example.com')
            
        Returns:
            The CSP directive instance for method chaining
        """
        for source in sources:
            self.values.add(source)
        return self
    
    def allow_nonce(self, nonce: Optional[str] = None) -> 'CSPDirective':
        """
        Allow content with a specific nonce.
        
        Args:
            nonce: The nonce to allow (if None, a random nonce will be generated)
            
        Returns:
            The CSP directive instance for method chaining
        """
        if nonce is None:
            nonce = self._generate_nonce()
        
        self._nonce = nonce
        self.values.add(f"'nonce-{nonce}'")
        return self
    
    def _generate_nonce(self) -> str:
        """
        Generate a random nonce.
        
        Returns:
            A random nonce
        """
        return uuid.uuid4().hex
    
    def get_nonce(self) -> Optional[str]:
        """
        Get the nonce for this directive.
        
        Returns:
            The nonce, or None if no nonce has been set
        """
        return self._nonce
    
    def to_string(self) -> str:
        """
        Convert the directive to a string.
        
        Returns:
            The directive as a string
        """
        if not self.values:
            return ""
        
        return f"{self.name} {' '.join(sorted(self.values))}"


class ContentSecurityPolicy:
    """
    Content Security Policy builder.
    
    This class provides a fluent interface for building Content Security Policies.
    """
    
    def __init__(self):
        """
        Initialize the Content Security Policy.
        """
        self.directives: Dict[str, CSPDirective] = {}
        self.report_only = False
        self.report_uri = None
    
    def add_directive(self, directive: CSPDirective) -> 'ContentSecurityPolicy':
        """
        Add a directive to the policy.
        
        Args:
            directive: The directive to add
            
        Returns:
            The Content Security Policy instance for method chaining
        """
        self.directives[directive.name] = directive
        return self
    
    def default_src(self) -> CSPDirective:
        """
        Get or create the default-src directive.
        
        Returns:
            The default-src directive
        """
        if "default-src" not in self.directives:
            self.directives["default-src"] = CSPDirective("default-src")
        
        return self.directives["default-src"]
    
    def script_src(self) -> CSPDirective:
        """
        Get or create the script-src directive.
        
        Returns:
            The script-src directive
        """
        if "script-src" not in self.directives:
            self.directives["script-src"] = CSPDirective("script-src")
        
        return self.directives["script-src"]
    
    def style_src(self) -> CSPDirective:
        """
        Get or create the style-src directive.
        
        Returns:
            The style-src directive
        """
        if "style-src" not in self.directives:
            self.directives["style-src"] = CSPDirective("style-src")
        
        return self.directives["style-src"]
    
    def img_src(self) -> CSPDirective:
        """
        Get or create the img-src directive.
        
        Returns:
            The img-src directive
        """
        if "img-src" not in self.directives:
            self.directives["img-src"] = CSPDirective("img-src")
        
        return self.directives["img-src"]
    
    def connect_src(self) -> CSPDirective:
        """
        Get or create the connect-src directive.
        
        Returns:
            The connect-src directive
        """
        if "connect-src" not in self.directives:
            self.directives["connect-src"] = CSPDirective("connect-src")
        
        return self.directives["connect-src"]
    
    def font_src(self) -> CSPDirective:
        """
        Get or create the font-src directive.
        
        Returns:
            The font-src directive
        """
        if "font-src" not in self.directives:
            self.directives["font-src"] = CSPDirective("font-src")
        
        return self.directives["font-src"]
    
    def object_src(self) -> CSPDirective:
        """
        Get or create the object-src directive.
        
        Returns:
            The object-src directive
        """
        if "object-src" not in self.directives:
            self.directives["object-src"] = CSPDirective("object-src")
        
        return self.directives["object-src"]
    
    def media_src(self) -> CSPDirective:
        """
        Get or create the media-src directive.
        
        Returns:
            The media-src directive
        """
        if "media-src" not in self.directives:
            self.directives["media-src"] = CSPDirective("media-src")
        
        return self.directives["media-src"]
    
    def frame_src(self) -> CSPDirective:
        """
        Get or create the frame-src directive.
        
        Returns:
            The frame-src directive
        """
        if "frame-src" not in self.directives:
            self.directives["frame-src"] = CSPDirective("frame-src")
        
        return self.directives["frame-src"]
    
    def worker_src(self) -> CSPDirective:
        """
        Get or create the worker-src directive.
        
        Returns:
            The worker-src directive
        """
        if "worker-src" not in self.directives:
            self.directives["worker-src"] = CSPDirective("worker-src")
        
        return self.directives["worker-src"]
    
    def manifest_src(self) -> CSPDirective:
        """
        Get or create the manifest-src directive.
        
        Returns:
            The manifest-src directive
        """
        if "manifest-src" not in self.directives:
            self.directives["manifest-src"] = CSPDirective("manifest-src")
        
        return self.directives["manifest-src"]
    
    def frame_ancestors(self) -> CSPDirective:
        """
        Get or create the frame-ancestors directive.
        
        Returns:
            The frame-ancestors directive
        """
        if "frame-ancestors" not in self.directives:
            self.directives["frame-ancestors"] = CSPDirective("frame-ancestors")
        
        return self.directives["frame-ancestors"]
    
    def form_action(self) -> CSPDirective:
        """
        Get or create the form-action directive.
        
        Returns:
            The form-action directive
        """
        if "form-action" not in self.directives:
            self.directives["form-action"] = CSPDirective("form-action")
        
        return self.directives["form-action"]
    
    def base_uri(self) -> CSPDirective:
        """
        Get or create the base-uri directive.
        
        Returns:
            The base-uri directive
        """
        if "base-uri" not in self.directives:
            self.directives["base-uri"] = CSPDirective("base-uri")
        
        return self.directives["base-uri"]
    
    def set_report_only(self, report_only: bool = True) -> 'ContentSecurityPolicy':
        """
        Set whether the policy is report-only.
        
        Args:
            report_only: Whether the policy is report-only
            
        Returns:
            The Content Security Policy instance for method chaining
        """
        self.report_only = report_only
        return self
    
    def set_report_uri(self, uri: str) -> 'ContentSecurityPolicy':
        """
        Set the report URI.
        
        Args:
            uri: The report URI
            
        Returns:
            The Content Security Policy instance for method chaining
        """
        self.report_uri = uri
        return self
    
    def to_string(self) -> str:
        """
        Convert the policy to a string.
        
        Returns:
            The policy as a string
        """
        directives = []
        
        for directive in self.directives.values():
            directive_str = directive.to_string()
            if directive_str:
                directives.append(directive_str)
        
        if self.report_uri:
            directives.append(f"report-uri {self.report_uri}")
        
        return "; ".join(directives)
    
    def get_header_name(self) -> str:
        """
        Get the header name for the policy.
        
        Returns:
            The header name
        """
        if self.report_only:
            return "Content-Security-Policy-Report-Only"
        else:
            return "Content-Security-Policy"
    
    @classmethod
    def create_strict_policy(cls) -> 'ContentSecurityPolicy':
        """
        Create a strict Content Security Policy.
        
        Returns:
            A strict Content Security Policy
        """
        policy = cls()
        
        # Set default-src to 'self'
        policy.default_src().allow_self()
        
        # Disallow object-src to prevent plugin execution
        policy.object_src().allow_none()
        
        # Restrict base-uri to 'self'
        policy.base_uri().allow_self()
        
        # Prevent framing from other sites
        policy.frame_ancestors().allow_self()
        
        # Restrict form submissions to 'self'
        policy.form_action().allow_self()
        
        return policy
    
    @classmethod
    def create_api_policy(cls) -> 'ContentSecurityPolicy':
        """
        Create a Content Security Policy suitable for APIs.
        
        Returns:
            A Content Security Policy suitable for APIs
        """
        policy = cls()
        
        # APIs typically don't need CSP, but we can set a minimal policy
        policy.default_src().allow_none()
        
        return policy


class ReferrerPolicy:
    """
    Referrer Policy values.
    """
    NO_REFERRER = "no-referrer"
    NO_REFERRER_WHEN_DOWNGRADE = "no-referrer-when-downgrade"
    ORIGIN = "origin"
    ORIGIN_WHEN_CROSS_ORIGIN = "origin-when-cross-origin"
    SAME_ORIGIN = "same-origin"
    STRICT_ORIGIN = "strict-origin"
    STRICT_ORIGIN_WHEN_CROSS_ORIGIN = "strict-origin-when-cross-origin"
    UNSAFE_URL = "unsafe-url"


class XSSProtection:
    """
    X-XSS-Protection values.
    """
    DISABLED = "0"
    ENABLED = "1"
    ENABLED_BLOCK = "1; mode=block"
    ENABLED_REPORT = "1; report="


class SecurityHeadersMiddleware(BaseMiddleware):
    """
    Middleware for adding security headers to responses.
    """
    
    def __init__(
        self,
        content_security_policy: Optional[ContentSecurityPolicy] = None,
        x_frame_options: str = "DENY",
        x_content_type_options: str = "nosniff",
        referrer_policy: str = ReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN,
        x_xss_protection: str = XSSProtection.ENABLED_BLOCK,
        strict_transport_security: str = "max-age=31536000; includeSubDomains",
        permissions_policy: Optional[Dict[str, List[str]]] = None,
        cache_control: Optional[str] = None,
        exempt_paths: Optional[List[str]] = None,
        exempt_content_types: Optional[List[str]] = None,
    ):
        """
        Initialize the security headers middleware.
        
        Args:
            content_security_policy: The Content Security Policy to use
            x_frame_options: The X-Frame-Options header value
            x_content_type_options: The X-Content-Type-Options header value
            referrer_policy: The Referrer-Policy header value
            x_xss_protection: The X-XSS-Protection header value
            strict_transport_security: The Strict-Transport-Security header value
            permissions_policy: The Permissions-Policy header value
            cache_control: The Cache-Control header value
            exempt_paths: Paths exempt from security headers
            exempt_content_types: Content types exempt from security headers
        """
        super().__init__()
        self.content_security_policy = content_security_policy
        self.x_frame_options = x_frame_options
        self.x_content_type_options = x_content_type_options
        self.referrer_policy = referrer_policy
        self.x_xss_protection = x_xss_protection
        self.strict_transport_security = strict_transport_security
        self.permissions_policy = permissions_policy or {}
        self.cache_control = cache_control
        self.exempt_paths = exempt_paths or []
        self.exempt_content_types = exempt_content_types or []
    
    def _is_exempt(self, request: Request, response: Response) -> bool:
        """
        Check if a request/response is exempt from security headers.
        
        Args:
            request: The request
            response: The response
            
        Returns:
            True if the request/response is exempt, False otherwise
        """
        # Check if the path is exempt
        for path in self.exempt_paths:
            if re.match(path, request.path):
                return True
        
        # Check if the content type is exempt
        content_type = response.headers.get("Content-Type", "")
        for exempt_type in self.exempt_content_types:
            if exempt_type in content_type:
                return True
        
        return False
    
    def _build_permissions_policy(self) -> str:
        """
        Build the Permissions-Policy header value.
        
        Returns:
            The Permissions-Policy header value
        """
        directives = []
        
        for feature, origins in self.permissions_policy.items():
            if not origins:
                directives.append(f"{feature}=()")
            else:
                origins_str = " ".join(f'"{origin}"' for origin in origins)
                directives.append(f"{feature}=({origins_str})")
        
        return ", ".join(directives)
    
    def _add_security_headers(self, response: Response) -> None:
        """
        Add security headers to a response.
        
        Args:
            response: The response to add headers to
        """
        # Add Content Security Policy
        if self.content_security_policy:
            header_name = self.content_security_policy.get_header_name()
            response.headers[header_name] = self.content_security_policy.to_string()
        
        # Add X-Frame-Options
        if self.x_frame_options:
            response.headers["X-Frame-Options"] = self.x_frame_options
        
        # Add X-Content-Type-Options
        if self.x_content_type_options:
            response.headers["X-Content-Type-Options"] = self.x_content_type_options
        
        # Add Referrer-Policy
        if self.referrer_policy:
            response.headers["Referrer-Policy"] = self.referrer_policy
        
        # Add X-XSS-Protection
        if self.x_xss_protection:
            response.headers["X-XSS-Protection"] = self.x_xss_protection
        
        # Add Strict-Transport-Security
        if self.strict_transport_security:
            response.headers["Strict-Transport-Security"] = self.strict_transport_security
        
        # Add Permissions-Policy
        if self.permissions_policy:
            response.headers["Permissions-Policy"] = self._build_permissions_policy()
        
        # Add Cache-Control
        if self.cache_control:
            response.headers["Cache-Control"] = self.cache_control
    
    async def process_request(self, request: Request) -> Request:
        """
        Process a request through the security headers middleware.
        
        Args:
            request: The request to process

        Returns:
            The processed request
        """
        # This middleware doesn't modify the request, just passes it through
        return request
    
    async def process_response(self, response: Response) -> Response:
        """
        Process a response through the security headers middleware.
        
        Args:
            response: The response to process

        Returns:
            The processed response
        """
        # Check if the request/response is exempt
        if not self._is_exempt(response.request, response):
            # Add security headers
            self._add_security_headers(response)

        return response


class XSSFilter:
    """
    Filter for preventing Cross-Site Scripting (XSS) attacks.
    """
    
    @staticmethod
    def sanitize_html(html: str, allowed_tags: Optional[Set[str]] = None, allowed_attributes: Optional[Dict[str, Set[str]]] = None) -> str:
        """
        Sanitize HTML to prevent XSS attacks.
        
        Args:
            html: The HTML to sanitize
            allowed_tags: The allowed HTML tags
            allowed_attributes: The allowed HTML attributes for each tag
            
        Returns:
            The sanitized HTML
        """
        try:
            import bleach
            
            # Default allowed tags and attributes
            if allowed_tags is None:
                allowed_tags = {
                    "a", "abbr", "acronym", "b", "blockquote", "code", "em", "i", "li",
                    "ol", "p", "strong", "ul", "br", "hr", "span", "div", "h1", "h2",
                    "h3", "h4", "h5", "h6", "table", "thead", "tbody", "tr", "th", "td",
                }
            
            if allowed_attributes is None:
                allowed_attributes = {
                    "a": {"href", "title", "target", "rel"},
                    "abbr": {"title"},
                    "acronym": {"title"},
                    "*": {"class", "id", "style"},
                }
            
            # Convert allowed_attributes to the format expected by bleach
            bleach_attrs = {}
            for tag, attrs in allowed_attributes.items():
                bleach_attrs[tag] = list(attrs)
            
            # Sanitize the HTML
            return bleach.clean(
                html,
                tags=list(allowed_tags),
                attributes=bleach_attrs,
                strip=True,
            )
        except ImportError:
            # If bleach is not available, use a more secure approach
            # This is not as secure as bleach, but it's better than nothing
            import re
            
            # First, make a copy of the HTML to work with
            sanitized_html = html
            
            # Remove all tags except allowed ones
            if allowed_tags:
                # Create a pattern that matches any tag not in the allowed list
                allowed_tags_str = "|".join(allowed_tags)
                pattern = f"<(?!/?({allowed_tags_str})\\b)[^>]*>"
                sanitized_html = re.sub(pattern, "", sanitized_html, flags=re.IGNORECASE)
                
                # Now clean up any dangerous attributes from allowed tags
                dangerous_attrs = ["on\\w+", "style", "javascript:", "vbscript:"]
                for attr in dangerous_attrs:
                    sanitized_html = re.sub(f"\\s{attr}=['\"][^'\"]*['\"]", "", sanitized_html, flags=re.IGNORECASE)
            else:
                # If no allowed tags, just strip all tags but keep the content
                try:
                    # Try to use a proper HTML parser if available
                    from html.parser import HTMLParser
                    from io import StringIO
                    
                    class TagStripper(HTMLParser):
                        def __init__(self):
                            super().__init__()
                            self.result = StringIO()
                            self.skip_script_content = False
                            
                        def handle_starttag(self, tag, attrs):
                            if tag.lower() == 'script':
                                self.skip_script_content = True
                                
                        def handle_endtag(self, tag):
                            if tag.lower() == 'script':
                                self.skip_script_content = False
                                
                        def handle_data(self, data):
                            if not self.skip_script_content:
                                self.result.write(data)
                    
                    stripper = TagStripper()
                    stripper.feed(sanitized_html)
                    sanitized_html = stripper.result.getvalue()
                    
                except (ImportError, Exception):
                    # Fallback to regex if HTML parser is not available or fails
                    # First remove script tags and their content
                    sanitized_html = re.sub(r"<script\b[^>]*>.*?</script>", "", sanitized_html, flags=re.IGNORECASE | re.DOTALL)
                    # Then remove all other tags but keep their content
                    sanitized_html = re.sub(r"<[^>]*>", "", sanitized_html)
            
            return sanitized_html
    
    @staticmethod
    def escape_html(text: str) -> str:
        """
        Escape HTML special characters to prevent XSS attacks.
        
        Args:
            text: The text to escape
            
        Returns:
            The escaped text
        """
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;")
        )
    
    @staticmethod
    def sanitize_json(data: Any) -> Any:
        """
        Sanitize JSON data to prevent XSS attacks.
        
        Args:
            data: The JSON data to sanitize
            
        Returns:
            The sanitized JSON data
        """
        if isinstance(data, str):
            # Escape HTML in strings
            return XSSFilter.escape_html(data)
        elif isinstance(data, dict):
            # Recursively sanitize dictionaries
            return {k: XSSFilter.sanitize_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            # Recursively sanitize lists
            return [XSSFilter.sanitize_json(item) for item in data]
        else:
            # Return other types as-is
            return data


class XSSProtectionMiddleware(BaseMiddleware):
    """
    Middleware for preventing Cross-Site Scripting (XSS) attacks.
    """
    
    def __init__(
        self,
        sanitize_json_response: bool = True,
        sanitize_html_response: bool = False,
        allowed_html_tags: Optional[Set[str]] = None,
        allowed_html_attributes: Optional[Dict[str, Set[str]]] = None,
        exempt_paths: Optional[List[str]] = None,
        exempt_content_types: Optional[List[str]] = None,
    ):
        """
        Initialize the XSS protection middleware.
        
        Args:
            sanitize_json_response: Whether to sanitize JSON responses
            sanitize_html_response: Whether to sanitize HTML responses
            allowed_html_tags: The allowed HTML tags for sanitization
            allowed_html_attributes: The allowed HTML attributes for sanitization
            exempt_paths: Paths exempt from XSS protection
            exempt_content_types: Content types exempt from XSS protection
        """
        super().__init__()
        self.sanitize_json_response = sanitize_json_response
        self.sanitize_html_response = sanitize_html_response
        self.allowed_html_tags = allowed_html_tags
        self.allowed_html_attributes = allowed_html_attributes
        self.exempt_paths = exempt_paths or []
        self.exempt_content_types = exempt_content_types or []
    
    def _is_exempt(self, request: Request, response: Response) -> bool:
        """
        Check if a request/response is exempt from XSS protection.
        
        Args:
            request: The request
            response: The response
            
        Returns:
            True if the request/response is exempt, False otherwise
        """
        # Check if the path is exempt
        for path in self.exempt_paths:
            if re.match(path, request.path):
                return True
        
        # Check if the content type is exempt
        content_type = response.headers.get("Content-Type", "")
        for exempt_type in self.exempt_content_types:
            if exempt_type in content_type:
                return True
        
        return False
    
    def _sanitize_response(self, response: Response) -> None:
        """
        Sanitize a response to prevent XSS attacks.
        
        Args:
            response: The response to sanitize
        """
        content_type = response.headers.get("Content-Type", "")
        
        if "application/json" in content_type and self.sanitize_json_response:
            # Sanitize JSON response
            if hasattr(response, "body") and response.body:
                response.body = XSSFilter.sanitize_json(response.body)
        
        elif "text/html" in content_type and self.sanitize_html_response:
            # Sanitize HTML response
            if hasattr(response, "body") and isinstance(response.body, str):
                response.body = XSSFilter.sanitize_html(
                    response.body,
                    allowed_tags=self.allowed_html_tags,
                    allowed_attributes=self.allowed_html_attributes,
                )
    
    async def process_request(self, request: Request) -> Request:
        """
        Process a request through the XSS protection middleware.
        
        Args:
            request: The request to process

        Returns:
            The processed request
        """
        # This middleware doesn't modify the request, just passes it through
        return request
    
    async def process_response(self, response: Response) -> Response:
        """
        Process a response through the XSS protection middleware.

        Args:
            response: The response to process

        Returns:
            The processed response
        """
        # Check if the request/response is exempt
        if not self._is_exempt(response.request, response):
            # Sanitize the response
            self._sanitize_response(response)

        return response 