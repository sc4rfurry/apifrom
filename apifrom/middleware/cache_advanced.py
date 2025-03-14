"""
Advanced caching middleware for APIFromAnything.

This module provides enhanced caching functionality with various backends,
eviction policies, and optimization features.
"""

import time
import json
import logging
import hashlib
import inspect
import asyncio
import redis
from typing import Dict, List, Any, Optional, Union, Callable, Tuple, Set, TypeVar
import threading
import os
import pickle
from datetime import datetime
from functools import wraps

from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.middleware.base import Middleware


# Set up logging
logger = logging.getLogger("apifrom.middleware.cache_advanced")


class CacheItem:
    """
    Represents an item in the cache with metadata.
    
    Attributes:
        key: The cache key
        value: The cached value
        expires_at: The expiration timestamp
        created_at: The creation timestamp
        last_accessed_at: The last access timestamp
        access_count: The number of times the item has been accessed
        size_bytes: The size of the item in bytes
    """
    
    def __init__(
        self,
        key: str,
        value: Any,
        ttl: int = 60,
        created_at: Optional[float] = None,
    ):
        """
        Initialize a cache item.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds
            created_at: Creation timestamp (defaults to now)
        """
        self.key = key
        self.value = value
        self.created_at = created_at or time.time()
        self.expires_at = self.created_at + ttl
        self.last_accessed_at = self.created_at
        self.access_count = 0
        
        # Estimate the size in bytes
        try:
            self.size_bytes = len(pickle.dumps(value))
        except:
            self.size_bytes = 0
    
    def access(self) -> None:
        """Update the last accessed time and access count."""
        self.last_accessed_at = time.time()
        self.access_count += 1
    
    def is_expired(self) -> bool:
        """
        Check if the item is expired.
        
        Returns:
            True if the item is expired, False otherwise
        """
        return time.time() > self.expires_at
    
    def get_age_seconds(self) -> float:
        """
        Get the age of the item in seconds.
        
        Returns:
            The age in seconds
        """
        return time.time() - self.created_at
    
    def get_idle_time_seconds(self) -> float:
        """
        Get the idle time of the item in seconds.
        
        Returns:
            The idle time in seconds
        """
        return time.time() - self.last_accessed_at
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the cache item to a dictionary.
        
        Returns:
            A dictionary representation of the cache item
        """
        return {
            "key": self.key,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "last_accessed_at": self.last_accessed_at,
            "access_count": self.access_count,
            "size_bytes": self.size_bytes,
            "ttl_seconds": self.expires_at - self.created_at,
            "remaining_ttl_seconds": max(0, self.expires_at - time.time()),
            "age_seconds": self.get_age_seconds(),
            "idle_time_seconds": self.get_idle_time_seconds(),
        }


class CacheEvictionPolicy:
    """Base class for cache eviction policies."""
    
    def select_items_to_evict(self, items: List[CacheItem], target_size: int) -> List[CacheItem]:
        """
        Select items to evict to reach the target size.
        
        Args:
            items: The list of cache items
            target_size: The target number of items to keep
            
        Returns:
            A list of items to evict
        """
        raise NotImplementedError("Subclasses must implement select_items_to_evict")


class LRUEvictionPolicy(CacheEvictionPolicy):
    """Least Recently Used (LRU) eviction policy."""
    
    def select_items_to_evict(self, items: List[CacheItem], target_size: int) -> List[CacheItem]:
        """
        Select items to evict based on the LRU policy.
        
        Args:
            items: The list of cache items
            target_size: The target number of items to keep
            
        Returns:
            A list of items to evict
        """
        # Sort items by last_accessed_at (oldest first)
        sorted_items = sorted(items, key=lambda item: item.last_accessed_at)
        
        # Return items to evict to reach the target size
        items_to_keep = min(target_size, len(sorted_items))
        return sorted_items[:-items_to_keep] if items_to_keep > 0 else sorted_items


class LFUEvictionPolicy(CacheEvictionPolicy):
    """Least Frequently Used (LFU) eviction policy."""
    
    def select_items_to_evict(self, items: List[CacheItem], target_size: int) -> List[CacheItem]:
        """
        Select items to evict based on the LFU policy.
        
        Args:
            items: The list of cache items
            target_size: The target number of items to keep
            
        Returns:
            A list of items to evict
        """
        # Sort items by access count (fewest first)
        sorted_items = sorted(items, key=lambda item: item.access_count)
        
        # Return items to evict to reach the target size
        items_to_keep = min(target_size, len(sorted_items))
        return sorted_items[:-items_to_keep] if items_to_keep > 0 else sorted_items


class TTLEvictionPolicy(CacheEvictionPolicy):
    """Time-To-Live (TTL) eviction policy."""
    
    def select_items_to_evict(self, items: List[CacheItem], target_size: int) -> List[CacheItem]:
        """
        Select items to evict based on the TTL policy.
        
        Args:
            items: The list of cache items
            target_size: The target number of items to keep
            
        Returns:
            A list of items to evict
        """
        # Sort items by expiration time (soonest first)
        sorted_items = sorted(items, key=lambda item: item.expires_at)
        
        # Return items to evict to reach the target size
        items_to_keep = min(target_size, len(sorted_items))
        return sorted_items[:-items_to_keep] if items_to_keep > 0 else sorted_items


class SizeEvictionPolicy(CacheEvictionPolicy):
    """Size-based eviction policy."""
    
    def select_items_to_evict(self, items: List[CacheItem], target_size: int) -> List[CacheItem]:
        """
        Select items to evict based on size.
        
        Args:
            items: The list of cache items
            target_size: The target number of items to keep
            
        Returns:
            A list of items to evict
        """
        # Sort items by size (largest first)
        sorted_items = sorted(items, key=lambda item: item.size_bytes, reverse=True)
        
        # Return items to evict to reach the target size
        items_to_keep = min(target_size, len(sorted_items))
        return sorted_items[:-items_to_keep] if items_to_keep > 0 else sorted_items


class HybridEvictionPolicy(CacheEvictionPolicy):
    """Hybrid eviction policy combining multiple factors."""
    
    def select_items_to_evict(self, items: List[CacheItem], target_size: int) -> List[CacheItem]:
        """
        Select items to evict based on a hybrid policy.
        
        Args:
            items: The list of cache items
            target_size: The target number of items to keep
            
        Returns:
            A list of items to evict
        """
        # Calculate a score for each item (lower is better to keep)
        now = time.time()
        for item in items:
            # Normalize factors to [0, 1] range
            ttl_factor = max(0, min(1, (item.expires_at - now) / 3600))  # 1 hour max
            recency_factor = max(0, min(1, (now - item.last_accessed_at) / 3600))  # 1 hour max
            frequency_factor = max(0, min(1, 1 / (item.access_count + 1)))  # Inverse of count
            size_factor = max(0, min(1, item.size_bytes / (1024 * 1024)))  # 1 MB max
            
            # Calculate weighted score
            item.score = (
                0.3 * ttl_factor + 
                0.3 * recency_factor + 
                0.2 * frequency_factor + 
                0.2 * size_factor
            )
        
        # Sort items by score (highest first, as they are worse to keep)
        sorted_items = sorted(items, key=lambda item: getattr(item, "score", 0), reverse=True)
        
        # Return items to evict to reach the target size
        items_to_keep = min(target_size, len(sorted_items))
        return sorted_items[:-items_to_keep] if items_to_keep > 0 else sorted_items


class CacheBackend:
    """Base class for cache backends."""
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value, or None if not found
        """
        raise NotImplementedError("Subclasses must implement get")
    
    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds
        """
        raise NotImplementedError("Subclasses must implement set")
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key was deleted, False otherwise
        """
        raise NotImplementedError("Subclasses must implement delete")
    
    def clear(self) -> None:
        """Clear the cache."""
        raise NotImplementedError("Subclasses must implement clear")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            A dictionary of cache statistics
        """
        raise NotImplementedError("Subclasses must implement get_stats")


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend."""
    
    def __init__(
        self,
        max_items: int = 1000,
        max_size_bytes: int = 50 * 1024 * 1024,  # 50 MB
        eviction_policy: Optional[CacheEvictionPolicy] = None,
    ):
        """
        Initialize the memory cache backend.
        
        Args:
            max_items: Maximum number of items to store
            max_size_bytes: Maximum cache size in bytes
            eviction_policy: The eviction policy to use
        """
        self.cache: Dict[str, CacheItem] = {}
        self.max_items = max_items
        self.max_size_bytes = max_size_bytes
        self.eviction_policy = eviction_policy or LRUEvictionPolicy()
        self.lock = threading.RLock()
        self.hit_count = 0
        self.miss_count = 0
        self.set_count = 0
        self.eviction_count = 0
        self.last_cleanup_time = time.time()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value, or None if not found
        """
        with self.lock:
            item = self.cache.get(key)
            
            if item is None:
                self.miss_count += 1
                return None
            
            if item.is_expired():
                self.cache.pop(key, None)
                self.miss_count += 1
                return None
            
            item.access()
            self.hit_count += 1
            return item.value
    
    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds
        """
        with self.lock:
            # Create a new cache item
            item = CacheItem(key, value, ttl)
            self.cache[key] = item
            self.set_count += 1
            
            # Check if we need to evict items
            self._evict_if_needed()
            
            # Periodically clean up expired items
            self._cleanup_if_needed()
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key was deleted, False otherwise
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear the cache."""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            A dictionary of cache statistics
        """
        with self.lock:
            total_size_bytes = sum(item.size_bytes for item in self.cache.values())
            hit_rate = self.hit_count / (self.hit_count + self.miss_count) if (self.hit_count + self.miss_count) > 0 else 0
            
            # Get the top 10 largest items
            largest_items = sorted(
                [(item.key, item.size_bytes) for item in self.cache.values()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Get the top 10 most accessed items
            most_accessed = sorted(
                [(item.key, item.access_count) for item in self.cache.values()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                "item_count": len(self.cache),
                "max_items": self.max_items,
                "total_size_bytes": total_size_bytes,
                "max_size_bytes": self.max_size_bytes,
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "set_count": self.set_count,
                "eviction_count": self.eviction_count,
                "hit_rate": hit_rate,
                "large_keys": largest_items,
                "popular_keys": most_accessed,
            }
    
    def _evict_if_needed(self) -> None:
        """Evict items if the cache exceeds its limits."""
        # Check if we need to evict items
        if len(self.cache) <= self.max_items:
            total_size = sum(item.size_bytes for item in self.cache.values())
            if total_size <= self.max_size_bytes:
                return
        
        # Select items to evict
        items = list(self.cache.values())
        target_size = max(1, int(0.8 * self.max_items))  # Aim for 80% capacity
        items_to_evict = self.eviction_policy.select_items_to_evict(items, target_size)
        
        # Evict the selected items
        for item in items_to_evict:
            self.cache.pop(item.key, None)
            self.eviction_count += 1
    
    def _cleanup_if_needed(self, force: bool = False) -> None:
        """
        Clean up expired items if needed.
        
        Args:
            force: Whether to force cleanup regardless of the time since last cleanup
        """
        now = time.time()
        # Clean up every 5 minutes
        if not force and (now - self.last_cleanup_time) < 300:
            return
        
        self.last_cleanup_time = now
        
        # Remove expired items
        expired_keys = [key for key, item in self.cache.items() if item.is_expired()]
        for key in expired_keys:
            self.cache.pop(key, None)


class RedisCacheBackend(CacheBackend):
    """
    Redis cache backend.
    """
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "apifrom:",
        serializer: Optional[Callable[[Any], bytes]] = None,
        deserializer: Optional[Callable[[bytes], Any]] = None,
    ):
        """
        Initialize the Redis cache backend.

        Args:
            redis_url: The Redis connection URL
            prefix: The key prefix to use
            serializer: Function to serialize values to bytes
            deserializer: Function to deserialize bytes to values
        """
        try:
            import redis
            from redis.exceptions import RedisError
        except ImportError:
            raise ImportError(
                "Redis cache backend requires redis-py package. "
                "Install it with: pip install redis"
            )
        
        self.redis_url = redis_url
        self.prefix = prefix
        self._redis = None
        self.serializer = serializer or (lambda v: pickle.dumps(v))
        self.deserializer = deserializer or (lambda v: pickle.loads(v))
        self.hit_count = 0
        self.miss_count = 0
        self.set_count = 0
        
        # Connect to Redis
        try:
            self._redis = redis.from_url(redis_url)
            self._redis.ping()
        except (RedisError, ConnectionError) as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self._redis = None
    @property
    def redis(self):
        """Get the Redis client, reconnecting if necessary."""
        if self._redis is None:
            try:
                import redis
                self._redis = redis.from_url(self.redis_url)
                self._redis.ping()
            except Exception as e:
                logger.warning(f"Failed to reconnect to Redis: {e}")
        return self._redis
    
    def _make_key(self, key: str) -> str:
        """
        Create a prefixed key.
        
        Args:
            key: The original key
            
        Returns:
            The prefixed key
        """
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value, or None if not found
        """
        if self.redis is None:
            self.miss_count += 1
            return None
        
        try:
            value = self.redis.get(self._make_key(key))
            if value is None:
                self.miss_count += 1
                return None
            
            self.hit_count += 1
            return self.deserializer(value)
        except Exception as e:
            logger.warning(f"Error getting value from Redis: {e}")
            self.miss_count += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds
        """
        if self.redis is None:
            return
        
        try:
            serialized = self.serializer(value)
            self.redis.setex(self._make_key(key), ttl, serialized)
            self.set_count += 1
        except Exception as e:
            logger.warning(f"Error setting value in Redis: {e}")
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key was deleted, False otherwise
        """
        if self.redis is None:
            return False
        
        try:
            return bool(self.redis.delete(self._make_key(key)))
        except Exception as e:
            logger.warning(f"Error deleting value from Redis: {e}")
            return False
    
    def clear(self) -> None:
        """Clear the cache."""
        if self.redis is None:
            return
        
        try:
            # Get all keys with the prefix
            keys = self.redis.keys(f"{self.prefix}*")
            
            # Delete all keys in batches
            if keys:
                for i in range(0, len(keys), 100):
                    batch = keys[i:i+100]
                    self.redis.delete(*batch)
        except Exception as e:
            logger.warning(f"Error clearing Redis cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            A dictionary of cache statistics
        """
        if self.redis is None:
            return {
                "connected": False,
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "set_count": self.set_count,
                "hit_rate": 0,
            }
        
        try:
            # Get Redis info
            info = self.redis.info()
            
            # Get all keys with the prefix
            keys = self.redis.keys(f"{self.prefix}*")
            item_count = len(keys)
            
            # Calculate hit rate
            hit_rate = self.hit_count / (self.hit_count + self.miss_count) if (self.hit_count + self.miss_count) > 0 else 0
            
            return {
                "connected": True,
                "item_count": item_count,
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "set_count": self.set_count,
                "hit_rate": hit_rate,
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            logger.warning(f"Error getting Redis stats: {e}")
            return {
                "connected": False,
                "error": str(e),
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "set_count": self.set_count,
                "hit_rate": 0,
            }


class TagBasedInvalidation:
    """
    Tag-based cache invalidation strategy.
    
    This class provides a way to invalidate cache entries based on tags.
    Tags are arbitrary strings that can be associated with cache entries.
    When a tag is invalidated, all cache entries associated with that tag
    are also invalidated.
    
    Example:
        ```python
        # Create a cache backend
        cache_backend = MemoryCacheBackend()
        
        # Create a tag-based invalidation strategy
        invalidation = TagBasedInvalidation(cache_backend)
        
        # Set a cache entry with tags
        cache_backend.set("user:123", {"name": "John"})
        invalidation.tag("user:123", ["user", "user:123"])
        
        # Invalidate all cache entries with the "user" tag
        invalidation.invalidate_tag("user")
        ```
    """
    
    def __init__(self, cache_backend: CacheBackend):
        """
        Initialize the tag-based invalidation strategy.
        
        Args:
            cache_backend: The cache backend to use
        """
        self.cache_backend = cache_backend
        self._tag_prefix = "_tag:"
    
    def tag(self, key: str, tags: List[str]) -> None:
        """
        Tag a cache entry with one or more tags.
        
        Args:
            key: The cache key
            tags: The tags to associate with the key
        """
        for tag in tags:
            # Add key to tag's entry list
            tag_key = f"tag:{tag}"
            keys = self.cache_backend.get(tag_key) or []
            if key not in keys:
                keys.append(key)
                self.cache_backend.set(tag_key, keys)
            
            # Add tag to key's tag list
            key_tags_key = f"tags:{key}"
            key_tags = self.cache_backend.get(key_tags_key) or []
            if tag not in key_tags:
                key_tags.append(tag)
                self.cache_backend.set(key_tags_key, key_tags)
    
    # Alias for tag method to match the test expectations
    add_tags = tag
    
    def invalidate_tag(self, tag: str) -> None:
        """
        Invalidate all cache entries associated with a tag.
        
        Args:
            tag: The tag to invalidate
        """
        tag_key = f"tag:{tag}"
        keys = self.cache_backend.get(tag_key) or []
        
        # Delete all cache entries associated with this tag
        for key in keys:
            self.cache_backend.delete(key)
        
        # Delete the tag itself
        self.cache_backend.delete(tag_key)
    
    def invalidate_tags(self, tags: List[str]) -> None:
        """
        Invalidate all cache entries associated with any of the given tags.
        
        Args:
            tags: The tags to invalidate
        """
        for tag in tags:
            self.invalidate_tag(tag)
    
    def get_keys_for_tag(self, tag: str) -> List[str]:
        """
        Get all cache keys associated with a tag.
        
        Args:
            tag: The tag to get keys for
            
        Returns:
            A list of cache keys
        """
        tag_key = f"{self._tag_prefix}{tag}"
        return self.cache_backend.get(tag_key) or []


class DependencyBasedInvalidation:
    """
    Dependency-based cache invalidation strategy.
    
    This class provides a way to invalidate cache entries based on dependencies.
    Dependencies are relationships between cache entries, where invalidating one
    entry will also invalidate all entries that depend on it.
    
    Example:
        ```python
        # Create a cache backend
        cache_backend = MemoryCacheBackend()
        
        # Create a dependency-based invalidation strategy
        invalidation = DependencyBasedInvalidation(cache_backend)
        
        # Set a cache entry with dependencies
        cache_backend.set("user:123", {"name": "John"})
        invalidation.add_dependency("user:123", "users")
        
        # Set another cache entry with dependencies
        cache_backend.set("post:456", {"title": "Hello"})
        invalidation.add_dependency("post:456", "posts")
        invalidation.add_dependency("post:456", "user:123")
        
        # Invalidate all cache entries that depend on "user:123"
        invalidation.invalidate("user:123")
        ```
    """
    
    def __init__(self, cache_backend: CacheBackend):
        """
        Initialize the dependency-based invalidation strategy.
        
        Args:
            cache_backend: The cache backend to use
        """
        self.cache_backend = cache_backend
        self._dep_prefix = "dep:"
        self._rev_prefix = "revdep:"
    
    def add_dependency(self, key: str, dependency: str) -> None:
        """
        Add a dependency to a cache entry.
        
        Args:
            key: The cache key
            dependency: The dependency key
        """
        # Add forward dependency (dependency -> keys)
        dep_key = f"{self._dep_prefix}{dependency}"
        keys = self.cache_backend.get(dep_key) or []
        if key not in keys:
            keys.append(key)
            self.cache_backend.set(dep_key, keys)
        
        # Add reverse dependency (key -> dependencies)
        rev_key = f"{self._rev_prefix}{key}"
        deps = self.cache_backend.get(rev_key) or []
        if dependency not in deps:
            deps.append(dependency)
            self.cache_backend.set(rev_key, deps)
    
    def add_dependencies(self, key: str, dependencies: List[str]) -> None:
        """
        Add multiple dependencies to a cache entry.
        
        Args:
            key: The cache key
            dependencies: List of dependency keys
        """
        for dependency in dependencies:
            self.add_dependency(key, dependency)
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate a cache entry and all entries that depend on it.
        
        Args:
            key: The key to invalidate
        """
        # Get all keys that depend on this key
        dep_key = f"{self._dep_prefix}{key}"
        keys = self.cache_backend.get(dep_key) or []
        
        # Invalidate all dependent keys
        for dependent_key in keys:
            self.cache_backend.delete(dependent_key)
            
            # Also invalidate reverse dependencies
            rev_key = f"{self._rev_prefix}{dependent_key}"
            self.cache_backend.delete(rev_key)
        
        # Invalidate the dependency key itself
        self.cache_backend.delete(dep_key)
        
        # Invalidate the key itself
        self.cache_backend.delete(key)
        
        # Invalidate reverse dependencies
        rev_key = f"{self._rev_prefix}{key}"
        self.cache_backend.delete(rev_key)
    
    def invalidate_dependency(self, dependency: str) -> None:
        """
        Invalidate all cache entries that depend on a specific dependency.
        
        Args:
            dependency: The dependency key to invalidate
        """
        # Get all keys that depend on this dependency
        dep_key = f"{self._dep_prefix}{dependency}"
        keys = self.cache_backend.get(dep_key) or []
        
        # Invalidate all dependent keys
        for key in keys:
            self.cache_backend.delete(key)
            
            # Also invalidate reverse dependencies
            rev_key = f"{self._rev_prefix}{key}"
            self.cache_backend.delete(rev_key)
        
        # Invalidate the dependency key itself
        self.cache_backend.delete(dep_key)
    
    def get_dependencies(self, key: str) -> List[str]:
        """
        Get all dependencies of a cache entry.
        
        Args:
            key: The cache key
            
        Returns:
            A list of dependency keys
        """
        rev_key = f"{self._rev_prefix}{key}"
        return self.cache_backend.get(rev_key) or []
    
    def get_dependents(self, key: str) -> List[str]:
        """
        Get all cache entries that depend on a key.
        
        Args:
            key: The dependency key
            
        Returns:
            A list of cache keys
        """
        dep_key = f"{self._dep_prefix}{key}"
        return self.cache_backend.get(dep_key) or []


class CacheControl:
    """
    Cache control decorators for API endpoints.
    
    This class provides decorators to control caching behavior for API endpoints.
    It includes decorators to cache responses, prevent caching, and invalidate cache entries.
    
    Example:
        ```python
        from apifrom import API, api
        from apifrom.middleware.cache_advanced import CacheControl
        
        app = API()
        
        @api(route="/users/{user_id}", method="GET")
        @CacheControl.cache(ttl=60, tags=["user"])
        def get_user(user_id: str):
            # This response will be cached for 60 seconds
            return {"id": user_id, "name": "John"}
        
        @api(route="/users/{user_id}", method="PUT")
        @CacheControl.invalidate(["user"])
        def update_user(user_id: str, name: str):
            # This will invalidate all cache entries with the "user" tag
            return {"id": user_id, "name": name}
        
        @api(route="/users/{user_id}/sensitive", method="GET")
        @CacheControl.no_cache
        def get_sensitive_user_data(user_id: str):
            # This response will not be cached
            return {"id": user_id, "ssn": "123-45-6789"}
        ```
    """
    
    @staticmethod
    def cache(ttl: int = 60, tags: Optional[List[str]] = None, dependencies: Optional[List[str]] = None):
        """
        Decorator to cache the response of an API endpoint.
        
        Args:
            ttl: Time to live in seconds
            tags: Tags to associate with the cache entry
            dependencies: Dependencies to associate with the cache entry
            
        Returns:
            A decorator function
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Call the original function
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # Store cache metadata on the result
                if hasattr(result, "headers"):
                    result.headers["X-Cache-TTL"] = str(ttl)
                    if tags:
                        result.headers["X-Cache-Tags"] = ",".join(tags)
                    if dependencies:
                        result.headers["X-Cache-Dependencies"] = ",".join(dependencies)
                
                return result
            
            # Store cache metadata on the wrapper function
            wrapper.__cache_control__ = {
                "cache": True,
                "ttl": ttl,
                "tags": tags or [],
                "dependencies": dependencies or []
            }
            
            return wrapper
        return decorator
    
    @staticmethod
    def no_cache(func):
        """
        Decorator to prevent caching of an API endpoint.
        
        Args:
            func: The function to decorate
            
        Returns:
            The decorated function
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Call the original function
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Set cache control headers
            if hasattr(result, "headers"):
                result.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                result.headers["Pragma"] = "no-cache"
                result.headers["Expires"] = "0"
            
            return result
        
        # Store cache metadata on the wrapper function
        wrapper.__cache_control__ = {
            "cache": False
        }
        
        return wrapper
    
    @staticmethod
    def invalidate(patterns: List[str]):
        """
        Decorator to invalidate cache entries matching the given patterns.
        
        Args:
            patterns: Patterns to match cache keys
            
        Returns:
            A decorator function
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Call the original function
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # Find the request object in args or kwargs
                request = None
                for arg in args:
                    if hasattr(arg, "app") and hasattr(arg.app, "middleware"):
                        request = arg
                        break
                
                if request is not None:
                    # Find the cache middleware
                    for middleware in request.app.middleware:
                        if hasattr(middleware, "__class__") and middleware.__class__.__name__ in ["CacheMiddleware", "AdvancedCacheMiddleware"]:
                            # Invalidate the patterns
                            for pattern in patterns:
                                middleware.invalidate(pattern)
                            break
                
                # Store invalidation patterns on the result
                if hasattr(result, "headers"):
                    result.headers["X-Cache-Invalidate"] = ",".join(patterns)
                
                return result
            
            # Store cache metadata on the wrapper function
            wrapper.__cache_control__ = {
                "invalidate": True,
                "patterns": patterns
            }
            
            return wrapper
        return decorator


class CacheMiddleware(Middleware):
    """
    Middleware for caching API responses.
    
    This middleware caches API responses based on the request method, path, and query parameters.
    It supports various cache backends and configuration options.
    """
    
    def __init__(
        self,
        cache_backend: Optional[CacheBackend] = None,
        ttl: int = 60,
        cache_methods: Optional[Set[str]] = None,
        ignore_paths: Optional[Set[str]] = None,
        vary_headers: Optional[Set[str]] = None,
        cache_control_header: bool = True,
    ):
        """
        Initialize the cache middleware.
        
        Args:
            cache_backend: The cache backend to use (defaults to MemoryCacheBackend)
            ttl: Default time-to-live in seconds
            cache_methods: Set of HTTP methods to cache (defaults to {"GET"})
            ignore_paths: Set of paths to exclude from caching
            vary_headers: Set of headers to include in the cache key
            cache_control_header: Whether to set Cache-Control headers
        """
        self.cache = cache_backend or MemoryCacheBackend()
        self.ttl = ttl
        self.cache_methods = cache_methods or {"GET"}
        self.ignore_paths = ignore_paths or set()
        self.vary_headers = vary_headers or {"Accept", "Accept-Encoding"}
        self.cache_control_header = cache_control_header
    
    async def process_request(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request and potentially return a cached response.
        
        Args:
            request: The request object
            call_next: The next middleware function
            
        Returns:
            The response object
        """
        # Skip caching for non-cacheable requests
        if not self._should_cache(request):
            return await call_next(request)
        
        # Generate a cache key for the request
        cache_key = self._generate_cache_key(request)
        
        # Try to get the response from the cache
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            # Return the cached response
            if self.cache_control_header:
                cached_response.headers["X-Cache"] = "HIT"
            return cached_response
        
        # Get the response from the next middleware
        try:
            response = await call_next(request)
        except TypeError:
            # Handle non-awaitable responses
            response = call_next(request)
        
        # Skip caching for non-cacheable responses
        if not self._should_cache_response(response):
            return response
        
        # Cache the response if it's cacheable
        if self._should_cache_response(response):
            # Clone the response to avoid modifying the original
            response_to_cache = response.copy()
            
            # Set cache headers
            if self.cache_control_header:
                response.headers["Cache-Control"] = f"max-age={self.ttl}"
                response.headers["X-Cache"] = "MISS"
            
            # Cache the response
            self.cache.set(cache_key, response_to_cache, self.ttl)
        
        return response
    
    def _should_cache(self, request: Request) -> bool:
        """
        Check if a request should be cached.
        
        Args:
            request: The request object
            
        Returns:
            True if the request should be cached, False otherwise
        """
        # Check if the method is cacheable
        if request.method not in self.cache_methods:
            return False
        
        # Check if the path is ignored
        for path in self.ignore_paths:
            if request.path.startswith(path):
                return False
        
        # Check if the request has cache control headers
        cache_control = request.headers.get("Cache-Control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False
        
        return True
    
    def _should_cache_response(self, response: Response) -> bool:
        """
        Check if a response should be cached.
        
        Args:
            response: The response object
            
        Returns:
            True if the response should be cached, False otherwise
        """
        # Only cache successful responses
        if response.status_code < 200 or response.status_code >= 300:
            return False
        
        # Check if the response has cache control headers
        cache_control = response.headers.get("Cache-Control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False
        
        return True
    
    def _generate_cache_key(self, request: Request) -> str:
        """
        Generate a cache key for a request.
        
        Args:
            request: The request object
            
        Returns:
            A cache key string
        """
        # Get the method and path
        key_parts = [request.method, request.path]
        
        # Add query parameters
        if request.query_params:
            sorted_params = sorted(request.query_params.items())
            key_parts.append(str(sorted_params))
        
        # Add vary headers
        for header in self.vary_headers:
            value = request.headers.get(header)
            if value:
                key_parts.append(f"{header}:{value}")
        
        # Generate a hash of the key parts
        key_str = ":".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            A dictionary of cache statistics
        """
        return self.cache.get_stats()
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()


class AdvancedCacheMiddleware(CacheMiddleware):
    """
    Advanced middleware for caching API responses.
    
    This middleware extends the basic CacheMiddleware with additional features
    such as per-endpoint TTL, response compression, and automatic cache key generation.
    """
    
    def __init__(
        self,
        cache_backend: Optional[CacheBackend] = None,
        ttl: int = 60,
        cache_methods: Optional[Set[str]] = None,
        ignore_paths: Optional[Set[str]] = None,
        vary_headers: Optional[Set[str]] = None,
        cache_control_header: bool = True,
        compress_responses: bool = False,
        endpoint_ttls: Optional[Dict[str, int]] = None,
        auto_vary: bool = True,
        invalidation_strategy: Optional[Union[TagBasedInvalidation, DependencyBasedInvalidation]] = None,
    ):
        """
        Initialize the advanced cache middleware.
        
        Args:
            cache_backend: The cache backend to use (defaults to MemoryCacheBackend)
            ttl: Default time-to-live in seconds
            cache_methods: Set of HTTP methods to cache (defaults to {"GET"})
            ignore_paths: Set of paths to exclude from caching
            vary_headers: Set of headers to include in the cache key
            cache_control_header: Whether to set Cache-Control headers
            compress_responses: Whether to compress responses before caching
            endpoint_ttls: Dictionary mapping endpoints to TTL values
            auto_vary: Whether to automatically determine vary headers
            invalidation_strategy: Strategy for cache invalidation
        """
        super().__init__(
            cache_backend=cache_backend,
            ttl=ttl,
            cache_methods=cache_methods,
            ignore_paths=ignore_paths,
            vary_headers=vary_headers,
            cache_control_header=cache_control_header,
        )
        
        self.compress_responses = compress_responses
        self.endpoint_ttls = endpoint_ttls or {}
        self.auto_vary = auto_vary
        self.invalidation_strategy = invalidation_strategy
        
        # Set up compression if enabled
        if self.compress_responses:
            try:
                import zlib
                self._compress = lambda data: zlib.compress(data)
                self._decompress = lambda data: zlib.decompress(data)
            except ImportError:
                logger.warning("zlib not available, compression disabled")
                self.compress_responses = False
    
    async def process_request(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request and potentially return a cached response.
        
        Args:
            request: The request object
            call_next: The next middleware function
            
        Returns:
            The response object
        """
        # Skip caching for non-cacheable requests
        if not self._should_cache(request):
            return await call_next(request)
        
        # Generate a cache key for the request
        cache_key = self._generate_cache_key(request)
        
        # Try to get the response from the cache
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            # Decompress if necessary
            if self.compress_responses and isinstance(cached_data, tuple) and len(cached_data) == 2:
                compressed, response_dict = cached_data
                if compressed:
                    try:
                        response_dict = json.loads(self._decompress(response_dict).decode())
                    except Exception as e:
                        logger.warning(f"Error decompressing cached response: {e}")
                        return await call_next(request)
            else:
                response_dict = cached_data
            
            # Reconstruct the response
            response = Response.from_dict(response_dict)
            
            # Set cache headers
            if self.cache_control_header:
                response.headers["X-Cache"] = "HIT"
            
            return response
        
        # Get the response from the next middleware
        try:
            response = await call_next(request)
        except TypeError:
            # Handle non-awaitable responses
            response = call_next(request)
        
        # Skip caching for non-cacheable responses
        if not self._should_cache_response(response):
            return response
        
        # Cache the response if it's cacheable
        if self._should_cache_response(response):
            # Get the TTL for this endpoint
            endpoint_ttl = self._get_endpoint_ttl(request.path)
            
            # Convert the response to a dictionary
            response_dict = response.to_dict()
            
            # Compress if enabled
            if self.compress_responses and len(json.dumps(response_dict)) > 1024:  # Only compress if > 1KB
                try:
                    compressed_data = self._compress(json.dumps(response_dict).encode())
                    cache_data = (True, compressed_data)
                except Exception as e:
                    logger.warning(f"Error compressing response: {e}")
                    cache_data = response_dict
            else:
                cache_data = response_dict
            
            # Set cache headers
            if self.cache_control_header:
                response.headers["Cache-Control"] = f"max-age={endpoint_ttl}"
                response.headers["X-Cache"] = "MISS"
            
            # Store in cache
            self.cache.set(cache_key, cache_data, ttl=endpoint_ttl)
        
        return response
    
    def _get_endpoint_ttl(self, path: str) -> int:
        """
        Get the TTL for an endpoint.
        
        Args:
            path: The endpoint path
            
        Returns:
            The TTL in seconds
        """
        # Check for exact path match
        if path in self.endpoint_ttls:
            return self.endpoint_ttls[path]
        
        # Check for prefix match
        for prefix, ttl in self.endpoint_ttls.items():
            if prefix.endswith("*") and path.startswith(prefix[:-1]):
                return ttl
        
        # Return default TTL
        return self.ttl
    
    def _generate_cache_key(self, request: Request) -> str:
        """
        Generate a cache key for a request.
        
        Args:
            request: The request object
            
        Returns:
            A cache key string
        """
        # Get the method and path
        key_parts = [request.method, request.path]
        
        # Add query parameters
        if request.query_params:
            sorted_params = sorted(request.query_params.items())
            key_parts.append(str(sorted_params))
        
        # Add vary headers
        vary_headers = set(self.vary_headers)
        
        # Add auto vary headers if enabled
        if self.auto_vary:
            # Add content negotiation headers
            for header in ["Accept", "Accept-Encoding", "Accept-Language"]:
                if header in request.headers:
                    vary_headers.add(header)
            
            # Add authorization if present
            if "Authorization" in request.headers:
                vary_headers.add("Authorization")
        
        for header in vary_headers:
            value = request.headers.get(header)
            if value:
                key_parts.append(f"{header}:{value}")
        
        # Generate a hash of the key parts
        key_str = ":".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def invalidate(self, pattern: str) -> None:
        """
        Invalidate cache entries matching a pattern.
        
        Args:
            pattern: The pattern to match
        """
        if self.invalidation_strategy:
            if isinstance(self.invalidation_strategy, TagBasedInvalidation):
                self.invalidation_strategy.invalidate_tag(pattern)
            elif isinstance(self.invalidation_strategy, DependencyBasedInvalidation):
                self.invalidation_strategy.invalidate_dependency(pattern)
        else:
            # Fallback to direct cache invalidation
            # This is a simplified implementation that only works with exact matches
            self.cache_backend.delete(pattern)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            A dictionary of cache statistics
        """
        return self.cache.get_stats()
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()


# Export public classes
__all__ = [
    "CacheItem",
    "CacheEvictionPolicy",
    "LRUEvictionPolicy",
    "LFUEvictionPolicy",
    "TTLEvictionPolicy",
    "SizeEvictionPolicy",
    "HybridEvictionPolicy",
    "CacheBackend",
    "MemoryCacheBackend",
    "RedisCacheBackend",
    "CacheMiddleware",
    "AdvancedCacheMiddleware",
    "TagBasedInvalidation",
    "DependencyBasedInvalidation",
    "CacheControl",
] 