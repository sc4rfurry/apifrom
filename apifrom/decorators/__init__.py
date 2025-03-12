"""
Decorators for the APIFromAnything library.

This package provides decorators that can be used to enhance API endpoints
with additional functionality.
"""

from apifrom.decorators.api import api
from apifrom.decorators.web import Web
from apifrom.decorators.web_optimize import WebOptimize

__all__ = ["api", "Web", "WebOptimize"] 