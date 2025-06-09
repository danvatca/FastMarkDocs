"""
Basic example demonstrating FastAPI Markdown Docs usage.

This example shows how to enhance a FastAPI application with documentation
loaded from markdown files.
"""

from fastapi import FastAPI, HTTPException
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add the src directory to the path so we can import the library
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi_markdown_docs import (
    MarkdownDocumentationLoader, 
    enhance_openapi_with_docs,
    CodeLanguage
)

# Create FastAPI app
app = FastAPI(
    title="Example API",
    description="An example API demonstrating FastAPI Markdown Docs",
    version="1.0.0"
)

# Pydantic models
class User(BaseModel):
    id: int
    name: str
    email: str
    active: bool = True

class UserCreate(BaseModel):
    name: str
    email: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    active: Optional[bool] = None

# Sample data
users_db = [
    User(id=1, name="John Doe", email="john@example.com"),
    User(id=2, name="Jane Smith", email="jane@example.com"),
    User(id=3, name="Bob Johnson", email="bob@example.com", active=False),
]

# API Routes
@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "message": "Welcome to the Example API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/users", response_model=List[User])
async def list_users(active_only: bool = True):
    """List all users, optionally filtering by active status."""
    if active_only:
        return [user for user in users_db if user.active]
    return users_db

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """Get a specific user by ID."""
    for user in users_db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/users", response_model=User)
async def create_user(user: UserCreate):
    """Create a new user."""
    new_id = max(u.id for u in users_db) + 1 if users_db else 1
    new_user = User(id=new_id, **user.dict())
    users_db.append(new_user)
    return new_user

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate):
    """Update an existing user."""
    for i, user in enumerate(users_db):
        if user.id == user_id:
            update_data = user_update.dict(exclude_unset=True)
            updated_user = user.copy(update=update_data)
            users_db[i] = updated_user
            return updated_user
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user."""
    for i, user in enumerate(users_db):
        if user.id == user_id:
            deleted_user = users_db.pop(i)
            return {"message": f"User {deleted_user.name} deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found")

# Documentation enhancement
def create_enhanced_openapi():
    """Create enhanced OpenAPI schema with markdown documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    # Generate base OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    try:
        # Configure documentation loader
        docs_config = {
            'docs_directory': os.path.join(os.path.dirname(__file__), 'docs'),
            'recursive': True,
            'cache_enabled': True,
            'supported_languages': [
                CodeLanguage.CURL,
                CodeLanguage.PYTHON,
                CodeLanguage.JAVASCRIPT
            ]
        }
        
        # Configure enhancement
        enhancement_config = {
            'include_code_samples': True,
            'include_response_examples': True,
            'include_parameter_examples': True,
            'base_url': 'http://localhost:8000',
            'code_sample_languages': [
                CodeLanguage.CURL,
                CodeLanguage.PYTHON,
                CodeLanguage.JAVASCRIPT
            ],
            'custom_headers': {
                'User-Agent': 'ExampleApp/1.0'
            }
        }
        
        # Load documentation and enhance schema
        docs_loader = MarkdownDocumentationLoader(docs_config)
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema, 
            docs_loader, 
            enhancement_config
        )
        
        app.openapi_schema = enhanced_schema
        return enhanced_schema
        
    except Exception as e:
        # Fallback to original schema if enhancement fails
        print(f"Warning: Failed to enhance OpenAPI schema: {e}")
        app.openapi_schema = openapi_schema
        return openapi_schema

# Set the custom OpenAPI function
app.openapi = create_enhanced_openapi

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Example API server...")
    print("API Documentation will be available at:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("  - OpenAPI JSON: http://localhost:8000/openapi.json")
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 