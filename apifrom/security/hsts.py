"""
HTTP Strict Transport Security (HSTS) implementation for APIFromAnything.

This module provides utilities for implementing HSTS preloading to ensure
that browsers always use HTTPS for your API.
"""

from typing import Callable, Dict, List, Optional, Set, Union

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware.base import BaseMiddleware


class HSTSMiddleware(BaseMiddleware):
    """
    Middleware for implementing HTTP Strict Transport Security (HSTS).
    
    This middleware adds the Strict-Transport-Security header to responses
    to instruct browsers to only use HTTPS for your API.
    """
    
    def __init__(
        self,
        max_age: int = 31536000,  # 1 year in seconds
        include_subdomains: bool = True,
        preload: bool = False,
        force_https_redirect: bool = True,
        exempt_paths: Optional[List[str]] = None,
    ):
        """
        Initialize the HSTS middleware.
        
        Args:
            max_age: The time, in seconds, that the browser should remember that a site is only to be accessed using HTTPS
            include_subdomains: Whether the HSTS policy applies to all subdomains
            preload: Whether to include the site in the HSTS preload list
            force_https_redirect: Whether to redirect HTTP requests to HTTPS
            exempt_paths: Paths exempt from HSTS
        """
        super().__init__()
        self.max_age = max_age
        self.include_subdomains = include_subdomains
        self.preload = preload
        self.force_https_redirect = force_https_redirect
        self.exempt_paths = exempt_paths or []
    
    def _is_exempt(self, request: Request) -> bool:
        """
        Check if a request is exempt from HSTS.
        
        Args:
            request: The request to check
            
        Returns:
            True if the request is exempt, False otherwise
        """
        for path in self.exempt_paths:
            if request.path.startswith(path):
                return True
        
        return False
    
    def _build_hsts_header(self) -> str:
        """
        Build the Strict-Transport-Security header value.
        
        Returns:
            The header value
        """
        header = f"max-age={self.max_age}"
        
        if self.include_subdomains:
            header += "; includeSubDomains"
            
        if self.preload:
            header += "; preload"
            
        return header
    
    def _add_hsts_header(self, response: Response) -> None:
        """
        Add the Strict-Transport-Security header to a response.

        Args:
            response: The response to add the header to
        """
        response.headers["Strict-Transport-Security"] = self._build_hsts_header()
    
    def _is_https(self, request: Request) -> bool:
        """
        Check if a request is using HTTPS.
        
        Args:
            request: The request to check
            
        Returns:
            True if the request is using HTTPS, False otherwise
        """
        # Check the X-Forwarded-Proto header (common in reverse proxies)
        forwarded_proto = request.headers.get("X-Forwarded-Proto")
        if forwarded_proto:
            return forwarded_proto.lower() == "https"
        
        # Check the request scheme
        return request.url.scheme.lower() == "https"
    
    def _get_https_redirect_url(self, request: Request) -> str:
        """
        Get the HTTPS redirect URL for a request.
        
        Args:
            request: The request to redirect
            
        Returns:
            The HTTPS redirect URL
        """
        # Replace the scheme with https
        url = str(request.url)
        if url.startswith("http:"):
            url = "https:" + url[5:]
        
        return url
    
    async def process_request(self, request: Request) -> Request:
        """
        Process a request through the HSTS middleware.
        
        Args:
            request: The request to process
            
        Returns:
            The processed request
        """
        # Check if the request is exempt
        if self._is_exempt(request):
            return request
        
        # Check if the request is using HTTPS
        if not self._is_https(request) and self.force_https_redirect:
            # Redirect to HTTPS
            redirect_url = self._get_https_redirect_url(request)
            # Store the redirect information in the request state
            request.state.hsts_redirect = True
            request.state.hsts_redirect_url = redirect_url
        
        return request
    
    async def process_response(self, response: Response) -> Response:
        """
        Process a response through the HSTS middleware.
        
        Args:
            response: The response to process
            
        Returns:
            The processed response
        """
        # Check if we need to redirect to HTTPS
        if hasattr(response.request.state, 'hsts_redirect') and response.request.state.hsts_redirect:
            redirect_response = Response(status_code=301)
            redirect_response.headers["Location"] = response.request.state.hsts_redirect_url
            return redirect_response
        
        # Check if the request is exempt
        if self._is_exempt(response.request):
            return response
        
        # Add the HSTS header if the request is using HTTPS
        if self._is_https(response.request):
            self._add_hsts_header(response)
        
        return response


