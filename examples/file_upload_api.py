"""
Example demonstrating file upload functionality with APIFromAnything.

This example shows how to create an API that handles file uploads,
including validation, storage, and retrieval of uploaded files.
"""

import os
import uuid
import mimetypes
from typing import Dict, List, Optional
from datetime import datetime

from apifrom import API
from apifrom.decorators.api import api
from apifrom.middleware import CORSMiddleware
from apifrom.security import SecurityHeadersMiddleware, JWTAuth
from apifrom.core.request import Request
from apifrom.core.response import Response


# Create an API instance
app = API(
    title="File Upload API",
    description="An API for handling file uploads",
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

# Configure upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory storage for file metadata
# In a real application, this would be stored in a database
file_metadata = {}


# Helper functions
def get_file_extension(filename: str) -> str:
    """Get the file extension from a filename."""
    return os.path.splitext(filename)[1].lower()


def is_allowed_file(filename: str, allowed_extensions: List[str]) -> bool:
    """Check if a file has an allowed extension."""
    return get_file_extension(filename) in allowed_extensions


def get_safe_filename(filename: str) -> str:
    """Generate a safe filename with a UUID to prevent collisions."""
    extension = get_file_extension(filename)
    return f"{uuid.uuid4().hex}{extension}"


def get_mime_type(filename: str) -> str:
    """Get the MIME type of a file."""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


# API endpoints
@api(app, route="/files", method="GET")
def list_files(file_type: Optional[str] = None) -> Dict:
    """
    List all uploaded files, optionally filtered by file type.
    
    Args:
        file_type: Filter by file type (e.g., 'image', 'document')
        
    Returns:
        List of file metadata
    """
    if file_type:
        filtered_files = {
            file_id: metadata
            for file_id, metadata in file_metadata.items()
            if metadata.get("file_type") == file_type
        }
        return {"files": list(filtered_files.values())}
    
    return {"files": list(file_metadata.values())}


@api(app, route="/files/{file_id}", method="GET")
def get_file_metadata(file_id: str) -> Dict:
    """
    Get metadata for a specific file.
    
    Args:
        file_id: The file ID
        
    Returns:
        File metadata
    """
    if file_id not in file_metadata:
        return {"error": "File not found"}
    
    return file_metadata[file_id]


@api(app, route="/files/{file_id}/download", method="GET")
def download_file(file_id: str) -> Response:
    """
    Download a file.
    
    Args:
        file_id: The file ID
        
    Returns:
        File content as a response
    """
    if file_id not in file_metadata:
        return Response(
            content={"error": "File not found"},
            status_code=404
        )
    
    metadata = file_metadata[file_id]
    file_path = os.path.join(UPLOAD_DIR, metadata["filename"])
    
    if not os.path.exists(file_path):
        return Response(
            content={"error": "File not found on server"},
            status_code=404
        )
    
    with open(file_path, "rb") as f:
        content = f.read()
    
    response = Response(
        content=content,
        status_code=200,
        media_type=metadata["mime_type"]
    )
    
    # Set Content-Disposition header for download
    response.headers["Content-Disposition"] = f"attachment; filename=\"{metadata['original_filename']}\""
    
    return response


@api(app, route="/upload", method="POST")
@jwt_auth.requires_auth
async def upload_file(request: Request) -> Dict:
    """
    Upload a file.
    
    Args:
        request: The request object containing the file
        
    Returns:
        Upload result with file metadata
    """
    # Check if the request contains a file
    if not request.files or "file" not in request.files:
        return {"error": "No file provided"}
    
    file = request.files["file"]
    original_filename = file.filename
    
    # Validate file extension
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".txt"]
    if not is_allowed_file(original_filename, allowed_extensions):
        return {
            "error": "File type not allowed",
            "allowed_extensions": allowed_extensions
        }
    
    # Generate a safe filename
    safe_filename = get_safe_filename(original_filename)
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    
    # Determine file type category
    extension = get_file_extension(original_filename)
    file_type = "image" if extension in [".jpg", ".jpeg", ".png", ".gif"] else "document"
    
    # Generate a file ID
    file_id = str(uuid.uuid4())
    
    # Store file metadata
    metadata = {
        "id": file_id,
        "original_filename": original_filename,
        "filename": safe_filename,
        "file_path": file_path,
        "file_type": file_type,
        "mime_type": get_mime_type(original_filename),
        "size": os.path.getsize(file_path),
        "uploaded_at": datetime.utcnow().isoformat(),
        "uploaded_by": request.state.jwt_payload.get("sub", "anonymous")
    }
    
    file_metadata[file_id] = metadata
    
    return {
        "message": "File uploaded successfully",
        "file": metadata
    }


