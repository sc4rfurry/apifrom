"""Tests for the advanced caching module using async/await syntax."""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch

from apifrom.middleware.cache_advanced import CacheBackend

# Create a simple async cache backend for testing
class AsyncTestCacheBackend(CacheBackend):
    """A simple async cache backend for testing."""
    
    def __init__(self):
        self.cache = {}
        
    async def get(self, key):
        """Get a value from the cache."""
        if key not in self.cache:
            return None
        return self.cache[key]
        
    async def set(self, key, value, ttl=None):
        """Set a value in the cache."""
        self.cache[key] = value
        
    async def delete(self, key):
        """Delete a key from the cache."""
        if key in self.cache:
            del self.cache[key]
            
    async def exists(self, key):
        """Check if a key exists in the cache."""
        return key in self.cache

@pytest.mark.asyncio
async def test_async_cache_backend():
    """Test the async cache backend functionality."""
    # Create a cache backend
    backend = AsyncTestCacheBackend()
    
    # Test get (cache miss)
    value = await backend.get("test_key")
    assert value is None
    
    # Test set and get (cache hit)
    test_data = {"data": "value"}
    await backend.set("test_key", test_data)
    
    # Test get after set
    value = await backend.get("test_key")
    assert value == test_data
    
    # Test exists (key exists)
    exists = await backend.exists("test_key")
    assert exists is True
    
    # Test delete
    await backend.delete("test_key")
    
    # Test exists after delete (key does not exist)
    exists = await backend.exists("test_key")
    assert exists is False 