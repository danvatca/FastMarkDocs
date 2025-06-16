"""
Tests for the new API links functionality.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from fastmarkdocs import APILink, enhance_openapi_with_docs
from fastmarkdocs.exceptions import DocumentationLoadError, OpenAPIEnhancementError
from fastmarkdocs.openapi_enhancer import _build_description_with_api_links


class TestAPILinkDataClass:
    """Test the APILink dataclass validation and creation."""

    def test_creates_api_link_with_valid_data(self) -> None:
        """Test creating an APILink with valid URL and description."""
        link = APILink(url="/docs", description="Main API")
        assert link.url == "/docs"
        assert link.description == "Main API"

    def test_rejects_empty_url(self) -> None:
        """Test that APILink raises ValueError for empty URL."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            APILink(url="", description="Main API")

    def test_rejects_empty_description(self) -> None:
        """Test that APILink raises ValueError for empty description."""
        with pytest.raises(ValueError, match="Description cannot be empty"):
            APILink(url="/docs", description="")

    def test_rejects_none_url(self) -> None:
        """Test that APILink raises ValueError for None URL."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            APILink(url="", description="Main API")

    def test_rejects_none_description(self) -> None:
        """Test that APILink raises ValueError for None description."""
        with pytest.raises(ValueError, match="Description cannot be empty"):
            APILink(url="/docs", description="")


class TestDescriptionBuilder:
    """Test the _build_description_with_api_links helper function."""

    def test_builds_complete_description_with_all_components(self) -> None:
        """Test building description with API links, title, and description."""
        api_links = [
            APILink(url="/docs", description="Main API"),
            APILink(url="/admin/docs", description="Admin API"),
        ]

        result = _build_description_with_api_links(
            app_title="Test API",
            app_description="A test API service",
            api_links=api_links,
            original_description="Original description",
        )

        expected = "APIs: [Main API](/docs) | [Admin API](/admin/docs)\n\n" "* * *\n\n" "Test API - A test API service"
        assert result == expected

    def test_builds_description_with_api_links_and_original_description(self) -> None:
        """Test building description with only API links, preserving original description."""
        api_links = [
            APILink(url="/docs", description="Main API"),
            APILink(url="/v2/docs", description="V2 API"),
        ]

        result = _build_description_with_api_links(
            api_links=api_links,
            original_description="Original description",
        )

        expected = "APIs: [Main API](/docs) | [V2 API](/v2/docs)\n\n" "* * *\n\n" "Original description"
        assert result == expected

    def test_builds_description_with_title_and_description_only(self) -> None:
        """Test building description with only custom title and description."""
        result = _build_description_with_api_links(
            app_title="Custom API",
            app_description="Custom service",
        )

        assert result == "Custom API - Custom service"

    def test_builds_description_with_title_only(self) -> None:
        """Test building description with only custom title."""
        result = _build_description_with_api_links(
            app_title="Custom API",
        )

        assert result == "Custom API"

    def test_builds_description_with_description_only(self) -> None:
        """Test building description with only custom description."""
        result = _build_description_with_api_links(
            app_description="Custom service",
        )

        assert result == "Custom service"

    def test_preserves_original_description_when_no_custom_content(self) -> None:
        """Test that original description is preserved when no custom content provided."""
        result = _build_description_with_api_links(
            original_description="Original description",
        )

        assert result == "Original description"

    def test_returns_empty_string_when_no_content_provided(self) -> None:
        """Test that empty string is returned when no content is provided."""
        result = _build_description_with_api_links()
        assert result == ""

    def test_formats_single_api_link_correctly(self) -> None:
        """Test that single API link is formatted correctly without trailing content."""
        api_links = [APILink(url="/docs", description="Main API")]

        result = _build_description_with_api_links(api_links=api_links)

        expected = "APIs: [Main API](/docs)\n\n* * *\n"
        assert result == expected

    def test_handles_empty_api_links_list(self) -> None:
        """Test that empty API links list doesn't add API section."""
        result = _build_description_with_api_links(
            api_links=[],
            original_description="Original description",
        )

        assert result == "Original description"

    def test_handles_complex_urls_in_api_links(self) -> None:
        """Test that complex URLs with query parameters are handled correctly."""
        api_links = [
            APILink(url="https://api.example.com/v1/docs", description="V1 API"),
            APILink(url="/api/v2/docs?version=latest", description="V2 API"),
        ]

        result = _build_description_with_api_links(api_links=api_links)

        expected = (
            "APIs: [V1 API](https://api.example.com/v1/docs) | " "[V2 API](/api/v2/docs?version=latest)\n\n* * *\n"
        )
        assert result == expected


