"""
Example demonstrating the HSTS preloading functionality.

This example shows how to create an API with HSTS preloading support
to ensure that browsers always use HTTPS for your API.
"""

from typing import Dict

from apifrom import API
from apifrom.decorators.api import api
from apifrom.security import HSTSMiddleware, HSTSPreloadChecker

# Create the API instance
app = API(
    title="HSTS Preload Demo API",
    description="A demonstration of HSTS preloading functionality",
    version="1.0.0",
    debug=True
)

# Add HSTS middleware with preloading enabled
app.add_middleware(
    HSTSMiddleware(
        # Set max-age to 1 year (required for preloading)
        max_age=31536000,
        # Include subdomains (required for preloading)
        include_subdomains=True,
        # Enable preload directive (required for preloading)
        preload=True,
        # Redirect HTTP to HTTPS (required for preloading)
        force_https_redirect=True,
        # Exempt certain paths from HSTS (optional)
        exempt_paths=["/not-secure"]
    )
)

# Define some API endpoints
@api(app)
def hello() -> Dict:
    """
    A simple hello endpoint.
    
    Returns:
        A greeting message
    """
    return {"message": "Hello, World!"}


@api(app, route="/not-secure")
def not_secure() -> Dict:
    """
    An endpoint exempt from HSTS.
    
    Returns:
        A message about the endpoint being exempt from HSTS
    """
    return {"message": "This endpoint is exempt from HSTS"}


@api(app, route="/hsts-status")
def hsts_status() -> Dict:
    """
    Check the HSTS status of a domain.
    
    Returns:
        Information about the HSTS status
    """
    # In a real application, you would get this from the request
    domain = "example.com"
    
    # Get the HSTS header that would be sent
    hsts_header = "max-age=31536000; includeSubDomains; preload"
    
    # Check if the domain is eligible for preloading
    eligibility = HSTSPreloadChecker.check_eligibility(
        domain=domain,
        hsts_header=hsts_header,
        has_valid_certificate=True,
        all_subdomains_https=True,
        redirect_to_https=True
    )
    
    # Get submission instructions if eligible
    if eligibility["eligible"]:
        submission_instructions = HSTSPreloadChecker.get_submission_instructions(domain)
    else:
        submission_instructions = "Fix the issues before submitting."
    
    return {
        "domain": domain,
        "hsts_header": hsts_header,
        "eligible_for_preloading": eligibility["eligible"],
        "issues": eligibility["issues"],
        "submission_instructions": submission_instructions
    }


@api(app, route="/check-domain")
def check_domain(domain: str) -> Dict:
    """
    Check if a domain is eligible for HSTS preloading.
    
    Args:
        domain: The domain to check
        
    Returns:
        Information about the domain's eligibility for HSTS preloading
    """
    # In a real application, you would make an HTTP request to the domain
    # and check the HSTS header, certificate, etc.
    
    # For this example, we'll simulate the check
    hsts_header = "max-age=31536000; includeSubDomains; preload"
    
    # Check if the domain is eligible for preloading
    eligibility = HSTSPreloadChecker.check_eligibility(
        domain=domain,
        hsts_header=hsts_header,
        has_valid_certificate=True,
        all_subdomains_https=True,
        redirect_to_https=True
    )
    
    return {
        "domain": domain,
        "hsts_header": hsts_header,
        "eligible_for_preloading": eligibility["eligible"],
        "issues": eligibility["issues"]
    }


if __name__ == "__main__":
    # Run the API server
    app.run(host="127.0.0.1", port=8000)
    
    print("\nHSTS-enabled API running at http://127.0.0.1:8000")
    print("\nThis API will redirect HTTP requests to HTTPS and add the HSTS header to responses.")
    print("In a production environment, you would need a valid SSL/TLS certificate.")
    print("\nTo test the HSTS header, you can use curl:")
    print("\ncurl -I http://127.0.0.1:8000/hello")
    print("\nYou should see a 301 redirect to HTTPS, and when you follow the redirect,")
    print("you should see the Strict-Transport-Security header in the response.")
    print("\nTo check if a domain is eligible for HSTS preloading, visit:")
    print("\nhttp://127.0.0.1:8000/check-domain?domain=example.com") 