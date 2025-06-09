"""
Copyright (c) 2025 Dan Vatca

FastMarkDocs - Enhanced OpenAPI documentation generation from markdown files.

This library provides sophisticated tools for generating rich, interactive API documentation
from structured markdown files for FastAPI applications. It combines markdown parsing,
multi-language code sample generation, and OpenAPI schema enhancement.

Key Features:
- Advanced markdown parsing with code sample extraction
- Multi-language code sample generation (cURL, Python, JavaScript, etc.)
- OpenAPI schema enhancement with examples and descriptions
- Production-ready with comprehensive error handling
- Framework-agnostic design (works with any OpenAPI-compatible framework)

Example:
    ```python
    from fastapi import FastAPI
    from fastmarkdocs import MarkdownDocumentationLoader, enhance_openapi_with_docs

    app = FastAPI()

    # Load documentation from markdown files
    docs_loader = MarkdownDocumentationLoader("docs/api")

    # Enhance OpenAPI schema with markdown documentation
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title="My API",
            version="1.0.0",
            routes=app.routes,
        )

        # Enhance with markdown documentation
        enhanced_schema = enhance_openapi_with_docs(openapi_schema, docs_loader)
        app.openapi_schema = enhanced_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    ```
"""

__version__ = "0.1.0"
__author__ = "Dan Vatca"
__email__ = "dan.vatca@gmail.com"
__license__ = "MIT"

# Core components
from .code_samples import CodeSampleGenerator
from .documentation_loader import MarkdownDocumentationLoader
from .exceptions import (
    CodeSampleGenerationError,
    DocumentationLoadError,
    FastAPIMarkdownDocsError,
    OpenAPIEnhancementError,
)
from .openapi_enhancer import OpenAPIEnhancer, enhance_openapi_with_docs

# Type definitions
from .types import (
    CodeLanguage,
    CodeSample,
    DocumentationData,
    HTTPMethod,
    MarkdownDocumentationConfig,
    OpenAPIEnhancementConfig,
)

# Utility functions
from .utils import (
    extract_code_samples,
    normalize_path,
    validate_markdown_structure,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    # Core classes
    "MarkdownDocumentationLoader",
    "OpenAPIEnhancer",
    "CodeSampleGenerator",
    # Main functions
    "enhance_openapi_with_docs",
    # Exceptions
    "FastAPIMarkdownDocsError",
    "DocumentationLoadError",
    "CodeSampleGenerationError",
    "OpenAPIEnhancementError",
    # Utilities
    "normalize_path",
    "extract_code_samples",
    "validate_markdown_structure",
    # Types
    "DocumentationData",
    "CodeSample",
    "OpenAPIEnhancementConfig",
    "MarkdownDocumentationConfig",
    "CodeLanguage",
    "HTTPMethod",
]
