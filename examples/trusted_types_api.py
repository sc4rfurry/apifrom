"""
Example demonstrating Trusted Types functionality.

This example shows how to use the Trusted Types middleware to protect against
DOM-based XSS attacks by restricting the strings that can be passed to DOM
injection sinks.
"""

import json
from typing import Dict, Any, Optional

from apifrom import API
from apifrom.decorators.api import api
from apifrom.security import (
    TrustedTypesMiddleware,
    TrustedTypesPolicy,
    TrustedTypesBuilder,
    TrustedTypesViolationReporter,
)


# Create a custom Trusted Types policy
custom_policy = TrustedTypesPolicy(name="custom-policy")

# Add a script handler that validates JavaScript syntax
def validate_script(script: str) -> str:
    # Check for common XSS patterns
    if "<script" in script.lower() or "javascript:" in script.lower():
        raise ValueError("Potential XSS attack detected in script")
    return script

# Add an HTML handler that sanitizes HTML
def sanitize_html(html: str) -> str:
    # Simple sanitization that removes script tags
    import re
    html = re.sub(r'<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'javascript:', '', html, flags=re.IGNORECASE)
    return html

# Add handlers to the policy
custom_policy.add_script_handler(validate_script)
custom_policy.add_html_handler(sanitize_html)

# Create a violation reporter
async def handle_violation(report: Dict[str, Any]) -> None:
    """
    Handle Trusted Types violation reports.
    
    Args:
        report: The violation report
    """
    print("Trusted Types Violation Report:")
    print(json.dumps(report, indent=2))

reporter = TrustedTypesViolationReporter(
    report_uri="/trusted-types-violation",
    callback=handle_violation
)

# Create an API with Trusted Types middleware
app = API(
    title="Trusted Types Protected API",
    description="An API with Trusted Types protection",
    version="1.0.0",
    debug=True
)

# Add Trusted Types middleware with custom policy
app.add_middleware(
    TrustedTypesMiddleware(
        policies=[
            custom_policy,
            TrustedTypesBuilder.create_escape_policy(),
            TrustedTypesBuilder.create_sanitize_policy(),
        ],
        require_for_script=True,
        allow_duplicates=False,
        report_only=False,
        report_uri="/trusted-types-violation",
        exempt_paths=["/api"]
    )
)


@api(app, route="/")
def index() -> str:
    """
    Root endpoint that returns HTML with Trusted Types protection.
    
    Returns:
        HTML content with Trusted Types protection
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trusted Types Protected Page</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            .alert {
                padding: 15px;
                margin-bottom: 20px;
                border: 1px solid transparent;
                border-radius: 4px;
            }
            .alert-info {
                color: #31708f;
                background-color: #d9edf7;
                border-color: #bce8f1;
            }
            .alert-warning {
                color: #8a6d3b;
                background-color: #fcf8e3;
                border-color: #faebcc;
            }
            .btn {
                display: inline-block;
                padding: 6px 12px;
                margin-bottom: 0;
                font-size: 14px;
                font-weight: 400;
                line-height: 1.42857143;
                text-align: center;
                white-space: nowrap;
                vertical-align: middle;
                cursor: pointer;
                background-image: none;
                border: 1px solid transparent;
                border-radius: 4px;
            }
            .btn-primary {
                color: #fff;
                background-color: #337ab7;
                border-color: #2e6da4;
            }
            pre {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
            }
            code {
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Trusted Types Protected Page</h1>
            <p>This page is protected by Trusted Types, which helps prevent DOM-based XSS attacks.</p>
            
            <div class="alert alert-info">
                <strong>Info:</strong> Trusted Types restricts the strings that can be passed to DOM injection sinks.
            </div>
            
            <h2>What are Trusted Types?</h2>
            <p>Trusted Types is a web platform feature that helps prevent DOM-based XSS attacks by requiring that values assigned to risky DOM sinks are marked as trusted.</p>
            
            <h3>Protected DOM Sinks</h3>
            <ul>
                <li><code>element.innerHTML</code></li>
                <li><code>element.outerHTML</code></li>
                <li><code>document.write</code></li>
                <li><code>document.writeln</code></li>
                <li><code>DOMParser.parseFromString</code></li>
                <li><code>script.src</code></li>
                <li><code>script.text</code></li>
                <li><code>eval</code></li>
                <li><code>setTimeout</code> with string arguments</li>
                <li><code>setInterval</code> with string arguments</li>
                <li><code>new Function()</code></li>
            </ul>
            
            <h3>Example</h3>
            <pre><code>
// Without Trusted Types
element.innerHTML = userInput; // Potentially unsafe

// With Trusted Types
const policy = trustedTypes.createPolicy('sanitizer', {
    createHTML: (input) => sanitizeHTML(input)
});
element.innerHTML = policy.createHTML(userInput); // Safe
            </code></pre>
            
            <div class="alert alert-warning">
                <strong>Warning:</strong> Attempting to assign untrusted strings to protected DOM sinks will throw an error when Trusted Types is enforced.
            </div>
            
            <button class="btn btn-primary" id="testButton">Test Trusted Types</button>
            <div id="output"></div>
            
            <script>
                document.getElementById('testButton').addEventListener('click', function() {
                    const output = document.getElementById('output');
                    
                    try {
                        // This will throw an error if Trusted Types is enforced
                        // output.innerHTML = '<img src="x" onerror="alert(\'XSS\')">';
                        
                        // Instead, we use a Trusted Types policy
                        if (window.trustedTypes && window.trustedTypes.createPolicy) {
                            const policy = window.trustedTypes.createPolicy('sanitize', {
                                createHTML: (input) => {
                                    // Simple sanitization
                                    return input.replace(/<script[^>]*>.*?<\/script>/gi, '')
                                               .replace(/javascript:/gi, '');
                                }
                            });
                            
                            // Safe assignment using the policy
                            output.innerHTML = policy.createHTML('<p>This HTML is safe</p>');
                        } else {
                            output.textContent = 'Trusted Types is not supported in this browser';
                        }
                    } catch (error) {
                        output.textContent = 'Error: ' + error.message;
                    }
                });
            </script>
        </div>
    </body>
    </html>
    """


@api(app, route="/api/validate-script")
def validate_script_endpoint(script: str) -> Dict[str, Any]:
    """
    Validate a script using the custom policy.
    
    Args:
        script: The script to validate
        
    Returns:
        A dictionary containing the validation result
    """
    try:
        validated_script = custom_policy.create_script(script)
        return {
            "valid": True,
            "script": validated_script
        }
    except ValueError as e:
        return {
            "valid": False,
            "error": str(e)
        }


@api(app, route="/api/sanitize-html")
def sanitize_html_endpoint(html: str) -> Dict[str, Any]:
    """
    Sanitize HTML using the custom policy.
    
    Args:
        html: The HTML to sanitize
        
    Returns:
        A dictionary containing the sanitized HTML
    """
    sanitized_html = custom_policy.create_html(html)
    return {
        "original": html,
        "sanitized": sanitized_html
    }


@api(app, route="/api/policies")
def list_policies() -> Dict[str, Any]:
    """
    List available Trusted Types policies.
    
    Returns:
        A dictionary containing information about available policies
    """
    return {
        "policies": [
            {
                "name": "custom-policy",
                "description": "Custom policy with script and HTML handlers"
            },
            {
                "name": "escape",
                "description": "Policy that escapes HTML"
            },
            {
                "name": "sanitize",
                "description": "Policy that sanitizes HTML"
            }
        ]
    }


@api(app, route="/trusted-types-violation", methods=["POST"])
async def trusted_types_violation(report: Dict[str, Any]) -> Dict[str, str]:
    """
    Endpoint for receiving Trusted Types violation reports.
    
    Args:
        report: The Trusted Types violation report
        
    Returns:
        A confirmation message
    """
    await handle_violation(report)
    return {"status": "Report received"}


@api(app, route="/unsafe")
def unsafe_page() -> str:
    """
    An unsafe page that doesn't use Trusted Types.
    
    Returns:
        HTML content without Trusted Types protection
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unsafe Page</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            .alert {
                padding: 15px;
                margin-bottom: 20px;
                border: 1px solid transparent;
                border-radius: 4px;
            }
            .alert-warning {
                color: #8a6d3b;
                background-color: #fcf8e3;
                border-color: #faebcc;
            }
            .btn {
                display: inline-block;
                padding: 6px 12px;
                margin-bottom: 0;
                font-size: 14px;
                font-weight: 400;
                line-height: 1.42857143;
                text-align: center;
                white-space: nowrap;
                vertical-align: middle;
                cursor: pointer;
                background-image: none;
                border: 1px solid transparent;
                border-radius: 4px;
            }
            .btn-danger {
                color: #fff;
                background-color: #d9534f;
                border-color: #d43f3a;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Unsafe Page</h1>
            <p>This page does not use Trusted Types and is vulnerable to DOM-based XSS attacks.</p>
            
            <div class="alert alert-warning">
                <strong>Warning:</strong> This page is intentionally vulnerable for demonstration purposes.
            </div>
            
            <button class="btn btn-danger" id="unsafeButton">Test Unsafe Assignment</button>
            <div id="output"></div>
            
            <script>
                document.getElementById('unsafeButton').addEventListener('click', function() {
                    const output = document.getElementById('output');
                    
                    // Unsafe assignment (would be blocked by Trusted Types)
                    output.innerHTML = '<p>This is potentially unsafe HTML</p>';
                    
                    // In a real attack, this could be:
                    // output.innerHTML = '<img src="x" onerror="alert(\'XSS\')">';
                });
            </script>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    # Run the API server
    app.run(host="127.0.0.1", port=8000)
    
    print("\nTrusted Types Protected API running at http://127.0.0.1:8000")
    print("\nAvailable endpoints:")
    print("  - GET /: HTML page with Trusted Types protection")
    print("  - GET /unsafe: HTML page without Trusted Types protection")
    print("  - GET /api/validate-script: Validate a script using the custom policy")
    print("  - GET /api/sanitize-html: Sanitize HTML using the custom policy")
    print("  - GET /api/policies: List available Trusted Types policies")
    print("  - POST /trusted-types-violation: Receive Trusted Types violation reports")
    print("\nTry comparing the HTML source of / and /unsafe to see the difference.") 