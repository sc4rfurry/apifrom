"""
Example demonstrating advanced caching features in APIFromAnything.

This example shows how to use distributed caching with Redis and implement
cache invalidation strategies for a simple blog API.
"""

import asyncio
import time
from typing import Dict, List, Optional

from apifrom.core.app import APIApp
from apifrom.decorators.api import api
from apifrom.middleware.cache_advanced import (
    AdvancedCacheMiddleware,
    RedisCacheBackend,
    DependencyBasedInvalidation,
    CacheControl
)

# Create an API application
app = APIApp(title="Advanced Caching Example")

# Create a Redis cache backend (will fall back to in-memory if Redis is not available)
try:
    cache_backend = RedisCacheBackend(url="redis://localhost:6379/0")
    print("Using Redis cache backend")
except ImportError:
    from apifrom.middleware.cache_advanced import MemoryCacheBackend
    cache_backend = MemoryCacheBackend()
    print("Using in-memory cache backend (Redis not available)")

# Create a dependency-based invalidation strategy
invalidation_strategy = DependencyBasedInvalidation(cache_backend)

# Create and register the advanced cache middleware
cache_middleware = AdvancedCacheMiddleware(
    cache_backend=cache_backend,
    invalidation_strategy=invalidation_strategy,
    ttl=60,  # Default TTL of 60 seconds
    vary_headers=["Accept", "Accept-Language"]
)
app.add_middleware(cache_middleware)

# In-memory database for demonstration purposes
posts_db = [
    {"id": 1, "title": "First Post", "content": "This is the first post", "author_id": 1},
    {"id": 2, "title": "Second Post", "content": "This is the second post", "author_id": 2},
]

authors_db = [
    {"id": 1, "name": "John Doe"},
    {"id": 2, "name": "Jane Smith"},
]

comments_db = [
    {"id": 1, "post_id": 1, "content": "Great post!", "author_id": 2},
    {"id": 2, "post_id": 1, "content": "Thanks!", "author_id": 1},
]


# Helper function to simulate a slow database query
async def slow_query(delay: float = 0.5):
    """Simulate a slow database query."""
    await asyncio.sleep(delay)


# API endpoints for posts
@api(app)
@CacheControl.cache(ttl=30, dependencies=["posts"])
async def get_posts() -> List[Dict]:
    """
    Get all posts.
    
    This endpoint is cached for 30 seconds and depends on the "posts" dependency.
    When a post is created, updated, or deleted, this cache will be invalidated.
    """
    print("Executing get_posts (slow query)")
    await slow_query()
    return posts_db


@api(app)
@CacheControl.cache(ttl=60, dependencies=["posts", "post:{post_id}"])
async def get_post(post_id: int) -> Dict:
    """
    Get a post by ID.
    
    This endpoint is cached for 60 seconds and depends on the "posts" and "post:{post_id}" dependencies.
    When this specific post is updated or deleted, this cache will be invalidated.
    """
    print(f"Executing get_post(post_id={post_id}) (slow query)")
    await slow_query()
    
    for post in posts_db:
        if post["id"] == post_id:
            # Get the author for the post
            author = None
            for a in authors_db:
                if a["id"] == post["author_id"]:
                    author = a
                    break
            
            # Get comments for the post
            post_comments = []
            for comment in comments_db:
                if comment["post_id"] == post_id:
                    post_comments.append(comment)
            
            # Return the post with author and comments
            return {
                **post,
                "author": author,
                "comments": post_comments
            }
    
    return {"error": "Post not found"}


@api(app)
@CacheControl.invalidate(["posts", "post:{post_id}"])
async def update_post(post_id: int, title: Optional[str] = None, content: Optional[str] = None) -> Dict:
    """
    Update a post.
    
    This endpoint invalidates the "posts" and "post:{post_id}" cache dependencies.
    """
    print(f"Executing update_post(post_id={post_id})")
    
    for post in posts_db:
        if post["id"] == post_id:
            if title is not None:
                post["title"] = title
            if content is not None:
                post["content"] = content
            return {"message": "Post updated", "post": post}
    
    return {"error": "Post not found"}


@api(app)
@CacheControl.invalidate(["posts"])
async def create_post(title: str, content: str, author_id: int) -> Dict:
    """
    Create a new post.
    
    This endpoint invalidates the "posts" cache dependency.
    """
    print("Executing create_post")
    
    # Generate a new ID
    post_id = max(post["id"] for post in posts_db) + 1
    
    # Create the new post
    new_post = {"id": post_id, "title": title, "content": content, "author_id": author_id}
    
    # Add it to the database
    posts_db.append(new_post)
    
    return {"message": "Post created", "post": new_post}


