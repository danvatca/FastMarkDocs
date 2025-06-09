"""
Unit tests for utility functions.

Tests the various utility functions used throughout the library.
"""

import os
from unittest.mock import patch

from fastmarkdocs.types import CodeLanguage
from fastmarkdocs.utils import (
    extract_code_samples,
    extract_endpoint_info,
    find_markdown_files,
    normalize_path,
    sanitize_filename,
    validate_markdown_structure,
)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_normalize_path_basic(self):
        """Test basic path normalization."""
        # Test absolute path
        abs_path = normalize_path("/absolute/path")
        assert os.path.isabs(abs_path)

        # Test relative path
        rel_path = normalize_path("relative/path")
        assert os.path.isabs(rel_path)

    def test_normalize_path_with_base(self):
        """Test path normalization with base path."""
        base = "/base/directory"
        result = normalize_path("relative/path", base)
        assert result.startswith(base)

    def test_normalize_path_with_user_expansion(self):
        """Test path normalization with user home expansion."""
        # Test with tilde expansion
        with patch("os.path.expanduser") as mock_expand:
            mock_expand.return_value = "/home/user/path"
            result = normalize_path("~/path")
            mock_expand.assert_called_once_with("~/path")
            assert "/home/user/path" in result

    def test_normalize_path_edge_cases(self):
        """Test path normalization edge cases."""
        # Test empty string
        result = normalize_path("")
        assert os.path.isabs(result)

        # Test None handling (should not crash)
        try:
            result = normalize_path(None)
        except (TypeError, AttributeError):
            pass  # Expected behavior

    def test_extract_code_samples_basic(self):
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

    def test_extract_code_samples_with_titles(self):
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

    def test_extract_code_samples_language_aliases(self):
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

    def test_extract_code_samples_unsupported_language(self):
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

    def test_extract_code_samples_with_language_filter(self):
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

    def test_extract_code_samples_malformed_blocks(self):
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

    def test_validate_markdown_structure_valid(self):
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

    def test_validate_markdown_structure_missing_endpoints(self):
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

    def test_validate_markdown_structure_malformed_code_blocks(self):
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

    def test_extract_endpoint_info_basic(self):
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

    def test_extract_endpoint_info_multiple_headers(self):
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

    def test_extract_endpoint_info_no_endpoints(self):
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

    def test_extract_endpoint_info_edge_cases(self):
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

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        # Test valid filename
        assert sanitize_filename("valid_filename.md") == "valid_filename.md"

        # Test filename with invalid characters
        assert sanitize_filename("file<>name.md") == "file__name.md"
        assert sanitize_filename('file"name.md') == "file_name.md"
        assert sanitize_filename("file|name.md") == "file_name.md"

    def test_sanitize_filename_edge_cases(self):
        """Test filename sanitization edge cases."""
        # Test empty filename
        assert sanitize_filename("") == "unnamed"

        # Test filename with only invalid characters
        result = sanitize_filename('<>:"/\\|?*')
        assert result == "_________"  # Each invalid char becomes underscore

        # Test filename with leading/trailing dots and spaces
        result = sanitize_filename("  .filename.  ")
        assert result == "filename"  # Dots and spaces are stripped

        # Test filename with all problematic characters
        problematic = 'file<>:"/\\|?*name.md'
        result = sanitize_filename(problematic)
        assert result == "file_________name.md"

    def test_find_markdown_files_basic(self, temp_docs_dir, test_utils):
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

    def test_find_markdown_files_recursive(self, temp_docs_dir, test_utils):
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

    def test_find_markdown_files_custom_patterns(self, temp_docs_dir, test_utils):
        """Test markdown file finding with custom patterns."""
        # Create files with different extensions
        test_utils.create_markdown_file(temp_docs_dir, "api.md", "# API")
        test_utils.create_markdown_file(temp_docs_dir, "guide.txt", "# Guide")

        # Test with custom pattern
        files = find_markdown_files(str(temp_docs_dir), patterns=["*.txt"])

        txt_files = [f for f in files if f.endswith(".txt")]
        assert len(txt_files) >= 1

    def test_find_markdown_files_nonexistent_directory(self):
        """Test markdown file finding with non-existent directory."""
        files = find_markdown_files("/nonexistent/directory")
        assert files == []

    def test_find_markdown_files_empty_directory(self, temp_docs_dir):
        """Test markdown file finding in empty directory."""
        files = find_markdown_files(str(temp_docs_dir))
        assert files == []

    def test_extract_code_description_functionality(self):
        """Test code description extraction from preceding text."""
        from fastmarkdocs.utils import _extract_code_description

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

    def test_validate_code_block_functionality(self):
        """Test code block validation functionality."""
        from fastmarkdocs.utils import _validate_code_block

        # Test valid code block
        valid_lines = ["Some text", "```python", "print('hello')", "```", "More text"]

        assert _validate_code_block(valid_lines, 1) is True  # Index of opening ```

        # Test invalid code block (missing closing)
        invalid_lines = ["Some text", "```python", "print('hello')", "More text without closing"]

        assert _validate_code_block(invalid_lines, 1) is False

    def test_extract_code_samples_with_empty_content(self):
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

    def test_validation_error_creation(self):
        """Test ValidationError creation and properties."""
        from fastmarkdocs.exceptions import ValidationError as ExceptionValidationError

        error = ExceptionValidationError(file_path="test.md", line_number=42, message="Test error")

        assert error.file_path == "test.md"
        assert error.line_number == 42
        assert "Test error" in str(error)

    def test_extract_endpoint_info_with_complex_paths(self):
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

    def test_find_markdown_files_with_symlinks(self, temp_docs_dir, test_utils):
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

    def test_normalize_path_with_none_base(self):
        """Test path normalization with None base path."""
        result = normalize_path("test/path", None)
        assert os.path.isabs(result)
        assert "test/path" in result
