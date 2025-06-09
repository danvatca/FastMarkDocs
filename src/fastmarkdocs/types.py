"""
Copyright (c) 2025 Dan Vatca

Type definitions for FastMarkDocs.

This module contains all type definitions, enums, and data classes used throughout
the library for type safety and better IDE support.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union


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

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("Code cannot be empty")


@dataclass
class APILink:
    """Represents a link to another API in the system."""

    url: str
    description: str

    def __post_init__(self) -> None:
        if not self.url:
            raise ValueError("URL cannot be empty")
        if not self.description:
            raise ValueError("Description cannot be empty")


@dataclass
class ResponseExample:
    """Represents a response example from documentation."""

    status_code: int
    description: str
    content: Optional[dict[str, Any]] = None
    headers: Optional[dict[str, str]] = None

    def __post_init__(self) -> None:
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

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Parameter name cannot be empty")


@dataclass
class EndpointDocumentation:
    """Complete documentation for an API endpoint."""

    path: str
    method: HTTPMethod
    summary: Optional[str] = None
    description: Optional[str] = None
    code_samples: list[CodeSample] = field(default_factory=list)
    response_examples: list[ResponseExample] = field(default_factory=list)
    parameters: list[ParameterDocumentation] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    deprecated: bool = False

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("Path cannot be empty")
        if not isinstance(self.method, HTTPMethod):
            raise TypeError("Method must be an HTTPMethod enum value")


@dataclass
class DocumentationData:
    """Container for all documentation data loaded from markdown files."""

    endpoints: list[EndpointDocumentation] = field(default_factory=list)
    global_examples: list[CodeSample] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access for backwards compatibility."""
        if key == "endpoints":
            return self.endpoints
        elif key == "global_examples":
            return self.global_examples
        elif key == "metadata":
            return self.metadata
        else:
            raise KeyError(f"'{key}' not found in DocumentationData")


@dataclass
class MarkdownDocumentationConfig:
    """Configuration for markdown documentation loading."""

    docs_directory: str = "docs"
    base_url_placeholder: str = "https://api.example.com"
    supported_languages: list[CodeLanguage] = field(default_factory=lambda: list(CodeLanguage))
    file_patterns: list[str] = field(default_factory=lambda: ["*.md", "*.markdown"])
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
    code_sample_languages: list[CodeLanguage] = field(
        default_factory=lambda: [CodeLanguage.CURL, CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT]
    )
    base_url: Optional[str] = "https://api.example.com"
    server_urls: list[str] = field(default_factory=lambda: ["https://api.example.com"])
    custom_headers: dict[str, str] = field(default_factory=dict)
    authentication_schemes: list[str] = field(default_factory=list)


@dataclass
class CodeSampleTemplate:
    """Template for generating code samples."""

    language: CodeLanguage
    template: str
    imports: list[str] = field(default_factory=list)
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
    languages_found: list[CodeLanguage]
    validation_errors: list[ValidationError]
    load_time_ms: float


@dataclass
class EnhancementResult:
    """Result of OpenAPI schema enhancement."""

    enhanced_schema: dict[str, Any]
    enhancement_stats: dict[str, int]
    warnings: list[str]
    errors: list[str]


# Union types for flexibility
PathParameter = Union[str, int, float]
QueryParameter = Union[str, int, float, bool, list[Union[str, int, float]]]
HeaderValue = Union[str, int, float]

# Type aliases for common patterns
EndpointKey = str  # Format: "METHOD:path"
FilePath = str
URLPath = str
MarkdownContent = str
JSONSchema = dict[str, Any]
OpenAPISchema = dict[str, Any]

# Configuration type unions
AnyConfig = Union[MarkdownDocumentationConfig, OpenAPIEnhancementConfig]
AnyDocumentationData = Union[DocumentationData, EndpointDocumentation, CodeSample]
