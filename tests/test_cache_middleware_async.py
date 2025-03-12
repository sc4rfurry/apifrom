"""
Tests for the Cache middleware using async/await syntax.
"""

import pytest
import time
import json
from unittest.mock import AsyncMock, patch

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware.cache import CacheMiddleware, MemoryCache
from tests.middleware_test_helper import AsyncMiddlewareTester, MockRequest, MockResponse


class TestMemoryCacheAsync:
    """
    Tests for the MemoryCache class using async/await syntax.
    """

    def test_get_set(self):
        """Test getting and setting values in the cache"""
        cache = MemoryCache(ttl=10)
        
        # Set a value
        cache.set("test_key", "test_value")
        
        # Get the value
        value = cache.get("test_key")
        assert value == "test_value"
        
        # Get a non-existent key
        value = cache.get("non_existent_key")
        assert value is None
    
    def test_ttl_expiration(self):
        """Test that values expire after TTL"""
        cache = MemoryCache(ttl=1)  # 1 second TTL
        
        # Set a value
        cache.set("test_key", "test_value")
        
        # Value should exist initially
        value = cache.get("test_key")
        assert value == "test_value"
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Value should be gone
        value = cache.get("test_key")
        assert value is None
    
    def test_max_size(self):
        """Test that the cache respects max_size"""
        cache = MemoryCache(max_size=2, ttl=10)
        
        # Set two values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Both should exist
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        
        # Add a third value
        cache.set("key3", "value3")
        
        # One of the original keys should be gone (the oldest one)
        assert (cache.get("key1") is None or cache.get("key2") is None)
        assert cache.get("key3") == "value3"
    
    def test_delete(self):
        """Test deleting values from the cache"""
        cache = MemoryCache()
        
        # Set a value
        cache.set("test_key", "test_value")
        
        # Delete it
        cache.delete("test_key")
        
        # Should be gone
        assert cache.get("test_key") is None
        
        # Deleting a non-existent key should not error
        cache.delete("non_existent_key")
    
    def test_clear(self):
        """Test clearing the entire cache"""
        cache = MemoryCache()
        
        # Set multiple values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Clear the cache
        cache.clear()
        
        # All values should be gone
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestCacheMiddlewareAsync:
    """
    Tests for the CacheMiddleware class using async/await syntax.
    """
    
    @pytest.fixture
    def cache(self):
        """Fixture for creating a memory cache"""
        return MemoryCache(ttl=10)
    
    @pytest.fixture
    def cache_middleware(self, cache):
        """Fixture for creating a cache middleware"""
        return CacheMiddleware(
            cache_backend=cache,
            ttl=10,
            methods=["GET"],
            exclude_routes=["/no-cache"],
            vary_headers=["Accept"],
            key_prefix="test-cache:"
        )
    
    @pytest.mark.asyncio
    async def test_should_cache(self, cache_middleware):
        """Test the _should_cache method"""
        # Should cache GET requests
        request = MockRequest(method="GET", path="/test")
        assert cache_middleware._should_cache(request) is True
        
        # Should not cache POST requests
        request = MockRequest(method="POST", path="/test")
        assert cache_middleware._should_cache(request) is False
        
        # Should not cache excluded routes
        request = MockRequest(method="GET", path="/no-cache/test")
        assert cache_middleware._should_cache(request) is False
        
        # Should not cache requests with Cache-Control: no-cache
        request = MockRequest(method="GET", path="/test", headers={"Cache-Control": "no-cache"})
        assert cache_middleware._should_cache(request) is False
    
    @pytest.mark.asyncio
    async def test_generate_cache_key(self, cache_middleware):
        """Test the _generate_cache_key method"""
        # Basic key
        request = MockRequest(method="GET", path="/test")
        key = cache_middleware._generate_cache_key(request)
        assert key.startswith("test-cache:")
        
        # Key with query params
        request = MockRequest(method="GET", path="/test", query_params={"q": "test"})
        key_with_params = cache_middleware._generate_cache_key(request)
        assert key_with_params != key  # Should be different
        
        # Key with vary headers
        request = MockRequest(method="GET", path="/test", headers={"Accept": "application/json"})
        key_with_headers = cache_middleware._generate_cache_key(request)
        assert key_with_headers != key  # Should be different
    
    @pytest.mark.asyncio
    async def test_process_request(self, cache_middleware, cache):
        """Test the process_request method"""
        # Create a request
        request = MockRequest(method="GET", path="/test")
        
        # Process the request (first time, not cached)
        processed_request = await AsyncMiddlewareTester.test_process_request(cache_middleware, request)
        
        # Should set state attributes
        assert processed_request.state.should_cache is True
        assert hasattr(processed_request.state, "cache_key")
        assert not hasattr(processed_request.state, "cached_response")
        
        # Create a cached response
        response = MockResponse(status_code=200, body={"data": "test"})
        response.request = processed_request
        
        # Process the response to cache it
        await cache_middleware.process_response(response)
        
        # Process a new request (should be cached now)
        new_request = MockRequest(method="GET", path="/test")
        processed_request = await AsyncMiddlewareTester.test_process_request(cache_middleware, new_request)
        
        # Should have a cached response
        assert hasattr(processed_request.state, "cached_response")
        assert processed_request.state.cached_response.headers["X-Cache"] == "HIT"
    
    @pytest.mark.asyncio
    async def test_process_response(self, cache_middleware):
        """Test the process_response method"""
        # Create a request and response
        request = MockRequest(method="GET", path="/test")
        response = MockResponse(status_code=200, body={"data": "test"})
        response.request = request
        
        # Set up the request state
        request.state.should_cache = True
        request.state.cache_key = cache_middleware._generate_cache_key(request)
        
        # Process the response
        processed_response = await cache_middleware.process_response(response)
        
        # Should add X-Cache header
        assert processed_response.headers["X-Cache"] == "MISS"
        
        # Process another request to get the cached response
        new_request = MockRequest(method="GET", path="/test")
        await AsyncMiddlewareTester.test_process_request(cache_middleware, new_request)
        
        # Should have a cached response with HIT header
        assert new_request.state.cached_response.headers["X-Cache"] == "HIT"
    
    @pytest.mark.asyncio
    async def test_middleware_chain(self, cache_middleware):
        """Test the middleware in a chain"""
        # Create a request
        request = MockRequest(method="GET", path="/test")
        
        # Create a response
        response = MockResponse(status_code=200, body={"data": "test"})
        
        # Process through the middleware chain
        processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [cache_middleware], response, request
        )
        
        # Should add X-Cache header
        assert processed_response.headers["X-Cache"] == "MISS"
        
        # Process again to get from cache
        new_request = MockRequest(method="GET", path="/test")
        new_response = MockResponse(status_code=200)
        
        processed_response = await AsyncMiddlewareTester.test_middleware_chain_with_response(
            [cache_middleware], new_response, new_request
        )
        
        # Should be a cache hit
        assert processed_response.headers["X-Cache"] == "HIT"
    
    @pytest.mark.asyncio
    async def test_no_cache_for_non_get(self, cache_middleware):
        """Test that non-GET requests are not cached"""
        # Create a POST request
        request = MockRequest(method="POST", path="/test")
        
        # Process the request
        processed_request = await AsyncMiddlewareTester.test_process_request(cache_middleware, request)
        
        # Should set should_cache to False
        assert processed_request.state.should_cache is False
        
        # Create a response
        response = MockResponse(status_code=200, body={"data": "test"})
        response.request = processed_request
        
        # Process the response
        processed_response = await cache_middleware.process_response(response)
        
        # Should not add X-Cache header
        assert "X-Cache" not in processed_response.headers
    
    @pytest.mark.asyncio
    async def test_no_cache_for_excluded_route(self, cache_middleware):
        """Test that excluded routes are not cached"""
        # Create a request for an excluded route
        request = MockRequest(method="GET", path="/no-cache/test")
        
        # Process the request
        processed_request = await AsyncMiddlewareTester.test_process_request(cache_middleware, request)
        
        # Should set should_cache to False
        assert processed_request.state.should_cache is False
    
    @pytest.mark.asyncio
    async def test_vary_headers(self, cache_middleware):
        """Test that vary headers affect the cache key"""
        # Create two requests with different Accept headers
        request1 = MockRequest(method="GET", path="/test", headers={"Accept": "application/json"})
        request2 = MockRequest(method="GET", path="/test", headers={"Accept": "text/html"})
        
        # Process the first request
        processed_request1 = await AsyncMiddlewareTester.test_process_request(cache_middleware, request1)
        
        # Create a response
        response1 = MockResponse(status_code=200, body={"format": "json"})
        response1.request = processed_request1
        
        # Process the response to cache it
        await cache_middleware.process_response(response1)
        
        # Process the second request
        processed_request2 = await AsyncMiddlewareTester.test_process_request(cache_middleware, request2)
        
        # Should not have a cached response (different key due to Accept header)
        assert not hasattr(processed_request2.state, "cached_response")
        
        # Create a second response
        response2 = MockResponse(status_code=200, body={"format": "html"})
        response2.request = processed_request2
        
        # Process the response to cache it
        await cache_middleware.process_response(response2)
        
        # Process the first request again
        new_request1 = MockRequest(method="GET", path="/test", headers={"Accept": "application/json"})
        processed_new_request1 = await AsyncMiddlewareTester.test_process_request(cache_middleware, new_request1)
        
        # Should have a cached response with the correct body
        assert hasattr(processed_new_request1.state, "cached_response")
        
        # The body might be serialized to JSON, so we need to handle that
        cached_body = processed_new_request1.state.cached_response.body
        if isinstance(cached_body, bytes):
            # If it's bytes, try to decode and parse as JSON
            try:
                cached_body = json.loads(cached_body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        
        assert cached_body.get("format") == "json" 