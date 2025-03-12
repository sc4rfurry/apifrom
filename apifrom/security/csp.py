"""
Content Security Policy (CSP) middleware for APIFromAnything.

This module provides middleware for adding Content Security Policy headers to API responses.
"""

from typing import Dict, List, Optional, Union, Callable, Any, Set
import re

from apifrom.middleware.base import BaseMiddleware
from apifrom.core.request import Request
from apifrom.core.response import Response


class CSPDirective:
    """
    Content Security Policy directive constants.
    """
    DEFAULT_SRC = "default-src"
    SCRIPT_SRC = "script-src"
    STYLE_SRC = "style-src"
    IMG_SRC = "img-src"
    CONNECT_SRC = "connect-src"
    FONT_SRC = "font-src"
    OBJECT_SRC = "object-src"
    MEDIA_SRC = "media-src"
    FRAME_SRC = "frame-src"
    FRAME_ANCESTORS = "frame-ancestors"
    FORM_ACTION = "form-action"
    BASE_URI = "base-uri"
    WORKER_SRC = "worker-src"
    MANIFEST_SRC = "manifest-src"
    PREFETCH_SRC = "prefetch-src"
    NAVIGATE_TO = "navigate-to"
    REPORT_TO = "report-to"
    REPORT_URI = "report-uri"
    SANDBOX = "sandbox"
    UPGRADE_INSECURE_REQUESTS = "upgrade-insecure-requests"
    BLOCK_ALL_MIXED_CONTENT = "block-all-mixed-content"
    REQUIRE_TRUSTED_TYPES_FOR = "require-trusted-types-for"
    TRUSTED_TYPES = "trusted-types"


class CSPSource:
    """
    Content Security Policy source constants.
    """
    NONE = "'none'"
    SELF = "'self'"
    UNSAFE_INLINE = "'unsafe-inline'"
    UNSAFE_EVAL = "'unsafe-eval'"
    STRICT_DYNAMIC = "'strict-dynamic'"
    UNSAFE_HASHES = "'unsafe-hashes'"
    REPORT_SAMPLE = "'report-sample'"
    HTTPS = "https:"
    DATA = "data:"
    BLOB = "blob:"
    FILESYSTEM = "filesystem:"
    MEDIASTREAM = "mediastream:"
    WS = "ws:"
    WSS = "wss:"


class CSPNonce:
    """
    Content Security Policy nonce generator.
    """
    
    @staticmethod
    def generate() -> str:
        """
        Generate a random nonce for CSP.
        
        Returns:
            A random nonce string
        """
        import secrets
        return f"'nonce-{secrets.token_urlsafe(16)}'"


