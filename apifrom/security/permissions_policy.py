"""
Permissions Policy implementation for APIFromAnything.

This module provides utilities for implementing Permissions Policy (formerly Feature Policy),
which allows developers to selectively enable, disable, or modify the behavior of certain
browser features and APIs.
"""

from typing import Dict, List, Optional, Union, Callable, Any, Set
import re

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware.base import BaseMiddleware


class PermissionsDirective:
    """
    Permissions Policy directive constants.
    """
    # Sensors
    ACCELEROMETER = "accelerometer"
    AMBIENT_LIGHT_SENSOR = "ambient-light-sensor"
    GYROSCOPE = "gyroscope"
    MAGNETOMETER = "magnetometer"
    
    # Device access
    CAMERA = "camera"
    DISPLAY_CAPTURE = "display-capture"
    DOCUMENT_DOMAIN = "document-domain"
    FULLSCREEN = "fullscreen"
    GEOLOCATION = "geolocation"
    MICROPHONE = "microphone"
    MIDI = "midi"
    PAYMENT = "payment"
    PICTURE_IN_PICTURE = "picture-in-picture"
    SCREEN_WAKE_LOCK = "screen-wake-lock"
    USB = "usb"
    WEB_SHARE = "web-share"
    XR_SPATIAL_TRACKING = "xr-spatial-tracking"
    
    # Execution context
    AUTOPLAY = "autoplay"
    CLIPBOARD_READ = "clipboard-read"
    CLIPBOARD_WRITE = "clipboard-write"
    CROSS_ORIGIN_ISOLATED = "cross-origin-isolated"
    ENCRYPTED_MEDIA = "encrypted-media"
    EXECUTION_WHILE_NOT_RENDERED = "execution-while-not-rendered"
    EXECUTION_WHILE_OUT_OF_VIEWPORT = "execution-while-out-of-viewport"
    FOCUS_WITHOUT_USER_ACTIVATION = "focus-without-user-activation"
    FORMS = "forms"
    HOVERED_OVER_BROWSING_CONTEXT = "hovered-over-browsing-context"
    IDLE_DETECTION = "idle-detection"
    NAVIGATION_OVERRIDE = "navigation-override"
    POPUP = "popup"
    SPEAKER_SELECTION = "speaker-selection"
    SYNC_XHR = "sync-xhr"
    VERTICAL_SCROLL = "vertical-scroll"
    
    # All directives
    ALL = [
        ACCELEROMETER, AMBIENT_LIGHT_SENSOR, AUTOPLAY, CAMERA, CLIPBOARD_READ,
        CLIPBOARD_WRITE, CROSS_ORIGIN_ISOLATED, DISPLAY_CAPTURE, DOCUMENT_DOMAIN,
        ENCRYPTED_MEDIA, EXECUTION_WHILE_NOT_RENDERED, EXECUTION_WHILE_OUT_OF_VIEWPORT,
        FOCUS_WITHOUT_USER_ACTIVATION, FORMS, FULLSCREEN, GEOLOCATION, GYROSCOPE,
        HOVERED_OVER_BROWSING_CONTEXT, IDLE_DETECTION, MAGNETOMETER, MICROPHONE,
        MIDI, NAVIGATION_OVERRIDE, PAYMENT, PICTURE_IN_PICTURE, POPUP, SCREEN_WAKE_LOCK,
        SPEAKER_SELECTION, SYNC_XHR, USB, VERTICAL_SCROLL, WEB_SHARE, XR_SPATIAL_TRACKING
    ]


class PermissionsAllowlist:
    """
    Allowlist values for Permissions Policy directives.
    """
    SELF = "self"
    NONE = "none"
    ANY = "*"
    SRC = "src"


class PermissionsPolicy:
    """
    Policy for configuring Permissions Policy.
    
    This class represents a Permissions Policy that can be used to control
    which browser features and APIs are available to a document and its
    embedded frames.
    """
    
    def __init__(self):
        """
        Initialize the Permissions Policy.
        """
        self.directives: Dict[str, Set[str]] = {}
    
    def add_directive(self, directive: str, allowlist: Union[str, List[str]]) -> "PermissionsPolicy":
        """
        Add a directive to the policy.
        
        Args:
            directive: The directive name
            allowlist: The allowlist value(s)
            
        Returns:
            The policy instance for chaining
        """
        if directive not in self.directives:
            self.directives[directive] = set()
        
        if isinstance(allowlist, list):
            for value in allowlist:
                self._add_allowlist_value(directive, value)
        else:
            self._add_allowlist_value(directive, allowlist)
        
        return self
    
    def _add_allowlist_value(self, directive: str, value: str) -> None:
        """
        Add an allowlist value to a directive.
        
        Args:
            directive: The directive name
            value: The allowlist value
        """
        if directive not in self.directives:
            self.directives[directive] = set()

        # Handle special values
        if value == PermissionsAllowlist.SELF:
            self.directives[directive].add("'self'")
        elif value == PermissionsAllowlist.NONE:
            # For "none", we use an empty string in the set
            self.directives[directive].add("")
        elif value == PermissionsAllowlist.SRC:
            self.directives[directive].add("'src'")
        else:
            self.directives[directive].add(value)
    
    def disable_all(self) -> "PermissionsPolicy":
        """
        Disable all features for all origins.
        
        Returns:
            The policy instance for chaining
        """
        for directive in PermissionsDirective.ALL:
            self.add_directive(directive, PermissionsAllowlist.NONE)
        
        return self
    
    def enable_for_self(self, directives: List[str]) -> "PermissionsPolicy":
        """
        Enable specified features for the same origin.
        
        Args:
            directives: The directives to enable
            
        Returns:
            The policy instance for chaining
        """
        for directive in directives:
            self.add_directive(directive, PermissionsAllowlist.SELF)
        
        return self
    
    def to_header(self) -> str:
        """
        Convert the policy to a header value.
        
        Returns:
            The Permissions-Policy header value
        """
        directive_strings = []
        
        for directive, allowlist in self.directives.items():
            # Handle empty allowlist (none)
            if len(allowlist) == 1 and next(iter(allowlist)) == '':
                directive_strings.append(f"{directive}=()")
                continue
            
            # Format the allowlist
            allowlist_str = ", ".join(allowlist)
            directive_strings.append(f"{directive}=({allowlist_str})")
        
        return ", ".join(directive_strings)
    
    def to_header_value(self) -> str:
        """
        Convert the policy to a header value.
        
        This is an alias for to_header() for backward compatibility.

        Returns:
            The Permissions-Policy header value
        """
        return self.to_header()


