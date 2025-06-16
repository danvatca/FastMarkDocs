---
layout: default
title: API Reference
description: Complete API reference for FastMarkDocs
nav_order: 3
---

# API Reference

Complete reference documentation for all FastMarkDocs classes, functions, and types.

## Core Functions

### enhance_openapi_with_docs()

The main function for enhancing OpenAPI schemas with markdown documentation.

```python
def enhance_openapi_with_docs(
    openapi_schema: Dict[str, Any],
    docs_directory: str,
    base_url: str = "https://api.example.com",
    include_code_samples: bool = True,
    include_response_examples: bool = True,
    code_sample_languages: Optional[List[CodeLanguage]] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    app_title: Optional[str] = None,
    app_description: Optional[str] = None,
    api_links: Optional[List[APILink]] = None,
    general_docs_file: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `openapi_schema` (Dict[str, Any]): The original OpenAPI schema to enhance
- `docs_directory` (str): Path to the directory containing markdown documentation
- `base_url` (str): Base URL for generated code samples (default: "https://api.example.com")
- `include_code_samples` (bool): Whether to include code samples in the enhanced schema
- `include_response_examples` (bool): Whether to include response examples
- `code_sample_languages` (Optional[List[CodeLanguage]]): List of languages for code sample generation
- `custom_headers` (Optional[Dict[str, str]]): Custom headers to include in code samples
- `app_title` (Optional[str]): Override the application title in the OpenAPI schema
- `app_description` (Optional[str]): Application description to include in the schema
- `api_links` (Optional[List[APILink]]): List of links to other APIs in your system
- `general_docs_file` (Optional[str]): Path to general documentation file (default: "general_docs.md" if found)

**Returns:** Enhanced OpenAPI schema (Dict[str, Any])

**Example:**
```python
from fastmarkdocs import enhance_openapi_with_docs

enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=app.openapi(),
    docs_directory="docs/api",
    base_url="https://api.example.com",
    code_sample_languages=["python", "javascript", "curl"],
    custom_headers={"Authorization": "Bearer token"}
)
```

## Core Classes

### MarkdownDocumentationLoader

Loads and processes markdown documentation files.

```python
class MarkdownDocumentationLoader:
    def __init__(
        self,
        docs_directory: str = "docs",
        base_url_placeholder: str = "https://api.example.com",
        supported_languages: Optional[List[CodeLanguage]] = None,
        file_patterns: Optional[List[str]] = None,
        encoding: str = "utf-8",
        recursive: bool = True,
        cache_enabled: bool = True,
        cache_ttl: int = 3600,
        general_docs_file: Optional[str] = None
    )
```

**Parameters:**
- `docs_directory` (str): Directory containing markdown files
- `base_url_placeholder` (str): Placeholder for base URL in documentation
- `supported_languages` (Optional[List[CodeLanguage]]): List of supported code sample languages for filtering
- `file_patterns` (Optional[List[str]]): File patterns to match (default: ["*.md", "*.markdown"])
- `encoding` (str): File encoding to use when reading files
- `recursive` (bool): Whether to search subdirectories recursively
- `cache_enabled` (bool): Whether to enable caching for performance
- `cache_ttl` (int): Cache time-to-live in seconds
- `general_docs_file` (Optional[str]): Path to general documentation file (default: "general_docs.md" if found)

#### Methods

##### load_documentation()

```python
def load_documentation() -> DocumentationData
```

Loads all documentation from the configured directory.

**Returns:** DocumentationData object containing all loaded documentation

**Example:**
```python
loader = MarkdownDocumentationLoader("docs/api")
documentation = loader.load_documentation()

print(f"Loaded {len(documentation.endpoints)} endpoints")
for endpoint in documentation.endpoints:
    print(f"{endpoint.method} {endpoint.path}")
```

##### load_file()

```python
def load_file(file_path: str) -> List[EndpointDocumentation]
```

Loads documentation from a specific file.

**Parameters:**
- `file_path` (str): Path to the markdown file to load

**Returns:** List of EndpointDocumentation objects

##### validate_documentation()

```python
def validate_documentation(documentation: DocumentationData) -> List[ValidationError]
```

Validates loaded documentation for common issues.

**Parameters:**
- `documentation` (DocumentationData): Documentation to validate

**Returns:** List of validation errors found

### CodeSampleGenerator

Generates code samples for API endpoints in multiple programming languages.

```python
class CodeSampleGenerator:
    def __init__(
        self,
        base_url: str = "https://api.example.com",
        custom_headers: Optional[Dict[str, str]] = None,
        code_sample_languages: Optional[List[CodeLanguage]] = None,
        server_urls: Optional[List[str]] = None,
        authentication_schemes: Optional[List[str]] = None,
        custom_templates: Optional[Dict[CodeLanguage, str]] = None,
        cache_enabled: bool = False
    )
