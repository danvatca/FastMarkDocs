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

import os
import re

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
    APILink,
    CodeLanguage,
    CodeSample,
    DocumentationData,
    EndpointDocumentation,
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


def _get_version_from_pyproject() -> str:
    """Get version from pyproject.toml during development."""
    root = os.path.dirname(__file__)
    # Look for pyproject.toml in the package root
    for _ in range(5):  # Search up to 5 levels up
        pyproject = os.path.join(root, "..", "..", "pyproject.toml")
        if os.path.exists(pyproject):
            break
        pyproject = os.path.join(root, "..", pyproject)
        if os.path.exists(pyproject):
            break
        root = os.path.dirname(root)
    else:
        # Final attempt at common locations
        pyproject = os.path.join(os.path.dirname(__file__), "..", "..", "pyproject.toml")

    try:
        with open(pyproject, encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("version"):
                    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', line)
                    if match:
                        return match.group(1)
    except (OSError, UnicodeDecodeError):
        # File reading errors are expected during version detection fallback
        # OSError covers FileNotFoundError, PermissionError, etc.
        # UnicodeDecodeError covers encoding issues
        return "unknown"
    return "unknown"


# Try to get version from package metadata (production)
__version__ = "unknown"

# First try the standard library (Python 3.8+)
try:
    import importlib.metadata

    __version__ = importlib.metadata.version("fastmarkdocs")
except (ImportError, Exception):
    # Python < 3.8 fallback
    try:
        import importlib_metadata  # type: ignore[import-not-found]

        __version__ = importlib_metadata.version("fastmarkdocs")
    except (ImportError, Exception):
        # Development fallback - read from pyproject.toml
        __version__ = _get_version_from_pyproject()

__author__ = "Dan Vatca"
__email__ = "dan.vatca@gmail.com"
__license__ = "MIT"

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
    "EndpointDocumentation",
    "OpenAPIEnhancementConfig",
    "MarkdownDocumentationConfig",
    "CodeLanguage",
    "HTTPMethod",
    "APILink",
]