class HSTSPreloadChecker:
    """
    Utility for checking if a domain is eligible for HSTS preloading.
    
    This class provides methods to check if a domain meets the requirements
    for inclusion in the HSTS preload list.
    """
    
    @staticmethod
    def check_eligibility(
        domain: str,
        hsts_header: str,
        has_valid_certificate: bool = True,
        all_subdomains_https: bool = False,
        redirect_to_https: bool = True,
    ) -> Dict[str, Union[bool, str]]:
        """
        Check if a domain is eligible for HSTS preloading.
        
        Args:
            domain: The domain to check
            hsts_header: The Strict-Transport-Security header value
            has_valid_certificate: Whether the domain has a valid SSL/TLS certificate
            all_subdomains_https: Whether all subdomains support HTTPS
            redirect_to_https: Whether the domain redirects HTTP to HTTPS
            
        Returns:
            A dictionary with the eligibility status and any issues
        """
        issues = []
        
        # Check if the domain has a valid certificate
        if not has_valid_certificate:
            issues.append("Domain does not have a valid SSL/TLS certificate")
        
        # Check if the domain redirects to HTTPS
        if not redirect_to_https:
            issues.append("Domain does not redirect HTTP to HTTPS")
        
        # Check if the HSTS header is present and valid
        if not hsts_header:
            issues.append("Strict-Transport-Security header is missing")
        else:
            # Check max-age
            if "max-age=" not in hsts_header:
                issues.append("max-age directive is missing from HSTS header")
            else:
                try:
                    max_age_str = hsts_header.split("max-age=")[1].split(";")[0].strip()
                    max_age = int(max_age_str)
                    if max_age < 10886400:  # 18 weeks in seconds
                        issues.append(f"max-age is too short: {max_age} seconds (minimum is 18 weeks)")
                except (ValueError, IndexError):
                    issues.append("Invalid max-age value in HSTS header")
            
            # Check includeSubDomains
            if "includeSubDomains" not in hsts_header:
                issues.append("includeSubDomains directive is missing from HSTS header")
            
            # Check preload
            if "preload" not in hsts_header:
                issues.append("preload directive is missing from HSTS header")
        
        # Check if all subdomains support HTTPS
        if not all_subdomains_https:
            issues.append("Not all subdomains support HTTPS")
        
        # Determine eligibility
        eligible = len(issues) == 0
        
        return {
            "eligible": eligible,
            "issues": issues,
            "domain": domain,
            "hsts_header": hsts_header,
        }
    
    @staticmethod
    def get_submission_instructions(domain: str) -> str:
        """
        Get instructions for submitting a domain to the HSTS preload list.
        
        Args:
            domain: The domain to submit
            
        Returns:
            Instructions for submitting the domain
        """
        # Validate and sanitize the domain to prevent injection attacks
        import re
        
        # Ensure domain is a valid domain name
        if not domain or not isinstance(domain, str):
            domain = "example.com"  # Default fallback
        
        # Strict domain validation pattern
        domain_pattern = re.compile(r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$', re.IGNORECASE)
        
        if not domain_pattern.match(domain):
            # If domain doesn't match the pattern, use a safe default
            domain = "example.com"
        
        return f"""
To submit {domain} to the HSTS preload list:

1. Ensure your domain meets all the requirements:
   - Serves all subdomains over HTTPS
   - Redirects from HTTP to HTTPS
   - Has a valid SSL/TLS certificate
   - Has an HSTS header with:
     - max-age of at least 31536000 seconds (1 year)
     - includeSubDomains directive
     - preload directive

2. Visit https://hstspreload.org/ and enter your domain.

3. Follow the instructions to submit your domain.

4. Wait for your domain to be added to the preload list.
   This can take several months, as it needs to be included in browser releases.

5. Once your domain is in the preload list, browsers will always use HTTPS
   for your domain and all subdomains, even on the first visit.

Note: Be careful when enabling HSTS preloading. Once your domain is in the
preload list, it can be difficult to remove, and all subdomains must support
HTTPS indefinitely.
""" 