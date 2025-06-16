# FastMarkDocs

A powerful library for enhancing FastAPI applications with rich markdown-based API documentation. Transform your API documentation workflow with beautiful, maintainable markdown files that generate comprehensive OpenAPI enhancements.

[![PyPI version](https://badge.fury.io/py/FastMarkDocs.svg)](https://badge.fury.io/py/FastMarkDocs)
[![Python Support](https://img.shields.io/pypi/pyversions/fastmarkdocs.svg)](https://pypi.org/project/fastmarkdocs/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/danvatca/fastmarkdocs/workflows/CI/badge.svg)](https://github.com/danvatca/fastmarkdocs/actions)
[![codecov](https://codecov.io/gh/danvatca/FastMarkDocs/branch/main/graph/badge.svg)](https://codecov.io/gh/danvatca/FastMarkDocs)

## Features

✨ **Rich Documentation**: Transform markdown files into comprehensive API documentation  
🔧 **OpenAPI Enhancement**: Automatically enhance your OpenAPI/Swagger schemas  
🌍 **Multi-language Code Samples**: Generate code examples in Python, JavaScript, TypeScript, Go, Java, PHP, Ruby, C#, and cURL  
📝 **Markdown-First**: Write documentation in familiar markdown format  
🔗 **API Cross-References**: Include links to other APIs in your system with automatic formatting  
🎨 **Customizable Templates**: Use custom templates for code generation  
⚡ **High Performance**: Built-in caching and optimized processing  
🧪 **Well Tested**: Comprehensive test suite with 100+ tests  
🔍 **Documentation Linting**: Built-in `fmd-lint` tool to analyze and improve documentation quality
🏗️ **Documentation Scaffolding**: `fmd-init` tool to bootstrap documentation for existing projects  

## Quick Start

### Installation

#### Basic Installation
```bash
pip install fastmarkdocs
```

#### Development Installation
```bash
# Clone the repository
git clone https://github.com/danvatca/fastmarkdocs.git
cd fastmarkdocs

# Install with Poetry (recommended)
poetry install

# Or with pip in development mode
pip install -e ".[dev]"
```

#### Documentation Development
For building and contributing to documentation:

```bash
# Install Ruby and Jekyll dependencies:
# On macOS: brew install ruby && gem install bundler jekyll
# On Ubuntu: sudo apt-get install ruby-full build-essential zlib1g-dev

# Setup and serve documentation
./build-docs.sh setup
./build-docs.sh serve
```

### Basic Usage

```python
from fastapi import FastAPI
from fastmarkdocs import enhance_openapi_with_docs

app = FastAPI()

# Enhance your OpenAPI schema with markdown documentation
enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=app.openapi(),
    docs_directory="docs/api",
    base_url="https://api.example.com",
    custom_headers={"Authorization": "Bearer token123"},
    general_docs_file="general_docs.md"  # Optional: specify general documentation
)

# Update your app's OpenAPI schema
app.openapi_schema = enhanced_schema
```

### Advanced Usage with API Links

For microservice architectures where you want to link between different APIs:

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastmarkdocs import APILink, enhance_openapi_with_docs

app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    # Define links to other APIs in your system
    api_links = [
        APILink(url="/docs", description="Authorization"),
        APILink(url="/api/storage/docs", description="Storage"),
        APILink(url="/api/monitoring/docs", description="Monitoring"),
    ]
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Enhance with custom title, description, and API links
    enhanced_schema = enhance_openapi_with_docs(
        openapi_schema=openapi_schema,
        docs_directory="docs/api",
        app_title="My API Gateway",
        app_description="Authorization and access control service",
        api_links=api_links,
    )
    
    app.openapi_schema = enhanced_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Documentation Structure

Create markdown files in your docs directory:

```
docs/api/
├── users.md
├── authentication.md
└── orders.md
```

Example markdown file (`users.md`):

```markdown
# User Management API

## GET /users

Retrieve a list of all users in the system.

### Description
This endpoint returns a paginated list of users with their basic information.

### Parameters
- `page` (integer, optional): Page number for pagination (default: 1)
- `limit` (integer, optional): Number of users per page (default: 10)

### Response Examples

```json
{
  "users": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com"
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 10
}
```

### Code Samples

```python
import requests

response = requests.get("https://api.example.com/users")
users = response.json()
```

```javascript
const response = await fetch('https://api.example.com/users');
const users = await response.json();
```

```

## CLI Tools

FastMarkDocs includes powerful CLI tools for creating and analyzing your API documentation.

### Documentation Initialization with fmd-init

The `fmd-init` tool helps you bootstrap documentation for existing FastAPI projects by scanning your code and generating markdown scaffolding:

```bash
# Basic usage - scan src/ directory
fmd-init src/

# Custom output directory
fmd-init src/ --output-dir api-docs/

# Preview what would be generated (dry run)
fmd-init src/ --dry-run --verbose

# JSON output format
fmd-init src/ --format json

# Overwrite existing files
fmd-init src/ --overwrite
```

**Features:**
- 🔍 **Automatic Discovery**: Scans Python files for FastAPI decorators (`@app.get`, `@router.post`, etc.)
- 📝 **Markdown Generation**: Creates structured documentation files grouped by tags
- 🏗️ **Scaffolding**: Generates TODO sections for parameters, responses, and examples
- 🔧 **Flexible Output**: Supports text and JSON formats, dry-run mode, custom directories
- 📊 **Detailed Reporting**: Shows endpoint breakdown by HTTP method and file locations

**Example Output:**
```
✅ Documentation scaffolding generated successfully!

📊 **Documentation Initialization Complete**
- **Endpoints discovered:** 15
- **Files generated:** 4

**Endpoints by method:**
- DELETE: 2
- GET: 8
- POST: 3
- PUT: 2

**Generated files:**
- docs/users.md
- docs/orders.md
- docs/admin.md
- docs/root.md
```

**Workflow Integration:**
1. 🏗️ Develop FastAPI endpoints in your project
2. 🔍 Run `fmd-init src/` to generate documentation scaffolding
3. ✏️ Review and enhance the generated documentation
4. 🔧 Use fastmarkdocs to enhance your OpenAPI schema
5. 🧪 Run `fmd-lint` to check documentation quality
6. 🚀 Deploy with enhanced documentation!

### Documentation Linting with fmd-lint

FastMarkDocs includes a powerful documentation linter that helps you maintain high-quality API documentation:

```bash
# Install FastMarkDocs (includes fmd-lint)
pip install fastmarkdocs

# Lint your documentation
fmd-lint --openapi openapi.json --docs docs/api
```

### What fmd-lint Analyzes

- **Missing Documentation**: Finds API endpoints without documentation
- **Incomplete Documentation**: Identifies missing descriptions, examples, or code samples
- **Common Mistakes**: Detects path parameter mismatches and other errors
- **Orphaned Documentation**: Finds docs for non-existent endpoints
- **Enhancement Failures**: Tests that documentation properly enhances OpenAPI

### Example Output

```
============================================================
🔍 FastMarkDocs Documentation Linter Results
============================================================

📊 ✅ Good documentation with 3 minor issues to address.
📈 Coverage: 85.7% | Completeness: 72.3% | Issues: 3

❌ Missing Documentation:
   • GET /users/{id}
   • POST /orders

⚠️ Common Mistakes:
   • path_parameter_mismatch: GET /users/{id} should be /users/{user_id}
     💡 Check if path parameters match your FastAPI routes

💡 Recommendations:
   ⚠️ Fix Documentation Mistakes
     Action: Review and fix path parameter mismatches
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Lint documentation
  run: fmd-lint --openapi openapi.json --docs docs/api
```

For complete documentation, see [docs/fmd-lint.md](docs/fmd-lint.md).

## Advanced Features

### General Documentation

FastMarkDocs supports "general documentation" that provides global information about your API. This content is included in the OpenAPI schema's `info.description` field and appears at the top of your API documentation.

#### How General Docs Work

1. **Default File**: Create a `general_docs.md` file in your docs directory
2. **Custom File**: Specify a different file using the `general_docs_file` parameter
3. **Global Content**: The content appears in the API overview, not in individual endpoints

#### Example General Documentation

Create a file `docs/api/general_docs.md`:

```markdown
# API Overview

Welcome to our comprehensive API documentation. This API provides access to user management, order processing, and analytics features.

## Authentication

All API endpoints require authentication using Bearer tokens:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.example.com/users
```

## Rate Limiting

API requests are limited to 1000 requests per hour per API key.

## Error Handling

Our API uses standard HTTP status codes and returns JSON error responses:

```json
{
  "error": "invalid_request",
  "message": "The request is missing required parameters"
}
```

## Support

For API support, contact: api-support@example.com
```

#### Using General Documentation

```python
from fastmarkdocs import enhance_openapi_with_docs

# Default: Uses general_docs.md if it exists
enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=app.openapi(),
    docs_directory="docs/api"
)

# Custom general docs file
enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=app.openapi(),
    docs_directory="docs/api",
    general_docs_file="api_overview.md"
)

# Disable general docs by passing None
enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=app.openapi(),
    docs_directory="docs/api",
    general_docs_file=None
)
```

#### General Docs with MarkdownDocumentationLoader

```python
from fastmarkdocs import MarkdownDocumentationLoader

# Load with custom general docs
loader = MarkdownDocumentationLoader(
    docs_directory="docs/api",
    general_docs_file="custom_overview.md"
)

docs = loader.load_documentation()

# Access general docs content (internal use)
if hasattr(loader, '_general_docs_content'):
    print("General docs loaded:", loader._general_docs_content is not None)
```

### Authentication Schemes

FastMarkDocs can automatically add authentication headers to generated code samples based on your API's authentication requirements:

```python
from fastmarkdocs import enhance_openapi_with_docs, CodeSampleGenerator

# Configure automatic authentication headers
enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=app.openapi(),
    docs_directory="docs/api",
    base_url="https://api.example.com",
    # Automatically adds appropriate auth headers to all code samples
    authentication_schemes=["bearer"]  # Options: "bearer", "api_key", "basic"
)

# For more control, use CodeSampleGenerator directly
generator = CodeSampleGenerator(
    base_url="https://api.example.com",
    authentication_schemes=["bearer", "api_key"],  # Supports multiple schemes
    custom_headers={"User-Agent": "MyApp/1.0"}
)
```

**Supported Authentication Schemes:**
- `"bearer"` - Adds `Authorization: Bearer YOUR_TOKEN_HERE` header
- `"api_key"` - Adds `X-API-Key: YOUR_API_KEY_HERE` header  
- `"basic"` - Adds `Authorization: Basic YOUR_CREDENTIALS_HERE` header

### Server URLs and Multi-Environment Support

Configure multiple server URLs for different environments:

```python
from fastmarkdocs import enhance_openapi_with_docs

enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=app.openapi(),
    docs_directory="docs/api",
    base_url="https://api.example.com",  # Primary server
    server_urls=[  # Additional servers for code samples
        "https://api.example.com",
        "https://staging-api.example.com", 
        "https://dev-api.example.com"
    ]
)
```

### Custom Code Generation

```python
from fastmarkdocs import CodeSampleGenerator
from fastmarkdocs.types import CodeLanguage

generator = CodeSampleGenerator(
    base_url="https://api.example.com",
    code_sample_languages=[CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT, CodeLanguage.CURL],
    custom_headers={"Authorization": "Bearer token"},
    authentication_schemes=["bearer"],  # Automatic auth headers
    server_urls=["https://api.example.com", "https://staging-api.example.com"],
    cache_enabled=True  # Enable caching for better performance
)

# Generate samples for a specific endpoint
samples = generator.generate_samples_for_endpoint(endpoint_data)
```

### Custom Code Templates

Create custom templates for specific languages with dynamic variables:

```python
from fastmarkdocs import CodeSampleGenerator
from fastmarkdocs.types import CodeLanguage

# Define custom templates with variables
custom_templates = {
    CodeLanguage.PYTHON: """
# {summary}
# {description}

import requests

def call_{method_lower}_api():
    response = requests.{method_lower}(
        '{url}',
        headers={{'Authorization': 'Bearer YOUR_TOKEN'}}
    )
    return response.json()

# Usage
result = call_{method_lower}_api()
print(result)
""",
    CodeLanguage.BASH: """
#!/bin/bash
# {summary}

curl -X {method} \\
  '{url}' \\
  -H 'Authorization: Bearer YOUR_TOKEN' \\
  -H 'Content-Type: application/json'
"""
}

generator = CodeSampleGenerator(
    base_url="https://api.example.com",
    custom_templates=custom_templates
)
```

**Available Template Variables:**
- `{method}` - HTTP method (GET, POST, etc.)
- `{method_lower}` - HTTP method in lowercase
- `{path}` - API endpoint path
- `{url}` - Complete URL
- `{base_url}` - Base URL
- `{summary}` - Endpoint summary
- `{description}` - Endpoint description

### Advanced Loader Configuration

```python
from fastmarkdocs import MarkdownDocumentationLoader
from fastmarkdocs.types import CodeLanguage

loader = MarkdownDocumentationLoader(
    docs_directory="docs/api",
    supported_languages=[CodeLanguage.PYTHON, CodeLanguage.CURL],  # Filter code samples
    file_patterns=["*.md", "*.markdown"],  # File types to process
    encoding="utf-8",
    recursive=True,  # Search subdirectories
    cache_enabled=True,  # Enable caching for performance
    cache_ttl=3600,  # Cache for 1 hour
    general_docs_file="api_overview.md"  # Custom general docs file
)
```

## API Reference

### Core Functions

#### `enhance_openapi_with_docs()`

Enhance an OpenAPI schema with markdown documentation.

**Parameters:**
- `openapi_schema` (dict): The original OpenAPI schema
- `docs_directory` (str): Path to markdown documentation directory
- `base_url` (str, optional): Base URL for code samples (default: "https://api.example.com")
- `include_code_samples` (bool, optional): Whether to include code samples (default: True)
- `include_response_examples` (bool, optional): Whether to include response examples (default: True)
- `code_sample_languages` (list[CodeLanguage], optional): Languages for code generation
- `custom_headers` (dict, optional): Custom headers for code samples
- `app_title` (str, optional): Override the application title
- `app_description` (str, optional): Application description to include
- `api_links` (list[APILink], optional): List of links to other APIs
- `general_docs_file` (str, optional): Path to general documentation file (default: "general_docs.md" if found)

**Returns:** Enhanced OpenAPI schema (dict)

**Basic Example:**
```python
from fastmarkdocs import enhance_openapi_with_docs

enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=app.openapi(),
    docs_directory="docs/api",
    base_url="https://api.example.com",
    include_code_samples=True,
    include_response_examples=True,
    general_docs_file="general_docs.md"  # Optional: specify general documentation
)
```

**Example with API Links:**
```python
from fastmarkdocs import APILink, enhance_openapi_with_docs

