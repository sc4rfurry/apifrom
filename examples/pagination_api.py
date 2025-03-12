"""
Pagination Example for APIFromAnything.

This example demonstrates how to implement pagination for API endpoints
that return large collections of data.
"""

import asyncio
import time
import math
from typing import List, Dict, Optional, Any, Tuple

from apifrom import API, api
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.performance import Web

# Create an API instance
app = API(
    title="Pagination Example API",
    description="An example of implementing pagination in APIFromAnything",
    version="1.0.0"
)

# Simulate a database with a large collection of items
ITEMS_DB = []


# Generate sample data
def generate_sample_data(count: int = 1000):
    """Generate sample data for the example."""
    global ITEMS_DB
    ITEMS_DB = [
        {
            "id": i,
            "name": f"Item {i}",
            "description": f"This is item {i} of {count}",
            "created_at": time.time() - (count - i)
        }
        for i in range(1, count + 1)
    ]


# Basic pagination implementation
@api(route="/items", method="GET")
def get_items(page: int = 1, limit: int = 10) -> Dict[str, Any]:
    """
    Get a paginated list of items.
    
    Args:
        page: The page number (1-indexed)
        limit: The number of items per page (default: 10, max: 100)
    
    Returns:
        A paginated response with items and pagination metadata
    """
    # Validate and sanitize parameters
    page = max(1, page)  # Ensure page is at least 1
    limit = max(1, min(100, limit))  # Ensure limit is between 1 and 100
    
    # Calculate pagination values
    total_items = len(ITEMS_DB)
    total_pages = math.ceil(total_items / limit)
    
    # Calculate start and end indices
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total_items)
    
    # Get the items for the current page
    items = ITEMS_DB[start_idx:end_idx]
    
    # Construct pagination metadata
    pagination = {
        "page": page,
        "limit": limit,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    
    # Add navigation links
    links = {}
    if page > 1:
        links["prev"] = f"/items?page={page-1}&limit={limit}"
    if page < total_pages:
        links["next"] = f"/items?page={page+1}&limit={limit}"
    links["first"] = f"/items?page=1&limit={limit}"
    links["last"] = f"/items?page={total_pages}&limit={limit}"
    
    # Construct the response
    return {
        "items": items,
        "pagination": pagination,
        "links": links
    }


# Advanced pagination with filtering and sorting
@api(route="/items/advanced", method="GET")
def get_items_advanced(
    page: int = 1,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "asc",
    name_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a paginated list of items with advanced options.
    
    Args:
        page: The page number (1-indexed)
        limit: The number of items per page (default: 10, max: 100)
        sort_by: The field to sort by (id, name, created_at)
        sort_order: The sort order (asc, desc)
        name_filter: Optional filter for item name
    
    Returns:
        A paginated response with items and pagination metadata
    """
    # Validate and sanitize parameters
    page = max(1, page)  # Ensure page is at least 1
    limit = max(1, min(100, limit))  # Ensure limit is between 1 and 100
    
    # Apply filters first
    filtered_items = ITEMS_DB
    
    if name_filter:
        filtered_items = [
            item for item in filtered_items 
            if name_filter.lower() in item["name"].lower()
        ]
    
    # Apply sorting
    valid_sort_fields = ["id", "name", "created_at"]
    sort_by = sort_by if sort_by in valid_sort_fields else "id"
    
    reverse = sort_order.lower() == "desc"
    filtered_items = sorted(filtered_items, key=lambda x: x[sort_by], reverse=reverse)
    
    # Calculate pagination values
    total_items = len(filtered_items)
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 1
    
    # Calculate start and end indices
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total_items)
    
    # Get the items for the current page
    items = filtered_items[start_idx:end_idx]
    
    # Construct pagination metadata
    pagination = {
        "page": page,
        "limit": limit,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    
    # Add navigation links
    base_url = f"/items/advanced?sort_by={sort_by}&sort_order={sort_order}"
    if name_filter:
        base_url += f"&name_filter={name_filter}"
    
    links = {}
    if page > 1:
        links["prev"] = f"{base_url}&page={page-1}&limit={limit}"
    if page < total_pages:
        links["next"] = f"{base_url}&page={page+1}&limit={limit}"
    links["first"] = f"{base_url}&page=1&limit={limit}"
    links["last"] = f"{base_url}&page={total_pages}&limit={limit}"
    
    # Construct the response
    return {
        "items": items,
        "pagination": pagination,
        "links": links,
        "filters_applied": {
            "name_filter": name_filter,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
    }


# Cursor-based pagination
@api(route="/items/cursor", method="GET")
def get_items_cursor(
    cursor: Optional[str] = None,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "asc"
) -> Dict[str, Any]:
    """
    Get a paginated list of items using cursor-based pagination.
    
    Args:
        cursor: The cursor pointing to the item after which to start (optional)
        limit: The number of items per page (default: 10, max: 100)
        sort_by: The field to sort by (id, name, created_at)
        sort_order: The sort order (asc, desc)
    
    Returns:
        A paginated response with items and pagination metadata
    """
    # Validate and sanitize parameters
    limit = max(1, min(100, limit))  # Ensure limit is between 1 and 100
    
    # Apply sorting
    valid_sort_fields = ["id", "name", "created_at"]
    sort_by = sort_by if sort_by in valid_sort_fields else "id"
    
    reverse = sort_order.lower() == "desc"
    sorted_items = sorted(ITEMS_DB, key=lambda x: x[sort_by], reverse=reverse)
    
    # Find the starting position if cursor is provided
    start_idx = 0
    if cursor:
        try:
            cursor_value = int(cursor)
            for idx, item in enumerate(sorted_items):
                if item["id"] == cursor_value:
                    start_idx = idx + 1  # Start after the cursor item
                    break
        except ValueError:
            # If cursor is invalid, start from the beginning
            pass
    
    # Calculate end index
    end_idx = min(start_idx + limit, len(sorted_items))
    
    # Get the items for the current page
    items = sorted_items[start_idx:end_idx]
    
    # Determine next and previous cursors
    next_cursor = None
    prev_cursor = None
    
    if end_idx < len(sorted_items):
        next_cursor = str(sorted_items[end_idx - 1]["id"])
    
    if start_idx > 0:
        prev_cursor = str(sorted_items[max(0, start_idx - limit - 1)]["id"])
    
    # Construct the response
    return {
        "items": items,
        "pagination": {
            "limit": limit,
            "next_cursor": next_cursor,
            "prev_cursor": prev_cursor,
            "has_next": next_cursor is not None,
            "has_prev": prev_cursor is not None
        },
        "links": {
            "next": f"/items/cursor?cursor={next_cursor}&limit={limit}&sort_by={sort_by}&sort_order={sort_order}" if next_cursor else None,
            "prev": f"/items/cursor?cursor={prev_cursor}&limit={limit}&sort_by={sort_by}&sort_order={sort_order}" if prev_cursor else None
        }
    }


# Async pagination example with optimized performance
@api(route="/items/async", method="GET")
@Web.optimize(cache_ttl=30)  # Cache results for 30 seconds
async def get_items_async(page: int = 1, limit: int = 10) -> Dict[str, Any]:
    """
    Get a paginated list of items asynchronously with performance optimization.
    
    Args:
        page: The page number (1-indexed)
        limit: The number of items per page (default: 10, max: 100)
    
    Returns:
        A paginated response with items and pagination metadata
    """
    # Validate and sanitize parameters
    page = max(1, page)  # Ensure page is at least 1
    limit = max(1, min(100, limit))  # Ensure limit is between 1 and 100
    
    # Simulate async database query
    await asyncio.sleep(0.1)
    
    # Calculate pagination values
    total_items = len(ITEMS_DB)
    total_pages = math.ceil(total_items / limit)
    
    # Calculate start and end indices
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total_items)
    
    # Get the items for the current page
    items = ITEMS_DB[start_idx:end_idx]
    
    # Construct pagination metadata
    pagination = {
        "page": page,
        "limit": limit,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    
    # Add navigation links
    links = {}
    if page > 1:
        links["prev"] = f"/items/async?page={page-1}&limit={limit}"
    if page < total_pages:
        links["next"] = f"/items/async?page={page+1}&limit={limit}"
    links["first"] = f"/items/async?page=1&limit={limit}"
    links["last"] = f"/items/async?page={total_pages}&limit={limit}"
    
    # Construct the response
    return {
        "items": items,
        "pagination": pagination,
        "links": links
    }


# Infinite scroll implementation
@api(route="/items/infinite", method="GET")
def get_items_infinite(offset: int = 0, limit: int = 20) -> Dict[str, Any]:
    """
    Get items for infinite scroll pagination.
    
    Args:
        offset: The number of items to skip
        limit: The number of items to return (default: 20, max: 100)
    
    Returns:
        A response suitable for infinite scroll implementation
    """
    # Validate and sanitize parameters
    offset = max(0, offset)  # Ensure offset is non-negative
    limit = max(1, min(100, limit))  # Ensure limit is between 1 and 100
    
    # Calculate end index
    end_idx = min(offset + limit, len(ITEMS_DB))
    
    # Get the items for the current page
    items = ITEMS_DB[offset:end_idx]
    
    # Calculate if there are more items
    has_more = end_idx < len(ITEMS_DB)
    
    # Construct the response
    return {
        "items": items,
        "has_more": has_more,
        "next_offset": end_idx if has_more else None
    }


# Initialize the example data
generate_sample_data(1000)

# Run the API server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000) 