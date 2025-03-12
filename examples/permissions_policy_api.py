"""
Example demonstrating Permissions Policy functionality.

This example shows how to use the Permissions Policy middleware to control
which browser features and APIs are available to a document and its embedded frames.
"""

from typing import Dict, Any, List

from apifrom import API
from apifrom.decorators.api import api
from apifrom.security import (
    PermissionsPolicyMiddleware,
    PermissionsPolicy,
    PermissionsDirective,
    PermissionsAllowlist,
    PermissionsPolicyBuilder,
)


# Create a custom Permissions Policy
custom_policy = (PermissionsPolicy()
    # Disable sensitive features
    .add_directive(PermissionsDirective.CAMERA, PermissionsAllowlist.NONE)
    .add_directive(PermissionsDirective.MICROPHONE, PermissionsAllowlist.NONE)
    .add_directive(PermissionsDirective.GEOLOCATION, PermissionsAllowlist.NONE)
    .add_directive(PermissionsDirective.PAYMENT, PermissionsAllowlist.NONE)
    .add_directive(PermissionsDirective.USB, PermissionsAllowlist.NONE)
    
    # Enable some features for same origin
    .add_directive(PermissionsDirective.FULLSCREEN, PermissionsAllowlist.SELF)
    .add_directive(PermissionsDirective.AUTOPLAY, PermissionsAllowlist.SELF)
    
    # Enable clipboard for same origin and specific domains
    .add_directive(PermissionsDirective.CLIPBOARD_READ, [
        PermissionsAllowlist.SELF,
        "https://trusted-site.example"
    ])
    .add_directive(PermissionsDirective.CLIPBOARD_WRITE, PermissionsAllowlist.SELF)
)

# Create an API with Permissions Policy middleware
app = API(
    title="Permissions Policy API",
    description="An API with Permissions Policy protection",
    version="1.0.0",
    debug=True
)

# Add Permissions Policy middleware with custom policy
app.add_middleware(
    PermissionsPolicyMiddleware(
        policy=custom_policy,
        exempt_paths=["/api/exempt"]
    )
)