class CSPViolationReporter:
    """
    Content Security Policy violation reporter.
    """
    
    def __init__(
        self,
        report_uri: Optional[str] = None,
        report_to: Optional[str] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Initialize the CSP violation reporter.
        
        Args:
            report_uri: The URI to send violation reports to
            report_to: The reporting group to send violation reports to
            callback: A callback function to handle violation reports
        """
        self.report_uri = report_uri
        self.report_to = report_to
        self.callback = callback
    
    def get_directives(self) -> Dict[str, str]:
        """
        Get the reporting directives.
        
        Returns:
            A dictionary of reporting directives
        """
        directives = {}
        if self.report_uri:
            directives[CSPDirective.REPORT_URI] = self.report_uri
        if self.report_to:
            directives[CSPDirective.REPORT_TO] = self.report_to
        return directives
    
    async def handle_report(self, report: Dict[str, Any]) -> None:
        """
        Handle a CSP violation report.
        
        Args:
            report: The violation report
        """
        if self.callback:
            await self.callback(report)


class CSPPolicy:
    """
    Content Security Policy builder.
    """
    
    def __init__(self, report_only: bool = False):
        """
        Initialize the CSP policy.
        
        Args:
            report_only: Whether to use the report-only mode
        """
        self.directives: Dict[str, Set[str]] = {}
        self.report_only = report_only
        self.reporter: Optional[CSPViolationReporter] = None
    
    def add_directive(self, directive: str, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add a directive to the policy.
        
        Args:
            directive: The directive name
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        if directive not in self.directives:
            self.directives[directive] = set()
        
        if isinstance(source, list):
            for s in source:
                self.directives[directive].add(s)
        else:
            self.directives[directive].add(source)
        
        return self
    
    def add_default_src(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add default-src directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.DEFAULT_SRC, source)
    
    def add_script_src(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add script-src directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.SCRIPT_SRC, source)
    
    def add_style_src(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add style-src directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.STYLE_SRC, source)
    
    def add_img_src(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add img-src directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.IMG_SRC, source)
    
    def add_connect_src(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add connect-src directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.CONNECT_SRC, source)
    
    def add_font_src(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add font-src directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.FONT_SRC, source)
    
    def add_object_src(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add object-src directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.OBJECT_SRC, source)
    
    def add_media_src(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add media-src directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.MEDIA_SRC, source)
    
    def add_frame_src(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add frame-src directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.FRAME_SRC, source)
    
    def add_frame_ancestors(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add frame-ancestors directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.FRAME_ANCESTORS, source)
    
    def add_form_action(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add form-action directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.FORM_ACTION, source)
    
    def add_base_uri(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add base-uri directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.BASE_URI, source)
    
    def add_worker_src(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add worker-src directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.WORKER_SRC, source)
    
    def add_manifest_src(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add manifest-src directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.MANIFEST_SRC, source)
    
    def add_prefetch_src(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add prefetch-src directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.PREFETCH_SRC, source)
    
    def add_navigate_to(self, source: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add navigate-to directive.
        
        Args:
            source: The source value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.NAVIGATE_TO, source)
    
    def add_sandbox(self, value: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add sandbox directive.
        
        Args:
            value: The sandbox value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.SANDBOX, value)
    
    def add_upgrade_insecure_requests(self) -> "CSPPolicy":
        """
        Add upgrade-insecure-requests directive.
        
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.UPGRADE_INSECURE_REQUESTS, "")
    
    def add_block_all_mixed_content(self) -> "CSPPolicy":
        """
        Add block-all-mixed-content directive.
        
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.BLOCK_ALL_MIXED_CONTENT, "")
    
    def add_require_trusted_types_for(self, value: str = "script") -> "CSPPolicy":
        """
        Add require-trusted-types-for directive.
        
        Args:
            value: The value for the directive
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.REQUIRE_TRUSTED_TYPES_FOR, f"'{value}'")
    
    def add_trusted_types(self, value: Union[str, List[str]]) -> "CSPPolicy":
        """
        Add trusted-types directive.
        
        Args:
            value: The trusted types value(s)
            
        Returns:
            The CSP policy instance for chaining
        """
        return self.add_directive(CSPDirective.TRUSTED_TYPES, value)
    
    def set_reporter(self, reporter: CSPViolationReporter) -> "CSPPolicy":
        """
        Set the violation reporter.
        
        Args:
            reporter: The violation reporter
            
        Returns:
            The CSP policy instance for chaining
        """
        self.reporter = reporter
        return self
    
    def to_header(self) -> str:
        """
        Convert the policy to a header value.
        
        Returns:
            The CSP header value
        """
        directives = []
        
        # Add reporting directives if a reporter is set
        if self.reporter:
            for directive, value in self.reporter.get_directives().items():
                directives.append(f"{directive} {value}")
        
        # Add all other directives
        for directive, sources in self.directives.items():
            if not sources:
                directives.append(directive)
            else:
                sources_str = " ".join(sources)
                directives.append(f"{directive} {sources_str}")
        
        return "; ".join(directives)
    
    def to_header_value(self) -> str:
        """
        Convert the policy to a header value.
        
        This is an alias for to_header() for backward compatibility.

        Returns:
            The CSP header value
        """
        return self.to_header()
    
    def get_header_name(self) -> str:
        """
        Get the appropriate header name based on the policy mode.
        
        Returns:
            The CSP header name
        """
        if self.report_only:
            return "Content-Security-Policy-Report-Only"
        return "Content-Security-Policy"


