"""
Copyright (c) 2025 Dan Vatca

Pytest configuration and shared fixtures for FastMarkDocs tests.

This module provides common fixtures and configuration used across all tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.routing import APIRoute

# Add src to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastmarkdocs import (
    MarkdownDocumentationLoader,
    CodeSampleGenerator,
    OpenAPIEnhancer,
    CodeLanguage,
    HTTPMethod
)


@pytest.fixture
def temp_docs_dir():
    """Create a temporary directory for test documentation files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing."""
    return """
# API Documentation

## GET /api/users

Retrieve a list of all users in the system.

This endpoint returns a paginated list of users with their basic information.

### Parameters

- `limit` (integer, optional): Maximum number of users to return. Default: 50
- `offset` (integer, optional): Number of users to skip. Default: 0

### Response Examples

```json
[
  {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "active": true
  }
]
```

### Code Examples

```python
import requests

response = requests.get("https://api.example.com/api/users")
users = response.json()
print(f"Found {len(users)} users")
```

```curl
curl -X GET "https://api.example.com/api/users" \\
  -H "Accept: application/json"
```

```javascript
fetch('https://api.example.com/api/users')
  .then(response => response.json())
  .then(users => console.log('Users:', users))
  .catch(error => console.error('Error:', error));
```

Tags: users, list

## POST /api/users

Create a new user in the system.

### Request Body

```json
{
  "name": "Jane Smith",
  "email": "jane@example.com"
}
```

### Response Examples

```json
{
  "id": 2,
  "name": "Jane Smith",
  "email": "jane@example.com",
  "active": true
}
```

### Code Examples

```python
import requests

data = {
    "name": "Jane Smith",
    "email": "jane@example.com"
}

response = requests.post(
    "https://api.example.com/api/users",
    json=data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 201:
    user = response.json()
    print(f"Created user: {user['name']}")
```

```curl
curl -X POST "https://api.example.com/api/users" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json" \\
  -d '{
    "name": "Jane Smith",
    "email": "jane@example.com"
  }'
```

Tags: users, create

## GET /api/users/{user_id}

Get details for a specific user.

### Parameters

- `user_id` (integer, required): The unique identifier for the user

### Response Examples

```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "active": true,
  "created_at": "2023-01-15T10:30:00Z"
}
```

### Code Examples

```python
import requests

user_id = 1
response = requests.get(f"https://api.example.com/api/users/{user_id}")

if response.status_code == 200:
    user = response.json()
    print(f"User: {user['name']}")
elif response.status_code == 404:
    print("User not found")
```

```curl
curl -X GET "https://api.example.com/api/users/1" \\
  -H "Accept: application/json"
```

Tags: users, details
"""


@pytest.fixture
def complex_markdown_content():
    """Complex markdown content with edge cases for testing."""
    return """
# Complex API Documentation

## POST /api/auth/login

Authenticate a user and create a session.

This endpoint supports multiple authentication methods including username/password
and API key authentication.

### Authentication Methods

#### Username and Password

```json
{
  "username": "admin",
  "password": "secure_password"
}
```

#### API Key

```json
{
  "api_key": "your-api-key-here"
}
```

### Response Examples

**Success (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "administrator"
  },
  "expires_at": "2023-12-31T23:59:59Z"
}
```

**Authentication Failed (401 Unauthorized):**
```json
{
  "error": "invalid_credentials",
  "message": "Invalid username or password"
}
```

### Code Examples

```python
import requests

# Username/password authentication
auth_data = {
    "username": "admin",
    "password": "secure_password"
}

response = requests.post(
    "https://api.example.com/api/auth/login",
    json=auth_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    token_data = response.json()
    print(f"Login successful. Token: {token_data['token']}")
else:
    error_data = response.json()
    print(f"Login failed: {error_data['message']}")
```

```curl
# Username/password login
curl -X POST "https://api.example.com/api/auth/login" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json" \\
  -d '{
    "username": "admin",
    "password": "secure_password"
  }'

