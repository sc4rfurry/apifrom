from typing import Dict, List, Optional, Set, Union, Literal, TypeVar, Any

from apifrom.core.request import Request
from apifrom.core.response import Response

# Define types for permissions policy directives
DirectiveValue = Union[Literal["self", "none", "*"], List[str]]
PolicyDict = Dict[str, DirectiveValue]

# Feature policy directives (legacy and current)
PERMISSIONS_POLICY_DIRECTIVES: Set[str] = {
    # Legacy features
    "accelerometer", "ambient-light-sensor", "autoplay", "battery", "camera",
    "display-capture", "document-domain", "encrypted-media", "execution-while-not-rendered",
    "execution-while-out-of-viewport", "fullscreen", "gamepad", "geolocation",
    "gyroscope", "layout-animations", "legacy-image-formats", "magnetometer",
    "microphone", "midi", "navigation-override", "oversized-images", "payment",
    "picture-in-picture", "publickey-credentials-get", "screen-wake-lock",
    "sync-xhr", "usb", "vr", "wake-lock", "web-share", "xr-spatial-tracking",
    
    # Newer features
    "clipboard-read", "clipboard-write", "cross-origin-isolated",
    "idle-detection", "interest-cohort", "serial"
}

class PermissionsPolicy:
    """
    Class for creating and validating Permissions-Policy headers.
    
    The Permissions-Policy header is used to allow or deny the use of browser
    features in a document or in any embedded frames.
    """
    
    def __init__(self, policy: Optional[PolicyDict] = None) -> None:
        """
        Initialize the permissions policy with the given directives.
        
        Args:
            policy: A dictionary mapping feature names to their allowed origins
        """
        self.policy: PolicyDict = policy or {}
        self._validate_policy()
    
    def _validate_policy(self) -> None:
        """Validates that all policy directives are recognized."""
        for directive in self.policy:
            if directive not in PERMISSIONS_POLICY_DIRECTIVES:
                raise ValueError(f"Unknown permissions policy directive: {directive}")
    
    def add_directive(self, feature: str, value: DirectiveValue) -> None:
        """
        Add a directive to the permissions policy.
        
        Args:
            feature: The feature name
            value: The allowed origins or special values like "self" or "none"
        """
        if feature not in PERMISSIONS_POLICY_DIRECTIVES:
            raise ValueError(f"Unknown permissions policy directive: {feature}")
        
        self.policy[feature] = value
    
    def remove_directive(self, feature: str) -> None:
        """Remove a directive from the permissions policy."""
        if feature in self.policy:
            del self.policy[feature]
    
    def to_header_value(self) -> str:
        """
        Convert the policy to a string for use in the Permissions-Policy header.
        
        Returns:
            The formatted header value
        """
        if not self.policy:
            return ""
            
        parts = []
        for feature, value in self.policy.items():
            if isinstance(value, list):
                if not value:  # Empty list means no origins allowed
                    parts.append(f"{feature}=()")
                else:
                    origins = " ".join(f'"{origin}"' for origin in value)
                    parts.append(f"{feature}=({origins})")
            elif value == "self":
                parts.append(f"{feature}=(self)")
            elif value == "*":
                parts.append(f"{feature}=*")
            elif value == "none":
                parts.append(f"{feature}=()")
            else:
                raise ValueError(f"Invalid directive value for {feature}: {value}")
                
        return ", ".join(parts)

