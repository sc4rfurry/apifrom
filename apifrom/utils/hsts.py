from typing import List, Optional, Dict, Union, Any

class HSTSUtils:
    """
    Utility class for HTTP Strict Transport Security (HSTS) header management.
    """
    
    @staticmethod
    def build_hsts_header(
        max_age: int = 31536000,
        include_subdomains: bool = True,
        preload: bool = False,
        exempt_paths: Optional[List[str]] = None
    ) -> str:
        """
        Build an HSTS header value.
        
        Args:
            max_age: Maximum time (in seconds) browsers should remember this site is HTTPS only
            include_subdomains: Whether the HSTS policy applies to all subdomains
            preload: Whether the site should be included in browser preload lists
            exempt_paths: List of paths that should be exempt from HSTS
            
        Returns:
            HSTS header value string
        """
        header_parts = [f"max-age={max_age}"]
        
        if include_subdomains:
            header_parts.append("includeSubDomains")
            
        if preload:
            header_parts.append("preload")
            
        return "; ".join(header_parts)
    
    @staticmethod
    def should_apply_hsts(
        path: str,
        exempt_paths: Optional[List[str]] = None
    ) -> bool:
        """
        Determine whether HSTS should be applied based on the request path.
        
        Args:
            path: The request path
            exempt_paths: List of paths that should be exempt from HSTS
            
        Returns:
            Boolean indicating whether HSTS should be applied
        """
        if exempt_paths is None:
            return True
            
        for exempt_path in exempt_paths:
            if path.startswith(exempt_path):
                return False
                
        return True
    
    @staticmethod
    def get_hsts_directives(header_value: str) -> Dict[str, Union[bool, str, int]]:
        """
        Parse HSTS header value into directives.
        
        Args:
            header_value: HSTS header value string
            
        Returns:
            Dictionary of directives
        """
        directives: Dict[str, Union[bool, str, int]] = {}
        
        if not header_value:
            return directives
            
        parts = [part.strip() for part in header_value.split(";")]
        
        for part in parts:
            if not part:
                continue
                
            if "=" in part:
                key, value = part.split("=", 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == "max-age":
                    try:
                        directives[key] = int(value)
                    except ValueError:
                        directives[key] = 0
                else:
                    directives[key] = value
            else:
                directives[part.strip().lower()] = True
                
        return directives