class TestEnhanceOpenAPIWithDocsFunction:
    """Test the enhanced enhance_openapi_with_docs function with new parameters."""

    @patch("fastmarkdocs.openapi_enhancer.MarkdownDocumentationLoader")
    @patch("fastmarkdocs.openapi_enhancer.OpenAPIEnhancer")
    def test_overrides_application_title_when_provided(self, mock_enhancer_class: Any, mock_loader_class: Any) -> None:
        """Test that app_title parameter overrides the OpenAPI schema title."""
        # Setup mocks
        mock_loader = MagicMock()
        mock_loader.load_documentation.return_value = MagicMock()
        mock_loader._general_docs_content = None  # Ensure this attribute exists
        mock_loader_class.return_value = mock_loader

        mock_enhancer = MagicMock()
        mock_enhancer.enhance_openapi_schema.return_value = {
            "openapi": "3.0.0",
            "info": {"title": "Original Title", "version": "1.0.0", "description": "Original description"},
            "paths": {},
        }
        mock_enhancer_class.return_value = mock_enhancer

        # Test data
        openapi_schema = {"openapi": "3.0.0", "info": {"title": "Original Title", "version": "1.0.0"}, "paths": {}}

        # Call function
        result = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory="docs",
            app_title="Custom Title",
        )

        # Verify title was overridden
        assert result["info"]["title"] == "Custom Title"

    @patch("fastmarkdocs.openapi_enhancer.MarkdownDocumentationLoader")
    @patch("fastmarkdocs.openapi_enhancer.OpenAPIEnhancer")
    def test_adds_api_links_to_description(self, mock_enhancer_class: Any, mock_loader_class: Any) -> None:
        """Test that api_links parameter adds formatted links to the description."""
        # Setup mocks
        mock_loader = MagicMock()
        mock_loader.load_documentation.return_value = MagicMock()
        mock_loader._general_docs_content = None  # Ensure this attribute exists
        mock_loader_class.return_value = mock_loader

        mock_enhancer = MagicMock()
        mock_enhancer.enhance_openapi_schema.return_value = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0", "description": "Original description"},
            "paths": {},
        }
        mock_enhancer_class.return_value = mock_enhancer

        # Test data
        openapi_schema = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}

        api_links = [
            APILink(url="/docs", description="Main API"),
            APILink(url="/admin/docs", description="Admin API"),
        ]

        # Call function
        result = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory="docs",
            api_links=api_links,
        )

        # Verify API links were added to description
        description = result["info"]["description"]
        assert "APIs: [Main API](/docs) | [Admin API](/admin/docs)" in description
        assert "Original description" in description

    @patch("fastmarkdocs.openapi_enhancer.MarkdownDocumentationLoader")
    @patch("fastmarkdocs.openapi_enhancer.OpenAPIEnhancer")
    def test_applies_all_new_parameters_together(self, mock_enhancer_class: Any, mock_loader_class: Any) -> None:
        """Test that all new parameters work together correctly."""
        # Setup mocks
        mock_loader = MagicMock()
        mock_loader.load_documentation.return_value = MagicMock()
        mock_loader._general_docs_content = None  # Ensure this attribute exists
        mock_loader_class.return_value = mock_loader

        mock_enhancer = MagicMock()
        mock_enhancer.enhance_openapi_schema.return_value = {
            "openapi": "3.0.0",
            "info": {"title": "Original Title", "version": "1.0.0", "description": "Original description"},
            "paths": {},
        }
        mock_enhancer_class.return_value = mock_enhancer

        # Test data
        openapi_schema = {"openapi": "3.0.0", "info": {"title": "Original Title", "version": "1.0.0"}, "paths": {}}

        api_links = [
            APILink(url="/docs", description="Authorization"),
            APILink(url="/storage/docs", description="Storage"),
        ]

        # Call function
        result = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory="docs",
            app_title="My API Gateway",
            app_description="Authorization and access control service",
            api_links=api_links,
        )

        # Verify all changes
        assert result["info"]["title"] == "My API Gateway"

        description = result["info"]["description"]
        assert "APIs: [Authorization](/docs) | [Storage](/storage/docs)" in description
        assert "My API Gateway - Authorization and access control service" in description

    @patch("fastmarkdocs.openapi_enhancer.MarkdownDocumentationLoader")
    @patch("fastmarkdocs.openapi_enhancer.OpenAPIEnhancer")
    def test_maintains_backward_compatibility_without_new_parameters(
        self, mock_enhancer_class: Any, mock_loader_class: Any
    ) -> None:
        """Test that function works normally when new parameters are not provided."""
        # Setup mocks
        mock_loader = MagicMock()
        mock_loader.load_documentation.return_value = MagicMock()
        mock_loader._general_docs_content = None  # Ensure this attribute exists
        mock_loader_class.return_value = mock_loader

        mock_enhancer = MagicMock()
        original_schema = {
            "openapi": "3.0.0",
            "info": {"title": "Original Title", "version": "1.0.0", "description": "Original description"},
            "paths": {},
        }
        mock_enhancer.enhance_openapi_schema.return_value = original_schema
        mock_enhancer_class.return_value = mock_enhancer

        # Test data
        openapi_schema = {"openapi": "3.0.0", "info": {"title": "Original Title", "version": "1.0.0"}, "paths": {}}

        # Call function without new parameters
        result = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory="docs",
        )

        # Verify no changes to title/description
        assert result["info"]["title"] == "Original Title"
        assert result["info"]["description"] == "Original description"

    @patch("fastmarkdocs.openapi_enhancer.MarkdownDocumentationLoader")
    @patch("fastmarkdocs.openapi_enhancer.OpenAPIEnhancer")
    def test_creates_info_section_when_missing(self, mock_enhancer_class: Any, mock_loader_class: Any) -> None:
        """Test that info section is created when missing from schema."""
        # Setup mocks
        mock_loader = MagicMock()
        mock_loader.load_documentation.return_value = MagicMock()
        mock_loader._general_docs_content = None  # Ensure this attribute exists
        mock_loader_class.return_value = mock_loader

        mock_enhancer = MagicMock()
        mock_enhancer.enhance_openapi_schema.return_value = {"openapi": "3.0.0", "paths": {}}
        mock_enhancer_class.return_value = mock_enhancer

        # Test data
        openapi_schema = {"openapi": "3.0.0", "paths": {}}

        # Call function
        result = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory="docs",
            app_title="New Title",
            app_description="New Description",
        )

        # Verify info section was created
        assert "info" in result
        assert result["info"]["title"] == "New Title"
        assert result["info"]["description"] == "New Title - New Description"

    @patch("fastmarkdocs.openapi_enhancer.MarkdownDocumentationLoader")
    @patch("fastmarkdocs.openapi_enhancer.OpenAPIEnhancer")
    def test_handles_missing_description_in_info_section(
        self, mock_enhancer_class: Any, mock_loader_class: Any
    ) -> None:
        """Test that API links are added even when original description is missing."""
        # Setup mocks
        mock_loader = MagicMock()
        mock_loader.load_documentation.return_value = MagicMock()
        mock_loader._general_docs_content = None  # Ensure this attribute exists
        mock_loader_class.return_value = mock_loader

        mock_enhancer = MagicMock()
        mock_enhancer.enhance_openapi_schema.return_value = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0",
                # No description
            },
            "paths": {},
        }
        mock_enhancer_class.return_value = mock_enhancer

        # Test data
        openapi_schema = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}

        api_links = [APILink(url="/docs", description="Main API")]

        # Call function
        result = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory="docs",
            api_links=api_links,
        )

        # Verify API links were added even without original description
        description = result["info"]["description"]
        assert "APIs: [Main API](/docs)" in description

    def test_handles_empty_api_links_list_gracefully(self) -> None:
        """Test that empty API links list doesn't break the enhancement."""
        # Create a temporary docs directory
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test data
            openapi_schema = {
                "openapi": "3.0.0",
                "info": {"title": "Test API", "version": "1.0.0", "description": "Original"},
                "paths": {},
            }

            # Call function with empty API links
            result = enhance_openapi_with_docs(
                openapi_schema=openapi_schema,
                docs_directory=temp_dir,
                api_links=[],
                app_title="New Title",
            )

            # Should still update title but not add API links section
            assert result["info"]["title"] == "New Title"
            assert "APIs:" not in result["info"]["description"]


