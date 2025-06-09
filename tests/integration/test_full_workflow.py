"""
Integration tests for the complete FastMarkDocs workflow.

Tests the end-to-end functionality from markdown files to enhanced OpenAPI schemas.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from fastapi import FastAPI

from fastmarkdocs import (
    MarkdownDocumentationLoader,
    CodeSampleGenerator,
    OpenAPIEnhancer,
    enhance_openapi_with_docs
)
from fastmarkdocs.types import CodeLanguage, HTTPMethod


class TestFullWorkflow:
    """Test the complete workflow from markdown to enhanced OpenAPI."""

    def test_complete_workflow_basic(self, temp_docs_dir, test_utils):
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
        test_utils.create_markdown_file(temp_docs_dir, 'users.md', comprehensive_docs)
        
        # Create a sample OpenAPI schema
        openapi_schema = {
            "openapi": "3.0.2",
            "info": {"title": "User Management API", "version": "1.0.0"},
            "paths": {
                "/api/users": {
                    "get": {
                        "summary": "List users",
                        "responses": {"200": {"description": "Success"}}
                    },
                    "post": {
                        "summary": "Create user",
                        "responses": {"201": {"description": "Created"}}
                    }
                }
            }
        }
        
        # Test the complete workflow
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory=str(temp_docs_dir)
        )
        
        # Verify the enhancement worked
        assert enhanced_schema is not None
        assert 'paths' in enhanced_schema
        
        # Check GET /api/users endpoint
        get_users = enhanced_schema['paths']['/api/users']['get']
        assert 'x-codeSamples' in get_users
        
        # Check POST /api/users endpoint
        post_users = enhanced_schema['paths']['/api/users']['post']
        assert 'x-codeSamples' in post_users

    def test_workflow_with_multiple_files(self, temp_docs_dir, test_utils):
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
        
        test_utils.create_markdown_file(temp_docs_dir, 'users.md', users_docs)
        test_utils.create_markdown_file(temp_docs_dir, 'auth.md', auth_docs)
        
        # Create OpenAPI schema with both endpoints
        openapi_schema = {
            "openapi": "3.0.2",
            "info": {"title": "Multi-API", "version": "1.0.0"},
            "paths": {
                "/api/users": {
                    "get": {
                        "summary": "List users",
                        "responses": {"200": {"description": "Success"}}
                    }
                },
                "/api/auth/login": {
                    "post": {
                        "summary": "Login",
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        # Enhance with documentation
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory=str(temp_docs_dir)
        )
        
        # Both endpoints should be enhanced
        assert 'x-codeSamples' in enhanced_schema['paths']['/api/users']['get']
        assert 'x-codeSamples' in enhanced_schema['paths']['/api/auth/login']['post']

    def test_workflow_with_custom_configuration(self, temp_docs_dir, test_utils):
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
        
        test_utils.create_markdown_file(temp_docs_dir, 'test.md', docs_content)
        
        openapi_schema = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        # Test with custom configuration
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory=str(temp_docs_dir),
            base_url='https://custom.api.com',
            code_sample_languages=[CodeLanguage.PYTHON, CodeLanguage.GO],  # Only Python and Go
            custom_headers={'Authorization': 'Bearer token123'},
            include_code_samples=True,
            include_response_examples=False
        )
        
        # Check that only specified languages are included
        code_samples = enhanced_schema['paths']['/api/test']['get']['x-codeSamples']
        languages = [sample['lang'] for sample in code_samples]
        
        assert 'python' in languages
        assert 'go' in languages
        assert 'curl' not in languages  # Should not be included
        assert 'javascript' not in languages  # Should not be included
        
        # Check custom base URL
        python_sample = next(s for s in code_samples if s['lang'] == 'python')
        assert 'https://custom.api.com' in python_sample['source']
        
        # Check custom headers (look for the header value in language-appropriate format)
        assert 'Bearer token123' in python_sample['source']

    def test_workflow_error_handling(self, temp_docs_dir):
        """Test workflow error handling and fallback behavior."""
        # Test with empty directory
        openapi_schema = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/test": {
                    "get": {
                        "summary": "Test",
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        # Should not fail with empty directory
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory=str(temp_docs_dir)
        )
        
        # Should return original schema unchanged
        assert enhanced_schema == openapi_schema

    def test_workflow_with_fastapi_app(self, temp_docs_dir, test_utils):
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
        
        test_utils.create_markdown_file(temp_docs_dir, 'items.md', docs_content)
        
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
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory=str(temp_docs_dir)
        )
        
        # Verify enhancement
        assert 'x-codeSamples' in enhanced_schema['paths']['/items']['get']
        assert 'x-codeSamples' in enhanced_schema['paths']['/items']['post']
        
        # Verify the enhanced schema is valid
        assert enhanced_schema['info']['title'] == "Test API"
        assert enhanced_schema['info']['version'] == "1.0.0"

    def test_workflow_performance_large_scale(self, temp_docs_dir, test_utils):
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
        
        test_utils.create_markdown_file(temp_docs_dir, 'large.md', large_docs)
        
        # Create corresponding OpenAPI schema
        openapi_schema = {
            "openapi": "3.0.2",
            "info": {"title": "Large API", "version": "1.0.0"},
            "paths": {}
        }
        
        for i in range(50):
            openapi_schema["paths"][f"/api/endpoint{i}"] = {
                "get": {
                    "summary": f"Endpoint {i}",
                    "responses": {"200": {"description": "Success"}}
                }
            }
        
        # Test performance
        import time
        start_time = time.time()
        
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory=str(temp_docs_dir)
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete in reasonable time (less than 5 seconds)
        assert processing_time < 5.0
        
        # Verify all endpoints were enhanced
        enhanced_count = 0
        for path, path_item in enhanced_schema['paths'].items():
            if 'get' in path_item and 'x-codeSamples' in path_item['get']:
                enhanced_count += 1
        
        assert enhanced_count == 50

    def test_workflow_component_integration(self, temp_docs_dir, test_utils):
        """Test integration between individual components."""
        docs_content = """
