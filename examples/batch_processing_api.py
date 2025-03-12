"""
Batch Processing Example for APIFromAnything.

This example demonstrates how to use batch processing in APIFromAnything
to efficiently process multiple similar operations in bulk.
"""

import asyncio
import time
import random
from typing import List, Dict, Any

from apifrom import API, api
from apifrom.performance import (
    BatchProcessor,
    batch_process,
    Web
)

# Create an API instance
app = API(
    title="Batch Processing Example API",
    description="An example of using batch processing in APIFromAnything",
    version="1.0.0"
)

# Simulate a database
users_db = []

# Simulate a slow operation (e.g. database query, external API call)
async def slow_operation(delay=0.1):
    await asyncio.sleep(delay)


#
# Example 1: Using the @batch_process decorator
#

@api(route="/users/batch", method="POST")
@batch_process(max_batch_size=100, max_wait_time=0.1)
async def create_users_batch(batch_data):
    """
    Create multiple users in a batch.
    
    Instead of creating users one at a time with multiple requests,
    this endpoint collects requests and processes them in a batch.
    """
    # Simulate database operation
    await slow_operation()
    
    # The batch_data is a list of (args, kwargs) tuples
    results = []
    user_id_start = len(users_db) + 1
    
    # Process each item in the batch
    for i, ((request,), kwargs) in enumerate(batch_data):
        # Extract user data from the request
        user_data = await request.json()
        
        # Create the user
        user_id = user_id_start + i
        new_user = {
            "id": user_id,
            "name": user_data.get("name", ""),
            "email": user_data.get("email", ""),
            "created_at": time.time()
        }
        
        # Add to the database
        users_db.append(new_user)
        
        # Add to results
        results.append(new_user)
    
    return results


#
# Example 2: Using the Web.optimize decorator with batch processing
#

@api(route="/users/web-batch", method="POST")
@Web.optimize(
    batch_processing=True,
    batch_size=50,
    cache_ttl=30
)
async def create_users_web_batch(request):
    """
    Create a user (optimized with Web.optimize).
    
    This endpoint uses the Web.optimize decorator to enable batch processing.
    It works similarly to the above example but uses a more general-purpose optimizer.
    """
    # Get user data from the request
    user_data = await request.json()
    
    # Simulate database operation
    await slow_operation()
    
    # Create the user
    user_id = len(users_db) + 1
    new_user = {
        "id": user_id,
        "name": user_data.get("name", ""),
        "email": user_data.get("email", ""),
        "created_at": time.time()
    }
    
    # Add to the database
    users_db.append(new_user)
    
    return new_user


#
# Example 3: Using BatchProcessor directly for batch operations
#

@api(route="/operations/batch", method="POST")
async def batch_operations(request):
    """
    Process multiple operations in a single request.
    
    This endpoint demonstrates using BatchProcessor directly to
    process different types of operations in a single batch request.
    """
    # Get operations from the request
    data = await request.json()
    operations = data.get("operations", [])
    
    # Define a function to process each operation
    async def process_operation(op):
        op_type = op.get("type")
        
        # Simulate database operation
        await slow_operation(delay=0.05)
        
        if op_type == "create_user":
            # Create a user
            user_id = len(users_db) + 1
            new_user = {
                "id": user_id,
                "name": op.get("name", ""),
                "email": op.get("email", ""),
                "created_at": time.time()
            }
            users_db.append(new_user)
            return {"status": "created", "user": new_user}
        
        elif op_type == "get_user":
            # Get a user
            user_id = op.get("id")
            for user in users_db:
                if user["id"] == user_id:
                    return {"status": "found", "user": user}
            return {"status": "not_found", "id": user_id}
        
        elif op_type == "update_user":
            # Update a user
            user_id = op.get("id")
            for user in users_db:
                if user["id"] == user_id:
                    if "name" in op:
                        user["name"] = op["name"]
                    if "email" in op:
                        user["email"] = op["email"]
                    return {"status": "updated", "user": user}
            return {"status": "not_found", "id": user_id}
        
        elif op_type == "delete_user":
            # Delete a user
            user_id = op.get("id")
            for i, user in enumerate(users_db):
                if user["id"] == user_id:
                    del users_db[i]
                    return {"status": "deleted", "id": user_id}
            return {"status": "not_found", "id": user_id}
        
        else:
            # Unknown operation
            return {"status": "error", "message": f"Unknown operation type: {op_type}"}
    
    # Process all operations in parallel batches
    results = await BatchProcessor.map(
        process_operation,
        operations,
        batch_size=20,
        worker_count=5
    )
    
    return {"results": results}


#
# Example 4: Performance comparison
#

@api(route="/performance-test", method="GET")
async def performance_test():
    """
    Run a performance test to compare batch vs. individual processing.
    """
    # Test parameters
    num_users = 100
    batch_size = 20
    
    # Generate test data
    test_users = []
    for i in range(num_users):
        test_users.append({
            "name": f"Test User {i}",
            "email": f"user{i}@example.com"
        })
    
    # Test individual processing
    start_time = time.time()
    individual_results = []
    
    for user_data in test_users:
        # Create a user
        user_id = len(users_db) + 1
        new_user = {
            "id": user_id,
            "name": user_data.get("name", ""),
            "email": user_data.get("email", ""),
            "created_at": time.time()
        }
        
        # Simulate database operation
        await slow_operation(delay=0.01)
        
        # Add to the database
        users_db.append(new_user)
        individual_results.append(new_user)
    
    individual_time = time.time() - start_time
    
    # Reset database
    users_db.clear()
    
    # Test batch processing
    start_time = time.time()
    
    # Define a function to process a batch
    async def process_batch(batch):
        # Simulate database operation (one per batch)
        await slow_operation(delay=0.01)
        
        results = []
        user_id_start = len(users_db) + 1
        
        # Process each item in the batch
        for i, user_data in enumerate(batch):
            # Create the user
            user_id = user_id_start + i
            new_user = {
                "id": user_id,
                "name": user_data.get("name", ""),
                "email": user_data.get("email", ""),
                "created_at": time.time()
            }
            
            # Add to the database
            users_db.append(new_user)
            
            # Add to results
            results.append(new_user)
        
        return results
    
    # Split users into batches
    batches = [test_users[i:i+batch_size] for i in range(0, len(test_users), batch_size)]
    
    # Process batches
    batch_results = []
    for batch in batches:
        results = await process_batch(batch)
        batch_results.extend(results)
    
    batch_time = time.time() - start_time
    
    # Return performance results
    return {
        "individual_processing": {
            "time": individual_time,
            "users_processed": len(individual_results)
        },
        "batch_processing": {
            "time": batch_time,
            "users_processed": len(batch_results),
            "num_batches": len(batches),
            "batch_size": batch_size
        },
        "improvement": {
            "time_saved": individual_time - batch_time,
            "speedup_factor": individual_time / batch_time if batch_time > 0 else "infinite"
        }
    }


# Run the API server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000) 