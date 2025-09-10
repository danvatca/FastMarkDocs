"""Tests for the __init__ module."""

import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import fastmarkdocs


class TestInitModule:
    """Test the __init__ module functionality."""

    def test_version_attribute_exists(self):
        """Test that __version__ attribute exists."""
        assert hasattr(fastmarkdocs, "__version__")
        assert isinstance(fastmarkdocs.__version__, str)

    def test_author_attributes(self):
        """Test that author attributes exist."""
        assert hasattr(fastmarkdocs, "__author__")
        assert hasattr(fastmarkdocs, "__email__")
        assert hasattr(fastmarkdocs, "__license__")
        assert fastmarkdocs.__author__ == "Dan Vatca"
        assert fastmarkdocs.__email__ == "dan.vatca@gmail.com"
        assert fastmarkdocs.__license__ == "MIT"

    def test_all_exports(self):
        """Test that all expected exports are available."""
        expected_exports = [
            "__version__", "__author__", "__email__", "__license__",
            "MarkdownDocumentationLoader", "OpenAPIEnhancer", "CodeSampleGenerator",
            "enhance_openapi_with_docs",
            "FastAPIMarkdownDocsError", "DocumentationLoadError",
            "CodeSampleGenerationError", "OpenAPIEnhancementError",
            "normalize_path", "extract_code_samples", "validate_markdown_structure",
            "DocumentationData", "CodeSample", "EndpointDocumentation",
            "OpenAPIEnhancementConfig", "MarkdownDocumentationConfig",
            "CodeLanguage", "HTTPMethod",
        ]

        for export in expected_exports:
            assert hasattr(fastmarkdocs, export), f"Missing export: {export}"

    def test_get_version_from_pyproject_success(self):
        """Test successful version extraction from pyproject.toml."""
        from fastmarkdocs import _get_version_from_pyproject

        pyproject_content = '''
[tool.poetry]
name = "fastmarkdocs"
version = "1.2.3"
description = "Test"
'''

        with tempfile.TemporaryDirectory() as temp_dir:
            pyproject_path = Path(temp_dir) / "pyproject.toml"
            pyproject_path.write_text(pyproject_content)

            # Mock __file__ to point to our temp directory
            with patch('fastmarkdocs.os.path.dirname') as mock_dirname:
                mock_dirname.return_value = temp_dir
                with patch('fastmarkdocs.os.path.exists') as mock_exists:
                    def exists_side_effect(path):
                        return str(pyproject_path) in path
                    mock_exists.side_effect = exists_side_effect

                    with patch('fastmarkdocs.open', mock_open(read_data=pyproject_content)):
                        version = _get_version_from_pyproject()
                        assert version == "1.2.3"

    def test_get_version_from_pyproject_file_not_found(self):
        """Test version extraction when pyproject.toml is not found."""
        from fastmarkdocs import _get_version_from_pyproject

        with patch('fastmarkdocs.os.path.exists', return_value=False):
            with patch('fastmarkdocs.open', side_effect=OSError("File not found")):
                version = _get_version_from_pyproject()
                assert version == "unknown"

    def test_get_version_from_pyproject_unicode_error(self):
        """Test version extraction with unicode decode error."""
        from fastmarkdocs import _get_version_from_pyproject

        with patch('fastmarkdocs.os.path.exists', return_value=True):
            with patch('fastmarkdocs.open', side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "error")):
                version = _get_version_from_pyproject()
                assert version == "unknown"

    def test_get_version_from_pyproject_no_version_line(self):
        """Test version extraction when no version line is found."""
        from fastmarkdocs import _get_version_from_pyproject

        pyproject_content = '''
[tool.poetry]
name = "fastmarkdocs"
description = "Test without version"
'''

        with patch('fastmarkdocs.os.path.exists', return_value=True):
            with patch('fastmarkdocs.open', mock_open(read_data=pyproject_content)):
                version = _get_version_from_pyproject()
                assert version == "unknown"

    def test_version_detection_fallback_chain(self):
        """Test the version detection fallback chain."""
        # This test covers the import fallback logic in __init__.py
        from fastmarkdocs import _get_version_from_pyproject

        # Test that the fallback function exists and is callable
        assert callable(_get_version_from_pyproject)

        # Test that it returns a string
        version = _get_version_from_pyproject()
        assert isinstance(version, str)