```

**Parameters:**
- `base_url` (str): Base URL for generated code samples
- `custom_headers` (Optional[Dict[str, str]]): Headers to include in generated samples
- `code_sample_languages` (Optional[List[CodeLanguage]]): Languages to generate samples for
- `server_urls` (Optional[List[str]]): List of server URLs for multi-environment support
- `authentication_schemes` (Optional[List[str]]): Authentication schemes to support (e.g., "bearer", "api_key", "basic")
- `custom_templates` (Optional[Dict[CodeLanguage, str]]): Custom templates for code generation with variables
- `cache_enabled` (bool): Whether to enable caching for improved performance

#### Methods

##### generate_samples_for_endpoint()

```python
def generate_samples_for_endpoint(
    endpoint: EndpointDocumentation
) -> List[CodeSample]
```

Generates code samples for a specific endpoint.

**Parameters:**
- `endpoint` (EndpointDocumentation): Endpoint to generate samples for

**Returns:** List of generated code samples

##### generate_samples()

```python
def generate_samples(
    method: HTTPMethod,
    path: str,
    parameters: List[ParameterDocumentation] = None,
    request_body: Dict[str, Any] = None
) -> List[CodeSample]
```

Generates code samples for specified endpoint details.

**Example:**
```python
from fastmarkdocs import CodeSampleGenerator
from fastmarkdocs.types import CodeLanguage, HTTPMethod

generator = CodeSampleGenerator(
    base_url="https://api.example.com",
    code_sample_languages=[CodeLanguage.PYTHON, CodeLanguage.CURL],
    custom_headers={"Authorization": "Bearer token"}
)

samples = generator.generate_samples(
    method=HTTPMethod.GET,
    path="/users",
    parameters=[]
)

for sample in samples:
    print(f"{sample.language}:")
    print(sample.code)
```

### OpenAPIEnhancer

Enhances OpenAPI schemas with documentation data.

```python
class OpenAPIEnhancer:
    def __init__(
        self,
        include_code_samples: bool = True,
        include_response_examples: bool = True,
        include_parameter_examples: bool = True,
        code_sample_languages: Optional[List[CodeLanguage]] = None,
        base_url: str = "https://api.example.com",
        server_urls: Optional[List[str]] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        authentication_schemes: Optional[List[str]] = None
    )
```

**Parameters:**
- `include_code_samples` (bool): Whether to include code samples in the enhanced schema
- `include_response_examples` (bool): Whether to include response examples
- `include_parameter_examples` (bool): Whether to include parameter examples
- `code_sample_languages` (Optional[List[CodeLanguage]]): Languages to generate samples for
- `base_url` (str): Base URL for generated code samples
- `server_urls` (Optional[List[str]]): List of server URLs for multi-environment support
- `custom_headers` (Optional[Dict[str, str]]): Headers to include in generated samples
- `authentication_schemes` (Optional[List[str]]): Authentication schemes to support

#### Methods

##### enhance_openapi_schema()

```python
def enhance_openapi_schema(
    openapi_schema: Dict[str, Any],
    documentation: DocumentationData
) -> Dict[str, Any]
```

Enhances an OpenAPI schema with documentation data.

**Parameters:**
- `openapi_schema` (Dict[str, Any]): Original OpenAPI schema
- `documentation` (DocumentationData): Documentation to integrate

**Returns:** Enhanced OpenAPI schema

## Data Types

### DocumentationData

Container for all documentation data loaded from markdown files.

```python
@dataclass
class DocumentationData:
    endpoints: List[EndpointDocumentation] = field(default_factory=list)
    global_examples: List[CodeSample] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Attributes:**
- `endpoints`: List of documented endpoints
- `global_examples`: Global code examples not tied to specific endpoints
- `metadata`: Additional metadata about the documentation

### EndpointDocumentation

Complete documentation for an API endpoint.

```python
@dataclass
class EndpointDocumentation:
    path: str
    method: HTTPMethod
    summary: Optional[str] = None
    description: Optional[str] = None
    code_samples: List[CodeSample] = field(default_factory=list)
    response_examples: List[ResponseExample] = field(default_factory=list)
    parameters: List[ParameterDocumentation] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
```

**Attributes:**
- `path`: API endpoint path (e.g., "/users/{id}")
- `method`: HTTP method (GET, POST, etc.)
- `summary`: Brief description of the endpoint
- `description`: Detailed description
- `code_samples`: List of code examples
- `response_examples`: List of response examples
- `parameters`: List of parameter documentation
- `tags`: List of tags for categorization
- `deprecated`: Whether the endpoint is deprecated

### CodeSample

Represents a code sample extracted from markdown or generated automatically.

```python
@dataclass
class CodeSample:
    language: CodeLanguage
    code: str
    description: Optional[str] = None
    title: Optional[str] = None
```

**Attributes:**
- `language`: Programming language of the sample
- `code`: The actual code content
- `description`: Optional description of what the code does
- `title`: Optional title for the code sample

### ParameterDocumentation