# API key login
curl -X POST "https://api.example.com/api/auth/login" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json" \\
  -d '{
    "api_key": "your-api-key-here"
  }'
```

```javascript
// Username/password authentication
const authData = {
  username: 'admin',
  password: 'secure_password'
};

fetch('https://api.example.com/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  body: JSON.stringify(authData)
})
.then(response => {
  if (response.ok) {
    return response.json();
  }
  throw new Error(`HTTP ${response.status}: ${response.statusText}`);
})
.then(data => console.log('Login successful:', data))
.catch(error => console.error('Login failed:', error));
```

Tags: authentication, security

## DELETE /api/users/{user_id}

Delete a user from the system.

**Warning:** This action is irreversible.

### Parameters

- `user_id` (integer, required): The unique identifier for the user to delete

### Response Examples

**Success (204 No Content):**
No response body.

**User Not Found (404 Not Found):**
```json
{
  "error": "user_not_found",
  "message": "User with ID 123 not found"
}
```

### Code Examples

```python
import requests

user_id = 123
response = requests.delete(f"https://api.example.com/api/users/{user_id}")

if response.status_code == 204:
    print("User deleted successfully")
elif response.status_code == 404:
    print("User not found")
else:
    print(f"Error: {response.status_code}")
```

```curl
curl -X DELETE "https://api.example.com/api/users/123" \\
  -H "Accept: application/json"
```

Tags: users, delete, admin
"""


@pytest.fixture
def malformed_markdown_content():
    """Malformed markdown content for testing error handling."""
    return """
# Malformed Documentation

## GET /api/broken

This endpoint has malformed documentation.

### Code Examples

```python
# Missing closing backticks
import requests
response = requests.get("/api/broken")

## POST /api/another

Another endpoint without proper structure.

##### cURL
```bash
curl command without proper closing

##### Python
```python
# Another missing closing backticks
import requests