@api(app, route="/")
def index() -> str:
    """
    Root endpoint that returns HTML with Permissions Policy protection.
    
    Returns:
        HTML content with Permissions Policy protection
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Permissions Policy Protected Page</title>
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
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 10px;
                margin-top: 20px;
            }
            .feature-item {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
            .feature-name {
                font-weight: bold;
                margin-bottom: 5px;
            }
            .feature-status {
                font-size: 0.9em;
                color: #666;
            }
            .status-allowed {
                color: #5cb85c;
            }
            .status-blocked {
                color: #d9534f;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Permissions Policy Protected Page</h1>
            <p>This page is protected by Permissions Policy, which controls which browser features and APIs are available.</p>
            
            <div class="alert alert-info">
                <strong>Info:</strong> Permissions Policy allows developers to selectively enable, disable, or modify the behavior of certain browser features and APIs.
            </div>
            
            <h2>What is Permissions Policy?</h2>
            <p>Permissions Policy is a web platform feature that gives a website the ability to allow or block the use of browser features in its own frame or in iframes that it embeds.</p>
            
            <h3>Example</h3>
            <pre><code>
// Permissions-Policy header
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), 
                   fullscreen=(self), autoplay=(self), 
                   clipboard-read=(self https://trusted-site.example), 
                   clipboard-write=(self)
            </code></pre>
            
            <div class="alert alert-warning">
                <strong>Warning:</strong> Attempting to use disabled features will result in permission being denied.
            </div>
            
            <h3>Feature Status</h3>
            <div class="feature-grid">
                <div class="feature-item">
                    <div class="feature-name">Camera</div>
                    <div class="feature-status status-blocked">Blocked</div>
                </div>
                <div class="feature-item">
                    <div class="feature-name">Microphone</div>
                    <div class="feature-status status-blocked">Blocked</div>
                </div>
                <div class="feature-item">
                    <div class="feature-name">Geolocation</div>
                    <div class="feature-status status-blocked">Blocked</div>
                </div>
                <div class="feature-item">
                    <div class="feature-name">Payment</div>
                    <div class="feature-status status-blocked">Blocked</div>
                </div>
                <div class="feature-item">
                    <div class="feature-name">USB</div>
                    <div class="feature-status status-blocked">Blocked</div>
                </div>
                <div class="feature-item">
                    <div class="feature-name">Fullscreen</div>
                    <div class="feature-status status-allowed">Allowed (same origin)</div>
                </div>
                <div class="feature-item">
                    <div class="feature-name">Autoplay</div>
                    <div class="feature-status status-allowed">Allowed (same origin)</div>
                </div>
                <div class="feature-item">
                    <div class="feature-name">Clipboard Read</div>
                    <div class="feature-status status-allowed">Allowed (same origin, trusted site)</div>
                </div>
                <div class="feature-item">
                    <div class="feature-name">Clipboard Write</div>
                    <div class="feature-status status-allowed">Allowed (same origin)</div>
                </div>
            </div>
            
            <h3>Test Features</h3>
            <p>Click the buttons below to test various browser features:</p>
            
            <button class="btn btn-primary" id="testGeolocation">Test Geolocation (Blocked)</button>
            <button class="btn btn-primary" id="testFullscreen">Test Fullscreen (Allowed)</button>
            <button class="btn btn-primary" id="testClipboard">Test Clipboard (Allowed)</button>
            
            <div id="output" style="margin-top: 20px;"></div>
            
            <script>
                const output = document.getElementById('output');
                
                document.getElementById('testGeolocation').addEventListener('click', function() {
                    output.textContent = 'Testing geolocation...';
                    
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                            function(position) {
                                // This should not be called due to Permissions Policy
                                output.textContent = `Geolocation allowed: ${position.coords.latitude}, ${position.coords.longitude}`;
                            },
                            function(error) {
                                output.textContent = `Geolocation blocked: ${error.message}`;
                            }
                        );
                    } else {
                        output.textContent = 'Geolocation not supported in this browser';
                    }
                });
                
                document.getElementById('testFullscreen').addEventListener('click', function() {
                    output.textContent = 'Testing fullscreen...';
                    
                    try {
                        if (document.documentElement.requestFullscreen) {
                            document.documentElement.requestFullscreen()
                                .then(() => {
                                    output.textContent = 'Fullscreen allowed';
                                })
                                .catch(error => {
                                    output.textContent = `Fullscreen blocked: ${error.message}`;
                                });
                        } else {
                            output.textContent = 'Fullscreen not supported in this browser';
                        }
                    } catch (error) {
                        output.textContent = `Fullscreen error: ${error.message}`;
                    }
                });
                
                document.getElementById('testClipboard').addEventListener('click', function() {
                    output.textContent = 'Testing clipboard...';
                    
                    if (navigator.clipboard) {
                        navigator.clipboard.writeText('Test clipboard text')
                            .then(() => {
                                output.textContent = 'Clipboard write allowed';
                                
                                // Try to read from clipboard
                                return navigator.clipboard.readText();
                            })
                            .then(text => {
                                output.textContent += `\\nClipboard read allowed: "${text}"`;
                            })
                            .catch(error => {
                                output.textContent += `\\nClipboard operation blocked: ${error.message}`;
                            });
                    } else {
                        output.textContent = 'Clipboard API not supported in this browser';
                    }
                });
            </script>
        </div>
    </body>
    </html>
    """


@api(app, route="/api/policies")
def list_policies() -> Dict[str, Any]:
    """
    List available Permissions Policy configurations.
    
    Returns:
        A dictionary containing information about available policies
    """
    return {
        "policies": {
            "strict": PermissionsPolicyBuilder.create_strict_policy().to_header_value(),
            "minimal": PermissionsPolicyBuilder.create_minimal_policy().to_header_value(),
            "api": PermissionsPolicyBuilder.create_api_policy().to_header_value(),
            "web": PermissionsPolicyBuilder.create_web_policy().to_header_value(),
            "custom": custom_policy.to_header_value()
        }
    }


