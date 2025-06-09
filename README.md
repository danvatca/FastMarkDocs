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
🎨 **Customizable Templates**: Use custom templates for code generation  
⚡ **High Performance**: Built-in caching and optimized processing  
🧪 **Well Tested**: Comprehensive test suite with 100+ tests  

## Quick Start

### Installation

```bash
pip install fastmarkdocs
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
    custom_headers={"Authorization": "Bearer token123"}
)

# Update your app's OpenAPI schema
app.openapi_schema = enhanced_schema
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

## Advanced Features

### Custom Code Generation

```python
from fastmarkdocs import CodeSampleGenerator

generator = CodeSampleGenerator(
    base_url="https://api.example.com",
    custom_headers={"X-API-Key": "your-key"},
    code_sample_languages=["python", "javascript", "go"]
)

# Generate samples for a specific endpoint
samples = generator.generate_samples_for_endpoint(endpoint_data)
```

### Template Customization

```python
from fastmarkdocs import DocumentationLoader

loader = DocumentationLoader(
    docs_directory="docs/api",
    custom_templates={
        "python": """
import requests

def {method_lower}_{path_safe}():
    response = requests.{method_lower}("{url}")
    return response.json()
"""
    }
)
```

### Caching Configuration

```python
from fastmarkdocs import DocumentationLoader

loader = DocumentationLoader(
    docs_directory="docs/api",
    enable_caching=True,
    cache_ttl=3600  # 1 hour
)
```

## API Reference

### Core Functions

#### `enhance_openapi_with_docs()`

Enhance an OpenAPI schema with markdown documentation.

**Parameters:**
- `openapi_schema` (dict): The original OpenAPI schema
- `docs_directory` (str): Path to markdown documentation directory
- `base_url` (str, optional): Base URL for code samples
- `custom_headers` (dict, optional): Custom headers for code samples
- `code_sample_languages` (list, optional): Languages for code generation

**Returns:** Enhanced OpenAPI schema (dict)

### Classes

#### `DocumentationLoader`

Load and process markdown documentation files.

```python
loader = DocumentationLoader(
    docs_directory="docs/api",
    enable_caching=True,
    cache_ttl=3600,
    custom_templates={}
)

# Load all documentation
docs = loader.load_documentation()
```

#### `CodeSampleGenerator`

Generate code samples for API endpoints.

```python
generator = CodeSampleGenerator(
    base_url="https://api.example.com",
    custom_headers={"Authorization": "Bearer token"},
    code_sample_languages=["python", "javascript"]
)

# Generate samples
samples = generator.generate_samples_for_endpoint(endpoint)
```

#### `OpenAPIEnhancer`

Enhance OpenAPI schemas with documentation data.

```python
enhancer = OpenAPIEnhancer(
    base_url="https://api.example.com",
    custom_headers={"X-API-Key": "key"},
    code_sample_languages=["python", "go"]
)

# Enhance schema
enhanced = enhancer.enhance_openapi_schema(schema, documentation)
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
# First time setup
./build-docs.sh setup

# Build and serve locally with live reload
./build-docs.sh serve

# Or using Make
make -f Makefile.docs docs-serve
```

The documentation will be available at `http://localhost:4000` with automatic reloading when you make changes.

See [docs/BUILD.md](docs/BUILD.md) for detailed documentation build instructions.

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
