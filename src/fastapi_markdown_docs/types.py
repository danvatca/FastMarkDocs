"""
Type definitions for FastAPI Markdown Docs.

This module contains all the type definitions used throughout the library,
including data structures for documentation, code samples, and configuration.
"""

from typing import Dict, List, Optional, Union, Any
from enum import Enum
from dataclasses import dataclass, field


class CodeLanguage(str, Enum):
    """Supported code sample languages."""
    CURL = "curl"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    PHP = "php"
    RUBY = "ruby"
    CSHARP = "csharp"

    def __str__(self) -> str:
        return self.value


class HTTPMethod(str, Enum):
    """HTTP methods supported for code sample generation."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

    def __str__(self) -> str:
        return self.value


@dataclass
class CodeSample:
    """Represents a code sample extracted from markdown."""
    language: CodeLanguage
    code: str
    description: Optional[str] = None
    title: Optional[str] = None

    def __post_init__(self):
        if not self.code:
            raise ValueError("Code cannot be empty")


@dataclass
class ResponseExample:
    """Represents a response example from documentation."""
    status_code: int
    description: str
    content: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if not isinstance(self.status_code, int) or self.status_code < 100 or self.status_code >= 600:
            raise ValueError("Status code must be a valid HTTP status code (100-599)")


@dataclass
class ParameterDocumentation:
    """Documentation for a single parameter."""
    name: str
    description: str
    example: Optional[Any] = None
    required: Optional[bool] = None
    type: Optional[str] = None

    def __post_init__(self):
        if not self.name:
            raise ValueError("Parameter name cannot be empty")


@dataclass
class EndpointDocumentation:
    """Complete documentation for an API endpoint."""
    path: str
    method: HTTPMethod
    summary: Optional[str] = None
    description: Optional[str] = None
    code_samples: List[CodeSample] = field(default_factory=list)
    response_examples: List[ResponseExample] = field(default_factory=list)
    parameters: List[ParameterDocumentation] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False

    def __post_init__(self):
        if not self.path:
            raise ValueError("Path cannot be empty")
        if not isinstance(self.method, HTTPMethod):
            raise TypeError("Method must be an HTTPMethod enum value")


@dataclass
class DocumentationData:
    """Container for all documentation data loaded from markdown files."""
    endpoints: List[EndpointDocumentation] = field(default_factory=list)
    global_examples: List[CodeSample] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __getitem__(self, key):
        """Allow dictionary-style access for backwards compatibility."""
        if key == 'endpoints':
            return self.endpoints
        elif key == 'global_examples':
            return self.global_examples
        elif key == 'metadata':
            return self.metadata
        else:
            raise KeyError(f"'{key}' not found in DocumentationData")


@dataclass
class MarkdownDocumentationConfig:
    """Configuration for markdown documentation loading."""
    docs_directory: str = "docs"
    base_url_placeholder: str = "https://api.example.com"
    supported_languages: List[CodeLanguage] = field(default_factory=lambda: list(CodeLanguage))
    file_patterns: List[str] = field(default_factory=lambda: ["*.md", "*.markdown"])
    encoding: str = "utf-8"
    recursive: bool = True
    cache_enabled: bool = True
    cache_ttl: int = 3600


@dataclass
class OpenAPIEnhancementConfig:
    """Configuration for OpenAPI schema enhancement."""
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


@dataclass
class CodeSampleTemplate:
    """Template for generating code samples."""
    language: CodeLanguage
    template: str
    imports: List[str] = field(default_factory=list)
    setup_code: Optional[str] = None
    cleanup_code: Optional[str] = None


@dataclass
class ValidationError:
    """Represents a validation error in documentation."""
    file_path: str
    line_number: Optional[int]
    error_type: str
    message: str
    suggestion: Optional[str] = None


@dataclass
class DocumentationStats:
    """Statistics about loaded documentation."""
    total_files: int
    total_endpoints: int
    total_code_samples: int
    languages_found: List[CodeLanguage]
    validation_errors: List[ValidationError]
    load_time_ms: float


@dataclass
class EnhancementResult:
    """Result of OpenAPI schema enhancement."""
    enhanced_schema: Dict[str, Any]
    enhancement_stats: Dict[str, int]
    warnings: List[str]
    errors: List[str]


# Union types for flexibility
PathParameter = Union[str, int, float]
QueryParameter = Union[str, int, float, bool, List[Union[str, int, float]]]
HeaderValue = Union[str, int, float]

# Type aliases for common patterns
EndpointKey = str  # Format: "METHOD:path"
FilePath = str
URLPath = str
MarkdownContent = str
JSONSchema = Dict[str, Any]
OpenAPISchema = Dict[str, Any]

# Configuration type unions
AnyConfig = Union[MarkdownDocumentationConfig, OpenAPIEnhancementConfig]
AnyDocumentationData = Union[DocumentationData, EndpointDocumentation, CodeSample] 