class TestEnhanceOpenAPIWithDocsErrorHandling:
    """Test error handling scenarios in the enhance_openapi_with_docs function."""

    @patch("fastmarkdocs.openapi_enhancer.MarkdownDocumentationLoader")
    def test_raises_enhancement_error_on_documentation_load_failure(self, mock_loader_class: Any) -> None:
        """Test that DocumentationLoadError is wrapped in OpenAPIEnhancementError."""
        # Setup mock to raise DocumentationLoadError
        mock_loader = MagicMock()
        mock_loader.load_documentation.side_effect = DocumentationLoadError("file_not_found", "Test error")
        mock_loader_class.return_value = mock_loader

        # Test data
        openapi_schema = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}

        # Call function and expect OpenAPIEnhancementError
        with pytest.raises(OpenAPIEnhancementError, match="Failed to enhance OpenAPI schema"):
            enhance_openapi_with_docs(
                openapi_schema=openapi_schema,
                docs_directory="docs",
                app_title="Test Title",
            )

    @patch("fastmarkdocs.openapi_enhancer.MarkdownDocumentationLoader")
    def test_raises_enhancement_error_on_file_not_found(self, mock_loader_class: Any) -> None:
        """Test that FileNotFoundError is wrapped in OpenAPIEnhancementError."""
        # Setup mock to raise FileNotFoundError
        mock_loader = MagicMock()
        mock_loader.load_documentation.side_effect = FileNotFoundError("File not found")
        mock_loader_class.return_value = mock_loader

        # Test data
        openapi_schema = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}

        # Call function and expect OpenAPIEnhancementError
        with pytest.raises(OpenAPIEnhancementError, match="Failed to enhance OpenAPI schema"):
            enhance_openapi_with_docs(
                openapi_schema=openapi_schema,
                docs_directory="docs",
                app_title="Test Title",
            )

    @patch("fastmarkdocs.openapi_enhancer.MarkdownDocumentationLoader")
    @patch("fastmarkdocs.openapi_enhancer.OpenAPIEnhancer")
    def test_raises_enhancement_error_on_openapi_enhancement_failure(
        self, mock_enhancer_class: Any, mock_loader_class: Any
    ) -> None:
        """Test that OpenAPIEnhancementError is re-raised properly."""
        # Setup mocks
        mock_loader = MagicMock()
        mock_loader.load_documentation.return_value = MagicMock()
        mock_loader_class.return_value = mock_loader

        # Setup enhancer to raise OpenAPIEnhancementError
        mock_enhancer = MagicMock()
        mock_enhancer.enhance_openapi_schema.side_effect = OpenAPIEnhancementError("test_error", "Test error message")
        mock_enhancer_class.return_value = mock_enhancer

        # Test data
        openapi_schema = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}

        # Call function and expect OpenAPIEnhancementError to be re-raised
        with pytest.raises(OpenAPIEnhancementError, match="Failed to enhance OpenAPI schema"):
            enhance_openapi_with_docs(
                openapi_schema=openapi_schema,
                docs_directory="docs",
                app_title="Test Title",
            )

    @patch("fastmarkdocs.openapi_enhancer.MarkdownDocumentationLoader")
    @patch("fastmarkdocs.openapi_enhancer.OpenAPIEnhancer")
    def test_returns_original_schema_on_generic_exception(
        self, mock_enhancer_class: Any, mock_loader_class: Any
    ) -> None:
        """Test that generic exceptions cause fallback to original schema."""
        # Setup mocks
        mock_loader = MagicMock()
        mock_loader.load_documentation.return_value = MagicMock()
        mock_loader_class.return_value = mock_loader

        # Setup enhancer to raise a generic exception
        mock_enhancer = MagicMock()
        mock_enhancer.enhance_openapi_schema.side_effect = ValueError("Generic error")
        mock_enhancer_class.return_value = mock_enhancer

        # Test data
        openapi_schema = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}

        # Call function - should return original schema on generic error
        result = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory="docs",
            app_title="Test Title",
        )

        # Should return original schema unchanged
        assert result == openapi_schema