# Define links to other APIs in your system
api_links = [
    APILink(url="/docs", description="Authorization"),
    APILink(url="/api/storage/docs", description="Storage"),
    APILink(url="/api/monitoring/docs", description="Monitoring"),
]

enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=app.openapi(),
    docs_directory="docs/api",
    app_title="My API Gateway",
    app_description="Authorization and access control service",
    api_links=api_links,
    general_docs_file="general_docs.md"  # Optional: include general documentation
)
```

**Example with General Documentation:**
```python
# Using default general_docs.md file
enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=app.openapi(),
    docs_directory="docs/api"
    # Automatically includes content from docs/api/general_docs.md
)

# Using custom general documentation file
enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=app.openapi(),
    docs_directory="docs/api",
    general_docs_file="custom_overview.md"
)
```

### Configuration Classes

#### `MarkdownDocumentationConfig`

Configuration for markdown documentation loading.

```python
from fastmarkdocs import MarkdownDocumentationConfig, CodeLanguage

config = MarkdownDocumentationConfig(
    docs_directory="docs/api",
    base_url_placeholder="https://api.example.com",
    supported_languages=[CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT, CodeLanguage.CURL],
    file_patterns=["*.md", "*.markdown"],
    encoding="utf-8",
    recursive=True,
    cache_enabled=True,
    cache_ttl=3600  # 1 hour
)
```

#### `OpenAPIEnhancementConfig`

Configuration for OpenAPI schema enhancement.

```python
from fastmarkdocs import OpenAPIEnhancementConfig, CodeLanguage