@api(app, route="/files/{file_id}", method="DELETE")
@jwt_auth.requires_auth
def delete_file(file_id: str) -> Dict:
    """
    Delete a file.
    
    Args:
        file_id: The file ID
        
    Returns:
        Deletion result
    """
    if file_id not in file_metadata:
        return {"error": "File not found"}
    
    metadata = file_metadata[file_id]
    file_path = os.path.join(UPLOAD_DIR, metadata["filename"])
    
    # Delete the file from disk
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Remove metadata
    del file_metadata[file_id]
    
    return {
        "message": f"File {file_id} deleted successfully"
    }


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
    # In a real application, you would verify credentials against a database
    # For this example, we'll use hardcoded credentials
    if username == "admin" and password == "password":
        # Generate JWT token
        token = jwt_auth.create_token(
            payload={
                "sub": username,
                "exp": datetime.utcnow() + datetime.timedelta(hours=24)
            }
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "username": username
            }
        }
    
    return {"error": "Invalid username or password"}


@api(app, route="/upload-form", method="GET")
def upload_form() -> str:
    """
    Return an HTML form for file uploads.
    
    Returns:
        HTML content with a file upload form
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>File Upload Form</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input[type="text"],
            input[type="password"] {
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }
            input[type="file"] {
                display: block;
                margin-top: 5px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
            .result {
                margin-top: 20px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
                display: none;
            }
            .error {
                color: red;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>File Upload Demo</h1>
            
            <div id="login-section">
                <h2>Login</h2>
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" value="admin">
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" value="password">
                </div>
                <button id="login-button">Login</button>
                <div id="login-error" class="error"></div>
            </div>
            
            <div id="upload-section" style="display: none;">
                <h2>Upload File</h2>
                <div class="form-group">
                    <label for="file">Select a file:</label>
                    <input type="file" id="file" name="file">
                </div>
                <button id="upload-button">Upload</button>
                <div id="upload-error" class="error"></div>
                
                <div id="result" class="result">
                    <h3>Upload Result</h3>
                    <pre id="result-json"></pre>
                </div>
                
                <h2>Your Files</h2>
                <button id="list-files-button">Refresh File List</button>
                <div id="file-list"></div>
            </div>
        </div>
        
        <script>
            let token = '';
            
            // Login function
            document.getElementById('login-button').addEventListener('click', async () => {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                try {
                    const response = await fetch('/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ username, password })
                    });
                    
                    const data = await response.json();
                    
                    if (data.error) {
                        document.getElementById('login-error').textContent = data.error;
                    } else {
                        token = data.access_token;
                        document.getElementById('login-section').style.display = 'none';
                        document.getElementById('upload-section').style.display = 'block';
                        listFiles();
                    }
                } catch (error) {
                    document.getElementById('login-error').textContent = 'Login failed: ' + error.message;
                }
            });
            
            // Upload function
            document.getElementById('upload-button').addEventListener('click', async () => {
                const fileInput = document.getElementById('file');
                const file = fileInput.files[0];
                
                if (!file) {
                    document.getElementById('upload-error').textContent = 'Please select a file';
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        },
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.error) {
                        document.getElementById('upload-error').textContent = data.error;
                    } else {
                        document.getElementById('result').style.display = 'block';
                        document.getElementById('result-json').textContent = JSON.stringify(data, null, 2);
                        fileInput.value = '';
                        listFiles();
                    }
                } catch (error) {
                    document.getElementById('upload-error').textContent = 'Upload failed: ' + error.message;
                }
            });
            
            // List files function
            async function listFiles() {
                try {
                    const response = await fetch('/files');
                    const data = await response.json();
                    
                    const fileListElement = document.getElementById('file-list');
                    fileListElement.innerHTML = '';
                    
                    if (data.files && data.files.length > 0) {
                        const table = document.createElement('table');
                        table.style.width = '100%';
                        table.style.borderCollapse = 'collapse';
                        table.style.marginTop = '10px';
                        
                        // Create table header
                        const thead = document.createElement('thead');
                        const headerRow = document.createElement('tr');
                        
                        ['Filename', 'Type', 'Size', 'Uploaded At', 'Actions'].forEach(text => {
                            const th = document.createElement('th');
                            th.textContent = text;
                            th.style.border = '1px solid #ddd';
                            th.style.padding = '8px';
                            th.style.textAlign = 'left';
                            headerRow.appendChild(th);
                        });
                        
                        thead.appendChild(headerRow);
                        table.appendChild(thead);
                        
                        // Create table body
                        const tbody = document.createElement('tbody');
                        
                        data.files.forEach(file => {
                            const row = document.createElement('tr');
                            
                            // Filename
                            const filenameCell = document.createElement('td');
                            filenameCell.textContent = file.original_filename;
                            filenameCell.style.border = '1px solid #ddd';
                            filenameCell.style.padding = '8px';
                            row.appendChild(filenameCell);
                            
                            // Type
                            const typeCell = document.createElement('td');
                            typeCell.textContent = file.file_type;
                            typeCell.style.border = '1px solid #ddd';
                            typeCell.style.padding = '8px';
                            row.appendChild(typeCell);
                            
                            // Size
                            const sizeCell = document.createElement('td');
                            sizeCell.textContent = formatFileSize(file.size);
                            sizeCell.style.border = '1px solid #ddd';
                            sizeCell.style.padding = '8px';
                            row.appendChild(sizeCell);
                            
                            // Uploaded At
                            const uploadedAtCell = document.createElement('td');
                            uploadedAtCell.textContent = new Date(file.uploaded_at).toLocaleString();
                            uploadedAtCell.style.border = '1px solid #ddd';
                            uploadedAtCell.style.padding = '8px';
                            row.appendChild(uploadedAtCell);
                            
                            // Actions
                            const actionsCell = document.createElement('td');
                            actionsCell.style.border = '1px solid #ddd';
                            actionsCell.style.padding = '8px';
                            
                            // Download button
                            const downloadButton = document.createElement('button');
                            downloadButton.textContent = 'Download';
                            downloadButton.style.marginRight = '5px';
                            downloadButton.style.backgroundColor = '#4CAF50';
                            downloadButton.addEventListener('click', () => {
                                window.location.href = `/files/${file.id}/download`;
                            });
                            actionsCell.appendChild(downloadButton);
                            
                            // Delete button
                            const deleteButton = document.createElement('button');
                            deleteButton.textContent = 'Delete';
                            deleteButton.style.backgroundColor = '#f44336';
                            deleteButton.addEventListener('click', async () => {
                                if (confirm('Are you sure you want to delete this file?')) {
                                    try {
                                        const response = await fetch(`/files/${file.id}`, {
                                            method: 'DELETE',
                                            headers: {
                                                'Authorization': `Bearer ${token}`
                                            }
                                        });
                                        
                                        const data = await response.json();
                                        
                                        if (data.error) {
                                            alert(data.error);
                                        } else {
                                            listFiles();
                                        }
                                    } catch (error) {
                                        alert('Delete failed: ' + error.message);
                                    }
                                }
                            });
                            actionsCell.appendChild(deleteButton);
                            
                            row.appendChild(actionsCell);
                            
                            tbody.appendChild(row);
                        });
                        
                        table.appendChild(tbody);
                        fileListElement.appendChild(table);
                    } else {
                        fileListElement.textContent = 'No files uploaded yet.';
                    }
                } catch (error) {
                    console.error('Error listing files:', error);
                }
            }
            
            // Format file size
            function formatFileSize(bytes) {
                if (bytes < 1024) {
                    return bytes + ' B';
                } else if (bytes < 1024 * 1024) {
                    return (bytes / 1024).toFixed(2) + ' KB';
                } else if (bytes < 1024 * 1024 * 1024) {
                    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
                } else {
                    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
                }
            }
            
            // List files button
            document.getElementById('list-files-button').addEventListener('click', listFiles);
        </script>
    </body>
    </html>
    """


# Main entry point
if __name__ == "__main__":
    # Run the API server
    app.run(host="127.0.0.1", port=8000)
    
    print("\nFile Upload API running at http://127.0.0.1:8000")
    print("\nAvailable endpoints:")
    print("  - GET /upload-form: HTML form for file uploads")
    print("  - POST /upload: Upload a file (requires authentication)")
    print("  - GET /files: List all uploaded files")
    print("  - GET /files/{file_id}: Get metadata for a specific file")
    print("  - GET /files/{file_id}/download: Download a file")
    print("  - DELETE /files/{file_id}: Delete a file (requires authentication)")
    print("  - POST /auth/login: Authenticate a user and get a JWT token")
    print("\nExample usage:")
    print("1. Visit http://127.0.0.1:8000/upload-form to use the web interface")
    print("2. Login with username 'admin' and password 'password'")
    print("3. Upload files and manage them through the interface") 