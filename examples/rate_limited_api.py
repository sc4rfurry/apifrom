"""
Rate limiting example using APIFromAnything.

This example demonstrates how to use the rate limiting middleware to protect
an API created with the APIFromAnything library from abuse.
"""

import logging
import time
from typing import Dict, List

from apifrom import API, api
from apifrom.middleware import (
    RateLimitMiddleware,
    RateLimit,
    FixedWindowRateLimiter,
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create API instance
app = API(
    title="Rate Limited API Example",
    description="An API with rate limiting created with APIFromAnything",
    version="1.0.0",
    debug=True
)

# Add rate limit middleware with fixed window rate limiter
fixed_window_limiter = FixedWindowRateLimiter(
    limit=5,  # 5 requests per minute
    window=60,  # 1 minute window
)
app.add_middleware(
    RateLimitMiddleware(
        limiter=fixed_window_limiter,
        exclude_routes=["/unlimited"],  # Don't rate limit these routes
    )
)

# Simulated database
quotes_db = [
    {"id": 1, "text": "The only limit to our realization of tomorrow will be our doubts of today.", "author": "Franklin D. Roosevelt"},
    {"id": 2, "text": "The greatest glory in living lies not in never falling, but in rising every time we fall.", "author": "Nelson Mandela"},
    {"id": 3, "text": "The way to get started is to quit talking and begin doing.", "author": "Walt Disney"},
    {"id": 4, "text": "If life were predictable it would cease to be life, and be without flavor.", "author": "Eleanor Roosevelt"},
    {"id": 5, "text": "Life is what happens when you're busy making other plans.", "author": "John Lennon"},
]


@api(route="/quotes", method="GET")
def get_quotes() -> List[Dict]:
    """
    Get all quotes.
    
    This endpoint is rate limited to 5 requests per minute.
    
    Returns:
        A list of quote objects
    """
    logger.info("Fetching quotes...")
    return quotes_db


@api(route="/quotes/{quote_id}", method="GET")
def get_quote(quote_id: int) -> Dict:
    """
    Get a quote by ID.
    
    This endpoint is rate limited to 5 requests per minute.
    
    Args:
        quote_id: The ID of the quote to retrieve
        
    Returns:
        A quote object
    """
    logger.info(f"Fetching quote {quote_id}...")
    
    for quote in quotes_db:
        if quote["id"] == quote_id:
            return quote
    
    return {"error": "Quote not found"}


@api(route="/quotes/author/{author}", method="GET")
@RateLimit.limit(limit=2, window=60)  # Override default rate limit
def get_quotes_by_author(author: str) -> List[Dict]:
    """
    Get quotes by author.
    
    This endpoint is rate limited to 2 requests per minute.
    
    Args:
        author: The author to filter by
        
    Returns:
        A list of quote objects
    """
    logger.info(f"Fetching quotes by {author}...")
    
    return [quote for quote in quotes_db if quote["author"] == author]


@api(route="/unlimited/quotes", method="GET")
@RateLimit.exempt
def get_unlimited_quotes() -> List[Dict]:
    """
    Get all quotes without rate limiting.
    
    This endpoint is exempt from rate limiting.
    
    Returns:
        A list of quote objects
    """
    logger.info("Fetching quotes without rate limiting...")
    return quotes_db


@api(route="/quotes", method="POST")
def create_quote(text: str, author: str) -> Dict:
    """
    Create a new quote.
    
    This endpoint is rate limited to 5 requests per minute.
    
    Args:
        text: The text of the quote
        author: The author of the quote
        
    Returns:
        The created quote object
    """
    logger.info("Creating new quote...")
    
    quote_id = max(quote["id"] for quote in quotes_db) + 1
    new_quote = {"id": quote_id, "text": text, "author": author}
    quotes_db.append(new_quote)
    
    return new_quote


@api(route="/sliding-window/test", method="GET")
def test_sliding_window() -> Dict:
    """
    Test the sliding window rate limiter.
    
    This endpoint uses a separate sliding window rate limiter.
    
    Returns:
        A success message
    """
    # Create a sliding window rate limiter for this endpoint
    if not hasattr(test_sliding_window, "limiter"):
        test_sliding_window.limiter = SlidingWindowRateLimiter(
            limit=3,  # 3 requests per 10 seconds
            window=10,  # 10 second window
        )
    
    # Check if the request is allowed
    key = "test-key"
    allowed, limit_info = test_sliding_window.limiter.check_limit(key)
    
    if not allowed:
        return {
            "error": "Rate limit exceeded",
            "limit_info": limit_info,
        }
    
    # Update the rate limiter
    test_sliding_window.limiter.update(key)
    
    return {
        "message": "Request allowed",
        "limit_info": limit_info,
    }


@api(route="/token-bucket/test", method="GET")
def test_token_bucket() -> Dict:
    """
    Test the token bucket rate limiter.
    
    This endpoint uses a separate token bucket rate limiter.
    
    Returns:
        A success message
    """
    # Create a token bucket rate limiter for this endpoint
    if not hasattr(test_token_bucket, "limiter"):
        test_token_bucket.limiter = TokenBucketRateLimiter(
            rate=0.1,  # 0.1 tokens per second (1 token every 10 seconds)
            capacity=3,  # Maximum of 3 tokens
        )
    
    # Check if the request is allowed
    key = "test-key"
    allowed, limit_info = test_token_bucket.limiter.check_limit(key)
    
    if not allowed:
        return {
            "error": "Rate limit exceeded",
            "limit_info": limit_info,
        }
    
    # Update the rate limiter
    test_token_bucket.limiter.update(key)
    
    return {
        "message": "Request allowed",
        "limit_info": limit_info,
    }


@api(route="/rate-limit/status", method="GET")
def get_rate_limit_status() -> Dict:
    """
    Get the current rate limit status.
    
    Returns:
        The current rate limit status
    """
    # Get the rate limit status for the default limiter
    key = "test-key"
    allowed, limit_info = fixed_window_limiter.check_limit(key)
    
    return {
        "fixed_window": {
            "allowed": allowed,
            "limit_info": limit_info,
        }
    }


if __name__ == "__main__":
    # Run the API server
    app.run(host="0.0.0.0", port=8005) 