config = OpenAPIEnhancementConfig(
    include_code_samples=True,
    include_response_examples=True,
    include_parameter_examples=True,
    code_sample_languages=[CodeLanguage.CURL, CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT],
    base_url="https://api.example.com",
    server_urls=["https://api.example.com", "https://staging-api.example.com"],
    custom_headers={"Authorization": "Bearer {token}"},
    authentication_schemes=["bearerAuth", "apiKey"]
)
```

### Types and Data Classes

#### `APILink`

Represents a link to another API in your system.

```python
from fastmarkdocs import APILink

# Create API links
api_link = APILink(
    url="/api/storage/docs",
    description="Storage API"
)

# Use in enhance_openapi_with_docs
api_links = [
    APILink(url="/docs", description="Main API"),
    APILink(url="/admin/docs", description="Admin API"),
]
```

#### `DocumentationData`

Container for all documentation data loaded from markdown files.

```python
from fastmarkdocs import DocumentationData, EndpointDocumentation

data = DocumentationData(
    endpoints=[],  # List of EndpointDocumentation
    global_examples=[],  # List of CodeSample
    metadata={}  # Dict of metadata
)

# Access endpoints
for endpoint in data.endpoints:
    print(f"{endpoint.method} {endpoint.path}")
```

#### `EndpointDocumentation`

Documentation for a single API endpoint.

```python
from fastmarkdocs import EndpointDocumentation, HTTPMethod, CodeSample

