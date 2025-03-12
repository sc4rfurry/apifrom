"""
Example demonstrating database integration with APIFromAnything.

This example shows how to create a RESTful API with database integration
using SQLAlchemy and SQLite. It implements a simple task management API
with CRUD operations.
"""

from typing import List, Dict, Optional
import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

from apifrom import API
from apifrom.decorators.api import api
from apifrom.middleware import CORSMiddleware
from apifrom.security import JWTAuth, SecurityHeadersMiddleware

# Create an API instance
app = API(
    title="Task Management API",
    description="A RESTful API for task management with database integration",
    version="1.0.0",
    debug=True
)

# Add middleware
app.add_middleware(CORSMiddleware(allow_origins=["*"]))
app.add_middleware(SecurityHeadersMiddleware())

# Configure JWT authentication
jwt_auth = JWTAuth(
    secret_key="your-secret-key",  # In production, use a secure secret key
    algorithm="HS256",
    token_location="headers"
)

# Database setup
Base = declarative_base()
DB_PATH = os.path.join(os.path.dirname(__file__), "tasks.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Define database models
class User(Base):
    """User model for database."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship with Task model
    tasks = relationship("Task", back_populates="owner")


class Task(Base):
    """Task model for database."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationship with User model
    owner = relationship("User", back_populates="tasks")


# Create database tables
Base.metadata.create_all(bind=engine)


# Database dependency
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


# Seed initial data
def seed_database():
    """Seed the database with initial data."""
    db = get_db()
    
    # Check if data already exists
    if db.query(User).count() > 0:
        return
    
    # Create users
    users = [
        User(username="alice", email="alice@example.com", password_hash="hashed_password"),
        User(username="bob", email="bob@example.com", password_hash="hashed_password"),
    ]
    db.add_all(users)
    db.commit()
    
    # Create tasks
    tasks = [
        Task(title="Complete project", description="Finish the APIFromAnything project", owner_id=1),
        Task(title="Write documentation", description="Document the API features", owner_id=1),
        Task(title="Test API", description="Test all endpoints", owner_id=2),
    ]
    db.add_all(tasks)
    db.commit()


# API endpoints
@api(app, route="/users", method="GET")
def get_users() -> List[Dict]:
    """
    Get all users.
    
    Returns:
        List of users
    """
    db = get_db()
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        }
        for user in users
    ]


@api(app, route="/users/{user_id}", method="GET")
def get_user(user_id: int) -> Dict:
    """
    Get a user by ID.
    
    Args:
        user_id: The user ID
        
    Returns:
        User details
    """
    db = get_db()
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return {"error": "User not found"}
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "completed": task.completed,
            }
            for task in user.tasks
        ]
    }


@api(app, route="/users", method="POST")
def create_user(username: str, email: str, password: str) -> Dict:
    """
    Create a new user.
    
    Args:
        username: The username
        email: The email address
        password: The password
        
    Returns:
        Created user details
    """
    db = get_db()
    
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        return {"error": "Username or email already exists"}
    
    # In a real application, you would hash the password
    password_hash = f"hashed_{password}"
    
    # Create new user
    new_user = User(
        username=username,
        email=email,
        password_hash=password_hash
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "created_at": new_user.created_at.isoformat(),
    }


@api(app, route="/tasks", method="GET")
def get_tasks(completed: Optional[bool] = None) -> List[Dict]:
    """
    Get all tasks, optionally filtered by completion status.
    
    Args:
        completed: Filter by completion status
        
    Returns:
        List of tasks
    """
    db = get_db()
    query = db.query(Task)
    
    if completed is not None:
        query = query.filter(Task.completed == completed)
    
    tasks = query.all()
    
    return [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "completed": task.completed,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "owner_id": task.owner_id,
        }
        for task in tasks
    ]


@api(app, route="/tasks/{task_id}", method="GET")
def get_task(task_id: int) -> Dict:
    """
    Get a task by ID.
    
    Args:
        task_id: The task ID
        
    Returns:
        Task details
    """
    db = get_db()
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        return {"error": "Task not found"}
    
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "completed": task.completed,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "owner_id": task.owner_id,
        "owner": {
            "id": task.owner.id,
            "username": task.owner.username,
            "email": task.owner.email,
        }
    }


