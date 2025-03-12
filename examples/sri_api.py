"""
Example demonstrating Subresource Integrity (SRI) functionality.

This example shows how to use the SRI middleware to add integrity attributes
to script and link tags in HTML responses, protecting against tampering with
external resources.
"""

import json
from typing import Dict, Any, Optional

from apifrom import API
from apifrom.decorators.api import api
from apifrom.security import (
    SRIMiddleware,
    SRIPolicy,
    SRIGenerator,
    SRIHashAlgorithm,
    SRIBuilder,
)


# Create a custom SRI policy
custom_policy = (SRIPolicy()
    # jQuery
    .add_script_source(
        "https://code.jquery.com/jquery-3.6.0.min.js",
        "sha384-vtXRMe3mGCbOeY7l30aIg8H9p3GdeSe4IFlP6G8JMa7o7lXvnz3GFKzPxzJdPfGK"
    )
    # Bootstrap
    .add_script_source(
        "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js",
        "sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p"
    )
    .add_style_source(
        "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",
        "sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3"
    )
)

# Create an API with SRI middleware
app = API(
    title="SRI Protected API",
    description="An API with Subresource Integrity protection",
    version="1.0.0",
    debug=True
)

# Add SRI middleware with custom policy
app.add_middleware(
    SRIMiddleware(
        script_sources=custom_policy.script_sources,
        style_sources=custom_policy.style_sources,
        verify_external_resources=True,
        exempt_paths=["/api"]
    )
)


@api(app, route="/")
def index() -> str:
    """
    Root endpoint that returns HTML with external resources.
    
    Returns:
        HTML content with external resources
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SRI Protected Page</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <h1>SRI Protected Page</h1>
            <p class="lead">This page is protected by Subresource Integrity (SRI).</p>
            <div class="alert alert-info">
                Check the HTML source to see the integrity attributes added to script and link tags.
            </div>
            <button class="btn btn-primary">Click Me</button>
        </div>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """


@api(app, route="/api/generate-hash")
def generate_hash(content: str, algorithm: str = "sha384") -> Dict[str, str]:
    """
    Generate an SRI hash for the given content.
    
    Args:
        content: The content to hash
        algorithm: The hash algorithm to use (sha256, sha384, or sha512)
        
    Returns:
        A dictionary containing the SRI hash
    """
    # Map the algorithm string to the enum
    algo_map = {
        "sha256": SRIHashAlgorithm.SHA256,
        "sha384": SRIHashAlgorithm.SHA384,
        "sha512": SRIHashAlgorithm.SHA512
    }
    
    # Get the algorithm enum
    algo = algo_map.get(algorithm.lower(), SRIHashAlgorithm.SHA384)
    
    # Generate the hash
    sri_hash = SRIGenerator.generate_hash(content, algo)
    
    return {
        "content": content[:50] + "..." if len(content) > 50 else content,
        "algorithm": algorithm,
        "hash": sri_hash
    }


@api(app, route="/api/verify-integrity")
def verify_integrity(content: str, integrity: str) -> Dict[str, Any]:
    """
    Verify that content matches an integrity value.
    
    Args:
        content: The content to verify
        integrity: The integrity value to check against
        
    Returns:
        A dictionary containing the verification result
    """
    # Verify the integrity
    is_valid = SRIGenerator.verify_integrity(content, integrity)
    
    return {
        "content": content[:50] + "..." if len(content) > 50 else content,
        "integrity": integrity,
        "is_valid": is_valid
    }


@api(app, route="/api/cdn-resources")
def cdn_resources() -> Dict[str, Any]:
    """
    List common CDN resources with their integrity values.
    
    Returns:
        A dictionary containing common CDN resources with their integrity values
    """
    # Get the common CDN policy
    cdn_policy = SRIBuilder.create_common_cdn_policy()
    
    return {
        "scripts": cdn_policy.script_sources,
        "styles": cdn_policy.style_sources
    }


@api(app, route="/unprotected")
def unprotected() -> str:
    """
    An unprotected endpoint that returns HTML without SRI attributes.
    
    Returns:
        HTML content without SRI attributes
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unprotected Page</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <h1>Unprotected Page</h1>
            <p class="lead">This page does not have SRI protection.</p>
            <div class="alert alert-warning">
                External resources on this page are loaded without integrity checks.
            </div>
            <button class="btn btn-primary">Click Me</button>
        </div>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """


@api(app, route="/api/extract-from-html", methods=["POST"])
async def extract_from_html(html: str) -> Dict[str, Any]:
    """
    Extract script and style sources from HTML and generate integrity values.
    
    Args:
        html: The HTML content to extract sources from
        
    Returns:
        A dictionary containing the extracted sources with integrity values
    """
    # Create a policy from the HTML
    policy = await SRIBuilder.create_policy_from_html(html)
    
    return {
        "scripts": policy.script_sources,
        "styles": policy.style_sources
    }


if __name__ == "__main__":
    # Run the API server
    app.run(host="127.0.0.1", port=8000)
    
    print("\nSRI Protected API running at http://127.0.0.1:8000")
    print("\nAvailable endpoints:")
    print("  - GET /: HTML page with SRI-protected resources")
    print("  - GET /unprotected: HTML page without SRI protection")
    print("  - GET /api/generate-hash: Generate an SRI hash for content")
    print("  - GET /api/verify-integrity: Verify content against an integrity value")
    print("  - GET /api/cdn-resources: List common CDN resources with integrity values")
    print("  - POST /api/extract-from-html: Extract sources from HTML and generate integrity values")
    print("\nTry comparing the HTML source of / and /unprotected to see the difference.") 