endpoint = EndpointDocumentation(
    path="/users/{user_id}",
    method=HTTPMethod.GET,
    summary="Get user by ID",
    description="Retrieve a specific user by their unique identifier",
    code_samples=[],  # List of CodeSample
    response_examples=[],  # List of ResponseExample
    parameters=[],  # List of ParameterDocumentation
    tags=["users"],
    deprecated=False
)
```

#### `CodeSample`

Represents a code sample in a specific language.

```python
from fastmarkdocs import CodeSample, CodeLanguage

sample = CodeSample(
    language=CodeLanguage.PYTHON,
    code="""
import requests

response = requests.get("https://api.example.com/users/123")
user = response.json()
""",
    description="Get user by ID using requests library",
    title="Python Example"
)
```

### Core Classes

#### `MarkdownDocumentationLoader`

Load and process markdown documentation files from a directory.

**Parameters:**
- `docs_directory` (str): Path to markdown documentation directory (default: "docs")
- `base_url_placeholder` (str): Placeholder URL for code samples (default: "https://api.example.com")
- `supported_languages` (list[CodeLanguage], optional): Languages to support for code samples
- `file_patterns` (list[str], optional): File patterns to match (default: ["*.md", "*.markdown"])
- `encoding` (str): File encoding (default: "utf-8")
- `recursive` (bool): Whether to search directories recursively (default: True)
- `cache_enabled` (bool): Whether to enable caching (default: True)
- `cache_ttl` (int): Cache time-to-live in seconds (default: 3600)
- `general_docs_file` (str, optional): Path to general documentation file

**Methods:**
- `load_documentation()` → `DocumentationData`: Load all documentation
- `parse_markdown_file(file_path)` → `dict`: Parse a single markdown file
- `clear_cache()`: Clear the documentation cache
- `get_stats()` → `dict`: Get loading statistics

```python
from fastmarkdocs import MarkdownDocumentationLoader, CodeLanguage

