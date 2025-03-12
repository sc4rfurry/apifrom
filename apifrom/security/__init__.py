"""
Security module for APIFromAnything.

This module provides security features for APIFromAnything, including authentication,
authorization, CSRF protection, security headers, and more.
"""

# Authentication
from apifrom.security.auth import (
    jwt_required,
    api_key_required,
    basic_auth_required,
    oauth2_required,
)

# CSRF Protection
from apifrom.security.csrf import (
    CSRFMiddleware,
    CSRFToken,
)

# Security Headers
from apifrom.security.headers import (
    SecurityHeadersMiddleware,
    XSSProtectionMiddleware,
)

# HSTS Preloading
from apifrom.security.hsts import (
    HSTSMiddleware,
    HSTSPreloadChecker,
)

# Content Security Policy
from apifrom.security.csp import (
    CSPMiddleware,
    CSPPolicy,
    CSPDirective,
    CSPSource,
    CSPNonce,
    CSPViolationReporter,
    CSPBuilder,
)

# Subresource Integrity
from apifrom.security.sri import (
    SRIMiddleware,
    SRIPolicy,
    SRIGenerator,
    SRIHashAlgorithm,
    SRIBuilder,
)

# Trusted Types
from apifrom.security.trusted_types import (
    TrustedTypesMiddleware,
    TrustedTypesPolicy,
    TrustedTypesBuilder,
    TrustedTypesViolationReporter,
)

# Permissions Policy
from apifrom.security.permissions_policy import (
    PermissionsPolicyMiddleware,
    PermissionsPolicy,
    PermissionsDirective,
    PermissionsAllowlist,
    PermissionsPolicyBuilder,
)

__all__ = [
    # Authentication
    "jwt_required",
    "api_key_required",
    "basic_auth_required",
    "oauth2_required",
    
    # CSRF Protection
    "CSRFMiddleware",
    "CSRFToken",
    
    # Security Headers
    "SecurityHeadersMiddleware",
    "XSSProtectionMiddleware",
    
    # HSTS Preloading
    "HSTSMiddleware",
    "HSTSPreloadChecker",
    
    # Content Security Policy
    "CSPMiddleware",
    "CSPPolicy",
    "CSPDirective",
    "CSPSource",
    "CSPNonce",
    "CSPViolationReporter",
    "CSPBuilder",
    
    # Subresource Integrity
    "SRIMiddleware",
    "SRIPolicy",
    "SRIGenerator",
    "SRIHashAlgorithm",
    "SRIBuilder",
    
    # Trusted Types
    "TrustedTypesMiddleware",
    "TrustedTypesPolicy",
    "TrustedTypesBuilder",
    "TrustedTypesViolationReporter",
    
    # Permissions Policy
    "PermissionsPolicyMiddleware",
    "PermissionsPolicy",
    "PermissionsDirective",
    "PermissionsAllowlist",
    "PermissionsPolicyBuilder",
] 