class PermissionsPolicyMiddleware:
    """
    Middleware that adds Permissions-Policy headers to responses.
    """
    
    def __init__(
        self,
        policy: Optional[PermissionsPolicy] = None,
        exempt_paths: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize the permissions policy middleware.
        
        Args:
            policy: The permissions policy to apply
            exempt_paths: Paths that should not have the policy applied
        """
        self.policy = policy or PermissionsPolicy()
        self.exempt_paths = exempt_paths or []
    
    def _is_exempt(self, request: Request) -> bool:
        """Check if the request path is exempt from the permissions policy."""
        if not self.exempt_paths:
            return False
            
        path = request.path or ""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)
    
    async def __call__(self, request: Request, call_next: Any) -> Response:
        """
        Process the request and add the Permissions-Policy header to the response.
        
        Args:
            request: The HTTP request
            call_next: The next middleware or endpoint handler
        
        Returns:
            The HTTP response with permissions policy headers added
        """
        response = await call_next(request)
        
        if self._is_exempt(request):
            return response
            
        header_value = self.policy.to_header_value()
        if header_value:
            response.headers["Permissions-Policy"] = header_value
            
        return response

def permissions_policy(
    accelerometer: Optional[DirectiveValue] = None,
    ambient_light_sensor: Optional[DirectiveValue] = None,
    autoplay: Optional[DirectiveValue] = None,
    battery: Optional[DirectiveValue] = None,
    camera: Optional[DirectiveValue] = None,
    display_capture: Optional[DirectiveValue] = None,
    document_domain: Optional[DirectiveValue] = None,
    encrypted_media: Optional[DirectiveValue] = None,
    execution_while_not_rendered: Optional[DirectiveValue] = None,
    execution_while_out_of_viewport: Optional[DirectiveValue] = None,
    fullscreen: Optional[DirectiveValue] = None,
    gamepad: Optional[DirectiveValue] = None,
    geolocation: Optional[DirectiveValue] = None,
    gyroscope: Optional[DirectiveValue] = None,
    layout_animations: Optional[DirectiveValue] = None,
    legacy_image_formats: Optional[DirectiveValue] = None,
    magnetometer: Optional[DirectiveValue] = None,
    microphone: Optional[DirectiveValue] = None,
    midi: Optional[DirectiveValue] = None,
    navigation_override: Optional[DirectiveValue] = None,
    oversized_images: Optional[DirectiveValue] = None,
    payment: Optional[DirectiveValue] = None,
    picture_in_picture: Optional[DirectiveValue] = None,
    publickey_credentials_get: Optional[DirectiveValue] = None,
    screen_wake_lock: Optional[DirectiveValue] = None,
    sync_xhr: Optional[DirectiveValue] = None,
    usb: Optional[DirectiveValue] = None,
    vr: Optional[DirectiveValue] = None,
    wake_lock: Optional[DirectiveValue] = None,
    web_share: Optional[DirectiveValue] = None,
    xr_spatial_tracking: Optional[DirectiveValue] = None,
    clipboard_read: Optional[DirectiveValue] = None,
    clipboard_write: Optional[DirectiveValue] = None,
    cross_origin_isolated: Optional[DirectiveValue] = None,
    idle_detection: Optional[DirectiveValue] = None,
    interest_cohort: Optional[DirectiveValue] = None,
    serial: Optional[DirectiveValue] = None,
) -> PermissionsPolicy:
    """
    Creates a permissions policy with the specified directives.
    
    Each directive can be set to:
    - "self": allows the feature to be used only in the same origin
    - "none": disables the feature
    - "*": allows the feature to be used in any origin
    - List of strings: specifies allowed origins for the feature
    
    Args:
        accelerometer: Controls access to accelerometer sensors
        ambient_light_sensor: Controls access to ambient light sensors
        autoplay: Controls whether media can autoplay
        battery: Controls access to Battery Status API
        camera: Controls access to video input devices
        display_capture: Controls the ability to capture screen content
        document_domain: Controls use of document.domain API
        encrypted_media: Controls access to Encrypted Media Extensions
        execution_while_not_rendered: Controls execution when not rendered
        execution_while_out_of_viewport: Controls execution when out of viewport
        fullscreen: Controls the ability to use fullscreen mode
        gamepad: Controls access to the Gamepad API
        geolocation: Controls access to Geolocation API
        gyroscope: Controls access to gyroscope sensors
        layout_animations: Controls the use of layout animations
        legacy_image_formats: Controls use of legacy image formats
        magnetometer: Controls access to magnetometer sensors
        microphone: Controls access to audio input devices
        midi: Controls access to the Web MIDI API
        navigation_override: Controls the ability to override navigation
        oversized_images: Controls the loading of oversized images
        payment: Controls access to the Payment Request API
        picture_in_picture: Controls the use of picture-in-picture mode
        publickey_credentials_get: Controls access to WebAuthn API
        screen_wake_lock: Controls the Screen Wake Lock API
        sync_xhr: Controls synchronous XHR requests
        usb: Controls access to the WebUSB API
        vr: Controls access to VR hardware through the WebVR API
        wake_lock: Controls the Wake Lock API
        web_share: Controls the Web Share API
        xr_spatial_tracking: Controls access to WebXR Device API
        clipboard_read: Controls read access to the clipboard
        clipboard_write: Controls write access to the clipboard
        cross_origin_isolated: Controls cross-origin isolation
        idle_detection: Controls the Idle Detection API
        interest_cohort: Controls the FLoC (Federated Learning of Cohorts) API
        serial: Controls access to the Web Serial API
        
    Returns:
        A PermissionsPolicy instance
    """
    policy = PermissionsPolicy()
    
    # Convert snake_case to kebab-case and add directives
    locals_dict = locals()
    for feature in PERMISSIONS_POLICY_DIRECTIVES:
        # Convert kebab-case to snake_case for lookup
        snake_feature = feature.replace("-", "_")
        if snake_feature in locals_dict and locals_dict[snake_feature] is not None:
            policy.add_directive(feature, locals_dict[snake_feature])
            
    return policy

