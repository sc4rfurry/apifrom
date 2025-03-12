"""
Adapters for integrating APIFromAnything with various platforms and frameworks.

This module provides adapters for running APIFromAnything applications on different
platforms, such as AWS Lambda, Google Cloud Functions, Azure Functions, Vercel, and Netlify.
"""

# Import adapters if their dependencies are available
try:
    from apifrom.adapters.aws_lambda import LambdaAdapter
except ImportError:
    pass

try:
    from apifrom.adapters.gcp_functions import CloudFunctionAdapter
except ImportError:
    pass

try:
    from apifrom.adapters.azure_functions import AzureFunctionAdapter
except ImportError:
    pass

try:
    from apifrom.adapters.vercel import VercelAdapter
except ImportError:
    pass

try:
    from apifrom.adapters.netlify import NetlifyAdapter
except ImportError:
    pass

__all__ = [
    "LambdaAdapter",
    "CloudFunctionAdapter",
    "AzureFunctionAdapter",
    "VercelAdapter",
    "NetlifyAdapter",
] 