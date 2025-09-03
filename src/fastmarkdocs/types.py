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
    """Enhanced response example supporting multiple content types."""

    status_code: int
    description: str
    content: Optional[Union[dict[str, Any], str, bytes]] = None
    content_type: str = "application/json"
    headers: Optional[dict[str, str]] = None
    raw_content: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.status_code, int) or self.status_code < 100 or self.status_code >= 600:
            raise ValueError("Status code must be a valid HTTP status code (100-599)")

        # Auto-detect content type if not specified and raw content is available
        if self.content_type == "application/json" and self.raw_content:
            self.content_type = self._detect_content_type(self.raw_content)

        # Set content based on detected content type if not already set
        if self.content is None and self.raw_content:
            self._set_content_from_raw()

    def _detect_content_type(self, content: str) -> str:
        """Auto-detect content type from raw content."""
        import json
        import re

        content = content.strip()

        # Prometheus metrics detection
        if (
            content.startswith("# HELP")
            or content.startswith("# TYPE")
            or re.search(r"^# (HELP|TYPE)", content, re.MULTILINE)
        ):
            return "text/plain; version=0.0.4"

        # HTML detection (check before XML to avoid false positives)
        if content.startswith("<!DOCTYPE html") or content.startswith("<html"):
            return "text/html"

        # XML detection
        if content.startswith("<?xml") or (content.startswith("<") and content.endswith(">")):
            return "application/xml"

        # YAML detection (basic heuristic)
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*:\s", content, re.MULTILINE):
            return "application/yaml"

        # CSV detection (basic heuristic)
        lines = content.split("\n")
        if len(lines) > 1 and all("," in line for line in lines[:3]):
            return "text/csv"

        # JSON detection
        try:
            json.loads(content)
            return "application/json"
        except (json.JSONDecodeError, ValueError):
            pass

        # Default to plain text
        return "text/plain"

    def _set_content_from_raw(self) -> None:
        """Set content field based on detected content type and raw content."""
        if not self.raw_content:
            return

        if self.content_type == "application/json":
            try:
                import json

                self.content = json.loads(self.raw_content)
            except (json.JSONDecodeError, ValueError):
                # If JSON parsing fails, treat as plain text
                self.content = self.raw_content
                self.content_type = "text/plain"
        elif self.content_type == "application/yaml":
            # Handle YAML content - try to parse if PyYAML is available
            try:
                import yaml

                self.content = yaml.safe_load(self.raw_content)
            except ImportError:
                # If PyYAML not available, store as string
                self.content = self.raw_content
            except Exception:  # yaml.YAMLError or other parsing errors
                # If YAML parsing fails, store as string
                self.content = self.raw_content
        else:
            # For all other content types (text/plain, XML, HTML, CSV, etc.), store as string
            self.content = self.raw_content


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
class TagDescription:
    """Represents a tag with its description from markdown overview sections."""

    name: str
    description: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Tag name cannot be empty")
        if not self.description:
            raise ValueError("Tag description cannot be empty")


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
    tag_descriptions: dict[str, str] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access for backwards compatibility."""
        if key == "endpoints":
            return self.endpoints
        elif key == "global_examples":
            return self.global_examples
        elif key == "metadata":
            return self.metadata
        elif key == "tag_descriptions":
            return self.tag_descriptions
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
    """Enhanced configuration for OpenAPI schema enhancement supporting multiple content types."""

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
    supported_content_types: list[str] = field(
        default_factory=lambda: [
            "application/json",
            "text/plain",
            "text/plain; version=0.0.4",  # Prometheus metrics
            "application/xml",
            "application/yaml",
            "text/html",
            "text/csv",
        ]
    )
    content_type_detection: bool = True
    preserve_raw_content: bool = True
    validate_content_format: bool = True


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