# Component Integration Test

## GET /api/integration
Test endpoint for component integration.

### Parameters
- `param1` (string): Test parameter

### Response Examples
```json
{"result": "success", "data": [1, 2, 3]}
```

### Code Examples
```python
import requests
response = requests.get("/api/integration", params={"param1": "value"})
```

```curl
curl -X GET "https://api.example.com/api/integration?param1=value"
```

Tags: integration, test
"""
        
        test_utils.create_markdown_file(temp_docs_dir, 'integration.md', docs_content)
        
        # Test individual components
        loader = MarkdownDocumentationLoader(
            docs_directory=str(temp_docs_dir),
            cache_enabled=False
        )
        
        documentation = loader.load_documentation()
        assert len(documentation.endpoints) == 1
        
        endpoint = documentation.endpoints[0]
        assert endpoint.path == '/api/integration'
        assert endpoint.method == HTTPMethod.GET
        assert len(endpoint.code_samples) == 2
        assert len(endpoint.response_examples) == 1
        assert 'integration' in endpoint.tags
        
        # Test code sample generator
        generator = CodeSampleGenerator(
            base_url='https://test.api.com',
            code_sample_languages=[CodeLanguage.CURL, CodeLanguage.PYTHON]
        )
        
        generated_samples = generator.generate_samples_for_endpoint(endpoint)
        assert len(generated_samples) == 2
        
        # Test OpenAPI enhancer
        openapi_schema = {
            "openapi": "3.0.2",
            "info": {"title": "Integration Test", "version": "1.0.0"},
            "paths": {
                "/api/integration": {
                    "get": {
                        "summary": "Integration test",
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        enhancer = OpenAPIEnhancer(
            include_code_samples=True,
            include_response_examples=True,
            base_url='https://test.api.com'
        )
        
        enhanced_schema = enhancer.enhance_openapi_schema(openapi_schema, documentation)
        
        # Verify complete integration
        get_operation = enhanced_schema['paths']['/api/integration']['get']
        assert 'x-codeSamples' in get_operation
        assert 'responses' in get_operation
        assert '200' in get_operation['responses']
        
        # Check that response examples were added
        response_200 = get_operation['responses']['200']
        if 'content' in response_200 and 'application/json' in response_200['content']:
            assert 'examples' in response_200['content']['application/json'] 