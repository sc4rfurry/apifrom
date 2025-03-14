"""
Subresource Integrity (SRI) implementation for APIFromAnything.

This module provides utilities for implementing Subresource Integrity (SRI)
to ensure that resources loaded from external sources have not been tampered with.
"""

import base64
import hashlib
from enum import Enum
from typing import Dict, List, Optional, Union, Callable, Any

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware.base import BaseMiddleware


class SRIHashAlgorithm(Enum):
    """
    Hash algorithms supported by Subresource Integrity.
    """
    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"


class SRIGenerator:
    """
    Utility for generating Subresource Integrity hashes.
    """
    
    @staticmethod
    def generate_hash(content: Union[str, bytes], algorithm: SRIHashAlgorithm = SRIHashAlgorithm.SHA384) -> str:
        """
        Generate a Subresource Integrity hash for the given content.
        
        Args:
            content: The content to hash (string or bytes)
            algorithm: The hash algorithm to use
            
        Returns:
            The SRI hash string in the format 'algorithm-base64hash'
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        hash_obj = hashlib.new(algorithm.value)
        hash_obj.update(content)
        hash_digest = hash_obj.digest()
        
        base64_hash = base64.b64encode(hash_digest).decode('ascii')
        return f"{algorithm.value}-{base64_hash}"
    
    @staticmethod
    def generate_integrity_attribute(content: Union[str, bytes], algorithms: Optional[List[SRIHashAlgorithm]] = None) -> str:
        """
        Generate a complete integrity attribute for HTML elements.
        
        Args:
            content: The content to hash
            algorithms: The hash algorithms to use (defaults to [SHA384])
            
        Returns:
            The integrity attribute value with multiple hashes if requested
        """
        if algorithms is None:
            algorithms = [SRIHashAlgorithm.SHA384]
        
        hashes = [SRIGenerator.generate_hash(content, algorithm) for algorithm in algorithms]
        return " ".join(hashes)
    
    @staticmethod
    def verify_integrity(content: Union[str, bytes], integrity_value: str) -> bool:
        """
        Verify that content matches an integrity value.
        
        Args:
            content: The content to verify
            integrity_value: The integrity value to check against
            
        Returns:
            True if the content matches any of the hashes in the integrity value
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        # Split the integrity value into individual hash specifications
        hash_specs = integrity_value.split()
        
        for hash_spec in hash_specs:
            # Split the algorithm and base64 hash
            try:
                algorithm, base64_hash = hash_spec.split('-', 1)
                
                # Create a new hash object with the specified algorithm
                hash_obj = hashlib.new(algorithm)
                hash_obj.update(content)
                hash_digest = hash_obj.digest()
                
                # Compare the computed hash with the provided hash
                computed_base64 = base64.b64encode(hash_digest).decode('ascii')
                if computed_base64 == base64_hash:
                    return True
            except (ValueError, TypeError, AttributeError, ImportError):
                # Skip invalid hash specifications
                continue
        
        return False


class SRIMiddleware(BaseMiddleware):
    """
    Middleware for adding Subresource Integrity headers to responses.
    
    This middleware can modify HTML responses to add integrity attributes
    to script and link tags that load external resources.
    """
    
    def __init__(
        self,
        script_sources: Optional[Dict[str, str]] = None,
        style_sources: Optional[Dict[str, str]] = None,
        verify_external_resources: bool = False,
        algorithms: Optional[List[SRIHashAlgorithm]] = None,
        exempt_paths: Optional[List[str]] = None,
    ):
        """
        Args:
            script_sources: Dictionary mapping script URLs to their integrity values
            style_sources: Dictionary mapping style URLs to their integrity values
            verify_external_resources: Whether to verify external resources
            algorithms: List of hash algorithms to use for verification
            exempt_paths: Paths exempt from SRI
        """
        super().__init__()
        self.script_sources = script_sources or {}
        self.style_sources = style_sources or {}
        self.verify_external_resources = verify_external_resources
        self.algorithms = algorithms or [SRIHashAlgorithm.SHA384]
        self.exempt_paths = exempt_paths or []
        
        # Cache for computed integrity values
        # Cache for computed integrity values
        self._integrity_cache: Dict[str, str] = {}
    def _is_exempt(self, request: Request) -> bool:
        """
        Check if a request is exempt from SRI processing.
        
        Args:
            request: The request to check
            
        Returns:
            True if the request is exempt, False otherwise
        """
        for path in self.exempt_paths:
            if request.path.startswith(path):
                return True
        
        return False
    
    async def _fetch_and_compute_integrity(self, url: str) -> Optional[str]:
        """
        Fetch a resource and compute its integrity value.
        
        Args:
            url: The URL of the resource to fetch
            
        Returns:
            The integrity value, or None if the resource could not be fetched
        """
        # Check if we already have the integrity value cached
        if url in self._integrity_cache:
            return self._integrity_cache[url]
        
        try:
            # Use a simple HTTP client to fetch the resource
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        integrity = SRIGenerator.generate_integrity_attribute(content, self.algorithms)
                        self._integrity_cache[url] = integrity
                        return integrity
        except Exception:
            # If there's any error fetching the resource, return None
            return None
        
        return None
    
    def _add_integrity_to_html(self, html_content: str) -> str:
        """
        Add integrity attributes to script and link tags in HTML content.
        
        Args:
            html_content: The HTML content to modify
            
        Returns:
            The modified HTML content
        """
        # This is a simple implementation that uses string replacement
        # For production use, consider using a proper HTML parser
        
        # Process script tags
        for url, integrity in self.script_sources.items():
            # Look for script tags with the specified URL
            old_tag = f'<script src="{url}"'
            if old_tag in html_content and 'integrity=' not in old_tag:
                new_tag = f'<script src="{url}" integrity="{integrity}" crossorigin="anonymous"'
                html_content = html_content.replace(old_tag, new_tag)
        
        # Process link tags (for stylesheets)
        for url, integrity in self.style_sources.items():
            # Look for link tags with the specified URL
            old_tag = f'<link rel="stylesheet" href="{url}"'
            if old_tag in html_content and 'integrity=' not in old_tag:
                new_tag = f'<link rel="stylesheet" href="{url}" integrity="{integrity}" crossorigin="anonymous"'
                html_content = html_content.replace(old_tag, new_tag)
        
        return html_content
    
    async def process_request(self, request: Request) -> Request:
        """
        Process a request through the SRI middleware.
        
        Args:
            request: The request to process
            
        Returns:
            The processed request
        """
        # This middleware doesn't modify the request, just passes it through
        return request
    
    async def process_response(self, response: Response) -> Response:
        """
        Process a response through the SRI middleware.
        
        Args:
            response: The response to process
            
        Returns:
            The processed response
        """
        # Check if the request is exempt
        if self._is_exempt(response.request):
            return response

        # Check if the response is HTML
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type and hasattr(response, "body"):
            # Add integrity attributes to script and link tags
            response.body = self._add_integrity_to_html(response.body)
        
        return response


