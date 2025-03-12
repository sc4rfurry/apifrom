"""
Example demonstrating Content Security Policy (CSP) middleware.

This example shows how to use the CSP middleware to add Content Security Policy
headers to API responses, protecting against various attacks like XSS, clickjacking,
and data injection.
"""

import json
from typing import Dict, Any, Optional

from apifrom import API
from apifrom.security import (
    CSPMiddleware,
    CSPPolicy,
    CSPDirective,
    CSPSource,
    CSPNonce,
    CSPViolationReporter,
    CSPBuilder,
)


# Create a violation reporter callback
async def handle_csp_violation(report: Dict[str, Any]) -> None:
    """
    Handle CSP violation reports.
    
    Args:
        report: The violation report
    """
    print("CSP Violation Report:")
    print(json.dumps(report, indent=2))


# Create a CSP violation reporter
reporter = CSPViolationReporter(
    report_uri="/csp-report",
    callback=handle_csp_violation
)

# Create a custom CSP policy
custom_policy = (CSPPolicy()
    .add_default_src([CSPSource.SELF])
    .add_script_src([CSPSource.SELF, "https://cdn.example.com"])
    .add_style_src([CSPSource.SELF, CSPSource.UNSAFE_INLINE])
    .add_img_src([CSPSource.SELF, CSPSource.DATA, "https://images.example.com"])
    .add_font_src([CSPSource.SELF, "https://fonts.googleapis.com", "https://fonts.gstatic.com"])
    .add_connect_src([CSPSource.SELF, "https://api.example.com"])
    .add_object_src([CSPSource.NONE])
    .add_frame_ancestors([CSPSource.NONE])
    .add_base_uri([CSPSource.SELF])
    .add_form_action([CSPSource.SELF])
    .add_upgrade_insecure_requests()
    .add_block_all_mixed_content()
    .set_reporter(reporter)
)

# Create an API with CSP middleware
api = API(
    title="CSP Protected API",
    description="An API with Content Security Policy protection",
    version="1.0.0",
    debug=True
)

# Add CSP middleware with custom policy
api.add_middleware(CSPMiddleware(
    policy=custom_policy,
    exempt_paths=["/health", "/metrics"]
))

# Add a report-only CSP middleware for testing
report_only_policy = CSPBuilder.create_report_only_policy("/csp-report")
api.add_middleware(CSPMiddleware(
    policy=report_only_policy,
    exempt_paths=["/csp-report"]
))


@api.route("/", methods=["GET"])
def index() -> Dict[str, str]:
    """
    Root endpoint.
    
    Returns:
        A welcome message
    """
    return {"message": "Welcome to the CSP Protected API"}


@api.route("/csp-report", methods=["POST"])
async def csp_report(report: Dict[str, Any]) -> Dict[str, str]:
    """
    Endpoint for receiving CSP violation reports.
    
    Args:
        report: The CSP violation report
        
    Returns:
        A confirmation message
    """
    await handle_csp_violation(report)
    return {"status": "Report received"}


@api.route("/policies", methods=["GET"])
def list_policies() -> Dict[str, Any]:
    """
    List available CSP policies.
    
    Returns:
        A dictionary of available CSP policies
    """
    policies = {
        "api": CSPBuilder.create_api_policy().to_header_value(),
        "web": CSPBuilder.create_web_policy().to_header_value(),
        "strict": CSPBuilder.create_strict_policy().to_header_value(),
        "custom": custom_policy.to_header_value(),
    }
    return {"policies": policies}


@api.route("/nonce", methods=["GET"])
def generate_nonce() -> Dict[str, str]:
    """
    Generate a CSP nonce.
    
    Returns:
        A dictionary containing a CSP nonce
    """
    return {"nonce": CSPNonce.generate()}


@api.route("/check-policy", methods=["POST"])
def check_policy(policy_string: str) -> Dict[str, Any]:
    """
    Check a CSP policy string for common issues.
    
    Args:
        policy_string: The CSP policy string to check
        
    Returns:
        A dictionary containing the check results
    """
    issues = []
    
    # Check for unsafe-inline in script-src
    if "script-src" in policy_string and "unsafe-inline" in policy_string:
        issues.append("'unsafe-inline' in script-src is not recommended")
    
    # Check for unsafe-eval
    if "unsafe-eval" in policy_string:
        issues.append("'unsafe-eval' is not recommended")
    
    # Check for missing object-src
    if "object-src" not in policy_string:
        issues.append("Missing object-src directive")
    
    # Check for missing frame-ancestors
    if "frame-ancestors" not in policy_string:
        issues.append("Missing frame-ancestors directive")
    
    # Check for wildcard sources
    if "*" in policy_string:
        issues.append("Wildcard (*) sources are not recommended")
    
    return {
        "policy": policy_string,
        "issues": issues,
        "is_secure": len(issues) == 0
    }


@api.route("/create-policy", methods=["POST"])
def create_policy(
    default_src: Optional[str] = None,
    script_src: Optional[str] = None,
    style_src: Optional[str] = None,
    img_src: Optional[str] = None,
    connect_src: Optional[str] = None,
    font_src: Optional[str] = None,
    object_src: Optional[str] = None,
    frame_ancestors: Optional[str] = None,
    report_uri: Optional[str] = None,
    upgrade_insecure_requests: bool = True,
    block_all_mixed_content: bool = True
) -> Dict[str, str]:
    """
    Create a custom CSP policy.
    
    Args:
        default_src: The default-src directive
        script_src: The script-src directive
        style_src: The style-src directive
        img_src: The img-src directive
        connect_src: The connect-src directive
        font_src: The font-src directive
        object_src: The object-src directive
        frame_ancestors: The frame-ancestors directive
        report_uri: The report-uri directive
        upgrade_insecure_requests: Whether to include upgrade-insecure-requests
        block_all_mixed_content: Whether to include block-all-mixed-content
        
    Returns:
        A dictionary containing the generated CSP policy
    """
    policy = CSPPolicy()
    
    if default_src:
        policy.add_default_src(default_src.split())
    else:
        policy.add_default_src([CSPSource.SELF])
    
    if script_src:
        policy.add_script_src(script_src.split())
    
    if style_src:
        policy.add_style_src(style_src.split())
    
    if img_src:
        policy.add_img_src(img_src.split())
    
    if connect_src:
        policy.add_connect_src(connect_src.split())
    
    if font_src:
        policy.add_font_src(font_src.split())
    
    if object_src:
        policy.add_object_src(object_src.split())
    else:
        policy.add_object_src([CSPSource.NONE])
    
    if frame_ancestors:
        policy.add_frame_ancestors(frame_ancestors.split())
    else:
        policy.add_frame_ancestors([CSPSource.NONE])
    
    if report_uri:
        reporter = CSPViolationReporter(report_uri=report_uri)
        policy.set_reporter(reporter)
    
    if upgrade_insecure_requests:
        policy.add_upgrade_insecure_requests()
    
    if block_all_mixed_content:
        policy.add_block_all_mixed_content()
    
    return {"policy": policy.to_header_value()}


if __name__ == "__main__":
    api.run(host="0.0.0.0", port=8000)
    print(f"CSP Protected API running at http://localhost:8000")
    print("Available endpoints:")
    print("  - GET /: Welcome message")
    print("  - GET /policies: List available CSP policies")
    print("  - GET /nonce: Generate a CSP nonce")
    print("  - POST /check-policy: Check a CSP policy string")
    print("  - POST /create-policy: Create a custom CSP policy")
    print("  - POST /csp-report: Receive CSP violation reports")
    print("\nTest the CSP headers with:")
    print("  curl -I http://localhost:8000") 