@api(app)
@CacheControl.invalidate(["posts", "post:{post_id}"])
async def delete_post(post_id: int) -> Dict:
    """
    Delete a post.
    
    This endpoint invalidates the "posts" and "post:{post_id}" cache dependencies.
    """
    print(f"Executing delete_post(post_id={post_id})")
    
    for i, post in enumerate(posts_db):
        if post["id"] == post_id:
            del posts_db[i]
            
            # Also delete associated comments
            comments_to_delete = []
            for j, comment in enumerate(comments_db):
                if comment["post_id"] == post_id:
                    comments_to_delete.append(j)
            
            # Delete comments in reverse order to avoid index issues
            for j in sorted(comments_to_delete, reverse=True):
                del comments_db[j]
            
            return {"message": "Post deleted"}
    
    return {"error": "Post not found"}


# API endpoints for comments
@api(app)
@CacheControl.cache(ttl=30, dependencies=["comments", "post:{post_id}"])
async def get_comments(post_id: int) -> List[Dict]:
    """
    Get all comments for a post.
    
    This endpoint is cached for 30 seconds and depends on the "comments" and "post:{post_id}" dependencies.
    """
    print(f"Executing get_comments(post_id={post_id}) (slow query)")
    await slow_query()
    
    post_comments = []
    for comment in comments_db:
        if comment["post_id"] == post_id:
            post_comments.append(comment)
    
    return post_comments


@api(app)
@CacheControl.invalidate(["comments", "post:{post_id}"])
async def add_comment(post_id: int, content: str, author_id: int) -> Dict:
    """
    Add a comment to a post.
    
    This endpoint invalidates the "comments" and "post:{post_id}" cache dependencies.
    """
    print(f"Executing add_comment(post_id={post_id})")
    
    # Check if the post exists
    post_exists = False
    for post in posts_db:
        if post["id"] == post_id:
            post_exists = True
            break
    
    if not post_exists:
        return {"error": "Post not found"}
    
    # Generate a new ID
    comment_id = max(comment["id"] for comment in comments_db) + 1 if comments_db else 1
    
    # Create the new comment
    new_comment = {"id": comment_id, "post_id": post_id, "content": content, "author_id": author_id}
    
    # Add it to the database
    comments_db.append(new_comment)
    
    return {"message": "Comment added", "comment": new_comment}


# API endpoint to manually invalidate cache
@api(app)
async def invalidate_cache(pattern: str) -> Dict:
    """
    Manually invalidate cache entries matching a pattern.
    
    This endpoint allows manual invalidation of cache entries.
    """
    print(f"Executing invalidate_cache(pattern={pattern})")
    
    cache_middleware.invalidate(pattern)
    
    return {"message": f"Cache invalidated for pattern: {pattern}"}


# API endpoint to get cache statistics
@api(app)
@CacheControl.no_cache
async def get_cache_stats() -> Dict:
    """
    Get cache statistics.
    
    This endpoint is not cached.
    """
    print("Executing get_cache_stats")
    
    # For Redis, we could get actual stats, but for simplicity we'll just return basic info
    return {
        "backend_type": cache_backend.__class__.__name__,
        "invalidation_strategy": invalidation_strategy.__class__.__name__,
        "default_ttl": cache_middleware.ttl,
        "vary_headers": cache_middleware.vary_headers
    }


# Run the application if executed directly
if __name__ == "__main__":
    print("Starting advanced caching example API...")
    print("Try the following endpoints:")
    print("  GET /posts - List all posts (cached)")
    print("  GET /post?post_id=1 - Get a specific post (cached)")
    print("  POST /update_post?post_id=1&title=Updated - Update a post (invalidates cache)")
    print("  POST /create_post?title=New&content=Content&author_id=1 - Create a post (invalidates cache)")
    print("  GET /comments?post_id=1 - Get comments for a post (cached)")
    print("  POST /add_comment?post_id=1&content=New comment&author_id=2 - Add a comment (invalidates cache)")
    print("  GET /invalidate_cache?pattern=posts - Manually invalidate cache")
    print("  GET /get_cache_stats - Get cache statistics (not cached)")
    print("\nNotice how the first request to a cached endpoint is slow, but subsequent requests are fast")
    print("until the cache is invalidated or expires.")
    
    app.run(host="0.0.0.0", port=8000) 