class SRIPolicy:
    """
    Policy for configuring Subresource Integrity.
    """
    
    def __init__(self):
        """
        Initialize the SRI policy.
        """
        self.script_sources = {}
        self.style_sources = {}
        self.algorithms = [SRIHashAlgorithm.SHA384]
        self.verify_external_resources = False
    
    def add_script_source(self, url: str, integrity: Optional[str] = None) -> "SRIPolicy":
        """
        Add a script source to the policy.
        
        Args:
            url: The URL of the script
            integrity: The integrity value (will be computed if None)
            
        Returns:
            The SRI policy instance for chaining
        """
        self.script_sources[url] = integrity
        return self
    
    def add_style_source(self, url: str, integrity: Optional[str] = None) -> "SRIPolicy":
        """
        Add a style source to the policy.
        
        Args:
            url: The URL of the stylesheet
            integrity: The integrity value (will be computed if None)
            
        Returns:
            The SRI policy instance for chaining
        """
        self.style_sources[url] = integrity
        return self
    
    def set_algorithms(self, algorithms: List[SRIHashAlgorithm]) -> "SRIPolicy":
        """
        Set the hash algorithms to use.
        
        Args:
            algorithms: The hash algorithms to use
            
        Returns:
            The SRI policy instance for chaining
        """
        self.algorithms = algorithms
        return self
    
    def enable_verification(self, enable: bool = True) -> "SRIPolicy":
        """
        Enable or disable verification of external resources.
        
        Args:
            enable: Whether to enable verification
            
        Returns:
            The SRI policy instance for chaining
        """
        self.verify_external_resources = enable
        return self
    
    async def compute_missing_integrity_values(self) -> "SRIPolicy":
        """
        Compute integrity values for sources that don't have them.
        
        Returns:
            The SRI policy instance for chaining
        """
        # Compute integrity values for script sources
        for url, integrity in list(self.script_sources.items()):
            if integrity is None:
                self.script_sources[url] = await self._compute_integrity(url)
        
        # Compute integrity values for style sources
        for url, integrity in list(self.style_sources.items()):
            if integrity is None:
                self.style_sources[url] = await self._compute_integrity(url)
        
        return self
    
    async def _compute_integrity(self, url: str) -> Optional[str]:
        """
        Compute the integrity value for a URL.
        
        Args:
            url: The URL to compute the integrity for
            
        Returns:
            The integrity value, or None if it could not be computed
        """
        try:
            # Use a simple HTTP client to fetch the resource
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        return SRIGenerator.generate_integrity_attribute(content, self.algorithms)
        except Exception:
            # If there's any error fetching the resource, return None
            return None
        
        return None


class SRIBuilder:
    """
    Helper class for building SRI policies.
    """
    
    @staticmethod
    def create_common_cdn_policy() -> SRIPolicy:
        """
        Create an SRI policy for common CDN resources.
        
        Returns:
            An SRI policy for common CDN resources
        """
        return (SRIPolicy()
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
            # Font Awesome
            .add_style_source(
                "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
                "sha512-9usAa10IRO0HhonpyAIVpjrylPvoDwiPUiKdWk5t3PyolY1cOd4DSE0Ga+ri4AuTroPR5aQvXU9xC6qOPnzFeg=="
            )
        )
    
    @staticmethod
    def create_empty_policy() -> SRIPolicy:
        """
        Create an empty SRI policy.
        
        Returns:
            An empty SRI policy
        """
        return SRIPolicy()
    
    @staticmethod
    async def create_policy_from_html(html_content: str) -> SRIPolicy:
        """
        Create an SRI policy from HTML content by extracting script and link tags.
        
        Args:
            html_content: The HTML content to extract sources from
            
        Returns:
            An SRI policy with the extracted sources
        """
        policy = SRIPolicy()
        
        # Extract script sources
        import re
        script_pattern = re.compile(r'<script[^>]+src="([^"]+)"[^>]*>')
        for match in script_pattern.finditer(html_content):
            url = match.group(1)
            if url.startswith(("http://", "https://")):
                policy.add_script_source(url)
        
        # Extract style sources
        style_pattern = re.compile(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"[^>]*>')
        for match in style_pattern.finditer(html_content):
            url = match.group(1)
            if url.startswith(("http://", "https://")):
                policy.add_style_source(url)
        
        # Compute integrity values
        await policy.compute_missing_integrity_values()
        
        return policy 