@api(app, route="/api/features")
def list_features() -> Dict[str, List[str]]:
    """
    List available Permissions Policy features.
    
    Returns:
        A dictionary containing lists of features by category
    """
    return {
        "sensors": [
            PermissionsDirective.ACCELEROMETER,
            PermissionsDirective.AMBIENT_LIGHT_SENSOR,
            PermissionsDirective.GYROSCOPE,
            PermissionsDirective.MAGNETOMETER
        ],
        "device_access": [
            PermissionsDirective.CAMERA,
            PermissionsDirective.DISPLAY_CAPTURE,
            PermissionsDirective.DOCUMENT_DOMAIN,
            PermissionsDirective.FULLSCREEN,
            PermissionsDirective.GEOLOCATION,
            PermissionsDirective.MICROPHONE,
            PermissionsDirective.MIDI,
            PermissionsDirective.PAYMENT,
            PermissionsDirective.PICTURE_IN_PICTURE,
            PermissionsDirective.SCREEN_WAKE_LOCK,
            PermissionsDirective.USB,
            PermissionsDirective.WEB_SHARE,
            PermissionsDirective.XR_SPATIAL_TRACKING
        ],
        "execution_context": [
            PermissionsDirective.AUTOPLAY,
            PermissionsDirective.CLIPBOARD_READ,
            PermissionsDirective.CLIPBOARD_WRITE,
            PermissionsDirective.CROSS_ORIGIN_ISOLATED,
            PermissionsDirective.ENCRYPTED_MEDIA,
            PermissionsDirective.EXECUTION_WHILE_NOT_RENDERED,
            PermissionsDirective.EXECUTION_WHILE_OUT_OF_VIEWPORT,
            PermissionsDirective.FOCUS_WITHOUT_USER_ACTIVATION,
            PermissionsDirective.FORMS,
            PermissionsDirective.HOVERED_OVER_BROWSING_CONTEXT,
            PermissionsDirective.IDLE_DETECTION,
            PermissionsDirective.NAVIGATION_OVERRIDE,
            PermissionsDirective.POPUP,
            PermissionsDirective.SPEAKER_SELECTION,
            PermissionsDirective.SYNC_XHR,
            PermissionsDirective.VERTICAL_SCROLL
        ]
    }


@api(app, route="/api/create-policy", methods=["POST"])
def create_policy(features: Dict[str, str]) -> Dict[str, str]:
    """
    Create a custom Permissions Policy.
    
    Args:
        features: Dictionary mapping feature names to allowlist values
        
    Returns:
        A dictionary containing the generated policy header value
    """
    policy = PermissionsPolicy()
    
    for feature, allowlist in features.items():
        # Parse allowlist string into a list
        if allowlist.lower() == "none":
            allowlist_value = PermissionsAllowlist.NONE
        elif allowlist.lower() == "self":
            allowlist_value = PermissionsAllowlist.SELF
        elif allowlist.lower() == "*":
            allowlist_value = PermissionsAllowlist.ANY
        elif allowlist.lower() == "src":
            allowlist_value = PermissionsAllowlist.SRC
        else:
            # Assume it's a comma-separated list of origins
            allowlist_value = allowlist.split(",")
        
        policy.add_directive(feature, allowlist_value)
    
    return {
        "policy": policy.to_header_value()
    }


@api(app, route="/api/exempt")
def exempt_endpoint() -> Dict[str, Any]:
    """
    An endpoint exempt from Permissions Policy.
    
    Returns:
        A dictionary containing information about the endpoint
    """
    return {
        "message": "This endpoint is exempt from Permissions Policy",
        "header": "No Permissions-Policy header will be added to the response"
    }


@api(app, route="/iframe-test")
def iframe_test() -> str:
    """
    An endpoint that demonstrates Permissions Policy with iframes.
    
    Returns:
        HTML content with iframes to test Permissions Policy
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Permissions Policy Iframe Test</title>
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
            .iframe-container {
                margin-top: 20px;
                border: 1px solid #ddd;
                padding: 10px;
                border-radius: 4px;
            }
            iframe {
                width: 100%;
                height: 300px;
                border: 1px solid #ccc;
            }
            h3 {
                margin-top: 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Permissions Policy Iframe Test</h1>
            <p>This page demonstrates how Permissions Policy affects iframes.</p>
            
            <div class="iframe-container">
                <h3>Iframe with default permissions (inherited from parent)</h3>
                <iframe src="/"></iframe>
            </div>
            
            <div class="iframe-container">
                <h3>Iframe with allow="geolocation" attribute (overrides parent policy)</h3>
                <iframe src="/" allow="geolocation"></iframe>
            </div>
            
            <div class="iframe-container">
                <h3>Iframe with allow="camera" attribute (overrides parent policy)</h3>
                <iframe src="/" allow="camera"></iframe>
            </div>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    # Run the API server
    app.run(host="127.0.0.1", port=8000)
    
    print("\nPermissions Policy API running at http://127.0.0.1:8000")
    print("\nAvailable endpoints:")
    print("  - GET /: HTML page with Permissions Policy protection")
    print("  - GET /iframe-test: HTML page with iframes to test Permissions Policy")
    print("  - GET /api/policies: List available Permissions Policy configurations")
    print("  - GET /api/features: List available Permissions Policy features")
    print("  - POST /api/create-policy: Create a custom Permissions Policy")
    print("  - GET /api/exempt: Endpoint exempt from Permissions Policy")
    print("\nCheck the response headers to see the Permissions-Policy header.") 