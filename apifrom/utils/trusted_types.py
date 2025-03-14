from typing import List, Dict, Any, Optional, Callable, Union, Set, TypeVar, Generic

# Type annotations for handlers
script_handlers: List[Callable] = []
html_handlers: List[Callable] = []
script_url_handlers: List[Callable] = []
url_handlers: List[Callable] = []

class TrustedTypesPolicy:
    """Base class for trusted types policies"""
    def __init__(self, name: str):
        self.name = name

class TrustedTypeMiddleware:
    """Middleware for enforcing trusted types in web applications"""
    def __init__(
        self, 
        policies: Optional[List[TrustedTypesPolicy]] = None, 
        report_only: bool = False,
        exempt_paths: Optional[List[str]] = None
    ):
        self.policies = policies or []
        self.report_only = report_only
        self.exempt_paths = exempt_paths or []