@api(app, route="/tasks", method="POST")
@jwt_auth.requires_auth
def create_task(title: str, description: str, owner_id: int) -> Dict:
    """
    Create a new task.
    
    Args:
        title: The task title
        description: The task description
        owner_id: The owner's user ID
        
    Returns:
        Created task details
    """
    db = get_db()
    
    # Check if owner exists
    owner = db.query(User).filter(User.id == owner_id).first()
    if not owner:
        return {"error": "Owner not found"}
    
    # Create new task
    new_task = Task(
        title=title,
        description=description,
        owner_id=owner_id
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return {
        "id": new_task.id,
        "title": new_task.title,
        "description": new_task.description,
        "completed": new_task.completed,
        "created_at": new_task.created_at.isoformat(),
        "updated_at": new_task.updated_at.isoformat(),
        "owner_id": new_task.owner_id,
    }


@api(app, route="/tasks/{task_id}", method="PUT")
@jwt_auth.requires_auth
def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None
) -> Dict:
    """
    Update a task.
    
    Args:
        task_id: The task ID
        title: The new title (optional)
        description: The new description (optional)
        completed: The new completion status (optional)
        
    Returns:
        Updated task details
    """
    db = get_db()
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        return {"error": "Task not found"}
    
    # Update fields if provided
    if title is not None:
        task.title = title
    
    if description is not None:
        task.description = description
    
    if completed is not None:
        task.completed = completed
    
    # Update the task
    db.commit()
    db.refresh(task)
    
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "completed": task.completed,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "owner_id": task.owner_id,
    }


@api(app, route="/tasks/{task_id}", method="DELETE")
@jwt_auth.requires_auth
def delete_task(task_id: int) -> Dict:
    """
    Delete a task.
    
    Args:
        task_id: The task ID
        
    Returns:
        Deletion status
    """
    db = get_db()
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        return {"error": "Task not found"}
    
    # Delete the task
    db.delete(task)
    db.commit()
    
    return {"message": f"Task {task_id} deleted successfully"}


@api(app, route="/users/{user_id}/tasks", method="GET")
def get_user_tasks(user_id: int, completed: Optional[bool] = None) -> List[Dict]:
    """
    Get all tasks for a specific user.
    
    Args:
        user_id: The user ID
        completed: Filter by completion status
        
    Returns:
        List of user's tasks
    """
    db = get_db()
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}
    
    # Query tasks
    query = db.query(Task).filter(Task.owner_id == user_id)
    
    if completed is not None:
        query = query.filter(Task.completed == completed)
    
    tasks = query.all()
    
    return [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "completed": task.completed,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        }
        for task in tasks
    ]


@api(app, route="/auth/login", method="POST")
def login(username: str, password: str) -> Dict:
    """
    Authenticate a user and return a JWT token.
    
    Args:
        username: The username
        password: The password
        
    Returns:
        Authentication result with JWT token
    """
    db = get_db()
    user = db.query(User).filter(User.username == username).first()
    
    # In a real application, you would verify the password hash
    if not user or user.password_hash != f"hashed_{password}":
        return {"error": "Invalid username or password"}
    
    # Generate JWT token
    token = jwt_auth.create_token(
        payload={
            "sub": user.username,
            "user_id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    }


# Main entry point
if __name__ == "__main__":
    # Seed the database with initial data
    seed_database()
    
    # Run the API server
    app.run(host="127.0.0.1", port=8000)
    
    print("\nTask Management API running at http://127.0.0.1:8000")
    print("\nAvailable endpoints:")
    print("  - GET /users: Get all users")
    print("  - GET /users/{user_id}: Get a user by ID")
    print("  - POST /users: Create a new user")
    print("  - GET /tasks: Get all tasks")
    print("  - GET /tasks/{task_id}: Get a task by ID")
    print("  - POST /tasks: Create a new task (requires authentication)")
    print("  - PUT /tasks/{task_id}: Update a task (requires authentication)")
    print("  - DELETE /tasks/{task_id}: Delete a task (requires authentication)")
    print("  - GET /users/{user_id}/tasks: Get all tasks for a specific user")
    print("  - POST /auth/login: Authenticate a user and get a JWT token")
    print("\nExample authentication flow:")
    print("1. Create a user: POST /users")
    print("2. Login: POST /auth/login")
    print("3. Use the returned JWT token in the Authorization header for protected endpoints") 