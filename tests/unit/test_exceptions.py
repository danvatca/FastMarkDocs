"""
Unit tests for custom exceptions.

Tests the custom exception classes and their behavior.
"""

from fastmarkdocs.exceptions import (
    CodeSampleGenerationError,
    ConfigurationError,
    DocumentationLoadError,
    FastAPIMarkdownDocsError,
    OpenAPIEnhancementError,
    TemplateError,
    ValidationError,
)


class TestExceptions:
    """Test custom exception classes."""

    def test_base_exception_with_details(self) -> None:
        """Test base exception with details."""
        exc = FastAPIMarkdownDocsError("Test message", "Additional details")

        assert str(exc) == "Test message: Additional details"
        assert exc.message == "Test message"
        assert exc.details == "Additional details"

    def test_base_exception_without_details(self) -> None:
        """Test base exception without details."""
        exc = FastAPIMarkdownDocsError("Test message")

        assert str(exc) == "Test message"
        assert exc.message == "Test message"
        assert exc.details is None

    def test_documentation_load_error(self) -> None:
        """Test DocumentationLoadError."""
        exc = DocumentationLoadError("test.md", "File not found", "Additional context")

        assert "test.md" in str(exc)
        assert "File not found" in str(exc)
        assert exc.file_path == "test.md"

    def test_code_sample_generation_error(self) -> None:
        """Test CodeSampleGenerationError."""
        exc = CodeSampleGenerationError("python", "GET:/api/users", "Template error", "Missing variable")

        assert "python" in str(exc)
        assert "GET:/api/users" in str(exc)
        assert "Template error" in str(exc)
        assert exc.language == "python"
        assert exc.endpoint == "GET:/api/users"

    def test_openapi_enhancement_error(self) -> None:
        """Test OpenAPIEnhancementError."""
        exc = OpenAPIEnhancementError("/paths/users", "Invalid schema", "Missing required field")

        assert "/paths/users" in str(exc)
        assert "Invalid schema" in str(exc)
        assert exc.schema_path == "/paths/users"

    def test_validation_error_with_line_number(self) -> None:
        """Test ValidationError with line number."""
        exc = ValidationError("test.md", line_number=42, message="Invalid syntax", details="Missing colon")

        assert "test.md" in str(exc)
        assert "line 42" in str(exc)
        assert "Invalid syntax" in str(exc)
        assert exc.file_path == "test.md"
        assert exc.line_number == 42

    def test_validation_error_without_line_number(self) -> None:
        """Test ValidationError without line number."""
        exc = ValidationError("test.md", message="Invalid syntax")

        assert "test.md" in str(exc)
        assert "unknown location" in str(exc)
        assert "Invalid syntax" in str(exc)
        assert exc.line_number is None

    def test_configuration_error(self) -> None:
        """Test ConfigurationError."""
        exc = ConfigurationError("api_key", "Missing required value", "Check your settings")

        assert "api_key" in str(exc)
        assert "Missing required value" in str(exc)
        assert exc.config_key == "api_key"

    def test_template_error(self) -> None:
        """Test TemplateError."""
        exc = TemplateError("python_template", "Invalid syntax", "Missing closing brace")

        assert "python_template" in str(exc)
        assert "Invalid syntax" in str(exc)
        assert exc.template_name == "python_template"

    def test_exception_inheritance(self) -> None:
        """Test that all exceptions inherit from base exception."""
        assert issubclass(DocumentationLoadError, FastAPIMarkdownDocsError)
        assert issubclass(CodeSampleGenerationError, FastAPIMarkdownDocsError)
        assert issubclass(OpenAPIEnhancementError, FastAPIMarkdownDocsError)
        assert issubclass(ValidationError, FastAPIMarkdownDocsError)
        assert issubclass(ConfigurationError, FastAPIMarkdownDocsError)
        assert issubclass(TemplateError, FastAPIMarkdownDocsError)

    def test_exception_with_none_details(self) -> None:
        """Test exceptions with None details."""
        exc1 = DocumentationLoadError("test.md", "Error message", None)
        exc2 = CodeSampleGenerationError("python", "endpoint", "Error", None)
        exc3 = OpenAPIEnhancementError("path", "Error", None)

        assert exc1.details is None
        assert exc2.details is None
        assert exc3.details is None
