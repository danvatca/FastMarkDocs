# User Guide

This comprehensive guide covers everything you need to know about using FastMarkDocs to enhance your FastAPI applications with rich markdown-based documentation.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Quick Start](#quick-start)
- [Markdown Structure](#markdown-structure)
- [Documentation Organization](#documentation-organization)
- [Code Samples](#code-samples)
- [Response Examples](#response-examples)
- [Configuration](#configuration)
- [Best Practices](#best-practices)
- [Integration Patterns](#integration-patterns)
- [Troubleshooting](#troubleshooting)

## Core Concepts

FastMarkDocs bridges the gap between markdown documentation and OpenAPI schemas by:

1. **Parsing markdown files** to extract API endpoint documentation
2. **Generating code samples** in multiple programming languages
3. **Enhancing OpenAPI schemas** with extracted documentation
4. **Providing rich examples** for better API understanding

### Key Components

- **MarkdownDocumentationLoader**: Loads and parses markdown files
- **CodeSampleGenerator**: Creates code examples in various languages
- **OpenAPIEnhancer**: Integrates documentation into OpenAPI schemas
- **enhance_openapi_with_docs()**: Main function for schema enhancement

## Quick Start

### Basic Usage

The simplest way to enhance your FastAPI application:

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastmarkdocs import enhance_openapi_with_docs

app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        routes=app.routes,
    )
    
    # Enhance with markdown documentation
    enhanced_schema = enhance_openapi_with_docs(
        openapi_schema=openapi_schema,
        docs_directory="docs/api"  # Path to your markdown files
    )
    
    app.openapi_schema = enhanced_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### With Custom Configuration

```python
from fastmarkdocs import enhance_openapi_with_docs, CodeLanguage

enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=openapi_schema,
    docs_directory="docs/api",
    base_url="https://api.example.com",
    include_code_samples=True,
    include_response_examples=True,
    code_sample_languages=[
        CodeLanguage.CURL,
        CodeLanguage.PYTHON,
        CodeLanguage.JAVASCRIPT
    ],
    custom_headers={
        "Authorization": "Bearer YOUR_TOKEN",
        "X-API-Version": "v1"
    }
)
```

## Markdown Structure

FastMarkDocs follows a specific markdown structure to identify and parse API documentation.

### Basic Endpoint Structure

```markdown
## GET /api/users

Brief description of what this endpoint does.

More detailed description can go here, explaining the purpose,
behavior, and any important notes about the endpoint.

### Parameters

- `limit` (integer, optional): Maximum number of results. Default: 50
- `offset` (integer, optional): Number of results to skip. Default: 0
- `search` (string, optional): Search term to filter results

### Response Examples

```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com"
    }
  ],
  "total": 1,
  "page": 1
}
```

### Code Examples

```python
import requests

response = requests.get("https://api.example.com/api/users")
users = response.json()
```

```curl
curl -X GET "https://api.example.com/api/users" \
  -H "Accept: application/json"
```

Tags: users, list
```

### Header Levels

- **Level 2 (`##`)**: Endpoint definition (method + path)
- **Level 3 (`###`)**: Sections like Parameters, Response Examples, Code Examples
- **Level 4 (`####`)**: Sub-sections within main sections

### Supported HTTP Methods

FastMarkDocs recognizes all standard HTTP methods:

- `GET` - Retrieve data
- `POST` - Create new resources
- `PUT` - Update entire resources
- `PATCH` - Partial updates
- `DELETE` - Remove resources
- `HEAD` - Get headers only
- `OPTIONS` - Get allowed methods

## Documentation Organization

### File Structure

Organize your documentation files logically:

```
docs/
├── api/
│   ├── users.md          # User-related endpoints
│   ├── auth.md           # Authentication endpoints
│   ├── products.md       # Product endpoints
│   └── orders.md         # Order endpoints
├── guides/
│   ├── authentication.md # Auth guide
│   └── pagination.md     # Pagination guide
└── README.md             # Overview
```

### Multiple Endpoints per File

You can document multiple related endpoints in a single file:

```markdown
# User Management

## GET /api/users
List all users in the system.

## POST /api/users
Create a new user.

## GET /api/users/{user_id}
Get details for a specific user.

## PUT /api/users/{user_id}
Update user information.

## DELETE /api/users/{user_id}
Remove a user from the system.
```

### File Naming Conventions

- Use descriptive names: `users.md`, `authentication.md`
- Group related endpoints: `user-management.md`
- Use hyphens for multi-word names: `order-processing.md`

## Code Samples

FastMarkDocs supports multiple programming languages for code samples.

### Supported Languages

- **curl** - Command-line HTTP client
- **python** - Using requests library
- **javascript** - Using fetch API
- **typescript** - With type annotations
- **go** - Using net/http package
- **java** - Using HttpURLConnection
- **php** - Using cURL
- **ruby** - Using net/http
- **csharp** - Using HttpClient

### Manual Code Samples

Add code samples directly in your markdown:

```markdown
### Code Examples

```python
import requests

# Get all users
response = requests.get("https://api.example.com/api/users")
if response.status_code == 200:
    users = response.json()
    print(f"Found {len(users)} users")
```

```curl
curl -X GET "https://api.example.com/api/users" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

```javascript
// Fetch users with error handling
async function getUsers() {
  try {
    const response = await fetch('https://api.example.com/api/users');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const users = await response.json();
    console.log('Users:', users);
  } catch (error) {
    console.error('Error fetching users:', error);
  }
}
```
```

### Generated Code Samples

FastMarkDocs can automatically generate code samples:

```python
from fastmarkdocs import CodeSampleGenerator, CodeLanguage, EndpointDocumentation, HTTPMethod

generator = CodeSampleGenerator(
    base_url="https://api.example.com",
    code_sample_languages=[
        CodeLanguage.CURL,
        CodeLanguage.PYTHON,
        CodeLanguage.JAVASCRIPT
    ],
    custom_headers={
        "Authorization": "Bearer YOUR_TOKEN",
        "User-Agent": "MyApp/1.0"
    }
)

# Create endpoint documentation
endpoint = EndpointDocumentation(
    path="/api/users",
    method=HTTPMethod.GET,
    summary="List users"
)

# Generate samples for the endpoint
samples = generator.generate_samples_for_endpoint(endpoint)
```

### Custom Templates

Create custom code generation templates:

```python
from fastmarkdocs import CodeSampleGenerator, CodeLanguage

custom_templates = {
    CodeLanguage.PYTHON: """
import httpx

async def {method_lower}_{path_safe}():
    async with httpx.AsyncClient() as client:
        response = await client.{method_lower}("{url}")
        return response.json()
"""
}

generator = CodeSampleGenerator(
    base_url="https://api.example.com",
    custom_templates=custom_templates
)
```

## Response Examples

Provide clear examples of API responses to help users understand the data structure.

### JSON Response Examples

```markdown
### Response Examples

#### Success Response (200 OK)

```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2025-01-15T10:30:00Z",
  "profile": {
    "avatar_url": "https://example.com/avatars/123.jpg",
    "bio": "Software developer"
  }
}
```

#### Error Response (404 Not Found)

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User with ID 123 not found",
    "details": {
      "user_id": 123,
      "timestamp": "2025-01-15T10:30:00Z"
    }
  }
}
```
```

### Multiple Response Types

Document different response scenarios:

```markdown
### Response Examples

#### Successful Creation (201 Created)
```json
{
  "id": 456,
  "name": "Jane Smith",
  "email": "jane@example.com",
  "status": "active"
}
```

#### Validation Error (400 Bad Request)
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid input data",
  "fields": {
    "email": "Invalid email format",
    "name": "Name is required"
  }
}
```

#### Authentication Error (401 Unauthorized)
```json
{
  "error": "UNAUTHORIZED",
  "message": "Invalid or expired token"
}
```
```

## Configuration

### Using MarkdownDocumentationLoader Directly

For more control, use the loader directly:

```python
from fastmarkdocs import MarkdownDocumentationLoader, OpenAPIEnhancer, CodeLanguage

# Create and configure the loader
loader = MarkdownDocumentationLoader(
    docs_directory="docs/api",
    recursive=True,
    cache_enabled=True,
    cache_ttl=3600,  # 1 hour
    supported_languages=[
        CodeLanguage.CURL,
        CodeLanguage.PYTHON,
        CodeLanguage.JAVASCRIPT
    ]
)

# Load documentation
documentation = loader.load_documentation()

# Access the loaded data
print(f"Loaded {len(documentation.endpoints)} endpoints")
print(f"Found {len(documentation.global_examples)} global examples")

# You can also use dictionary-style access for backward compatibility
print(f"Endpoints: {len(documentation['endpoints'])}")
```

### Using OpenAPIEnhancer Directly

For advanced customization:

```python
from fastmarkdocs import OpenAPIEnhancer, MarkdownDocumentationLoader, CodeLanguage

# Create enhancer with custom configuration
enhancer = OpenAPIEnhancer(
    include_code_samples=True,
    include_response_examples=True,
    include_parameter_examples=True,
    base_url="https://api.example.com",
    code_sample_languages=[
        CodeLanguage.CURL,
        CodeLanguage.PYTHON,
        CodeLanguage.JAVASCRIPT,
        CodeLanguage.GO
    ],
    custom_headers={
        "Authorization": "Bearer YOUR_TOKEN",
        "X-API-Version": "v1"
    },
    authentication_schemes=["bearer", "api_key"]
)

# Load documentation
loader = MarkdownDocumentationLoader("docs/api")
documentation = loader.load_documentation()

# Enhance schema
enhanced_schema = enhancer.enhance_openapi_schema(openapi_schema, documentation)
```

### Environment-Based Configuration

```python
import os
from fastmarkdocs import enhance_openapi_with_docs

# Use environment variables for configuration
enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=schema,
    docs_directory=os.getenv("DOCS_DIR", "docs"),
    base_url=os.getenv("API_BASE_URL", "https://api.example.com"),
    custom_headers={
        "Authorization": f"Bearer {os.getenv('API_TOKEN', 'YOUR_TOKEN')}"
    }
)
```

## Best Practices

### Documentation Writing

1. **Be Descriptive**: Write clear, concise descriptions for each endpoint
2. **Include Examples**: Provide realistic request and response examples
3. **Document Parameters**: Explain all parameters, their types, and requirements
4. **Use Consistent Formatting**: Follow the same structure across all files
5. **Keep It Updated**: Regularly update documentation to match API changes

### File Organization

1. **Group Related Endpoints**: Keep related endpoints in the same file
2. **Use Clear File Names**: Make file names descriptive and consistent
3. **Maintain Directory Structure**: Organize files logically by feature or domain
4. **Include Overview Files**: Add README files to explain the structure

### Code Sample Guidelines

1. **Show Real Examples**: Use realistic data in examples
2. **Include Error Handling**: Show how to handle common errors
3. **Demonstrate Best Practices**: Use proper authentication and validation
4. **Keep Examples Simple**: Focus on the essential parts of the request

### Performance Optimization

1. **Enable Caching**: Use caching for production environments
2. **Limit File Scanning**: Use specific file patterns to reduce scanning
3. **Optimize File Structure**: Keep documentation files reasonably sized
4. **Monitor Load Times**: Track documentation loading performance

## Integration Patterns

### FastAPI Integration

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastmarkdocs import enhance_openapi_with_docs

app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        routes=app.routes,
    )
    
    enhanced_schema = enhance_openapi_with_docs(
        openapi_schema=openapi_schema,
        docs_directory="docs/api"
    )
    
    app.openapi_schema = enhanced_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Conditional Enhancement

```python
import os
from fastmarkdocs import enhance_openapi_with_docs

def create_openapi_schema(base_schema):
    # Only enhance in development or when explicitly enabled
    if os.getenv("ENHANCE_DOCS", "false").lower() == "true":
        try:
            return enhance_openapi_with_docs(
                openapi_schema=base_schema,
                docs_directory="docs/api"
            )
        except Exception as e:
            print(f"Warning: Documentation enhancement failed: {e}")
    
    return base_schema
```

### Microservices Pattern

```python
# Service-specific documentation
def enhance_user_service_docs(schema):
    return enhance_openapi_with_docs(
        openapi_schema=schema,
        docs_directory="docs/users",
        base_url="https://users.api.example.com"
    )

def enhance_order_service_docs(schema):
    return enhance_openapi_with_docs(
        openapi_schema=schema,
        docs_directory="docs/orders",
        base_url="https://orders.api.example.com"
    )
```

## Troubleshooting

### Common Issues

#### Documentation Not Loading

**Problem**: Documentation files are not being found or loaded.

**Solutions**:
1. Check file paths and directory structure
2. Verify file permissions
3. Ensure markdown files follow the expected format
4. Check for syntax errors in markdown

```python
# Debug documentation loading
from fastmarkdocs import MarkdownDocumentationLoader

loader = MarkdownDocumentationLoader("docs/api", cache_enabled=False)
try:
    docs = loader.load_documentation()
    print(f"Loaded {len(docs.endpoints)} endpoints")
except Exception as e:
    print(f"Loading failed: {e}")
```

#### Code Samples Not Generating

**Problem**: Code samples are not appearing in the enhanced schema.

**Solutions**:
1. Verify code sample languages are supported
2. Check endpoint path matching
3. Ensure proper markdown formatting
4. Validate OpenAPI schema structure

```python
# Debug code sample generation
from fastmarkdocs import CodeSampleGenerator, EndpointDocumentation, HTTPMethod

generator = CodeSampleGenerator()
endpoint = EndpointDocumentation(path="/api/test", method=HTTPMethod.GET)

try:
    samples = generator.generate_samples_for_endpoint(endpoint)
    print(f"Generated {len(samples)} samples")
except Exception as e:
    print(f"Generation failed: {e}")
```

#### Performance Issues

**Problem**: Documentation loading is slow.

**Solutions**:
1. Enable caching for production
2. Reduce the number of files scanned
3. Use specific file patterns
4. Optimize markdown file sizes

```python
# Optimized configuration
loader = MarkdownDocumentationLoader(
    docs_directory="docs/api",
    cache_enabled=True,
    cache_ttl=7200,  # 2 hours
    file_patterns=["*_api.md"],  # Specific pattern
    recursive=False  # Don't scan subdirectories
)
```

### Debugging Tips

1. **Enable Verbose Logging**: Use logging to track what's happening
2. **Test Individual Components**: Test loader, generator, and enhancer separately
3. **Validate Markdown**: Check markdown syntax and structure
4. **Check File Permissions**: Ensure files are readable
5. **Monitor Memory Usage**: Watch for memory issues with large documentation sets

### Getting Help

If you encounter issues not covered here:

1. Check the [API Reference](api-reference.md) for detailed function documentation
2. Look at the [Examples](examples.md) for working code samples
3. Review the [Advanced Guide](advanced.md) for complex scenarios
4. Open an issue on [GitHub](https://github.com/danvatca/fastmarkdocs/issues)

---

*This user guide covers the essential aspects of using FastMarkDocs. For more advanced topics, see the [Advanced Guide](advanced.md).* 