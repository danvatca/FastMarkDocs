---
layout: default
title: Examples
description: Real-world examples and tutorials for FastMarkDocs
---

# Examples

This page provides real-world examples and tutorials for using FastMarkDocs in different scenarios.

## Table of Contents

- [Basic FastAPI Integration](#basic-fastapi-integration)
- [E-commerce API Documentation](#e-commerce-api-documentation)
- [Authentication & Authorization](#authentication--authorization)
- [Multi-language Code Samples](#multi-language-code-samples)
- [Custom Templates](#custom-templates)
- [CI/CD Integration](#cicd-integration)
- [Performance Optimization](#performance-optimization)

## Basic FastAPI Integration

### Simple User Management API

Here's a complete example of a FastAPI application with FastMarkDocs integration:

**main.py**
```python
from fastapi import FastAPI, HTTPException
from fastapi.openapi.utils import get_openapi
from fastmarkdocs import enhance_openapi_with_docs
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="User Management API",
    description="A simple user management system with FastMarkDocs",
    version="1.0.0"
)

# Models
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

# In-memory database
users_db = [
    User(id=1, name="John Doe", email="john@example.com"),
    User(id=2, name="Jane Smith", email="jane@example.com"),
]

# Routes
@app.get("/users", response_model=List[User])
async def list_users(active_only: bool = True):
    """List all users."""
    if active_only:
        return [user for user in users_db if user.active]
    return users_db

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """Get a user by ID."""
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
    """Update a user."""
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

# FastMarkDocs integration
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    enhanced_schema = enhance_openapi_with_docs(
        openapi_schema=openapi_schema,
        docs_directory="docs/api",
        base_url="https://api.example.com",
        code_sample_languages=["python", "javascript", "curl"]
    )
    
    app.openapi_schema = enhanced_schema
    return enhanced_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**docs/api/users.md**
```markdown
# User Management API

## GET /users

Retrieve a list of users from the system.

### Description
This endpoint returns a list of users. By default, only active users are returned, 
but you can include inactive users by setting the `active_only` parameter to `false`.

### Parameters
- `active_only` (boolean, optional): Filter to only active users (default: true)

### Response Examples

**Success Response (200)**
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "active": true
  },
  {
    "id": 2,
    "name": "Jane Smith",
    "email": "jane@example.com",
    "active": true
  }
]
```

### Code Examples

```python
import requests

# Get active users only
response = requests.get("https://api.example.com/users")
users = response.json()
print(f"Found {len(users)} active users")

# Get all users
response = requests.get("https://api.example.com/users?active_only=false")
all_users = response.json()
print(f"Found {len(all_users)} total users")
```

```javascript
// Get active users only
const response = await fetch('https://api.example.com/users');
const users = await response.json();
console.log(`Found ${users.length} active users`);

// Get all users
const allResponse = await fetch('https://api.example.com/users?active_only=false');
const allUsers = await allResponse.json();
console.log(`Found ${allUsers.length} total users`);
```

Tags: users, list

## GET /users/{user_id}

Retrieve a specific user by their ID.

### Parameters
- `user_id` (integer, required): The unique identifier for the user

### Response Examples

**Success Response (200)**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "active": true
}
```

**Error Response (404)**
```json
{
  "detail": "User not found"
}
```

### Code Examples

```python
import requests

user_id = 1
response = requests.get(f"https://api.example.com/users/{user_id}")

if response.status_code == 200:
    user = response.json()
    print(f"User: {user['name']} ({user['email']})")
elif response.status_code == 404:
    print("User not found")
```

```javascript
const userId = 1;

try {
  const response = await fetch(`https://api.example.com/users/${userId}`);
  
  if (response.ok) {
    const user = await response.json();
    console.log(`User: ${user.name} (${user.email})`);
  } else if (response.status === 404) {
    console.log('User not found');
  }
} catch (error) {
  console.error('Error:', error);
}
```

Tags: users, details

## POST /users

Create a new user in the system.

### Request Body
```json
{
  "name": "Alice Johnson",
  "email": "alice@example.com"
}
```

### Response Examples

**Success Response (200)**
```json
{
  "id": 3,
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "active": true
}
```

### Code Examples

```python
import requests

user_data = {
    "name": "Alice Johnson",
    "email": "alice@example.com"
}

response = requests.post(
    "https://api.example.com/users",
    json=user_data
)

if response.status_code == 200:
    new_user = response.json()
    print(f"Created user with ID: {new_user['id']}")
```

```javascript
const userData = {
  name: "Alice Johnson",
  email: "alice@example.com"
};

const response = await fetch('https://api.example.com/users', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(userData)
});

if (response.ok) {
  const newUser = await response.json();
  console.log(`Created user with ID: ${newUser.id}`);
}
```

Tags: users, create
```

## E-commerce API Documentation

### Product Catalog API

**docs/api/products.md**
```markdown
# Product Catalog API

## GET /products

Retrieve a list of products with optional filtering and pagination.

### Description
This endpoint returns a paginated list of products. You can filter by category, 
price range, and search by name or description.

### Parameters
- `category` (string, optional): Filter by product category
- `min_price` (number, optional): Minimum price filter
- `max_price` (number, optional): Maximum price filter
- `search` (string, optional): Search in product name and description
- `page` (integer, optional): Page number for pagination (default: 1)
- `limit` (integer, optional): Number of products per page (default: 20, max: 100)

### Response Examples

**Success Response (200)**
```json
{
  "products": [
    {
      "id": 1,
      "name": "Wireless Headphones",
      "description": "High-quality wireless headphones with noise cancellation",
      "price": 199.99,
      "category": "electronics",
      "in_stock": true,
      "image_url": "https://example.com/images/headphones.jpg"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

### Code Examples

```python
import requests

# Basic product listing
response = requests.get("https://api.example.com/products")
data = response.json()
products = data['products']

# Filter by category and price range
params = {
    "category": "electronics",
    "min_price": 100,
    "max_price": 500,
    "page": 1,
    "limit": 10
}
response = requests.get("https://api.example.com/products", params=params)
filtered_products = response.json()['products']
```

```javascript
// Basic product listing
const response = await fetch('https://api.example.com/products');
const data = await response.json();
const products = data.products;

// Filter by category and price range
const params = new URLSearchParams({
  category: 'electronics',
  min_price: '100',
  max_price: '500',
  page: '1',
  limit: '10'
});

const filteredResponse = await fetch(`https://api.example.com/products?${params}`);
const filteredData = await filteredResponse.json();
const filteredProducts = filteredData.products;
```

Tags: products, catalog, search

## POST /products

Create a new product in the catalog.

### Request Body
```json
{
  "name": "Smart Watch",
  "description": "Feature-rich smartwatch with health monitoring",
  "price": 299.99,
  "category": "electronics",
  "in_stock": true,
  "image_url": "https://example.com/images/smartwatch.jpg"
}
```

### Response Examples

**Success Response (201)**
```json
{
  "id": 2,
  "name": "Smart Watch",
  "description": "Feature-rich smartwatch with health monitoring",
  "price": 299.99,
  "category": "electronics",
  "in_stock": true,
  "image_url": "https://example.com/images/smartwatch.jpg",
  "created_at": "2023-12-01T10:00:00Z"
}
```

### Code Examples

```python
import requests

product_data = {
    "name": "Smart Watch",
    "description": "Feature-rich smartwatch with health monitoring",
    "price": 299.99,
    "category": "electronics",
    "in_stock": True,
    "image_url": "https://example.com/images/smartwatch.jpg"
}

response = requests.post(
    "https://api.example.com/products",
    json=product_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

if response.status_code == 201:
    new_product = response.json()
    print(f"Created product: {new_product['name']} (ID: {new_product['id']})")
```

Tags: products, create, admin
```

## Authentication & Authorization

### JWT Authentication Example

**docs/api/auth.md**
```markdown
# Authentication API

## POST /auth/login

Authenticate a user and receive a JWT token.

### Description
This endpoint authenticates a user with email and password, returning a JWT token
that can be used for subsequent API requests.

### Request Body
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

### Response Examples

**Success Response (200)**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

**Error Response (401)**
```json
{
  "detail": "Invalid email or password"
}
```

### Code Examples

```python
import requests

# Login and get token
login_data = {
    "email": "user@example.com",
    "password": "securepassword123"
}

response = requests.post("https://api.example.com/auth/login", json=login_data)

if response.status_code == 200:
    auth_data = response.json()
    token = auth_data['access_token']
    
    # Use token for authenticated requests
    headers = {"Authorization": f"Bearer {token}"}
    protected_response = requests.get(
        "https://api.example.com/protected-endpoint",
        headers=headers
    )
```

```javascript
// Login and get token
const loginData = {
  email: "user@example.com",
  password: "securepassword123"
};

const response = await fetch('https://api.example.com/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(loginData)
});

if (response.ok) {
  const authData = await response.json();
  const token = authData.access_token;
  
  // Store token for future requests
  localStorage.setItem('authToken', token);
  
  // Use token for authenticated requests
  const protectedResponse = await fetch('https://api.example.com/protected-endpoint', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
}
```

Tags: authentication, login, jwt
```

## Multi-language Code Samples

### Advanced Configuration Example

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastmarkdocs import enhance_openapi_with_docs

app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Enhanced configuration with multiple languages
    enhanced_schema = enhance_openapi_with_docs(
        openapi_schema=openapi_schema,
        docs_directory="docs/api",
        base_url="https://api.example.com",
        code_sample_languages=[
            "python",
            "javascript", 
            "typescript",
            "go",
            "java",
            "php",
            "ruby",
            "csharp",
            "curl"
        ],
        custom_headers={
            "Authorization": "Bearer YOUR_TOKEN",
            "User-Agent": "MyApp/1.0",
            "Accept": "application/json"
        }
    )
    
    app.openapi_schema = enhanced_schema
    return enhanced_schema

app.openapi = custom_openapi
```

## Custom Templates

### Creating Custom Code Templates

```python
from fastmarkdocs import CodeSampleGenerator
from fastmarkdocs.types import CodeLanguage

# Custom templates for specific coding styles
custom_templates = {
    "python": """
# {title}
import requests
import json
from typing import Dict, Any

def {method_lower}_{path_safe}() -> Dict[str, Any]:
    \"\"\"
    {description}
    \"\"\"
    url = "{url}"
    headers = {headers}
    
    try:
        response = requests.{method_lower}(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {{e}}")
        return {{"error": str(e)}}

# Usage
result = {method_lower}_{path_safe}()
print(json.dumps(result, indent=2))
""",
    
    "javascript": """
// {title}
/**
 * {description}
 */
async function {methodLower}{PathCamelCase}() {{
    const url = '{url}';
    const headers = {headers};
    
    try {{
        const response = await fetch(url, {{
            method: '{method}',
            headers: headers
        }});
        
        if (!response.ok) {{
            throw new Error(`HTTP error! status: ${{response.status}}`);
        }}
        
        const data = await response.json();
        return data;
    }} catch (error) {{
        console.error('Error:', error);
        throw error;
    }}
}}

// Usage
{methodLower}{PathCamelCase}()
    .then(data => console.log(data))
    .catch(error => console.error('Failed:', error));
"""
}

generator = CodeSampleGenerator(
    base_url="https://api.example.com",
    custom_templates=custom_templates,
    custom_headers={"Authorization": "Bearer token"}
)
```

## CI/CD Integration

### GitHub Actions Workflow

**.github/workflows/docs-validation.yml**
```yaml
name: Validate API Documentation

on:
  pull_request:
    paths:
      - 'docs/**'
      - 'src/**'
  push:
    branches: [main]

jobs:
  validate-docs:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        pip install fastmarkdocs fastapi uvicorn
        
    - name: Validate documentation structure
      run: |
        python -c "
        from fastmarkdocs import MarkdownDocumentationLoader
        loader = MarkdownDocumentationLoader('docs/api')
        docs = loader.load_documentation()
        print(f'✅ Loaded {len(docs.endpoints)} endpoints')
        assert len(docs.endpoints) > 0, 'No endpoints found'
        "
        
    - name: Test API with enhanced docs
      run: |
        python -c "
        import sys
        sys.path.append('.')
        from main import app
        schema = app.openapi()
        assert 'paths' in schema
        print('✅ OpenAPI schema generated successfully')
        "
```

### Documentation Validation Script

**scripts/validate_docs.py**
```python
#!/usr/bin/env python3
"""
Validation script for API documentation.
"""

import sys
import json
from pathlib import Path
from fastmarkdocs import MarkdownDocumentationLoader
from fastmarkdocs.exceptions import DocumentationLoadError

def validate_documentation():
    """Validate all documentation files."""
    try:
        loader = MarkdownDocumentationLoader("docs/api")
        documentation = loader.load_documentation()
        
        print(f"✅ Successfully loaded {len(documentation.endpoints)} endpoints")
        
        # Validate each endpoint
        for endpoint in documentation.endpoints:
            if not endpoint.summary:
                print(f"⚠️  Warning: {endpoint.method} {endpoint.path} has no summary")
            
            if not endpoint.code_samples:
                print(f"⚠️  Warning: {endpoint.method} {endpoint.path} has no code samples")
        
        # Check for required endpoints
        required_endpoints = [
            ("GET", "/users"),
            ("POST", "/users"),
            ("GET", "/users/{user_id}")
        ]
        
        for method, path in required_endpoints:
            found = any(
                ep.method.value == method and ep.path == path 
                for ep in documentation.endpoints
            )
            if not found:
                print(f"❌ Missing required endpoint: {method} {path}")
                return False
        
        print("📚 Documentation validation passed!")
        return True
        
    except DocumentationLoadError as e:
        print(f"❌ Documentation validation failed: {e}")
        return False

if __name__ == "__main__":
    if not validate_documentation():
        sys.exit(1)
```

## Performance Optimization

### Caching Configuration

```python
from fastapi import FastAPI
from fastmarkdocs import MarkdownDocumentationLoader, enhance_openapi_with_docs
import os

app = FastAPI()

# Production-optimized configuration
def create_optimized_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    # Use caching in production
    cache_enabled = os.getenv("ENVIRONMENT") == "production"
    
    enhanced_schema = enhance_openapi_with_docs(
        openapi_schema=app.openapi(),
        docs_directory="docs/api",
        base_url=os.getenv("API_BASE_URL", "https://api.example.com"),
        code_sample_languages=["python", "javascript", "curl"],  # Limit languages
        cache_enabled=cache_enabled,
        cache_ttl=3600  # 1 hour cache
    )
    
    app.openapi_schema = enhanced_schema
    return enhanced_schema

app.openapi = create_optimized_openapi
```

### Lazy Loading Pattern

```python
from fastapi import FastAPI
from fastmarkdocs import MarkdownDocumentationLoader
import threading

app = FastAPI()
_documentation_cache = None
_cache_lock = threading.Lock()

def get_documentation():
    """Get documentation with thread-safe lazy loading."""
    global _documentation_cache
    
    if _documentation_cache is None:
        with _cache_lock:
            if _documentation_cache is None:
                loader = MarkdownDocumentationLoader("docs/api")
                _documentation_cache = loader.load_documentation()
    
    return _documentation_cache

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    # Load documentation lazily
    documentation = get_documentation()
    
    # Generate and cache schema
    enhanced_schema = enhance_openapi_with_docs(
        openapi_schema=app.openapi(),
        documentation=documentation
    )
    
    app.openapi_schema = enhanced_schema
    return enhanced_schema

app.openapi = custom_openapi
```

## Next Steps

- **[Advanced Configuration](advanced.html)** - Learn about advanced features and customization
- **[API Reference](api-reference.html)** - Complete API documentation
- **[User Guide](user-guide.html)** - Comprehensive usage guide 