loader = MarkdownDocumentationLoader(
    docs_directory="docs/api",
    recursive=True,
    cache_enabled=True,
    cache_ttl=3600,
    supported_languages=[CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT, CodeLanguage.CURL],
    general_docs_file="overview.md"
)

# Load all documentation
docs = loader.load_documentation()

# Get statistics
stats = loader.get_stats()
print(f"Loaded {stats['total_endpoints']} endpoints")
```

#### `CodeSampleGenerator`

Generate code samples for API endpoints in multiple languages.

**Parameters:**
- `base_url` (str): Base URL for code samples (default: "https://api.example.com")
- `custom_headers` (dict[str, str]): Custom headers to include
- `code_sample_languages` (list[CodeLanguage]): Languages to generate
- `custom_templates` (dict[CodeLanguage, str]): Custom code templates

**Methods:**
- `generate_samples_for_endpoint(endpoint_data)` → `list[CodeSample]`: Generate samples for an endpoint
- `generate_curl_sample(method, url, headers, body)` → `CodeSample`: Generate cURL sample
- `generate_python_sample(method, url, headers, body)` → `CodeSample`: Generate Python sample

```python
from fastmarkdocs import CodeSampleGenerator, CodeLanguage

generator = CodeSampleGenerator(
    base_url="https://api.example.com",
    custom_headers={"Authorization": "Bearer {token}", "Content-Type": "application/json"},
    code_sample_languages=[CodeLanguage.CURL, CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT],
    custom_templates={
        CodeLanguage.PYTHON: """
import requests

def {method_lower}_{path_safe}():
    headers = {headers}
    response = requests.{method_lower}("{url}", headers=headers)
    return response.json()
"""
    }
)

