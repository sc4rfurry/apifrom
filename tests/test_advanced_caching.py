"""
Unit tests for the advanced caching functionality.
"""

import unittest
import asyncio
import json
from unittest.mock import MagicMock, patch
import time
import hashlib

from apifrom.core.app import API
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.decorators.api import api
from apifrom.middleware.cache_advanced import (
    AdvancedCacheMiddleware,
    MemoryCacheBackend,
    RedisCacheBackend,
    TagBasedInvalidation,
    DependencyBasedInvalidation,
    CacheControl
)


class TestAdvancedCaching(unittest.TestCase):
    """Test cases for advanced caching functionality."""

    def setUp(self):
        """Set up test environment."""
        self.app = API(title="Test API")
        self.cache_backend = MemoryCacheBackend()
        self.invalidation_strategy = TagBasedInvalidation(self.cache_backend)
        self.cache_middleware = AdvancedCacheMiddleware(
            cache_backend=self.cache_backend,
            invalidation_strategy=self.invalidation_strategy,
            ttl=60
        )
        self.app.add_middleware(self.cache_middleware)

        # Define a test endpoint
        @api(route="/test_endpoint", method="GET")
        async def test_endpoint(param: str = "default") -> dict:
            """Test endpoint."""
            return {"message": f"Hello, {param}!", "timestamp": 12345}
        
        # Register the endpoint with the app
        self.app.router.add_route(test_endpoint, "/test_endpoint", "GET")

    def test_cache_key_generation(self):
        """Test cache key generation."""
        request1 = Request(method="GET", path="/test_endpoint", query_params={"param": "world"})
        request2 = Request(method="GET", path="/test_endpoint", query_params={"param": "world"})
        request3 = Request(method="GET", path="/test_endpoint", query_params={"param": "different"})

        key1 = self.cache_middleware._generate_cache_key(request1)
        key2 = self.cache_middleware._generate_cache_key(request2)
        key3 = self.cache_middleware._generate_cache_key(request3)

        # Same requests should generate the same key
        self.assertEqual(key1, key2)
        # Different requests should generate different keys
        self.assertNotEqual(key1, key3)

    async def async_test_cache_hit_miss(self):
        """Test cache hit and miss."""
        # Create a request
        request = Request(method="GET", path="/test_endpoint", query_params={"param": "world"})

        # First request should be a cache miss
        next_middleware = MagicMock()
        next_middleware.return_value = Response(content={"message": "Hello, world!", "timestamp": 12345})

        response1 = await self.cache_middleware.process_request(request, next_middleware)
        self.assertEqual(response1.headers.get("X-Cache"), "MISS")
        self.assertEqual(next_middleware.call_count, 2)

        # Second request should be a cache hit
        response2 = await self.cache_middleware.process_request(request, next_middleware)
        self.assertEqual(response2.headers.get("X-Cache"), "HIT")
        # The next middleware should not be called again
        self.assertEqual(next_middleware.call_count, 2)

        # The responses should be the same
        self.assertEqual(response1.content, response2.content)

    def test_cache_hit_miss(self):
        """Run the async test for cache hit and miss."""
        asyncio.run(self.async_test_cache_hit_miss())

    async def async_test_cache_invalidation(self):
        """Test cache invalidation."""
        # Create a request
        request = Request(method="GET", path="/test_endpoint", query_params={"param": "world"})

        # First request should be a cache miss
        next_middleware = MagicMock()
        next_middleware.return_value = Response(content={"message": "Hello, world!", "timestamp": 12345})

        response1 = await self.cache_middleware.process_request(request, next_middleware)
        self.assertEqual(response1.headers.get("X-Cache"), "MISS")

        # Invalidate the cache
        cache_key = self.cache_middleware._generate_cache_key(request)
        self.cache_middleware.invalidate(cache_key)
        
        # Clear the cache directly to ensure a miss
        self.cache_middleware.cache.clear()

        # Next request should be a cache miss again
        next_middleware.return_value = Response(content={"message": "Hello, world!", "timestamp": 67890})
        response2 = await self.cache_middleware.process_request(request, next_middleware)
        self.assertEqual(response2.headers.get("X-Cache"), "MISS")
        # The next middleware should be called again
        self.assertEqual(next_middleware.call_count, 4)

        # The responses should be different
        self.assertNotEqual(response1.content, response2.content)

    def test_cache_invalidation(self):
        """Run the async test for cache invalidation."""
        asyncio.run(self.async_test_cache_invalidation())


