from typing import Dict, List, Optional, Union
import hashlib
import base64
from enum import Enum


class SRIHashAlgorithm(str, Enum):
    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"


def generate_integrity_hash(content: Union[str, bytes], algorithm: SRIHashAlgorithm = SRIHashAlgorithm.SHA384) -> str:
    """
    Generates a Subresource Integrity hash for the given content.
    
    Args:
        content: The content to generate the hash for
        algorithm: The hashing algorithm to use
        
    Returns:
        The integrity hash string
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
        
    hash_func = getattr(hashlib, algorithm.value)
    digest = hash_func(content).digest()
    b64_digest = base64.b64encode(digest).decode('utf-8')
    
    return f"{algorithm.value}-{b64_digest}"


def validate_integrity(content: Union[str, bytes], integrity: str) -> bool:
    """
    Validates that the given content matches the provided integrity hash.
    
    Args:
        content: The content to validate
        integrity: The integrity hash to validate against
        
    Returns:
        True if the content is valid, False otherwise
    """
    if not integrity:
        return False
        
    parts = integrity.split('-', 1)
    if len(parts) != 2:
        return False
        
    algorithm, expected_hash = parts
    
    if algorithm not in [alg.value for alg in SRIHashAlgorithm]:
        return False
        
    calculated_integrity = generate_integrity_hash(content, SRIHashAlgorithm(algorithm))
    return calculated_integrity == integrity


class SRIMiddleware:
    def __init__(
        self, 
        algorithms: Optional[List[SRIHashAlgorithm]] = None,
        script_sources: Optional[Dict[str, str]] = None,
        style_sources: Optional[Dict[str, str]] = None,
        exempt_paths: Optional[List[str]] = None
    ):
        """
        Middleware for adding and verifying Subresource Integrity hashes.
        
        Args:
            algorithms: List of hash algorithms to use
            script_sources: Mapping of script URLs to their content
            style_sources: Mapping of style URLs to their content
            exempt_paths: List of paths that should be exempt from integrity checks
        """
        self.algorithms = algorithms or [SRIHashAlgorithm.SHA384]
        self.script_sources = script_sources or {}
        self.style_sources = style_sources or {}
        self.exempt_paths = exempt_paths or []
        self._integrity_cache: Dict[str, str] = {}

