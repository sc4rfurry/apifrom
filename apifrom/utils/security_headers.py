from typing import Dict, List, Optional, Union, Set, Any, Callable

def create_security_headers(
    content_security_policy: Optional[Dict[str, Union[str, List[str]]]] = None,
    x_frame_options: Optional[str] = None,
    x_content_type_options: str = "nosniff",
    referrer_policy: Optional[str] = None,
    strict_transport_security: Optional[Dict[str, Any]] = None,
    permissions_policy: Optional[Dict[str, Union[bool, str, List[str]]]] = None,
    x_xss_protection: str = "1; mode=block",
    cache_control: Optional[str] = None,
    exempt_paths: Optional[List[str]] = None,
    exempt_content_types: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Create a dictionary of security headers for HTTP responses.
    
    Args:
        content_security_policy: CSP directives as a dictionary
        x_frame_options: X-Frame-Options header value (e.g. "DENY", "SAMEORIGIN")
        x_content_type_options: X-Content-Type-Options header value
        referrer_policy: Referrer-Policy header value
        strict_transport_security: HSTS configuration as a dictionary
        permissions_policy: Permissions Policy directives as a dictionary
        x_xss_protection: X-XSS-Protection header value
        cache_control: Cache-Control header value
        exempt_paths: List of URL paths exempt from security headers
        exempt_content_types: List of content types exempt from security headers
        
    Returns:
        Dictionary of security headers
    """
    headers = {}
    
    if content_security_policy:
        csp_value = build_csp(content_security_policy)
        if csp_value:
            headers["Content-Security-Policy"] = csp_value
    
    if x_frame_options:
        headers["X-Frame-Options"] = x_frame_options
        
    if x_content_type_options:
        headers["X-Content-Type-Options"] = x_content_type_options
        
    if referrer_policy:
        headers["Referrer-Policy"] = referrer_policy
        
    if strict_transport_security:
        hsts_value = build_hsts(strict_transport_security)
        if hsts_value:
            headers["Strict-Transport-Security"] = hsts_value
            
    if permissions_policy:
        pp_value = build_permissions_policy(permissions_policy)
        if pp_value:
            headers["Permissions-Policy"] = pp_value
            
    if x_xss_protection:
        headers["X-XSS-Protection"] = x_xss_protection
        
    if cache_control:
        headers["Cache-Control"] = cache_control
        
    return headers
    
def build_csp(directives: Dict[str, Union[str, List[str]]]) -> str:
    """
    Build a Content-Security-Policy header value from directives.
    
    Args:
        directives: Dictionary of CSP directives
        
    Returns:
        CSP header value as string
    """
    parts = []
    
    for directive, sources in directives.items():
        if isinstance(sources, list):
            parts.append(f"{directive} {' '.join(sources)}")
        else:
            parts.append(f"{directive} {sources}")
            
    return "; ".join(parts)
    
def build_hsts(config: Dict[str, Any]) -> str:
    """
    Build a Strict-Transport-Security header value.
    
    Args:
        config: HSTS configuration options
        
    Returns:
        HSTS header value as string
    """
    parts = []
    
    if "max_age" in config:
        parts.append(f"max-age={config['max_age']}")
        
    if config.get("include_subdomains", False):
        parts.append("includeSubDomains")
        
    if config.get("preload", False):
        parts.append("preload")
        
    return "; ".join(parts)
    
def build_permissions_policy(directives: Dict[str, Union[bool, str, List[str]]]) -> str:
    """
    Build a Permissions-Policy header value.
    
    Args:
        directives: Dictionary of permissions policy directives
        
    Returns:
        Permissions-Policy header value as string
    """
    parts = []
    
    for feature, allowlist in directives.items():
        if allowlist is True:
            parts.append(f"{feature}=*")
        elif allowlist is False:
            parts.append(f"{feature}=()")
        elif isinstance(allowlist, str):
            parts.append(f"{feature}=({allowlist})")
        elif isinstance(allowlist, list):
            formatted_sources = [f'"{source}"' for source in allowlist]
            parts.append(f"{feature}=({' '.join(formatted_sources)})")
            
    return ", ".join(parts)
    
def should_apply_security_headers(
    path: str,
    content_type: Optional[str] = None,
    exempt_paths: Optional[List[str]] = None,
    exempt_content_types: Optional[List[str]] = None
) -> bool:
    """
    Determine if security headers should be applied to a response.
    
    Args:
        path: URL path of the request
        content_type: Content-Type of the response
        exempt_paths: List of URL paths exempt from security headers
        exempt_content_types: List of content types exempt from security headers
        
    Returns:
        True if security headers should be applied, False otherwise
    """
    # Check exempt paths
    if exempt_paths:
        for exempt_path in exempt_paths:
            if path.startswith(exempt_path):
                return False
                
    # Check exempt content types
    if exempt_content_types and content_type:
        for exempt_type in exempt_content_types:
            if content_type.startswith(exempt_type):
                return False
                
    return True