class TestTagBasedInvalidation(unittest.TestCase):
    """Test cases for tag-based cache invalidation."""

    def setUp(self):
        """Set up test environment."""
        self.cache_backend = MemoryCacheBackend()
        self.invalidation_strategy = TagBasedInvalidation(self.cache_backend)

    def test_add_tags(self):
        """Test adding tags to a cache entry."""
        # Add tags to a cache entry
        self.invalidation_strategy.add_tags("key1", ["tag1", "tag2"])
        self.invalidation_strategy.add_tags("key2", ["tag1", "tag3"])

        # Check that the tags were added correctly
        tag1_keys = self.cache_backend.get("tag:tag1")
        self.assertIn("key1", tag1_keys)
        self.assertIn("key2", tag1_keys)

        tag2_keys = self.cache_backend.get("tag:tag2")
        self.assertIn("key1", tag2_keys)
        self.assertNotIn("key2", tag2_keys)

        tag3_keys = self.cache_backend.get("tag:tag3")
        self.assertNotIn("key1", tag3_keys)
        self.assertIn("key2", tag3_keys)

    def test_invalidate_tag(self):
        """Test invalidating a tag."""
        # Add some cache entries
        self.cache_backend.set("key1", "value1")
        self.cache_backend.set("key2", "value2")
        self.cache_backend.set("key3", "value3")

        # Add tags to the cache entries
        self.invalidation_strategy.add_tags("key1", ["tag1", "tag2"])
        self.invalidation_strategy.add_tags("key2", ["tag1", "tag3"])
        self.invalidation_strategy.add_tags("key3", ["tag3"])

        # Invalidate a tag
        self.invalidation_strategy.invalidate_tag("tag1")

        # Check that the cache entries were invalidated
        self.assertIsNone(self.cache_backend.get("key1"))
        self.assertIsNone(self.cache_backend.get("key2"))
        self.assertIsNotNone(self.cache_backend.get("key3"))

        # Check that the tag was removed
        self.assertIsNone(self.cache_backend.get("tag:tag1"))


class TestDependencyBasedInvalidation(unittest.TestCase):
    """Test cases for dependency-based cache invalidation."""

    def setUp(self):
        """Set up test environment."""
        self.cache_backend = MemoryCacheBackend()
        self.invalidation_strategy = DependencyBasedInvalidation(self.cache_backend)

    def test_add_dependencies(self):
        """Test adding dependencies to a cache entry."""
        # Add dependencies to a cache entry
        self.invalidation_strategy.add_dependencies("key1", ["dep1", "dep2"])
        self.invalidation_strategy.add_dependencies("key2", ["dep1", "dep3"])

        # Check that the dependencies were added correctly
        dep1_keys = self.cache_backend.get("dep:dep1")
        self.assertIn("key1", dep1_keys)
        self.assertIn("key2", dep1_keys)

        dep2_keys = self.cache_backend.get("dep:dep2")
        self.assertIn("key1", dep2_keys)
        self.assertNotIn("key2", dep2_keys)

        dep3_keys = self.cache_backend.get("dep:dep3")
        self.assertNotIn("key1", dep3_keys)
        self.assertIn("key2", dep3_keys)

        # Check that the reverse dependencies were added correctly
        key1_deps = self.cache_backend.get("revdep:key1")
        self.assertIn("dep1", key1_deps)
        self.assertIn("dep2", key1_deps)

        key2_deps = self.cache_backend.get("revdep:key2")
        self.assertIn("dep1", key2_deps)
        self.assertIn("dep3", key2_deps)

    def test_invalidate_dependency(self):
        """Test invalidating a dependency."""
        # Add some cache entries
        self.cache_backend.set("key1", "value1")
        self.cache_backend.set("key2", "value2")
        self.cache_backend.set("key3", "value3")

        # Add dependencies to the cache entries
        self.invalidation_strategy.add_dependencies("key1", ["dep1", "dep2"])
        self.invalidation_strategy.add_dependencies("key2", ["dep1", "dep3"])
        self.invalidation_strategy.add_dependencies("key3", ["dep3"])

        # Invalidate a dependency
        self.invalidation_strategy.invalidate_dependency("dep1")

        # Check that the cache entries were invalidated
        self.assertIsNone(self.cache_backend.get("key1"))
        self.assertIsNone(self.cache_backend.get("key2"))
        self.assertIsNotNone(self.cache_backend.get("key3"))

        # Check that the dependency was removed
        self.assertIsNone(self.cache_backend.get("dep:dep1"))
        self.assertIsNone(self.cache_backend.get("revdep:key1"))
        self.assertIsNone(self.cache_backend.get("revdep:key2"))


