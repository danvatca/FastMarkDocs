"""
Copyright (c) 2025 Dan Vatca

Custom exceptions for FastMarkDocs.

This module defines custom exception classes for handling various error conditions
that can occur during documentation processing, code sample generation, and
OpenAPI schema enhancement.
"""

from typing import Optional


class FastAPIMarkdownDocsError(Exception):
    """Base exception for all FastMarkDocs errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class DocumentationLoadError(FastAPIMarkdownDocsError):
    """Raised when documentation files cannot be loaded or parsed."""

    def __init__(self, file_path: str, message: str, details: Optional[str] = None):
        self.file_path = file_path
        super().__init__(f"Failed to load documentation from '{file_path}': {message}", details)


class CodeSampleGenerationError(FastAPIMarkdownDocsError):
    """Raised when code sample generation fails."""

    def __init__(self, language: str, endpoint: str, message: str, details: Optional[str] = None):
        self.language = language
        self.endpoint = endpoint
        super().__init__(f"Failed to generate {language} code sample for '{endpoint}': {message}", details)


class OpenAPIEnhancementError(FastAPIMarkdownDocsError):
    """Raised when OpenAPI schema enhancement fails."""

    def __init__(self, schema_path: str, message: str, details: Optional[str] = None):
        self.schema_path = schema_path
        super().__init__(f"Failed to enhance OpenAPI schema at '{schema_path}': {message}", details)


class ValidationError(FastAPIMarkdownDocsError):
    """Raised when documentation validation fails."""

    def __init__(
        self, file_path: str, line_number: Optional[int] = None, message: str = "", details: Optional[str] = None
    ):
        self.file_path = file_path
        self.line_number = line_number
        location = f"line {line_number}" if line_number else "unknown location"
        super().__init__(f"Validation error in '{file_path}' at {location}: {message}", details)


class ConfigurationError(FastAPIMarkdownDocsError):
    """Raised when configuration is invalid."""

    def __init__(self, config_key: str, message: str, details: Optional[str] = None):
        self.config_key = config_key
        super().__init__(f"Invalid configuration for '{config_key}': {message}", details)


class TemplateError(FastAPIMarkdownDocsError):
    """Raised when template processing fails."""

    def __init__(self, template_name: str, message: str, details: Optional[str] = None):
        self.template_name = template_name
        super().__init__(f"Template error in '{template_name}': {message}", details)
