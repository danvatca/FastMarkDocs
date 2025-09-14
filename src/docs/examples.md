---
layout: default
title: Examples
description: Real-world examples and tutorials for FastMarkDocs
nav_order: 4
---

# Examples

This page provides real-world examples and tutorials for using FastMarkDocs in different scenarios.

## Table of Contents

- [Basic FastAPI Integration](#basic-fastapi-integration)
- [Smart Section Descriptions](#smart-section-descriptions)
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
from typing import Optional

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

Section: User Management

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

Section: User Management

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

Section: User Management
```

## Smart Section Descriptions

FastMarkDocs automatically generates rich section descriptions from markdown Overview sections. This feature enhances your OpenAPI documentation by providing comprehensive context for each API group.

### Complete Example with Section Descriptions

Here's a complete example showing how Overview sections create beautiful section descriptions:

**docs/api/users.md**
```markdown
# User Management API

## Overview

The **User Management API** provides comprehensive user account administration for enterprise applications, enabling centralized user lifecycle management with role-based access control and multi-factor authentication.

### 👤 **Core Capabilities**

**Account Management**
- User registration and profile creation
- Account activation and deactivation
- Secure password management with complexity requirements
- Profile information updates and maintenance

**Access Control**
- Role-based permissions (Admin, Manager, User)
- Multi-factor authentication with TOTP support
- Session management with configurable timeouts
- API key generation and management

### 🔐 **Security Features**

- **Password Security**: Bcrypt hashing with configurable complexity
- **Account Protection**: Automatic lockout after failed attempts
- **Audit Logging**: Comprehensive activity tracking for compliance
- **Data Privacy**: GDPR-compliant data handling and deletion

## Endpoints

### GET /users
List all users with optional filtering and pagination.

Section: User Management

### POST /users
Create a new user account with role assignment.

Section: User Management

### GET /users/{user_id}
Retrieve detailed information for a specific user.

Section: User Management

### PUT /users/{user_id}
Update user profile information and settings.

Section: User Management

### DELETE /users/{user_id}
Permanently delete a user account.

Section: User Management
```

**docs/api/authentication.md**
```markdown
# Authentication API

## Overview

The **Authentication API** provides secure user authentication and session management for the application. This API handles login, logout, token management, and multi-factor authentication workflows.

### 🔐 **Authentication Methods**

**Primary Authentication**
- Username/password authentication with secure hashing
- Email-based login with verification
- API key authentication for service-to-service calls
- OAuth 2.0 integration with external providers

**Multi-Factor Authentication**
- TOTP (Time-based One-Time Password) support
- SMS-based verification codes
- Recovery codes for account recovery
- Hardware token support (FIDO2/WebAuthn)

### 🎫 **Token Management**

- **JWT Tokens**: Stateless authentication with configurable expiration
- **Refresh Tokens**: Long-lived tokens for seamless re-authentication
- **Session Tokens**: Server-side session management
- **API Keys**: Permanent authentication for automated systems

## Endpoints

### POST /auth/login
Authenticate user credentials and create session.

Section: Authentication

### POST /auth/logout
Terminate user session and invalidate tokens.

Section: Authentication

### POST /auth/refresh
Refresh expired access tokens using refresh token.

Section: Authentication

### POST /auth/mfa/setup
Configure multi-factor authentication for user account.

Section: Authentication

### POST /auth/mfa/verify
Verify multi-factor authentication code.

Section: Authentication
```

### Generated OpenAPI Enhancement

The above markdown files automatically generate this comprehensive OpenAPI tags section:

```json
{
  "tags": [
    {
      "name": "users",
      "description": "The **User Management API** provides comprehensive user account administration for enterprise applications, enabling centralized user lifecycle management with role-based access control and multi-factor authentication.\n\n### 👤 **Core Capabilities**\n\n**Account Management**\n- User registration and profile creation\n- Account activation and deactivation\n- Secure password management with complexity requirements\n- Profile information updates and maintenance\n\n**Access Control**\n- Role-based permissions (Admin, Manager, User)\n- Multi-factor authentication with TOTP support\n- Session management with configurable timeouts\n- API key generation and management\n\n### 🔐 **Security Features**\n\n- **Password Security**: Bcrypt hashing with configurable complexity\n- **Account Protection**: Automatic lockout after failed attempts\n- **Audit Logging**: Comprehensive activity tracking for compliance\n- **Data Privacy**: GDPR-compliant data handling and deletion"
    },
    {
      "name": "auth",
      "description": "The **Authentication API** provides secure user authentication and session management for the application. This API handles login, logout, token management, and multi-factor authentication workflows.\n\n### 🔐 **Authentication Methods**\n\n**Primary Authentication**\n- Username/password authentication with secure hashing\n- Email-based login with verification\n- API key authentication for service-to-service calls\n- OAuth 2.0 integration with external providers\n\n**Multi-Factor Authentication**\n- TOTP (Time-based One-Time Password) support\n- SMS-based verification codes\n- Recovery codes for account recovery\n- Hardware token support (FIDO2/WebAuthn)\n\n### 🎫 **Token Management**\n\n- **JWT Tokens**: Stateless authentication with configurable expiration\n- **Refresh Tokens**: Long-lived tokens for seamless re-authentication\n- **Session Tokens**: Server-side session management\n- **API Keys**: Permanent authentication for automated systems"
    }
  ]
}
```

### Key Benefits

1. **Professional Documentation**: Rich, formatted descriptions appear in Swagger/Redoc interfaces
2. **Zero Configuration**: No manual OpenAPI tag configuration required
3. **Consistent Branding**: Maintain consistent documentation style across all API groups
4. **Enhanced Discoverability**: Users can quickly understand API capabilities
5. **Automatic Synchronization**: Documentation stays in sync between markdown and OpenAPI

### Best Practices

- **Use Rich Formatting**: Include emojis, bold text, and structured sections
- **Be Comprehensive**: Provide complete context about the API group's purpose
- **Organize Logically**: Use subsections to group related capabilities
- **Include Security Information**: Document authentication and authorization requirements
- **Maintain Consistency**: Use similar structure across all Overview sections

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

Section: Product Management

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

Section: Product Management
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

Section: Authentication
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
        print(f"Error: {e}")
        return {"error": str(e)}

# Usage
result = {method_lower}_{path_safe}()
print(json.dumps(result, indent=2))
""",
    
    "javascript": """
// {title}
/**
 * {description}
 */
async function {methodLower}{PathCamelCase}() {
    const url = '{url}';
    const headers = {headers};
    
    try {
        const response = await fetch(url, {
            method: '{method}',
            headers: headers
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

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