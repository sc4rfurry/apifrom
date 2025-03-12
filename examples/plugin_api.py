"""
Plugin system example using APIFromAnything.

This example demonstrates how to use the plugin system to extend the
functionality of an API created with the APIFromAnything library.
"""

import logging
import time
from typing import Dict, List

from apifrom import API, api, Plugin, PluginManager
from apifrom.core.request import Request
from apifrom.core.response import Response
from apifrom.plugins import LoggingPlugin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create API instance
app = API(
    title="Plugin API Example",
    description="An API with plugins created with APIFromAnything",
    version="1.0.0",
    debug=True
)

# Create and register the logging plugin
logging_plugin = LoggingPlugin(
    log_request_body=True,
    log_response_body=True,
    log_headers=True,
    exclude_paths=["/health"],
)
app.plugin_manager.register(logging_plugin)


# Create a custom plugin
class TimingPlugin(Plugin):
    """
    Plugin for timing API requests.
    """
    
    @property
    def name(self) -> str:
        return "timing"
    
    @property
    def description(self) -> str:
        return "Measures and logs the execution time of API requests"
    
    def initialize(self, api: API) -> None:
        logger.info(f"Initializing {self.name} plugin")
    
    def pre_request(self, request: Request) -> Request:
        # Store the start time
        request.state.timing_start_time = time.time()
        return request
    
    def post_response(self, response: Response, request: Request) -> Response:
        # Calculate the execution time
        start_time = getattr(request.state, "timing_start_time", None)
        if start_time:
            execution_time = time.time() - start_time
            logger.info(f"Request to {request.path} took {execution_time:.4f} seconds")
            
            # Add timing header to the response
            response.headers["X-Execution-Time"] = f"{execution_time:.4f}"
        
        return response


# Register the custom plugin
timing_plugin = TimingPlugin()
app.plugin_manager.register(timing_plugin)


# Simulated database
tasks_db = [
    {"id": 1, "title": "Learn APIFromAnything", "completed": False},
    {"id": 2, "title": "Create a plugin", "completed": False},
    {"id": 3, "title": "Build an API", "completed": True},
]


@api(route="/tasks", method="GET")
def get_tasks() -> List[Dict]:
    """
    Get all tasks.
    
    Returns:
        A list of task objects
    """
    logger.info("Fetching tasks...")
    time.sleep(0.1)  # Simulate a delay
    return tasks_db


@api(route="/tasks/{task_id}", method="GET")
def get_task(task_id: int) -> Dict:
    """
    Get a task by ID.
    
    Args:
        task_id: The ID of the task to retrieve
        
    Returns:
        A task object
    """
    logger.info(f"Fetching task {task_id}...")
    time.sleep(0.05)  # Simulate a delay
    
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    
    return {"error": "Task not found"}


@api(route="/tasks", method="POST")
def create_task(title: str) -> Dict:
    """
    Create a new task.
    
    Args:
        title: The title of the task
        
    Returns:
        The created task object
    """
    logger.info("Creating new task...")
    time.sleep(0.2)  # Simulate a delay
    
    task_id = max(task["id"] for task in tasks_db) + 1
    new_task = {"id": task_id, "title": title, "completed": False}
    tasks_db.append(new_task)
    
    return new_task


@api(route="/tasks/{task_id}", method="PUT")
def update_task(task_id: int, title: str = None, completed: bool = None) -> Dict:
    """
    Update a task.
    
    Args:
        task_id: The ID of the task to update
        title: The new title of the task (optional)
        completed: The new completion status of the task (optional)
        
    Returns:
        The updated task object
    """
    logger.info(f"Updating task {task_id}...")
    time.sleep(0.15)  # Simulate a delay
    
    for task in tasks_db:
        if task["id"] == task_id:
            if title is not None:
                task["title"] = title
            if completed is not None:
                task["completed"] = completed
            return task
    
    return {"error": "Task not found"}


@api(route="/tasks/{task_id}", method="DELETE")
def delete_task(task_id: int) -> Dict:
    """
    Delete a task.
    
    Args:
        task_id: The ID of the task to delete
        
    Returns:
        A success message
    """
    logger.info(f"Deleting task {task_id}...")
    time.sleep(0.1)  # Simulate a delay
    
    global tasks_db
    for i, task in enumerate(tasks_db):
        if task["id"] == task_id:
            del tasks_db[i]
            return {"message": f"Task with ID {task_id} deleted successfully"}
    
    return {"error": "Task not found"}


@api(route="/health", method="GET")
def health_check() -> Dict:
    """
    Health check endpoint.
    
    This endpoint is excluded from logging.
    
    Returns:
        A health status
    """
    return {"status": "healthy"}


@api(route="/error", method="GET")
def trigger_error() -> Dict:
    """
    Trigger an error.
    
    This endpoint intentionally raises an exception to demonstrate error handling.
    
    Returns:
        Never returns normally
    """
    logger.info("Triggering an error...")
    raise ValueError("This is a test error")


if __name__ == "__main__":
    # Run the API server
    app.run(host="0.0.0.0", port=8006) 