class CSPMiddleware(BaseMiddleware):
    """
    Middleware for adding Content Security Policy headers to responses.
    """
    
    def __init__(
        self,
        policy: Optional[CSPPolicy] = None,
        exempt_paths: Optional[List[str]] = None,
        exempt_path_regex: Optional[str] = None
    ):
        """
        Initialize the CSP middleware.
        
        Args:
            policy: The CSP policy to apply
            exempt_paths: List of paths to exempt from CSP
            exempt_path_regex: Regex pattern for paths to exempt from CSP
        """
        super().__init__()
        self.policy = policy or self._create_default_policy()
        self.exempt_paths = exempt_paths or []
        self.exempt_path_regex = exempt_path_regex
        self.exempt_path_pattern = re.compile(exempt_path_regex) if exempt_path_regex else None
    
    def _create_default_policy(self) -> CSPPolicy:
        """
        Create a default CSP policy.
        
        Returns:
            A default CSP policy
        """
        return (CSPPolicy()
            .add_default_src([CSPSource.SELF])
            .add_script_src([CSPSource.SELF])
            .add_style_src([CSPSource.SELF])
            .add_img_src([CSPSource.SELF, CSPSource.DATA])
            .add_font_src([CSPSource.SELF])
            .add_connect_src([CSPSource.SELF])
            .add_object_src([CSPSource.NONE])
            .add_frame_ancestors([CSPSource.NONE])
            .add_base_uri([CSPSource.SELF])
            .add_form_action([CSPSource.SELF])
            .add_upgrade_insecure_requests()
        )
    
    def _is_path_exempt(self, path: str) -> bool:
        """
        Check if a path is exempt from CSP.
        
        Args:
            path: The request path
            
        Returns:
            True if the path is exempt, False otherwise
        """
        if path in self.exempt_paths:
            return True
        
        if self.exempt_path_pattern and self.exempt_path_pattern.match(path):
            return True
        
        return False
    
    async def process_request(
        self,
        request: Request
    ) -> Request:
        """
        Process the request.

        Args:
            request: The request object

        Returns:
            The processed request
        """
        # This middleware doesn't modify the request, just passes it through
        return request
    
    async def process_response(self, response: Response) -> Response:
        """
        Process the response and add CSP headers.

        Args:
            response: The response object

        Returns:
            The response with CSP headers
        """
        # Skip if the path is exempt
        if self._is_path_exempt(response.request.path):
            return response
        
        # Add CSP headers to the response
        header_name = "Content-Security-Policy"
        if self.policy.report_only:
            header_name = "Content-Security-Policy-Report-Only"
        
        response.headers[header_name] = self.policy.to_header()
        
        return response


class CSPBuilder:
    """
    Helper class for building CSP policies.
    """
    
    @staticmethod
    def create_api_policy() -> CSPPolicy:
        """
        Create a CSP policy suitable for APIs.
        
        Returns:
            A CSP policy for APIs
        """
        return (CSPPolicy()
            .add_default_src([CSPSource.NONE])
            .add_frame_ancestors([CSPSource.NONE])
            .add_base_uri([CSPSource.NONE])
            .add_form_action([CSPSource.NONE])
            .add_upgrade_insecure_requests()
            .add_block_all_mixed_content()
        )
    
    @staticmethod
    def create_web_policy() -> CSPPolicy:
        """
        Create a CSP policy suitable for web applications.
        
        Returns:
            A CSP policy for web applications
        """
        return (CSPPolicy()
            .add_default_src([CSPSource.SELF])
            .add_script_src([CSPSource.SELF])
            .add_style_src([CSPSource.SELF])
            .add_img_src([CSPSource.SELF, CSPSource.DATA])
            .add_font_src([CSPSource.SELF, "https://fonts.gstatic.com"])
            .add_connect_src([CSPSource.SELF])
            .add_object_src([CSPSource.NONE])
            .add_frame_ancestors([CSPSource.SELF])
            .add_base_uri([CSPSource.SELF])
            .add_form_action([CSPSource.SELF])
            .add_upgrade_insecure_requests()
            .add_block_all_mixed_content()
        )
    
    @staticmethod
    def create_strict_policy() -> CSPPolicy:
        """
        Create a strict CSP policy.
        
        Returns:
            A strict CSP policy
        """
        return (CSPPolicy()
            .add_default_src([CSPSource.NONE])
            .add_script_src([CSPSource.SELF])
            .add_style_src([CSPSource.SELF])
            .add_img_src([CSPSource.SELF])
            .add_font_src([CSPSource.SELF])
            .add_connect_src([CSPSource.SELF])
            .add_object_src([CSPSource.NONE])
            .add_media_src([CSPSource.NONE])
            .add_frame_src([CSPSource.NONE])
            .add_frame_ancestors([CSPSource.NONE])
            .add_base_uri([CSPSource.NONE])
            .add_form_action([CSPSource.SELF])
            .add_upgrade_insecure_requests()
            .add_block_all_mixed_content()
            .add_require_trusted_types_for()
        )
    
    @staticmethod
    def create_report_only_policy(report_uri: str) -> CSPPolicy:
        """
        Create a report-only CSP policy.
        
        Args:
            report_uri: The URI to send violation reports to
            
        Returns:
            A report-only CSP policy
        """
        reporter = CSPViolationReporter(report_uri=report_uri)
        return (CSPPolicy(report_only=True)
            .add_default_src([CSPSource.SELF])
            .add_script_src([CSPSource.SELF])
            .add_style_src([CSPSource.SELF])
            .add_img_src([CSPSource.SELF])
            .add_font_src([CSPSource.SELF])
            .add_connect_src([CSPSource.SELF])
            .add_object_src([CSPSource.NONE])
            .add_frame_ancestors([CSPSource.NONE])
            .add_base_uri([CSPSource.SELF])
            .add_form_action([CSPSource.SELF])
            .add_upgrade_insecure_requests()
            .set_reporter(reporter)
        ) 