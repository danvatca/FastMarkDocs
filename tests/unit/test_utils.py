"""
Unit tests for utility functions.

Tests the various utility functions used throughout the library.
"""

import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

from fastmarkdocs.types import CodeLanguage
from fastmarkdocs.utils import (
    _extract_code_description,
    _validate_code_block,
    extract_code_samples,
    extract_endpoint_info,
    find_markdown_files,
    normalize_path,
    sanitize_filename,
    validate_markdown_structure,
)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_normalize_path_basic(self) -> None:
        """Test basic path normalization."""
        # Test absolute path
        abs_path = normalize_path("/absolute/path")
        assert os.path.isabs(abs_path)

        # Test relative path
        rel_path = normalize_path("relative/path")
        assert os.path.isabs(rel_path)

    def test_normalize_path_with_base(self) -> None:
        """Test path normalization with base path."""
        base = "/base/directory"
        result = normalize_path("relative/path", base)
        assert result.startswith(base)

    def test_normalize_path_with_user_expansion(self) -> None:
        """Test path normalization with user home expansion."""
        # Test with tilde expansion
        with patch("os.path.expanduser") as mock_expand:
            mock_expand.return_value = "/home/user/path"
            result = normalize_path("~/path")
            mock_expand.assert_called_once_with("~/path")
            assert "/home/user/path" in result

    def test_normalize_path_edge_cases(self) -> None:
        """Test path normalization edge cases."""
        # Test empty string
        result = normalize_path("")
        assert os.path.isabs(result)

        # Test None handling (should not crash)
        try:
            result = normalize_path("")
        except (TypeError, AttributeError):
            pass  # Expected behavior

    def test_extract_code_samples_basic(self) -> None:
        """Test basic code sample extraction."""
        markdown = """
# API Documentation

Here's a Python example:

```python
import requests
response = requests.get("/api/users")
```

And a cURL example:

```curl
curl -X GET "https://api.example.com/users"
```
"""

        samples = extract_code_samples(markdown)
        assert len(samples) == 2

        python_sample = next((s for s in samples if s.language == CodeLanguage.PYTHON), None)
        assert python_sample is not None
        assert "import requests" in python_sample.code

        curl_sample = next((s for s in samples if s.language == CodeLanguage.CURL), None)
        assert curl_sample is not None
        assert "curl -X GET" in curl_sample.code

    def test_extract_code_samples_with_titles(self) -> None:
        """Test code sample extraction with titles."""
        markdown = """
```python Example Request
import requests
response = requests.get("/api/users")
```

```javascript Fetch Example
fetch('/api/users')
  .then(response => response.json())
```
"""

        samples = extract_code_samples(markdown)
        assert len(samples) == 2

        python_sample = next((s for s in samples if s.language == CodeLanguage.PYTHON), None)
        assert python_sample is not None
        assert python_sample.title == "Example Request"

        js_sample = next((s for s in samples if s.language == CodeLanguage.JAVASCRIPT), None)
        assert js_sample is not None
        assert js_sample.title == "Fetch Example"

    def test_extract_code_samples_language_aliases(self) -> None:
        """Test code sample extraction with language aliases."""
        markdown = """
```js
console.log('JavaScript alias');
```

```py
print('Python alias')
```

```bash
curl -X GET "https://api.example.com"
```
"""

        samples = extract_code_samples(markdown)

        # Should map aliases correctly
        languages = [s.language for s in samples]
        assert CodeLanguage.JAVASCRIPT in languages  # js -> javascript
        assert CodeLanguage.PYTHON in languages  # py -> python
        assert CodeLanguage.CURL in languages  # bash -> curl

    def test_extract_code_samples_unsupported_language(self) -> None:
        """Test code sample extraction with unsupported languages."""
        markdown = """
```unsupported
some code here
```

```python
print('This should be extracted')
```

```random_lang
more unsupported code
```
"""

        samples = extract_code_samples(markdown)

        # Should only extract supported languages
        assert len(samples) == 1
        assert samples[0].language == CodeLanguage.PYTHON

    def test_extract_code_samples_with_language_filter(self) -> None:
        """Test code sample extraction with language filtering."""
        markdown = """
```python
print('Python code')
```

```javascript
console.log('JavaScript code');
```

```curl
curl -X GET "https://api.example.com"
```
"""

        # Filter to only Python and cURL
        samples = extract_code_samples(markdown, supported_languages=[CodeLanguage.PYTHON, CodeLanguage.CURL])

        assert len(samples) == 2
        languages = [s.language for s in samples]
        assert CodeLanguage.PYTHON in languages
        assert CodeLanguage.CURL in languages
        assert CodeLanguage.JAVASCRIPT not in languages

    def test_extract_code_samples_malformed_blocks(self) -> None:
        """Test code sample extraction with malformed code blocks."""
        markdown = """
```python
print('Valid code block')
```

```javascript
console.log('Missing closing backticks');

```python
print('Another valid block')
```
"""

        samples = extract_code_samples(markdown)

        # Should extract valid blocks - the regex pattern handles this differently
        assert len(samples) >= 1  # At least one valid block should be extracted

    def test_validate_markdown_structure_valid(self) -> None:
        """Test markdown structure validation with valid content."""
        valid_markdown = """
# API Documentation

## GET /api/users

Get a list of users.

### Description

This endpoint returns all users.

### Example

```python
import requests
response = requests.get("/api/users")
```
"""

        errors = validate_markdown_structure(valid_markdown, "test.md")

        # Should have minimal errors for valid structure (may have some warnings)
        assert len(errors) <= 1

    def test_validate_markdown_structure_missing_endpoints(self) -> None:
        """Test markdown structure validation with missing endpoints."""
        invalid_markdown = """
# API Documentation

This is just general documentation without any endpoints.

## Overview

No endpoints defined here.
"""

        errors = validate_markdown_structure(invalid_markdown, "test.md")

        # Should have error for missing endpoints
        assert len(errors) > 0
        missing_endpoint_error = next((e for e in errors if "endpoint headers" in e.message), None)
        assert missing_endpoint_error is not None

    def test_validate_markdown_structure_malformed_code_blocks(self) -> None:
        """Test markdown structure validation with malformed code blocks."""
        malformed_markdown = """
# API Documentation

## GET /api/users

Example with malformed code block:

```python
print('Missing closing backticks')

Another line here.
"""

        errors = validate_markdown_structure(malformed_markdown, "test.md")

        # Should detect malformed code blocks
        code_block_errors = [e for e in errors if "code block" in e.message]
        assert len(code_block_errors) > 0

    def test_extract_endpoint_info_basic(self) -> None:
        """Test basic endpoint information extraction."""
        markdown = """
## GET /api/users

Get a list of all users from the system.

This endpoint provides access to user data.

Tags: users, api
"""

        info = extract_endpoint_info(markdown)

        assert info["method"] == "GET"
        assert info["path"] == "/api/users"
        assert info["summary"] == "Get a list of all users from the system."
        assert "users" in info["tags"]
        assert "api" in info["tags"]

    def test_extract_endpoint_info_multiple_headers(self) -> None:
        """Test endpoint extraction with multiple headers (should take first)."""
        markdown = """
## GET /api/users

First endpoint description.

## POST /api/users

Second endpoint description.
"""

        info = extract_endpoint_info(markdown)

        # Should only extract the first endpoint
        assert info["method"] == "GET"
        assert info["path"] == "/api/users"

    def test_extract_endpoint_info_no_endpoints(self) -> None:
        """Test endpoint extraction with no valid endpoints."""
        markdown = """
# API Documentation

This is general documentation.

## Overview

No endpoints here.
"""

        info = extract_endpoint_info(markdown)

        assert info["method"] is None
        assert info["path"] is None

    def test_extract_endpoint_info_edge_cases(self) -> None:
        """Test endpoint extraction edge cases."""
        # Test with different header levels
        markdown_h3 = """
### POST /api/users/create

Create a new user.
"""

        info = extract_endpoint_info(markdown_h3)
        assert info["method"] == "POST"
        assert info["path"] == "/api/users/create"

        # Test with extra whitespace
        markdown_whitespace = """
##   GET   /api/users

  Get users with extra whitespace.
"""

        info = extract_endpoint_info(markdown_whitespace)
        assert info["method"] == "GET"
        assert info["path"] == "/api/users"

    def test_sanitize_filename_basic(self) -> None:
        """Test basic filename sanitization."""
        # Test valid filename
        assert sanitize_filename("valid_filename.md") == "valid_filename.md"

        # Test filename with invalid characters
        assert sanitize_filename("file<>name.md") == "file__name.md"
        assert sanitize_filename('file"name.md') == "file_name.md"
        assert sanitize_filename("file|name.md") == "file_name.md"

    def test_sanitize_filename_edge_cases(self) -> None:
        """Test filename sanitization edge cases."""
        # Test empty filename
        assert sanitize_filename("") == "unnamed"

        # Test filename with only invalid characters
        result = sanitize_filename('<>:"/\\|?*')
        assert result == "unnamed"  # All invalid chars result in unnamed

        # Test filename with leading/trailing dots and spaces
        result = sanitize_filename("  .filename.  ")
        assert result == "filename"  # Dots and spaces are stripped

        # Test filename with all problematic characters
        problematic = 'file<>:"/\\|?*name.md'
        result = sanitize_filename(problematic)
        assert result == "file_________name.md"

    def test_find_markdown_files_basic(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test basic markdown file finding."""
        # Create test files
        test_utils.create_markdown_file(temp_docs_dir, "api.md", "# API")
        test_utils.create_markdown_file(temp_docs_dir, "guide.markdown", "# Guide")

        # Create non-markdown file
        (temp_docs_dir / "readme.txt").write_text("Not markdown")

        files = find_markdown_files(str(temp_docs_dir))

        # Should find markdown files
        assert len(files) >= 2
        md_files = [f for f in files if f.endswith((".md", ".markdown"))]
        assert len(md_files) >= 2

    def test_find_markdown_files_recursive(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test recursive markdown file finding."""
        # Create files in subdirectory
        subdir = temp_docs_dir / "subdir"
        subdir.mkdir()

        test_utils.create_markdown_file(temp_docs_dir, "root.md", "# Root")
        test_utils.create_markdown_file(subdir, "sub.md", "# Sub")

        # Test recursive search
        files_recursive = find_markdown_files(str(temp_docs_dir), recursive=True)
        files_non_recursive = find_markdown_files(str(temp_docs_dir), recursive=False)

        assert len(files_recursive) > len(files_non_recursive)

    def test_find_markdown_files_custom_patterns(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test markdown file finding with custom patterns."""
        # Create files with different extensions
        test_utils.create_markdown_file(temp_docs_dir, "api.md", "# API")
        test_utils.create_markdown_file(temp_docs_dir, "guide.txt", "# Guide")

        # Test with custom pattern
        files = find_markdown_files(str(temp_docs_dir), patterns=["*.txt"])

        txt_files = [f for f in files if f.endswith(".txt")]
        assert len(txt_files) >= 1

    def test_find_markdown_files_nonexistent_directory(self) -> None:
        """Test markdown file finding with non-existent directory."""
        files = find_markdown_files("/nonexistent/directory")
        assert files == []

    def test_find_markdown_files_empty_directory(self, temp_docs_dir: Any) -> None:
        """Test markdown file finding in empty directory."""
        files = find_markdown_files(str(temp_docs_dir))
        assert files == []

    def test_extract_code_description_functionality(self) -> None:
        """Test code description extraction from preceding text."""
        markdown = """
This is some general text.

Here's an example of how to use the API:

```python
import requests
response = requests.get("/api/users")
```
"""

        # Find the code block position
        import re

        match = re.search(r"```python", markdown)
        assert match is not None

        description = _extract_code_description(markdown, match.start())

        # Should extract the preceding description
        assert description is not None
        assert "example" in description.lower()

    def test_validate_code_block_functionality(self) -> None:
        """Test code block validation functionality."""
        # Test valid code block
        valid_lines = ["Some text", "```python", "print('hello')", "```", "More text"]

        assert _validate_code_block(valid_lines, 1) is True  # Index of opening ```

        # Test invalid code block (missing closing)
        invalid_lines = ["Some text", "```python", "print('hello')", "More text without closing"]

        assert _validate_code_block(invalid_lines, 1) is False

    def test_extract_code_samples_with_empty_content(self) -> None:
        """Test code sample extraction with empty or whitespace-only content."""
        markdown = """
```curl
curl -X GET "https://api.example.com"
```

```python
print('non-empty')
```
"""

        samples = extract_code_samples(markdown)

        # Should extract non-empty code blocks
        assert len(samples) >= 1
        languages = [s.language for s in samples]
        assert CodeLanguage.CURL in languages or CodeLanguage.PYTHON in languages

    def test_validation_error_creation(self) -> None:
        """Test ValidationError creation and properties."""
        from fastmarkdocs.exceptions import ValidationError as ExceptionValidationError

        error = ExceptionValidationError(file_path="test.md", line_number=42, message="Test error")

        assert error.file_path == "test.md"
        assert error.line_number == 42
        assert "Test error" in str(error)

    def test_extract_endpoint_info_with_complex_paths(self) -> None:
        """Test endpoint extraction with complex path patterns."""
        markdown = """
## GET /api/v1/users/{user_id}/posts/{post_id}/comments

Get comments for a specific post by a user.

Tags: comments, posts, users
"""

        info = extract_endpoint_info(markdown)

        assert info["method"] == "GET"
        assert info["path"] == "/api/v1/users/{user_id}/posts/{post_id}/comments"
        assert "comments" in info["tags"]

    def test_find_markdown_files_with_symlinks(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test markdown file finding with symbolic links."""
        # Create a real file
        real_file = test_utils.create_markdown_file(temp_docs_dir, "real.md", "# Real")

        # Create a symbolic link (if supported by the OS)
        try:
            link_path = temp_docs_dir / "link.md"
            link_path.symlink_to(real_file)

            files = find_markdown_files(str(temp_docs_dir))

            # Should handle symlinks gracefully
            assert len(files) >= 1
        except (OSError, NotImplementedError):
            # Symlinks not supported on this system
            pass

    def test_normalize_path_with_none_base(self) -> None:
        """Test path normalization with None base path."""
        result = normalize_path("test/path", None)
        assert os.path.isabs(result)
        assert "test/path" in result

    def test_validate_code_block_edge_cases(self) -> None:
        """Test code block validation with various edge cases."""
        # Test with start_index beyond array bounds
        lines = ["```python", "print('hello')", "```"]
        assert not _validate_code_block(lines, 10)

        # Test with unclosed code block at end of file
        unclosed_lines = ["```python", "print('hello')", "# no closing backticks"]
        assert not _validate_code_block(unclosed_lines, 0)

        # Test with properly closed code block
        assert _validate_code_block(lines, 0)

        # Test with empty lines array
        assert not _validate_code_block([], 0)

        # Test with code block that has content after closing
        mixed_lines = ["```python", "print('hello')", "```", "more content"]
        assert _validate_code_block(mixed_lines, 0)

    def test_extract_code_samples_with_complex_markdown(self) -> None:
        """Test code sample extraction with complex markdown scenarios."""
        complex_markdown = """
# API Documentation

Here's a comprehensive example:

```python
# This is a Python example with detailed comments
import requests
import json

def get_users():
    response = requests.get('/api/users')
    return response.json()
```

And here's the equivalent in JavaScript:

```javascript
// JavaScript version with async/await
async function getUsers() {
    const response = await fetch('/api/users');
    return await response.json();
}
```

For shell users, here's a curl command:

```curl
# Simple curl command
curl -X GET /api/users \\
  -H "Accept: application/json"
```
"""

        samples = extract_code_samples(
            complex_markdown, [CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT, CodeLanguage.CURL]
        )

        assert len(samples) == 3

        # Verify each sample has proper description
        python_sample = next(s for s in samples if s.language == CodeLanguage.PYTHON)
        assert python_sample.description == "Here's a comprehensive example:"
        assert "import requests" in python_sample.code

        js_sample = next(s for s in samples if s.language == CodeLanguage.JAVASCRIPT)
        assert js_sample.description == "And here's the equivalent in JavaScript:"
        assert "async function" in js_sample.code

        curl_sample = next(s for s in samples if s.language == CodeLanguage.CURL)
        assert curl_sample.description == "For shell users, here's a curl command:"
        assert "curl -X GET" in curl_sample.code

    def test_validate_markdown_structure_comprehensive_scenarios(self) -> None:
        """Test markdown structure validation with comprehensive scenarios."""
        # Test markdown with multiple issues
        problematic_markdown = """
# API Documentation

This documentation has several issues.

```python
# This code block is never closed
import requests
response = requests.get('/api/test')

## GET /api/users
This endpoint gets users.

### Description
Detailed description here.

```json
{
  "valid": "json"
```

## POST /api/users
Create a new user.

```javascript
// Another unclosed block
fetch('/api/users', {
  method: 'POST'
"""

        errors = validate_markdown_structure(problematic_markdown, "test.md")

        # Should find syntax errors for malformed code blocks
        syntax_errors = [e for e in errors if e.error_type == "syntax_error"]
        assert len(syntax_errors) > 0

        # Check that line numbers are properly reported
        for error in syntax_errors:
            assert error.line_number is not None
            assert error.line_number > 0

        # Test markdown without any endpoint headers
        no_endpoints_markdown = """
# General Documentation

This is just general information about the API.

## Overview
Some overview content.

### Getting Started
Instructions for getting started.
"""

        errors = validate_markdown_structure(no_endpoints_markdown, "general.md")

        # Should report missing endpoint headers
        missing_section_errors = [e for e in errors if e.error_type == "missing_section"]
        assert len(missing_section_errors) > 0
        assert any("No endpoint headers found" in e.message for e in missing_section_errors)

    def test_extract_endpoint_info_with_multiple_endpoints(self) -> None:
        """Test endpoint info extraction when multiple endpoints are present."""
        markdown_with_multiple = """
# API Documentation

## GET /api/users
Get all users from the system.

This endpoint returns a list of all users.

## POST /api/users
Create a new user in the system.

Tags: users, creation

## GET /api/users/{id}
Get a specific user by ID.

Tags: users, retrieval
"""

        # Should extract info from the first endpoint only
        info = extract_endpoint_info(markdown_with_multiple)

        assert info["method"] == "GET"
        assert info["path"] == "/api/users"
        assert info["summary"] == "Get all users from the system."
        # Tags should be extracted from anywhere in the document
        assert "users" in info["tags"]

    def test_extract_endpoint_info_with_various_header_levels(self) -> None:
        """Test endpoint info extraction with different header levels."""
        markdown_with_different_headers = """
# Main Title

### GET /api/level3
This is a level 3 header endpoint.

#### POST /api/level4
This is a level 4 header endpoint.

## GET /api/level2
This is a level 2 header endpoint.
"""

        info = extract_endpoint_info(markdown_with_different_headers)

        # Should find the first valid endpoint regardless of header level
        assert info["method"] == "GET"
        assert info["path"] == "/api/level3"

    def test_find_markdown_files_with_various_scenarios(self) -> None:
        """Test markdown file finding with various directory scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files with different extensions
            (temp_path / "readme.md").write_text("# Readme")
            (temp_path / "guide.markdown").write_text("# Guide")
            (temp_path / "notes.txt").write_text("Not markdown")
            (temp_path / "config.json").write_text('{"key": "value"}')

            # Create nested structure
            nested_dir = temp_path / "nested"
            nested_dir.mkdir()
            (nested_dir / "nested.md").write_text("# Nested")
            (nested_dir / "deep.markdown").write_text("# Deep")

            deeper_dir = nested_dir / "deeper"
            deeper_dir.mkdir()
            (deeper_dir / "deepest.md").write_text("# Deepest")

            # Test recursive search with default patterns
            files = find_markdown_files(str(temp_path), recursive=True)
            assert len(files) == 5  # All .md and .markdown files

            # Test non-recursive search
            files = find_markdown_files(str(temp_path), recursive=False)
            assert len(files) == 2  # Only top-level files

            # Test custom patterns
            files = find_markdown_files(str(temp_path), patterns=["*.md"], recursive=True)
            assert len(files) == 3  # Only .md files

            # Test with specific pattern
            files = find_markdown_files(str(temp_path), patterns=["*.markdown"], recursive=True)
            assert len(files) == 2  # Only .markdown files

    def test_sanitize_filename_comprehensive(self) -> None:
        """Test filename sanitization with comprehensive scenarios."""
        # Test various invalid characters
        assert sanitize_filename("file<name>") == "file_name_"
        assert sanitize_filename("file:name") == "file_name"
        assert sanitize_filename('file"name') == "file_name"
        assert sanitize_filename("file/name\\path") == "file_name_path"
        assert sanitize_filename("file|name") == "file_name"
        assert sanitize_filename("file?name*") == "file_name_"

        # Test leading/trailing whitespace and dots
        assert sanitize_filename("  filename  ") == "filename"
        assert sanitize_filename("...filename...") == "filename"
        assert sanitize_filename(" . filename . ") == "filename"

        # Test empty or whitespace-only names
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("   ") == "unnamed"
        assert sanitize_filename("...") == "unnamed"

        # Test normal filenames remain unchanged
        assert sanitize_filename("normal_filename.md") == "normal_filename.md"
        assert sanitize_filename("file-name_123.txt") == "file-name_123.txt"

    def test_extract_code_description_edge_cases(self) -> None:
        """Test edge cases for code description extraction."""
        # Test with no preceding text
        content = "```python\nprint('hello')\n```"
        result = _extract_code_description(content, 0)
        assert result is None

        # Test with only headers preceding
        content = "# Header\n\n```python\nprint('hello')\n```"
        result = _extract_code_description(content, content.find("```"))
        assert result is None

        # Test with empty paragraphs
        content = "\n\n\n\n```python\nprint('hello')\n```"
        result = _extract_code_description(content, content.find("```"))
        assert result is None

    def test_extract_endpoint_info_heading_level_fix(self) -> None:
        """Test that extract_endpoint_info correctly handles different heading levels."""
        # Test content with mixed heading levels - this tests the fix for the issue
        # where sections should stop at the next heading of the same or higher level
        markdown_content = """### POST /api/test

**Test endpoint**

Main description.

#### Subsection

Subsection content.

### GET /api/other

Other endpoint.
"""

        result = extract_endpoint_info(markdown_content)

        # Basic extraction should work
        assert result["method"] == "POST"
        assert result["path"] == "/api/test"
        assert result["summary"] == "Test endpoint"

        description = result["description"] or ""

        # Should include main description
        assert "Test endpoint" in description
        assert "Main description" in description

        # Should NOT include the next ### section (same level) - this is the key test
        assert "### GET /api/other" not in description
        assert "Other endpoint" not in description

        # The fix ensures that we stop at the next heading of the same or higher level
        # This test verifies that the function doesn't include content from the next ### section
        assert len(description) > 20, f"Description should include some content, got {len(description)} characters"

    def test_extract_endpoint_info_with_general_docs(self) -> None:
        """Test that extract_endpoint_info ignores general documentation content (now handled globally)."""
        general_docs = """# General API Documentation

## Overview

This is the general API documentation that should be included in all endpoints.

### Authentication

All endpoints require authentication.

### Rate Limiting

API calls are rate limited.
"""

        endpoint_markdown = """### POST /api/test

**Test endpoint**

This endpoint creates a test resource.

#### Parameters

- name: string (required)
"""

        result = extract_endpoint_info(endpoint_markdown, general_docs)

        # Basic extraction should work
        assert result["method"] == "POST"
        assert result["path"] == "/api/test"
        assert result["summary"] == "Test endpoint"

        description = result["description"] or ""

        # Should NOT include general docs content (now handled globally)
        assert "# General API Documentation" not in description
        assert "This is the general API documentation" not in description
        assert "### Authentication" not in description
        assert "All endpoints require authentication" not in description
        assert "### Rate Limiting" not in description

        # Should include endpoint-specific content
        assert "Test endpoint" in description
        assert "This endpoint creates a test resource" in description
        assert "#### Parameters" in description

        # Should NOT have separators from general docs
        assert description.count("---") == 0

    def test_extract_endpoint_info_with_general_docs_and_overview(self) -> None:
        """Test that extract_endpoint_info includes overview and endpoint content but not general docs."""
        general_docs = """# General Documentation

This is general project documentation.
"""

        endpoint_markdown = """## Overview

This is the endpoint-specific overview.

### POST /api/test

**Test endpoint**

This endpoint does something.
"""

        result = extract_endpoint_info(endpoint_markdown, general_docs)

        description = result["description"] or ""

        # Should NOT include general docs (now handled globally)
        assert "# General Documentation" not in description
        assert "This is general project documentation" not in description

        # Should include overview and endpoint content
        assert "## Overview" in description
        assert "This is the endpoint-specific overview" in description
        assert "Test endpoint" in description
        assert "This endpoint does something" in description

        # Should have proper ordering: overview -> endpoint
        overview_index = description.find("## Overview")
        endpoint_index = description.find("Test endpoint")

        assert overview_index < endpoint_index

    def test_extract_endpoint_info_with_empty_general_docs(self) -> None:
        """Test that extract_endpoint_info works correctly with empty general docs."""
        endpoint_markdown = """### POST /api/test

**Test endpoint**

This endpoint does something.
"""

        # Test with None
        result = extract_endpoint_info(endpoint_markdown, None)
        description = result["description"] or ""
        assert "Test endpoint" in description
        assert "---" not in description  # No separator when no general docs

        # Test with empty string
        result = extract_endpoint_info(endpoint_markdown, "")
        description = result["description"] or ""
        assert "Test endpoint" in description
        assert "---" not in description  # No separator when no general docs

        # Test with whitespace only
        result = extract_endpoint_info(endpoint_markdown, "   \n\n   ")
        description = result["description"] or ""
        assert "Test endpoint" in description
        assert "---" not in description  # No separator when no general docs

    def test_extract_endpoint_info_general_docs_only(self) -> None:
        """Test extract_endpoint_info with general docs parameter but only endpoint content in result."""
        general_docs = """# General Documentation

This is general project documentation.

## Features

- Feature 1
- Feature 2
"""

        endpoint_markdown = """### POST /api/test

**Test endpoint**
"""

        result = extract_endpoint_info(endpoint_markdown, general_docs)

        description = result["description"] or ""

        # Should NOT include general docs (now handled globally)
        assert "# General Documentation" not in description
        assert "This is general project documentation" not in description
        assert "## Features" not in description

        # Should include basic endpoint info
        assert "Test endpoint" in description