# Generate samples for an endpoint
samples = generator.generate_samples_for_endpoint({
    "method": "GET",
    "path": "/users/{user_id}",
    "parameters": {"user_id": 123}
})
```

#### `OpenAPIEnhancer`

Enhance OpenAPI schemas with documentation data and code samples.

**Parameters:**
- `base_url` (str): Base URL for code samples
- `custom_headers` (dict[str, str]): Custom headers for code samples
- `code_sample_languages` (list[CodeLanguage]): Languages for code generation
- `include_code_samples` (bool): Whether to include code samples (default: True)
- `include_response_examples` (bool): Whether to include response examples (default: True)

**Methods:**
- `enhance_openapi_schema(schema, documentation_data)` → `dict`: Enhance a schema
- `add_code_samples_to_operation(operation, endpoint)`: Add code samples to an operation
- `add_response_examples_to_operation(operation, endpoint)`: Add response examples

```python
from fastmarkdocs import OpenAPIEnhancer, CodeLanguage

enhancer = OpenAPIEnhancer(
    base_url="https://api.example.com",
    custom_headers={"X-API-Key": "your-key"},
    code_sample_languages=[CodeLanguage.PYTHON, CodeLanguage.GO],
    include_code_samples=True,
    include_response_examples=True
)

# Enhance schema
enhanced = enhancer.enhance_openapi_schema(openapi_schema, documentation_data)
```

## Supported Languages

The library supports code generation for:

- **Python** - Using `requests` library
- **JavaScript** - Using `fetch` API
- **TypeScript** - With proper type annotations
- **Go** - Using `net/http` package
- **Java** - Using `HttpURLConnection`
- **PHP** - Using `cURL`
- **Ruby** - Using `net/http`
- **C#** - Using `HttpClient`
- **cURL** - Command-line examples

## Error Handling

The library provides comprehensive error handling:

```python
from fastmarkdocs.exceptions import (
    DocumentationLoadError,
    CodeSampleGenerationError,
    OpenAPIEnhancementError,
    ValidationError
)

try:
    docs = loader.load_documentation()
except DocumentationLoadError as e:
    print(f"Failed to load documentation: {e}")
```

## Testing

Run the test suite:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=fastmarkdocs

# Run specific test categories
pytest -m unit
pytest -m integration
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Documentation Development

To build and test the documentation locally:

```bash
# First time setup (install Ruby dependencies)
./build-docs.sh setup

# Build and serve locally with live reload
./build-docs.sh serve

# Or using Make
make -f Makefile.docs docs-serve
```

The documentation will be available at `http://localhost:4001` with automatic reloading when you make changes.

See [src/docs/BUILD.md](src/docs/BUILD.md) for detailed documentation build instructions.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/fastmarkdocs.git
cd fastmarkdocs

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run tests
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## Support

- 📖 [Documentation](https://github.com/danvatca/fastmarkdocs)
- 🐛 [Issue Tracker](https://github.com/danvatca/fastmarkdocs/issues)
- 💬 [Discussions](https://github.com/danvatca/fastmarkdocs/discussions)

## Related Projects

- [FastAPI](https://fastapi.tiangolo.com/) - The web framework this library enhances
- [OpenAPI](https://swagger.io/specification/) - The specification this library extends
- [Swagger UI](https://swagger.io/tools/swagger-ui/) - The UI that displays the enhanced documentation