Documentation for a single API parameter.

```python
@dataclass
class ParameterDocumentation:
    name: str
    description: str
    example: Optional[Any] = None
    required: Optional[bool] = None
    type: Optional[str] = None
```

**Attributes:**
- `name`: Parameter name
- `description`: Parameter description
- `example`: Example value
- `required`: Whether the parameter is required
- `type`: Parameter type (string, integer, etc.)

### ResponseExample

Represents a response example from documentation.

```python
@dataclass
class ResponseExample:
    status_code: int
    description: str
    content: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
```

**Attributes:**
- `status_code`: HTTP status code
- `description`: Description of the response
- `content`: Response body content
- `headers`: Response headers

## Enums

### CodeLanguage

Supported programming languages for code sample generation.

```python
class CodeLanguage(str, Enum):
    CURL = "curl"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    PHP = "php"
    RUBY = "ruby"
    CSHARP = "csharp"
```

### HTTPMethod

Supported HTTP methods.

```python
class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
```

## Configuration Classes

### MarkdownDocumentationConfig

Configuration for markdown documentation loading.

```python
@dataclass
class MarkdownDocumentationConfig:
    docs_directory: str = "docs"
    base_url_placeholder: str = "https://api.example.com"
    supported_languages: List[CodeLanguage] = field(default_factory=lambda: list(CodeLanguage))
    file_patterns: List[str] = field(default_factory=lambda: ["*.md", "*.markdown"])
    encoding: str = "utf-8"
    recursive: bool = True
    cache_enabled: bool = True
    cache_ttl: int = 3600
```

### OpenAPIEnhancementConfig

Configuration for OpenAPI schema enhancement.

```python
@dataclass
class OpenAPIEnhancementConfig:
    include_code_samples: bool = True
    include_response_examples: bool = True
    include_parameter_examples: bool = True
    code_sample_languages: List[CodeLanguage] = field(default_factory=lambda: [
        CodeLanguage.CURL, CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT
    ])
    base_url: Optional[str] = "https://api.example.com"
    server_urls: List[str] = field(default_factory=lambda: ["https://api.example.com"])
    custom_headers: Dict[str, str] = field(default_factory=dict)
    authentication_schemes: List[str] = field(default_factory=list)
```

## Utility Functions

### normalize_path()

```python
def normalize_path(path: str) -> str
```

Normalizes an API path for consistent processing.

**Parameters:**
- `path` (str): API path to normalize

**Returns:** Normalized path string

### extract_code_samples()

```python
def extract_code_samples(markdown_content: str) -> List[CodeSample]
```

Extracts code samples from markdown content.

**Parameters:**
- `markdown_content` (str): Markdown content to parse

**Returns:** List of extracted code samples

### validate_markdown_structure()

```python
def validate_markdown_structure(content: str) -> List[ValidationError]
```

Validates markdown structure for common issues.

**Parameters:**
- `content` (str): Markdown content to validate

**Returns:** List of validation errors

## Exceptions

### FastAPIMarkdownDocsError

Base exception for all FastMarkDocs errors.

```python
class FastAPIMarkdownDocsError(Exception):
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
```

### DocumentationLoadError

Raised when documentation cannot be loaded or parsed.

```python
class DocumentationLoadError(FastAPIMarkdownDocsError):
    pass
```

### CodeSampleGenerationError

Raised when code sample generation fails.

```python
class CodeSampleGenerationError(FastAPIMarkdownDocsError):
    pass
```

### OpenAPIEnhancementError

Raised when OpenAPI schema enhancement fails.

```python
class OpenAPIEnhancementError(FastAPIMarkdownDocsError):
    pass
```

## Example Usage

### Complete Example

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastmarkdocs import (
    MarkdownDocumentationLoader,
    OpenAPIEnhancer,
    CodeSampleGenerator,
    enhance_openapi_with_docs
)
from fastmarkdocs.types import CodeLanguage

app = FastAPI()

# Method 1: Simple enhancement
def simple_openapi():
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
        base_url="https://api.example.com"
    )
    
    app.openapi_schema = enhanced_schema
    return enhanced_schema

# Method 2: Advanced configuration
def advanced_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    # Load documentation
    loader = MarkdownDocumentationLoader(
        docs_directory="docs/api",
        recursive=True,
        cache_enabled=True
    )
    documentation = loader.load_documentation()
    
    # Generate base schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Enhance schema
    enhancer = OpenAPIEnhancer(
        base_url="https://api.example.com",
        code_sample_languages=[
            CodeLanguage.PYTHON,
            CodeLanguage.JAVASCRIPT,
            CodeLanguage.CURL
        ],
        custom_headers={"Authorization": "Bearer token"}
    )
    
    enhanced_schema = enhancer.enhance_openapi_schema(
        openapi_schema, 
        documentation
    )
    
    app.openapi_schema = enhanced_schema
    return enhanced_schema

# Use either method
app.openapi = simple_openapi
``` 