### Incomplete section
This section is incomplete and should be handled gracefully.
"""


@pytest.fixture
def sample_openapi_schema():
    """Sample OpenAPI schema for testing."""
    return {
        "openapi": "3.0.2",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "A test API for documentation enhancement"
        },
        "servers": [
            {"url": "https://api.example.com", "description": "Production server"}
        ],
        "paths": {
            "/api/users": {
                "get": {
                    "summary": "List users",
                    "description": "Retrieve a list of users",
                    "tags": ["users"],
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create user",
                    "description": "Create a new user",
                    "tags": ["users"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserCreate"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/users/{user_id}": {
                "get": {
                    "summary": "Get user",
                    "description": "Get a specific user by ID",
                    "tags": ["users"],
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "User found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "404": {
                            "description": "User not found"
                        }
                    }
                },
                "delete": {
                    "summary": "Delete user",
                    "description": "Delete a user by ID",
                    "tags": ["users"],
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {
                        "204": {"description": "User deleted"},
                        "404": {"description": "User not found"}
                    }
                }
            },
            "/api/auth/login": {
                "post": {
                    "summary": "Login",
                    "description": "Authenticate user",
                    "tags": ["authentication"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/LoginRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Login successful",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/LoginResponse"}
                                }
                            }
                        },
                        "401": {"description": "Authentication failed"}
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                        "active": {"type": "boolean"}
                    }
                },
                "UserCreate": {
                    "type": "object",
                    "required": ["name", "email"],
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"}
                    }
                },
                "LoginRequest": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                        "api_key": {"type": "string"}
                    }
                },
                "LoginResponse": {
                    "type": "object",
                    "properties": {
                        "token": {"type": "string"},
                        "user": {"$ref": "#/components/schemas/User"},
                        "expires_at": {"type": "string", "format": "date-time"}
                    }
                }
            }
        }
    }


@pytest.fixture
def mock_fastapi_app():
    """Create a mock FastAPI application for testing."""
    app = FastAPI(title="Test API", version="1.0.0", description="Test application")
    
    # Add some mock routes
    @app.get("/api/users")
    async def list_users():
        return []
    
    @app.post("/api/users")
    async def create_user():
        return {}
    
    @app.get("/api/users/{user_id}")
    async def get_user(user_id: int):
        return {}
    
    @app.delete("/api/users/{user_id}")
    async def delete_user(user_id: int):
        return {}
    
    @app.post("/api/auth/login")
    async def login():
        return {}
    
    return app


@pytest.fixture
def documentation_loader_config():
    """Configuration for MarkdownDocumentationLoader."""
    return {
        'docs_directory': 'test_docs',
        'recursive': True,
        'cache_enabled': False,
        'supported_languages': [
            CodeLanguage.CURL,
            CodeLanguage.PYTHON,
            CodeLanguage.JAVASCRIPT
        ],
        'file_patterns': ['*.md', '*.markdown'],
        'encoding': 'utf-8'
    }


@pytest.fixture
def code_generator_config():
    """Configuration for CodeSampleGenerator."""
    return {
        'base_url': 'https://api.example.com',
        'server_urls': ['https://api.example.com', 'https://staging.example.com'],
        'custom_headers': {
            'User-Agent': 'TestApp/1.0',
            'Accept': 'application/json'
        },
        'authentication_schemes': ['bearer', 'api_key'],
        'code_sample_languages': [
            CodeLanguage.CURL,
            CodeLanguage.PYTHON,
            CodeLanguage.JAVASCRIPT
        ]
    }


@pytest.fixture
def openapi_enhancement_config():
    """Configuration for OpenAPI enhancement."""
    return {
        'include_code_samples': True,
        'include_response_examples': True,
        'include_parameter_examples': True,
        'base_url': 'https://api.example.com',
        'code_sample_languages': [
            CodeLanguage.CURL,
            CodeLanguage.PYTHON,
            CodeLanguage.JAVASCRIPT
        ],
        'custom_headers': {
            'Authorization': 'Bearer test-token'
        },
        'authentication_schemes': ['bearer']
    }


@pytest.fixture
def sample_endpoint_documentation():
    """Sample endpoint documentation structure."""
    return {
        'path': '/api/users',
        'method': HTTPMethod.GET,
        'summary': 'List all users',
        'description': 'Retrieve a paginated list of users from the system',
        'code_samples': [
            {
                'language': CodeLanguage.PYTHON,
                'code': 'import requests\nresponse = requests.get("/api/users")',
                'description': 'Python example',
                'title': 'Python Request'
            },
            {
                'language': CodeLanguage.CURL,
                'code': 'curl -X GET "https://api.example.com/api/users"',
                'description': 'cURL example',
                'title': 'cURL Request'
            }
        ],
        'response_examples': [
            {
                'status_code': 200,
                'description': 'Successful response',
                'content': [{'id': 1, 'name': 'John Doe', 'email': 'john@example.com'}],
                'headers': {'Content-Type': 'application/json'}
            }
        ],
        'parameters': [
            {
                'name': 'limit',
                'description': 'Maximum number of users to return',
                'example': 50,
                'required': False,
                'type': 'integer'
            }
        ],
        'tags': ['users', 'list'],
        'deprecated': False
    }


# Test utilities
class TestUtils:
    """Utility functions for tests."""
    
    @staticmethod
    def create_markdown_file(temp_dir: Path, filename: str, content: str) -> Path:
        """Create a markdown file with the given content."""
        file_path = temp_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    @staticmethod
    def extract_app_routes(app: FastAPI) -> set[tuple[str, str]]:
        """Extract all routes from a FastAPI application."""
        routes = set()
        for route in app.routes:
            if isinstance(route, APIRoute):
                for method in route.methods:
                    if method != "OPTIONS":
                        routes.add((method, route.path))
        return routes
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in text for comparison."""
        return ' '.join(text.split())


@pytest.fixture
def test_utils():
    """Provide test utilities."""
    return TestUtils 