class PermissionsPolicyMiddleware(BaseMiddleware):
    """
    Middleware for adding Permissions Policy headers to responses.
    
    This middleware adds the Permissions-Policy header to responses
    to control which browser features and APIs are available to a document
    and its embedded frames.
    """
    
    def __init__(
        self,
        policy: Optional[PermissionsPolicy] = None,
        exempt_paths: Optional[List[str]] = None,
    ):
        """
        Initialize the Permissions Policy middleware.
        
        Args:
            policy: The Permissions Policy to apply
            exempt_paths: Paths exempt from Permissions Policy
        """
        super().__init__()
        self.policy = policy or self._create_default_policy()
        self.exempt_paths = exempt_paths or []
    
    def _create_default_policy(self) -> PermissionsPolicy:
        """
        Create a default Permissions Policy.
        
        Returns:
            A default Permissions Policy
        """
        return (PermissionsPolicy()
            .add_directive(PermissionsDirective.CAMERA, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.MICROPHONE, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.GEOLOCATION, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.PAYMENT, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.USB, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.MIDI, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.SYNC_XHR, PermissionsAllowlist.NONE)
        )
    
    def _is_exempt(self, request: Request) -> bool:
        """
        Check if a request is exempt from Permissions Policy.
        
        Args:
            request: The request to check
            
        Returns:
            True if the request is exempt, False otherwise
        """
        for path in self.exempt_paths:
            if request.path.startswith(path):
                return True
        
        return False
    
    async def process_request(self, request: Request) -> Request:
        """
        Process a request through the Permissions Policy middleware.
        
        Args:
            request: The request to process
            
        Returns:
            The processed request
        """
        # This middleware doesn't modify the request, just passes it through
        return request
    
    async def process_response(self, response: Response) -> Response:
        """
        Process a response through the Permissions Policy middleware.
        
        Args:
            response: The response to process
            
        Returns:
            The processed response
        """
        # Check if the request is exempt
        if self._is_exempt(response.request):
            return response

        # Add the Permissions-Policy header
        header_value = self.policy.to_header()
        response.headers["Permissions-Policy"] = header_value
        
        return response


class PermissionsPolicyBuilder:
    """
    Helper class for building Permissions Policy.
    """
    
    @staticmethod
    def create_strict_policy() -> PermissionsPolicy:
        """
        Create a strict Permissions Policy that disables all features.
        
        Returns:
            A strict Permissions Policy
        """
        return PermissionsPolicy().disable_all()
    
    @staticmethod
    def create_minimal_policy() -> PermissionsPolicy:
        """
        Create a minimal Permissions Policy that disables sensitive features.
        
        Returns:
            A minimal Permissions Policy
        """
        return (PermissionsPolicy()
            .add_directive(PermissionsDirective.CAMERA, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.MICROPHONE, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.GEOLOCATION, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.PAYMENT, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.USB, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.MIDI, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.SYNC_XHR, PermissionsAllowlist.NONE)
        )
    
    @staticmethod
    def create_api_policy() -> PermissionsPolicy:
        """
        Create a Permissions Policy suitable for APIs.
        
        Returns:
            A Permissions Policy for APIs
        """
        policy = PermissionsPolicy().disable_all()
        
        # Enable specific directives for 'self'
        policy.directives[PermissionsDirective.SYNC_XHR] = set(["'self'"])
        policy.directives[PermissionsDirective.FORMS] = set(["'self'"])
        policy.directives[PermissionsDirective.VERTICAL_SCROLL] = set(["'self'"])
        
        return policy
    
    @staticmethod
    def create_web_policy() -> PermissionsPolicy:
        """
        Create a Permissions Policy suitable for web applications.
        
        Returns:
            A Permissions Policy for web applications
        """
        return (PermissionsPolicy()
            # Disable sensitive features
            .add_directive(PermissionsDirective.CAMERA, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.MICROPHONE, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.GEOLOCATION, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.PAYMENT, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.USB, PermissionsAllowlist.NONE)
            .add_directive(PermissionsDirective.MIDI, PermissionsAllowlist.NONE)
            
            # Enable some features for same origin
            .add_directive(PermissionsDirective.FULLSCREEN, PermissionsAllowlist.SELF)
            .add_directive(PermissionsDirective.PICTURE_IN_PICTURE, PermissionsAllowlist.SELF)
            .add_directive(PermissionsDirective.AUTOPLAY, PermissionsAllowlist.SELF)
            .add_directive(PermissionsDirective.CLIPBOARD_READ, PermissionsAllowlist.SELF)
            .add_directive(PermissionsDirective.CLIPBOARD_WRITE, PermissionsAllowlist.SELF)
        ) 