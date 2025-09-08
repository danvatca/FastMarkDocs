"""
Integration tests for the complete FastMarkDocs workflow.

Tests the end-to-end functionality from markdown files to enhanced OpenAPI schemas.
"""

from typing import Any

from fastapi import FastAPI

from fastmarkdocs import enhance_openapi_with_docs
from fastmarkdocs.types import CodeLanguage


class TestFullWorkflow:
    """Test the complete workflow from markdown to enhanced OpenAPI."""

    def test_complete_workflow_basic(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test the complete workflow with basic documentation."""
        # Create comprehensive markdown documentation
        comprehensive_docs = """
# User Management API

## GET /api/users

Retrieve a list of all users in the system.

### Code Examples

```python
import requests
response = requests.get("https://api.example.com/api/users")
users = response.json()
```

```curl
curl -X GET "https://api.example.com/api/users" \\
  -H "Accept: application/json"
```

Tags: users, list

## POST /api/users

Create a new user in the system.

### Code Examples

```python
import requests
user_data = {"name": "John", "email": "john@example.com"}
response = requests.post("https://api.example.com/api/users", json=user_data)
```

Tags: users, create
"""

        # Create the documentation file
        test_utils.create_markdown_file(temp_docs_dir, "users.md", comprehensive_docs)

        # Create a sample OpenAPI schema
        openapi_schema = {
            "openapi": "3.0.2",
            "info": {"title": "User Management API", "version": "1.0.0"},
            "paths": {
                "/api/users": {
                    "get": {"summary": "List users", "responses": {"200": {"description": "Success"}}},
                    "post": {"summary": "Create user", "responses": {"201": {"description": "Created"}}},
                }
            },
        }

        # Test the complete workflow
        enhanced_schema = enhance_openapi_with_docs(openapi_schema=openapi_schema, docs_directory=str(temp_docs_dir))

        # Verify the enhancement worked
        assert enhanced_schema is not None
        assert "paths" in enhanced_schema

        # Check GET /api/users endpoint
        get_users = enhanced_schema["paths"]["/api/users"]["get"]
        assert "x-codeSamples" in get_users

        # Check POST /api/users endpoint
        post_users = enhanced_schema["paths"]["/api/users"]["post"]
        assert "x-codeSamples" in post_users

    def test_workflow_with_multiple_files(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test workflow with multiple documentation files."""
        # Create multiple documentation files
        users_docs = """
# Users API

## GET /api/users
List all users.

### Code Examples
```python
import requests
response = requests.get("/api/users")
```

Tags: users
"""

        auth_docs = """
# Authentication API

## POST /api/auth/login
Authenticate a user.

### Code Examples
```python
import requests
response = requests.post("/api/auth/login", json={"username": "user", "password": "pass"})
```

Tags: auth
"""

        test_utils.create_markdown_file(temp_docs_dir, "users.md", users_docs)
        test_utils.create_markdown_file(temp_docs_dir, "auth.md", auth_docs)

        # Create OpenAPI schema with both endpoints
        openapi_schema = {
            "openapi": "3.0.2",
            "info": {"title": "Multi-API", "version": "1.0.0"},
            "paths": {
                "/api/users": {"get": {"summary": "List users", "responses": {"200": {"description": "Success"}}}},
                "/api/auth/login": {"post": {"summary": "Login", "responses": {"200": {"description": "Success"}}}},
            },
        }

        # Enhance with documentation
        enhanced_schema = enhance_openapi_with_docs(openapi_schema=openapi_schema, docs_directory=str(temp_docs_dir))

        # Both endpoints should be enhanced
        assert "x-codeSamples" in enhanced_schema["paths"]["/api/users"]["get"]
        assert "x-codeSamples" in enhanced_schema["paths"]["/api/auth/login"]["post"]

    def test_workflow_with_custom_configuration(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test workflow with custom configuration options."""
        docs_content = """
# API Documentation

## GET /api/test
Test endpoint.

### Code Examples
```python
import requests
response = requests.get("/api/test")
```

```curl
curl -X GET "https://api.example.com/api/test"
```

```javascript
fetch('/api/test')
```

```go
resp, err := http.Get("/api/test")
```
"""

        test_utils.create_markdown_file(temp_docs_dir, "test.md", docs_content)

        openapi_schema = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/test": {"get": {"summary": "Test endpoint", "responses": {"200": {"description": "Success"}}}}
            },
        }

        # Test with custom configuration
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory=str(temp_docs_dir),
            base_url="https://custom.api.com",
            code_sample_languages=[CodeLanguage.PYTHON, CodeLanguage.GO],  # Only Python and Go
            custom_headers={"Authorization": "Bearer token123"},
            include_code_samples=True,
            include_response_examples=False,
        )

        # Check that only specified languages are included
        code_samples = enhanced_schema["paths"]["/api/test"]["get"]["x-codeSamples"]
        languages = [sample["lang"] for sample in code_samples]

        assert "python" in languages
        assert "go" in languages
        assert "curl" not in languages  # Should not be included
        assert "javascript" not in languages  # Should not be included

        # Check custom base URL
        python_sample = next(s for s in code_samples if s["lang"] == "python")
        assert "https://custom.api.com" in python_sample["source"]

        # Check custom headers (look for the header value in language-appropriate format)
        assert "Bearer token123" in python_sample["source"]

    def test_workflow_error_handling(self, temp_docs_dir: Any) -> None:
        """Test workflow error handling and fallback behavior."""
        # Test with empty directory
        openapi_schema = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {"/api/test": {"get": {"summary": "Test", "responses": {"200": {"description": "Success"}}}}},
        }

        # Should not fail with empty directory
        enhanced_schema = enhance_openapi_with_docs(openapi_schema=openapi_schema, docs_directory=str(temp_docs_dir))

        # Should return original schema unchanged
        assert enhanced_schema == openapi_schema

    def test_workflow_with_fastapi_app(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test workflow integration with a real FastAPI application."""
        # Create documentation
        docs_content = """
# FastAPI Test

## GET /items
Get all items.

### Code Examples
```python
import requests
response = requests.get("/items")
```

## POST /items
Create an item.

### Code Examples
```python
import requests
response = requests.post("/items", json={"name": "test"})
```
"""

        test_utils.create_markdown_file(temp_docs_dir, "items.md", docs_content)

        # Create a FastAPI app
        app = FastAPI(title="Test API", version="1.0.0")

        @app.get("/items")
        async def get_items():
            return [{"id": 1, "name": "item1"}]

        @app.post("/items")
        async def create_item(item: dict):
            return {"id": 2, "name": item["name"]}

        # Get the OpenAPI schema from the app
        openapi_schema = app.openapi()

        # Enhance with documentation
        enhanced_schema = enhance_openapi_with_docs(openapi_schema=openapi_schema, docs_directory=str(temp_docs_dir))

        # Verify enhancement
        assert "x-codeSamples" in enhanced_schema["paths"]["/items"]["get"]
        assert "x-codeSamples" in enhanced_schema["paths"]["/items"]["post"]

        # Verify the enhanced schema is valid
        assert enhanced_schema["info"]["title"] == "Test API"
        assert enhanced_schema["info"]["version"] == "1.0.0"

    def test_workflow_performance_large_scale(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test workflow performance with large-scale documentation."""
        # Create documentation for many endpoints
        large_docs = "# Large API Documentation\n\n"

        for i in range(50):
            large_docs += f"""
## GET /api/endpoint{i}
Description for endpoint {i}.

### Code Examples
```python
import requests
response = requests.get("/api/endpoint{i}")
```

```curl
curl -X GET "https://api.example.com/api/endpoint{i}"
```

"""

        test_utils.create_markdown_file(temp_docs_dir, "large.md", large_docs)

        # Create corresponding OpenAPI schema
        openapi_schema = {"openapi": "3.0.2", "info": {"title": "Large API", "version": "1.0.0"}, "paths": {}}

        for i in range(50):
            openapi_schema["paths"][f"/api/endpoint{i}"] = {
                "get": {"summary": f"Endpoint {i}", "responses": {"200": {"description": "Success"}}}
            }

        # Test performance
        import time

        start_time = time.time()

        enhanced_schema = enhance_openapi_with_docs(openapi_schema=openapi_schema, docs_directory=str(temp_docs_dir))

        end_time = time.time()
        processing_time = end_time - start_time

        # Should complete in reasonable time (less than 5 seconds)
        assert processing_time < 5.0

        # Verify all endpoints were enhanced
        enhanced_count = 0
        for _path, path_item in enhanced_schema["paths"].items():
            if "get" in path_item and "x-codeSamples" in path_item["get"]:
                enhanced_count += 1

        assert enhanced_count == 50

    def test_workflow_component_integration(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test integration between all major components."""
        # Create comprehensive documentation with all features
        content = """
# API Documentation

## Overview

This is a comprehensive API with multiple endpoints and features.

### Features

- User management
- Authentication
- Data processing

## Endpoints

### GET /api/users

List all users in the system.

#### Code Examples

```python
import requests
response = requests.get("/api/users")
```

```curl
curl -X GET "/api/users"
```

#### Response Examples

**Success (200 OK):**
```json
[{"id": 1, "name": "John"}]
```

Tags: users, list

### POST /api/auth/login

Authenticate a user.

Tags: auth, login
"""

        test_utils.create_markdown_file(temp_docs_dir, "api.md", content)

        # Create OpenAPI schema
        openapi_schema = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/users": {
                    "get": {
                        "summary": "List users",
                        "tags": ["users"],
                        "responses": {"200": {"description": "Success"}},
                    }
                },
                "/api/auth/login": {
                    "post": {
                        "summary": "Login",
                        "tags": ["auth"],
                        "responses": {"200": {"description": "Success"}},
                    }
                },
            },
        }

        # Test the complete workflow
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory=str(temp_docs_dir),
            include_code_samples=True,
            include_response_examples=True,
        )

        # Verify enhancements
        assert "paths" in enhanced_schema

        # Check GET /api/users enhancement
        get_users = enhanced_schema["paths"]["/api/users"]["get"]
        assert "x-codeSamples" in get_users
        assert len(get_users["x-codeSamples"]) >= 2  # Python and cURL

        # Verify code samples
        languages = [sample["lang"] for sample in get_users["x-codeSamples"]]
        assert "python" in languages
        assert "curl" in languages

        # Check response examples were preserved/enhanced
        assert "responses" in get_users
        assert "200" in get_users["responses"]

    def test_tag_descriptions_integration_workflow(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test complete workflow with tag descriptions from Overview sections."""
        # Create documentation with Overview sections for different API groups
        users_content = """
# User Management API

## Overview

The **User Management API** provides comprehensive user account administration for SynetoOS, enabling centralized user lifecycle management with role-based access control and multi-factor authentication. This API supports enterprise-grade user provisioning, security policies, and audit capabilities.

### 👥 **User Management Features**

**Complete User Lifecycle**
- User account creation with customizable roles and permissions
- Profile management and account status control (enable/disable)
- Secure user deletion with data integrity protection

**Role-Based Access Control**
- **Administrator Role**: Full system access and user management capabilities
- **Regular Role**: Limited access based on specific permissions and use cases
- **Support Role**: Special PIN-based authentication for maintenance and troubleshooting

## Endpoints

### GET /users

List all users in the system.

Tags: users, list

### POST /users

Create a new user account.

Tags: users, create

### DELETE /users/{id}

Delete a user account.

Tags: users, delete
"""

        auth_content = """
# Authentication API

## Overview

The **Authentication API** handles user login, session management, and security token operations for secure access to the system. This API provides robust authentication mechanisms including multi-factor authentication, session management, and secure token handling.

### 🔐 **Authentication Features**

**Multi-Factor Authentication**
- TOTP-based second factor with authenticator app integration
- Recovery codes for account recovery scenarios
- Per-user OTP configuration with administrative override

**Session Management**
- Secure session creation and validation
- Configurable session timeout policies
- Session invalidation and logout functionality

## Endpoints

### POST /auth/login

Authenticate a user and create a session.

Tags: authentication, login

### POST /auth/logout

Logout a user and invalidate the session.

Tags: authentication, logout

### GET /auth/session

Get current session information.

Tags: authentication, session
"""

        # Create markdown files
        test_utils.create_markdown_file(temp_docs_dir, "users.md", users_content)
        test_utils.create_markdown_file(temp_docs_dir, "auth.md", auth_content)

        # Create OpenAPI schema with operations that use these tags
        openapi_schema = {
            "openapi": "3.0.0",
            "info": {"title": "SynetoOS API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "tags": ["users"],
                        "responses": {"200": {"description": "Success"}},
                    },
                    "post": {
                        "summary": "Create user",
                        "tags": ["users"],
                        "responses": {"201": {"description": "Created"}},
                    },
                },
                "/users/{id}": {
                    "delete": {
                        "summary": "Delete user",
                        "tags": ["users"],
                        "responses": {"204": {"description": "Deleted"}},
                    }
                },
                "/auth/login": {
                    "post": {
                        "summary": "Login",
                        "tags": ["authentication"],
                        "responses": {"200": {"description": "Success"}},
                    }
                },
                "/auth/logout": {
                    "post": {
                        "summary": "Logout",
                        "tags": ["authentication"],
                        "responses": {"200": {"description": "Success"}},
                    }
                },
                "/auth/session": {
                    "get": {
                        "summary": "Get session",
                        "tags": ["authentication"],
                        "responses": {"200": {"description": "Success"}},
                    }
                },
            },
        }

        # Test the complete workflow with tag descriptions
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory=str(temp_docs_dir),
            include_code_samples=True,
            include_response_examples=True,
        )

        # Verify that tags section was created with descriptions
        assert "tags" in enhanced_schema
        assert len(enhanced_schema["tags"]) >= 2

        # Find the tags
        users_tag = next((tag for tag in enhanced_schema["tags"] if tag["name"] == "users"), None)
        auth_tag = next((tag for tag in enhanced_schema["tags"] if tag["name"] == "authentication"), None)

        # Verify users tag description
        assert users_tag is not None
        assert "description" in users_tag
        users_desc = users_tag["description"]
        assert "User Management API" in users_desc
        assert "comprehensive user account administration" in users_desc
        assert "👥" in users_desc  # Should include emoji sections
        assert "Role-Based Access Control" in users_desc
        assert "Administrator Role" in users_desc

        # Verify authentication tag description
        assert auth_tag is not None
        assert "description" in auth_tag
        auth_desc = auth_tag["description"]
        assert "Authentication API" in auth_desc
        assert "user login, session management" in auth_desc
        assert "🔐" in auth_desc  # Should include emoji sections
        assert "Multi-Factor Authentication" in auth_desc
        assert "Session Management" in auth_desc

        # Verify that all other enhancements still work
        assert "paths" in enhanced_schema

        # Check that operations still have their tags
        get_users = enhanced_schema["paths"]["/users"]["get"]
        assert "tags" in get_users
        assert "users" in get_users["tags"]

        login_op = enhanced_schema["paths"]["/auth/login"]["post"]
        assert "tags" in login_op
        assert "authentication" in login_op["tags"]
