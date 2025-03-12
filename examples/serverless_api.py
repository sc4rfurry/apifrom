"""
Example demonstrating how to use APIFromAnything in serverless environments.

This example shows how to create an API that can be deployed to AWS Lambda,
Google Cloud Functions, or Azure Functions using the appropriate adapters.
"""

from typing import Dict, List, Optional
import json
import os

from apifrom.core.app import APIApp
from apifrom.decorators.api import api
from apifrom.monitoring.metrics import MetricsCollector
from apifrom.monitoring.exporters import JSONExporter

# Determine which serverless platform to use based on environment variable
# This would be set differently in each serverless environment
PLATFORM = os.environ.get('SERVERLESS_PLATFORM', 'aws')

# Create an API application
app = APIApp(title="Serverless API Example")

# Create a metrics collector
metrics = MetricsCollector()

# In-memory database for demonstration purposes
# In a real serverless application, you would use a persistent database
tasks_db = [
    {"id": 1, "title": "Task 1", "completed": False},
    {"id": 2, "title": "Task 2", "completed": True},
]


# Define API endpoints
@api(app)
def get_tasks() -> List[Dict]:
    """
    Get all tasks.
    
    Returns:
        A list of all tasks.
    """
    # Track this request with a custom metric
    metrics.increment("tasks_retrieved")
    
    return tasks_db


@api(app)
def get_task(task_id: int) -> Dict:
    """
    Get a task by ID.
    
    Args:
        task_id: The ID of the task to retrieve.
        
    Returns:
        The task with the specified ID, or an error message if not found.
    """
    # Track this request with a custom metric
    metrics.increment("task_retrieved")
    
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    
    # Track not found errors
    metrics.increment("task_not_found")
    
    return {"error": "Task not found"}


@api(app)
def create_task(title: str, completed: bool = False) -> Dict:
    """
    Create a new task.
    
    Args:
        title: The title of the task.
        completed: Whether the task is completed (default: False).
        
    Returns:
        The newly created task.
    """
    # Track this request with a custom metric
    metrics.increment("task_created")
    
    # Generate a new ID
    task_id = max(task["id"] for task in tasks_db) + 1
    
    # Create the new task
    new_task = {"id": task_id, "title": title, "completed": completed}
    
    # Add it to the database
    tasks_db.append(new_task)
    
    return new_task


@api(app)
def update_task(task_id: int, title: Optional[str] = None, completed: Optional[bool] = None) -> Dict:
    """
    Update a task.
    
    Args:
        task_id: The ID of the task to update.
        title: The new title of the task (optional).
        completed: The new completed status of the task (optional).
        
    Returns:
        The updated task, or an error message if not found.
    """
    # Track this request with a custom metric
    metrics.increment("task_updated")
    
    for task in tasks_db:
        if task["id"] == task_id:
            if title is not None:
                task["title"] = title
            if completed is not None:
                task["completed"] = completed
            return task
    
    # Track not found errors
    metrics.increment("task_not_found")
    
    return {"error": "Task not found"}


@api(app)
def delete_task(task_id: int) -> Dict:
    """
    Delete a task.
    
    Args:
        task_id: The ID of the task to delete.
        
    Returns:
        A success message, or an error message if not found.
    """
    # Track this request with a custom metric
    metrics.increment("task_deleted")
    
    for i, task in enumerate(tasks_db):
        if task["id"] == task_id:
            del tasks_db[i]
            return {"message": "Task deleted"}
    
    # Track not found errors
    metrics.increment("task_not_found")
    
    return {"error": "Task not found"}


@api(app)
def get_metrics() -> str:
    """
    Get metrics for the API.
    
    Returns:
        JSON string containing metrics data.
    """
    exporter = JSONExporter(metrics)
    return exporter.export(pretty=True)


# Create the appropriate adapter based on the platform
if PLATFORM == 'aws':
    # AWS Lambda adapter
    from apifrom.adapters.aws_lambda import LambdaAdapter
    
    adapter = LambdaAdapter(app)
    
    def lambda_handler(event, context):
        """AWS Lambda handler function."""
        return adapter.handle(event, context)

elif PLATFORM == 'gcp':
    # Google Cloud Functions adapter
    from apifrom.adapters.gcp_functions import CloudFunctionAdapter
    
    adapter = CloudFunctionAdapter(app)
    
    def cloud_function_handler(request):
        """Google Cloud Function handler function."""
        return adapter.handle(request)

elif PLATFORM == 'azure':
    # Azure Functions adapter
    import azure.functions as func
    from apifrom.adapters.azure_functions import AzureFunctionAdapter
    
    adapter = AzureFunctionAdapter(app)
    
    def azure_function_handler(req: func.HttpRequest) -> func.HttpResponse:
        """Azure Function handler function."""
        return adapter.handle(req)

else:
    # Local development server
    if __name__ == "__main__":
        print("Starting local development server...")
        app.run(host="0.0.0.0", port=8000) 