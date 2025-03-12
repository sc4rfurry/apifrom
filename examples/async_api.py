"""
This example demonstrates how to use the APIFromAnything library to create
an API with asynchronous endpoints.
"""
import asyncio
import logging
from typing import List, Dict, Optional

from apifrom import APIApp

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create API instance
app = APIApp(
    title="Async API Example",
    description="An async API created with APIFromAnything",
    version="1.0.0",
    debug=True
)

# Simulated database
tasks = [
    {"id": 1, "title": "Task 1", "completed": False},
    {"id": 2, "title": "Task 2", "completed": True},
    {"id": 3, "title": "Task 3", "completed": False},
]


# Define async API endpoints
@app.api("/tasks")
async def get_tasks() -> List[Dict]:
    """
    Get all tasks.

    This is an async endpoint that simulates a database query.

    Returns:
        A list of tasks
    """
    # Simulate database query
    await asyncio.sleep(0.1)
    return tasks


@app.api("/tasks/{task_id}")
async def get_task(task_id: int) -> Optional[Dict]:
    """
    Get a task by ID.

    Args:
        task_id: The ID of the task to retrieve

    Returns:
        The task if found, None otherwise
    """
    # Simulate database query
    await asyncio.sleep(0.1)
    
    # Find task by ID
    for task in tasks:
        if task["id"] == task_id:
            return task
    
    return None


@app.api("/tasks", methods=["POST"])
async def create_task(title: str) -> Dict:
    """
    Create a new task.

    Args:
        title: The title of the task

    Returns:
        The created task
    """
    # Simulate database operation
    await asyncio.sleep(0.2)
    
    # Create new task
    task_id = max(task["id"] for task in tasks) + 1
    task = {"id": task_id, "title": title, "completed": False}
    tasks.append(task)
    
    return task


@app.api("/tasks/{task_id}", methods=["PUT"])
async def update_task(task_id: int, title: Optional[str] = None, completed: Optional[bool] = None) -> Optional[Dict]:
    """
    Update a task.

    Args:
        task_id: The ID of the task to update
        title: The new title (optional)
        completed: The new completed status (optional)

    Returns:
        The updated task if found, None otherwise
    """
    # Simulate database operation
    await asyncio.sleep(0.2)
    
    # Find and update task
    for task in tasks:
        if task["id"] == task_id:
            if title is not None:
                task["title"] = title
            if completed is not None:
                task["completed"] = completed
            return task
    
    return None


@app.api("/tasks/{task_id}", methods=["DELETE"])
async def delete_task(task_id: int) -> Dict:
    """
    Delete a task.

    Args:
        task_id: The ID of the task to delete

    Returns:
        A success message
    """
    # Simulate database operation
    await asyncio.sleep(0.2)
    
    # Find and remove task
    global tasks
    original_length = len(tasks)
    tasks = [task for task in tasks if task["id"] != task_id]
    
    if len(tasks) < original_length:
        return {"success": True, "message": f"Task {task_id} deleted"}
    else:
        return {"success": False, "message": f"Task {task_id} not found"}


@app.api("/long-running-task")
async def long_running_task() -> Dict:
    """
    A long-running task that demonstrates the benefits of async.

    Returns:
        A success message
    """
    # Simulate a long-running operation
    start_time = asyncio.get_event_loop().time()
    await asyncio.sleep(2.0)  # Simulate 2 seconds of work
    end_time = asyncio.get_event_loop().time()
    
    return {
        "message": "Long-running task completed",
        "execution_time": end_time - start_time
    }


# Run the API server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000) 