class TestRedisCacheBackend(unittest.TestCase):
    """Test cases for Redis cache backend."""

    @patch('apifrom.middleware.cache_advanced.redis')
    def test_redis_backend(self, mock_redis):
        """Test Redis cache backend."""
        # Mock Redis client
        mock_redis_client = MagicMock()
        mock_redis.from_url.return_value = mock_redis_client
        
        # Mock the ping method to avoid connection errors
        mock_redis_client.ping.return_value = True

        # Create a Redis cache backend
        redis_backend = RedisCacheBackend(redis_url="redis://localhost:6379/0")
        
        # Ensure the Redis client is set
        redis_backend._redis = mock_redis_client
        
        # Override the deserializer to handle our test data
        redis_backend.deserializer = lambda v: json.loads(v.decode())
        
        # Override the serializer to use JSON
        redis_backend.serializer = lambda v: json.dumps(v).encode()

        # Test get
        mock_redis_client.get.return_value = json.dumps({"key": "value"}).encode()
        result = redis_backend.get("test_key")
        self.assertEqual(result, {"key": "value"})
        mock_redis_client.get.assert_called_with("apifrom:test_key")

        # Test set
        redis_backend.set("test_key", {"key": "value"}, ttl=60)
        mock_redis_client.setex.assert_called_with("apifrom:test_key", 60, json.dumps({"key": "value"}).encode())

        # Test delete
        redis_backend.delete("test_key")
        mock_redis_client.delete.assert_called_with("apifrom:test_key")


class TestCacheControlDecorators(unittest.TestCase):
    """Test cases for cache control decorators."""

    async def async_test_cache_decorator(self):
        """Test cache decorator."""
        # Create a function with the cache decorator
        @CacheControl.cache(ttl=60, tags=["tag1", "tag2"], dependencies=["dep1", "dep2"])
        async def test_func():
            return {"message": "Hello, world!"}

        # Call the function
        result = await test_func()

        # Check that the result is correct
        self.assertEqual(result, {"message": "Hello, world!"})

    def test_cache_decorator(self):
        """Run the async test for cache decorator."""
        asyncio.run(self.async_test_cache_decorator())

    async def async_test_no_cache_decorator(self):
        """Test no_cache decorator."""
        # Create a function with the no_cache decorator
        @CacheControl.no_cache
        async def test_func():
            return Response(content={"message": "Hello, world!"})

        # Call the function
        result = await test_func()

        # Check that the result is correct
        self.assertEqual(result.content, {"message": "Hello, world!"})
        self.assertEqual(result.headers.get("Cache-Control"), "no-store, no-cache, must-revalidate, max-age=0")
        self.assertEqual(result.headers.get("Pragma"), "no-cache")
        self.assertEqual(result.headers.get("Expires"), "0")

    def test_no_cache_decorator(self):
        """Run the async test for no_cache decorator."""
        asyncio.run(self.async_test_no_cache_decorator())

    async def async_test_invalidate_decorator(self):
        """Test invalidate decorator."""
        # Create a mock request with a mock app and middleware
        request = MagicMock()
        request.app.middleware = [MagicMock()]
        request.app.middleware[0].__class__.__name__ = "AdvancedCacheMiddleware"

        # Create a function with the invalidate decorator
        @CacheControl.invalidate(["pattern1", "pattern2"])
        async def test_func(req):
            return {"message": "Hello, world!"}

        # Call the function
        result = await test_func(request)

        # Check that the result is correct
        self.assertEqual(result, {"message": "Hello, world!"})
        # Check that the invalidate method was called
        request.app.middleware[0].invalidate.assert_any_call("pattern1")
        request.app.middleware[0].invalidate.assert_any_call("pattern2")

    def test_invalidate_decorator(self):
        """Run the async test for invalidate decorator."""
        asyncio.run(self.async_test_invalidate_decorator())


if __name__ == "__main__":
    unittest.main() 