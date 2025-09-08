"""
Unit tests for the MarkdownDocumentationLoader class.

Tests the markdown parsing, documentation extraction, and caching functionality.
"""

import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from fastmarkdocs.documentation_loader import MarkdownDocumentationLoader
from fastmarkdocs.exceptions import DocumentationLoadError
from fastmarkdocs.types import CodeLanguage, HTTPMethod
from fastmarkdocs.utils import extract_endpoint_info


class TestMarkdownDocumentationLoader:
    """Test the MarkdownDocumentationLoader class."""

    def test_initialization_default_config(self) -> None:
        """Test loader initialization with default configuration."""
        loader = MarkdownDocumentationLoader()

        assert loader.docs_directory == Path("docs")
        assert loader.recursive is True
        assert loader.cache_enabled is True
        assert CodeLanguage.CURL in loader.supported_languages
        assert CodeLanguage.PYTHON in loader.supported_languages

    def test_initialization_custom_config(self, documentation_loader_config: Any) -> None:
        """Test loader initialization with custom configuration."""
        loader = MarkdownDocumentationLoader(**documentation_loader_config)

        assert loader.docs_directory == Path("test_docs")
        assert loader.recursive is True
        assert loader.cache_enabled is False
        assert len(loader.supported_languages) == 3

    def test_initialization_invalid_directory(self) -> None:
        """Test loader initialization with invalid directory."""
        with pytest.raises(DocumentationLoadError):
            MarkdownDocumentationLoader(docs_directory="/nonexistent/directory")

    def test_load_documentation_success(
        self, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any
    ) -> None:
        """Test successful documentation loading."""
        # Create test markdown file
        test_utils.create_markdown_file(temp_docs_dir, "api.md", sample_markdown_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)

        documentation = loader.load_documentation()

        assert documentation is not None
        assert len(documentation.endpoints) > 0

        # Check that endpoints were parsed correctly
        get_users_endpoint = next(
            (ep for ep in documentation.endpoints if ep.path == "/api/users" and ep.method == HTTPMethod.GET), None
        )

        assert get_users_endpoint is not None
        assert "users" in get_users_endpoint.summary.lower()

    def test_load_documentation_empty_directory(self, temp_docs_dir: Any) -> None:
        """Test loading documentation from empty directory."""
        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)

        documentation = loader.load_documentation()

        assert documentation is not None
        assert len(documentation.endpoints) == 0

    def test_load_documentation_with_caching(
        self, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any
    ) -> None:
        """Test documentation loading with caching enabled."""
        test_utils.create_markdown_file(temp_docs_dir, "api.md", sample_markdown_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=True)

        # First load
        documentation1 = loader.load_documentation()

        # Second load should use cache
        documentation2 = loader.load_documentation()

        # Should be the same object reference due to caching
        assert documentation1 is documentation2

    def test_clear_cache(self, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any) -> None:
        """Test cache clearing functionality."""
        test_utils.create_markdown_file(temp_docs_dir, "api.md", sample_markdown_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=True)

        # Load documentation to populate cache
        documentation1 = loader.load_documentation()

        # Clear cache
        loader.clear_cache()

        # Load again - should be different object
        documentation2 = loader.load_documentation()

        assert documentation1 is not documentation2

    def test_parse_markdown_file_success(
        self, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any
    ) -> None:
        """Test parsing a single markdown file."""
        file_path = test_utils.create_markdown_file(temp_docs_dir, "test.md", sample_markdown_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir))
        endpoints = loader._parse_markdown_file(file_path)

        assert len(endpoints) > 0

        # Check specific endpoint
        get_users = next((ep for ep in endpoints if ep.path == "/api/users" and ep.method == HTTPMethod.GET), None)

        assert get_users is not None
        assert "users" in get_users.summary.lower()

    def test_parse_markdown_file_malformed(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test parsing malformed markdown file."""
        malformed_content = """
# Malformed Documentation

## GET /api/broken

This endpoint has malformed documentation.

### Code Examples

```python
# Missing closing backticks
import requests
response = requests.get("/api/broken")

## POST /api/another

Another endpoint without proper structure.
"""

        file_path = test_utils.create_markdown_file(temp_docs_dir, "malformed.md", malformed_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir))

        # Should handle malformed content gracefully
        endpoints = loader._parse_markdown_file(file_path)

        # Should still extract some endpoints despite malformed content
        assert isinstance(endpoints, list)

    def test_parse_markdown_file_nonexistent(self, temp_docs_dir: Any) -> None:
        """Test parsing non-existent markdown file."""
        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir))

        with pytest.raises(DocumentationLoadError):
            loader._parse_markdown_file(Path(temp_docs_dir) / "nonexistent.md")

    def test_extract_endpoints_from_content(self, sample_markdown_content: Any) -> None:
        """Test endpoint extraction from markdown content."""
        loader = MarkdownDocumentationLoader()
        endpoints = loader._extract_endpoints_from_content(sample_markdown_content)

        assert len(endpoints) >= 3  # GET, POST, GET with ID

        # Check endpoint paths and methods
        paths_and_methods = [(ep.path, ep.method) for ep in endpoints]

        assert ("/api/users", HTTPMethod.GET) in paths_and_methods
        assert ("/api/users", HTTPMethod.POST) in paths_and_methods
        assert ("/api/users/{user_id}", HTTPMethod.GET) in paths_and_methods

    def test_extract_code_samples(self, sample_markdown_content: Any) -> None:
        """Test code sample extraction from markdown."""
        loader = MarkdownDocumentationLoader()
        endpoints = loader._extract_endpoints_from_content(sample_markdown_content)

        # Find endpoint with code samples
        get_users = next((ep for ep in endpoints if ep.path == "/api/users" and ep.method == HTTPMethod.GET), None)

        assert get_users is not None
        assert len(get_users.code_samples) > 0

        # Check for specific languages
        languages = [sample.language for sample in get_users.code_samples]
        assert CodeLanguage.PYTHON in languages
        assert CodeLanguage.CURL in languages

    def test_extract_response_examples(self, sample_markdown_content: Any) -> None:
        """Test response example extraction from markdown."""
        loader = MarkdownDocumentationLoader()
        endpoints = loader._extract_endpoints_from_content(sample_markdown_content)

        # Find endpoint with response examples
        get_users = next((ep for ep in endpoints if ep.path == "/api/users" and ep.method == HTTPMethod.GET), None)

        assert get_users is not None
        assert len(get_users.response_examples) > 0

        # Check response example structure
        response_example = get_users.response_examples[0]
        assert response_example.status_code == 200
        assert response_example.content is not None

    def test_extract_parameters(self, sample_markdown_content: Any) -> None:
        """Test parameter extraction from markdown."""
        loader = MarkdownDocumentationLoader()
        endpoints = loader._extract_endpoints_from_content(sample_markdown_content)

        # Find endpoint with parameters
        get_users = next((ep for ep in endpoints if ep.path == "/api/users" and ep.method == HTTPMethod.GET), None)

        assert get_users is not None
        assert len(get_users.parameters) > 0

        # Check parameter structure
        limit_param = next((param for param in get_users.parameters if param.name == "limit"), None)

        assert limit_param is not None
        assert limit_param.type == "integer"
        assert limit_param.required is False

    def test_extract_tags(self, sample_markdown_content: Any) -> None:
        """Test tag extraction from markdown."""
        loader = MarkdownDocumentationLoader()
        endpoints = loader._extract_endpoints_from_content(sample_markdown_content)

        # Check that tags were extracted
        for endpoint in endpoints:
            assert len(endpoint.tags) > 0

        # Check specific tags
        get_users = next((ep for ep in endpoints if ep.path == "/api/users" and ep.method == HTTPMethod.GET), None)

        assert "users" in get_users.tags
        assert "list" in get_users.tags

    def test_recursive_directory_loading(
        self, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any
    ) -> None:
        """Test recursive loading of markdown files from subdirectories."""
        # Create nested directory structure
        subdir = temp_docs_dir / "api" / "v1"
        subdir.mkdir(parents=True)

        # Create files in different directories
        test_utils.create_markdown_file(temp_docs_dir, "root.md", sample_markdown_content)
        test_utils.create_markdown_file(subdir, "users.md", sample_markdown_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), recursive=True, cache_enabled=False)

        documentation = loader.load_documentation()

        # Should find endpoints from both files
        assert len(documentation.endpoints) > 3  # More than one file's worth

    def test_non_recursive_directory_loading(
        self, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any
    ) -> None:
        """Test non-recursive loading (only root directory)."""
        # Create nested directory structure
        subdir = temp_docs_dir / "api"
        subdir.mkdir(parents=True)

        # Create files in different directories
        test_utils.create_markdown_file(temp_docs_dir, "root.md", sample_markdown_content)
        test_utils.create_markdown_file(subdir, "users.md", sample_markdown_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), recursive=False, cache_enabled=False)

        documentation = loader.load_documentation()

        # Should only find endpoints from root file
        assert len(documentation.endpoints) == 3  # Only from root.md

    def test_file_pattern_filtering(self, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any) -> None:
        """Test filtering files by pattern."""
        # Create files with different extensions
        test_utils.create_markdown_file(temp_docs_dir, "api.md", sample_markdown_content)
        test_utils.create_markdown_file(temp_docs_dir, "readme.txt", "Not markdown")
        test_utils.create_markdown_file(temp_docs_dir, "docs.markdown", sample_markdown_content)

        loader = MarkdownDocumentationLoader(
            docs_directory=str(temp_docs_dir), file_patterns=["*.md"], cache_enabled=False
        )

        documentation = loader.load_documentation()

        # Should only process .md files, not .txt or .markdown
        assert len(documentation.endpoints) == 3  # Only from api.md

    def test_supported_languages_filtering(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test filtering code samples by supported languages."""
        content_with_multiple_languages = """
# API Documentation

## GET /api/test

Test endpoint with multiple code examples.

### Code Examples

```python
import requests
response = requests.get("/api/test")
```

```javascript
fetch('/api/test').then(response => response.json())
```

```go
resp, err := http.Get("/api/test")
```

```java
HttpResponse response = client.get("/api/test");
```
"""

        test_utils.create_markdown_file(temp_docs_dir, "test.md", content_with_multiple_languages)

        loader = MarkdownDocumentationLoader(
            docs_directory=str(temp_docs_dir),
            supported_languages=[CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT],
            cache_enabled=False,
        )

        documentation = loader.load_documentation()

        endpoint = documentation.endpoints[0]
        languages = [sample.language for sample in endpoint.code_samples]

        # Should only include supported languages
        assert CodeLanguage.PYTHON in languages
        assert CodeLanguage.JAVASCRIPT in languages
        assert CodeLanguage.GO not in languages
        assert CodeLanguage.JAVA not in languages

    def test_encoding_handling(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test handling of different file encodings."""
        # Create file with UTF-8 content including special characters
        content_with_unicode = """
# API Documentation 📚

## GET /api/users

Retrieve users with special characters: café, naïve, résumé.

### Code Examples

```python
# Comment with unicode: 你好世界
import requests
response = requests.get("/api/users")
```
"""

        file_path = temp_docs_dir / "unicode.md"
        file_path.write_text(content_with_unicode, encoding="utf-8")

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), encoding="utf-8", cache_enabled=False)

        documentation = loader.load_documentation()

        assert len(documentation.endpoints) == 1
        endpoint = documentation.endpoints[0]
        assert "café" in endpoint.summary

    def test_error_handling_invalid_yaml_frontmatter(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test handling of invalid YAML frontmatter."""
        content_with_invalid_yaml = """---
title: API Documentation
invalid_yaml: [unclosed bracket
---

# API Documentation

## GET /api/test

Test endpoint.
"""

        test_utils.create_markdown_file(temp_docs_dir, "invalid.md", content_with_invalid_yaml)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)

        # Should handle invalid YAML gracefully
        documentation = loader.load_documentation()

        assert len(documentation.endpoints) == 1

    def test_metadata_extraction(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test extraction of metadata from markdown files."""
        content_with_metadata = """---
title: User Management API
version: 1.0.0
description: API for managing users
author: Test Author
---

# User Management API

## GET /api/users

List all users.
"""

        test_utils.create_markdown_file(temp_docs_dir, "users.md", content_with_metadata)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)

        documentation = loader.load_documentation()

        assert documentation.metadata["title"] == "User Management API"
        assert documentation.metadata["version"] == "1.0.0"
        assert documentation.metadata["author"] == "Test Author"

    def test_validation_error_handling(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test handling of validation errors during parsing."""
        # Create content that might cause validation issues
        invalid_content = """
# API Documentation

## INVALID_METHOD /api/test

This has an invalid HTTP method.

## GET

This has no path.

## GET /api/valid

This is valid.
"""

        test_utils.create_markdown_file(temp_docs_dir, "invalid.md", invalid_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)

        # Should handle validation errors gracefully and continue processing
        documentation = loader.load_documentation()

        # Should still extract the valid endpoint
        valid_endpoints = [ep for ep in documentation.endpoints if ep.path == "/api/valid"]
        assert len(valid_endpoints) == 1

    def test_performance_with_large_files(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test performance with large markdown files."""
        # Generate large content
        large_content = "# Large API Documentation\n\n"

        for i in range(100):
            large_content += f"""
## GET /api/endpoint{i}

Description for endpoint {i}.

### Code Examples

```python
import requests
response = requests.get("/api/endpoint{i}")
```

```curl
curl -X GET "https://api.example.com/api/endpoint{i}"
```
"""

        test_utils.create_markdown_file(temp_docs_dir, "large.md", large_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)

        # Should handle large files without issues
        documentation = loader.load_documentation()

        assert len(documentation.endpoints) == 100

    def test_concurrent_loading(self, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any) -> None:
        """Test concurrent loading of documentation."""
        import threading

        # Create multiple files
        for i in range(5):
            test_utils.create_markdown_file(
                temp_docs_dir, f"api{i}.md", sample_markdown_content.replace("/api/users", f"/api/users{i}")
            )

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=True)

        results = []

        def load_docs():
            result = loader.load_documentation()
            results.append(result)

        # Start multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=load_docs)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All results should be the same due to caching
        assert len(results) == 3
        assert all(result is results[0] for result in results)

    def test_cache_ttl_expiration(self, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any) -> None:
        """Test cache TTL expiration functionality."""
        test_utils.create_markdown_file(temp_docs_dir, "api.md", sample_markdown_content)

        # Use very short TTL for testing
        loader = MarkdownDocumentationLoader(
            docs_directory=str(temp_docs_dir),
            cache_enabled=True,
            cache_ttl=0.1,  # 100ms
        )

        # First load
        documentation1 = loader.load_documentation()

        # Wait for cache to expire
        time.sleep(0.2)

        # Second load should reload due to expired cache
        documentation2 = loader.load_documentation()

        # Should be different objects due to cache expiration
        assert documentation1 is not documentation2

    def test_concurrent_cache_loading(self, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any) -> None:
        """Test thread-safe cache loading with multiple threads."""
        test_utils.create_markdown_file(temp_docs_dir, "api.md", sample_markdown_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=True)

        results = []
        errors = []

        def load_docs():
            try:
                doc = loader.load_documentation()
                results.append(doc)
            except Exception as e:
                errors.append(e)

        # Start multiple threads simultaneously
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=load_docs)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have no errors
        assert len(errors) == 0
        assert len(results) == 5

        # All results should be the same object (cached)
        first_result = results[0]
        for result in results[1:]:
            assert result is first_result

    def test_concurrent_loading_with_error(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test concurrent loading when one thread encounters an error."""
        # Create a file that will cause an error during processing
        test_utils.create_markdown_file(temp_docs_dir, "api.md", "# Valid content")

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=True)

        results = []
        errors = []

        def load_docs_with_mock_error():
            try:
                # Mock an error in file processing
                with patch.object(loader, "_load_file", side_effect=Exception("Simulated error")):
                    doc = loader.load_documentation()
                    results.append(doc)
            except Exception as e:
                errors.append(e)

        def load_docs_normal():
            try:
                doc = loader.load_documentation()
                results.append(doc)
            except Exception as e:
                errors.append(e)

        # Start one thread that will error and one that will succeed
        error_thread = threading.Thread(target=load_docs_with_mock_error)
        normal_thread = threading.Thread(target=load_docs_normal)

        error_thread.start()
        time.sleep(0.1)  # Let error thread start first
        normal_thread.start()

        error_thread.join()
        normal_thread.join()

        # Should have one error and one success
        assert len(errors) == 1
        assert len(results) == 1

    def test_load_documentation_nonexistent_directory(self) -> None:
        """Test loading documentation from non-existent directory."""
        # This should fail at initialization, not at load time
        with pytest.raises(DocumentationLoadError) as exc_info:
            MarkdownDocumentationLoader(docs_directory="/nonexistent/path", cache_enabled=False)

        assert "does not exist" in str(exc_info.value)

    def test_file_processing_error_handling(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test error handling when file processing fails."""
        # Create a valid file
        test_utils.create_markdown_file(temp_docs_dir, "api.md", "# Valid content")

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)

        # Mock _load_file to raise an exception
        with patch.object(loader, "_load_file", side_effect=Exception("File processing error")):
            with pytest.raises(DocumentationLoadError) as exc_info:
                loader.load_documentation()

            assert "Failed to process file" in str(exc_info.value)

    def test_yaml_frontmatter_parsing(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test YAML frontmatter parsing with PyYAML."""
        content_with_yaml = """---
title: Test API Documentation
version: 1.2.3
published: true
priority: 10
rate: 99.5
description: API for testing purposes
---

## GET /api/test
Test endpoint with frontmatter
"""

        file_path = test_utils.create_markdown_file(temp_docs_dir, "with_yaml.md", content_with_yaml)
        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir))

        file_data = loader._load_file(str(file_path))

        # Should parse YAML frontmatter
        metadata = file_data["metadata"]
        assert metadata["title"] == "Test API Documentation"
        assert metadata["version"] == "1.2.3"
        assert metadata["published"] is True
        assert metadata["priority"] == 10
        assert metadata["rate"] == 99.5
        assert metadata is not None and metadata["description"] == "API for testing purposes"

    def test_response_examples_parsing_realistic(self) -> None:
        """Test response example parsing with realistic content."""
        loader = MarkdownDocumentationLoader()

        content_with_response_examples = """
## GET /api/test

### Response Examples

```json
{
  "id": 123,
  "name": "Test User",
  "active": true
}
```
"""

        examples = loader._extract_response_examples(content_with_response_examples)
        assert len(examples) == 1

        example = examples[0]
        assert example.status_code == 200  # Default status
        assert example.content["id"] == 123
        assert example.content["name"] == "Test User"
        assert example.content["active"] is True

    def test_response_examples_with_status_codes_realistic(self) -> None:
        """Test response example parsing with status codes in headers."""
        loader = MarkdownDocumentationLoader()

        content_with_status_codes = """
## POST /api/users

### Response Examples

```json 201
{
  "id": 123,
  "created": true
}
```

```json 400
{
  "error": "Bad request"
}
```
"""

        examples = loader._extract_response_examples(content_with_status_codes)
        assert len(examples) == 2

        # Check status codes are correctly parsed
        status_codes = [ex.status_code for ex in examples]
        assert 201 in status_codes
        assert 400 in status_codes

        # Check content is correctly parsed
        created_example = next(ex for ex in examples if ex.status_code == 201)
        assert created_example.content["id"] == 123
        assert created_example.content["created"] is True

    def test_is_cached_functionality(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test file caching detection functionality."""
        test_file = test_utils.create_markdown_file(temp_docs_dir, "test.md", "# Test")

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=True)

        # Initially not cached
        assert not loader._is_cached(str(test_file))

        # Load file to cache it
        loader._load_file(str(test_file))

        # Now should be cached
        assert loader._is_cached(str(test_file))

        # Modify file (change mtime)
        time.sleep(0.1)
        test_file.touch()

        # Should no longer be cached due to modified time
        assert not loader._is_cached(str(test_file))

    def test_get_stats_functionality(self, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any) -> None:
        """Test statistics gathering functionality."""
        test_utils.create_markdown_file(temp_docs_dir, "api.md", sample_markdown_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=True)

        # Load documentation first
        loader.load_documentation()

        # Get stats
        stats = loader.get_stats()

        assert "cache_enabled" in stats
        assert "cache_size" in stats
        assert stats["cache_enabled"] is True
        # Note: total_files_cached may not be in the actual implementation

    def test_load_file_with_encoding_issues(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test file loading with encoding issues."""
        # Create file with special characters
        content_with_special_chars = """
# API Documentation with Special Characters

## GET /api/café
Get café information

Description with émojis: 🚀 ✨ 🎉

```python
# Python code with special chars
response = requests.get('/api/café')
```
"""

        file_path = test_utils.create_markdown_file(temp_docs_dir, "special.md", content_with_special_chars)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir))

        # Should handle special characters gracefully
        file_data = loader._load_file(str(file_path))
        assert "café" in file_data["content"]
        assert "🚀" in file_data["content"]

    def test_split_content_by_endpoints_edge_cases(self) -> None:
        """Test edge cases in content splitting by endpoints."""
        loader = MarkdownDocumentationLoader()

        # Test content with no endpoint headers
        content_no_endpoints = """
# API Documentation

This is general documentation without specific endpoints.

Some general information about the API.
"""
        sections = loader._split_content_by_endpoints(content_no_endpoints)
        assert len(sections) == 1
        assert "API Documentation" in sections[0]

        # Test content with multiple consecutive endpoint headers
        content_multiple = """## GET /api/users
Get all users

## POST /api/users
Create a user

## GET /api/users/{id}
Get specific user
"""
        sections = loader._split_content_by_endpoints(content_multiple)
        # Should have 3 sections for the 3 endpoints
        assert len(sections) == 3
        assert "GET /api/users" in sections[0]
        assert "POST /api/users" in sections[1]
        assert "GET /api/users/{id}" in sections[2]

    def test_concurrent_loading_with_cache_failure_recovery(
        self, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any
    ) -> None:
        """Test recovery when concurrent loading fails and waiting threads need to retry."""
        test_utils.create_markdown_file(temp_docs_dir, "api.md", sample_markdown_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=True)

        # Mock the internal loading to fail first, then succeed
        original_load = loader._load_documentation_internal
        call_count = 0

        def failing_then_succeeding_load():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Simulated loading failure")
            return original_load()

        loader._load_documentation_internal = failing_then_succeeding_load

        results = []
        exceptions = []

        def load_docs():
            try:
                result = loader.load_documentation()
                results.append(result)
            except Exception as e:
                exceptions.append(e)

        # Start multiple threads
        threads = [threading.Thread(target=load_docs) for _ in range(3)]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=5)

        # At least one thread should succeed after the first failure
        assert len(results) > 0
        # The first attempt should fail, but subsequent ones should succeed
        assert call_count >= 2

    def test_file_modification_detection_in_cache(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test that cache properly detects file modifications."""
        # Create initial file
        file_path = test_utils.create_markdown_file(temp_docs_dir, "test.md", "## GET /api/v1\nOriginal content")

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=True)

        # Load file to cache it
        first_result = loader._load_file(str(file_path))
        assert "Original content" in first_result["content"]
        assert loader._is_cached(str(file_path))

        # Modify the file
        time.sleep(0.1)  # Ensure different modification time
        file_path.write_text("## GET /api/v2\nModified content")

        # Cache should detect modification and reload
        assert not loader._is_cached(str(file_path))

        second_result = loader._load_file(str(file_path))
        assert "Modified content" in second_result["content"]

    def test_response_examples_with_invalid_json_recovery(self) -> None:
        """Test response example parsing gracefully handles invalid JSON."""
        loader = MarkdownDocumentationLoader()

        content_with_invalid_json = """
## GET /api/test

### Response Examples

```json
{
  "valid": "start",
  "invalid": json content here,
  "missing": quotes
}
```
"""

        examples = loader._extract_response_examples(content_with_invalid_json)
        assert len(examples) == 1

        # Should detect invalid JSON as plain text and store directly in content
        example = examples[0]
        assert example.content_type == "text/plain"
        assert isinstance(example.content, str)
        assert "invalid" in example.content

    def test_cache_invalidation_on_file_access_errors(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test cache invalidation when file access fails."""
        file_path = test_utils.create_markdown_file(temp_docs_dir, "test.md", "## GET /test\nContent")

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=True)

        # Load file to cache it
        loader._load_file(str(file_path))
        assert loader._is_cached(str(file_path))

        # Mock file stat to raise OSError (simulating file access issues)
        with patch("os.path.getmtime", side_effect=OSError("Permission denied")):
            # Should invalidate cache and return False
            assert not loader._is_cached(str(file_path))
            # Cache entry should be removed
            assert str(file_path) not in loader._cache

    def test_general_docs_loading_default_file(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test loading general documentation from default general_docs.md file."""
        # Create general_docs.md file
        general_content = """# General API Documentation

## Overview

This is the general documentation for the entire API.

### Authentication

All endpoints require authentication.
"""
        test_utils.create_markdown_file(temp_docs_dir, "general_docs.md", general_content)

        # Create an endpoint file
        endpoint_content = """### POST /api/test

**Test endpoint**

This endpoint creates a test resource.
"""
        test_utils.create_markdown_file(temp_docs_dir, "test.md", endpoint_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)
        documentation = loader.load_documentation()

        # Should have endpoints
        assert len(documentation.endpoints) > 0

        # Check that general docs are loaded into the loader's _general_docs_content
        assert hasattr(loader, "_general_docs_content")
        general_docs_content = loader._general_docs_content
        assert general_docs_content is not None
        assert "# General API Documentation" in general_docs_content
        assert "This is the general documentation" in general_docs_content
        assert "### Authentication" in general_docs_content
        assert "All endpoints require authentication" in general_docs_content

        # Check that endpoint descriptions do NOT include general docs (now handled globally)
        endpoint = documentation.endpoints[0]
        description = endpoint.description or ""
        assert "Test endpoint" in description
        assert "# General API Documentation" not in description

    def test_general_docs_loading_custom_file(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test loading general documentation from custom file."""
        # Create custom general docs file
        general_content = """# Custom General Documentation

This is custom general documentation.
"""
        test_utils.create_markdown_file(temp_docs_dir, "custom_general.md", general_content)

        # Create an endpoint file
        endpoint_content = """### POST /api/test

**Test endpoint**

This endpoint creates a test resource.
"""
        test_utils.create_markdown_file(temp_docs_dir, "test.md", endpoint_content)

        loader = MarkdownDocumentationLoader(
            docs_directory=str(temp_docs_dir), general_docs_file="custom_general.md", cache_enabled=False
        )
        documentation = loader.load_documentation()

        # Should have endpoints
        assert len(documentation.endpoints) > 0

        # Check that custom general docs are loaded into the loader's _general_docs_content
        assert hasattr(loader, "_general_docs_content")
        general_docs_content = loader._general_docs_content
        assert general_docs_content is not None
        assert "# Custom General Documentation" in general_docs_content
        assert "This is custom general documentation" in general_docs_content

        # Check that endpoint descriptions do NOT include general docs
        endpoint = documentation.endpoints[0]
        description = endpoint.description or ""
        assert "Test endpoint" in description
        assert "# Custom General Documentation" not in description

    def test_general_docs_loading_absolute_path(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test loading general documentation from absolute path."""
        # Create general docs file in a different location
        import tempfile

        with tempfile.TemporaryDirectory() as other_dir:
            other_path = Path(other_dir)
            general_file = other_path / "external_general.md"
            general_content = """# External General Documentation

This is external general documentation.
"""
            general_file.write_text(general_content)

            # Create an endpoint file
            endpoint_content = """### POST /api/test

**Test endpoint**

This endpoint creates a test resource.
"""
            test_utils.create_markdown_file(temp_docs_dir, "test.md", endpoint_content)

            loader = MarkdownDocumentationLoader(
                docs_directory=str(temp_docs_dir), general_docs_file=str(general_file), cache_enabled=False
            )
            documentation = loader.load_documentation()

            # Should have endpoints
            assert len(documentation.endpoints) > 0

            # Check that external general docs are loaded into the loader's _general_docs_content
            assert hasattr(loader, "_general_docs_content")
            general_docs_content = loader._general_docs_content
            assert general_docs_content is not None
            assert "# External General Documentation" in general_docs_content
            assert "This is external general documentation" in general_docs_content

            # Check that endpoint descriptions do NOT include general docs
            endpoint = documentation.endpoints[0]
            description = endpoint.description or ""
            assert "Test endpoint" in description
            assert "# External General Documentation" not in description

    def test_general_docs_loading_nonexistent_file(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test loading when general docs file doesn't exist."""
        # Create an endpoint file without general docs
        endpoint_content = """### POST /api/test

**Test endpoint**

This endpoint creates a test resource.
"""
        test_utils.create_markdown_file(temp_docs_dir, "test.md", endpoint_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)
        documentation = loader.load_documentation()

        # Should have endpoints
        assert len(documentation.endpoints) > 0

        # Check that endpoint description doesn't include general docs
        endpoint = documentation.endpoints[0]
        description = endpoint.description or ""

        assert "Test endpoint" in description
        assert "# General API Documentation" not in description

    def test_general_docs_loading_with_frontmatter(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test loading general docs with YAML frontmatter."""
        # Create general docs with frontmatter
        general_content = """---
title: General Documentation
version: 1.0
---

# General API Documentation

This is the general documentation with frontmatter.
"""
        test_utils.create_markdown_file(temp_docs_dir, "general_docs.md", general_content)

        # Create an endpoint file
        endpoint_content = """### POST /api/test

**Test endpoint**

This endpoint creates a test resource.
"""
        test_utils.create_markdown_file(temp_docs_dir, "test.md", endpoint_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)
        documentation = loader.load_documentation()

        # Should have endpoints
        assert len(documentation.endpoints) > 0

        # Check that general docs are loaded without frontmatter
        assert hasattr(loader, "_general_docs_content")
        general_docs_content = loader._general_docs_content
        assert general_docs_content is not None
        assert "# General API Documentation" in general_docs_content
        assert "This is the general documentation with frontmatter" in general_docs_content
        # Frontmatter should be stripped - check that the YAML frontmatter content is not present
        assert "title: General Documentation" not in general_docs_content
        assert "version: 1.0" not in general_docs_content
        # The document should not start with frontmatter
        assert not general_docs_content.startswith("---")

        # Check that endpoint descriptions do NOT include general docs
        endpoint = documentation.endpoints[0]
        description = endpoint.description or ""
        assert "Test endpoint" in description
        assert "# General API Documentation" not in description

    def test_general_docs_loading_error_handling(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test error handling when general docs file has issues."""
        import warnings

        # Create a general docs file
        general_content = """# General Documentation

This is general documentation.
"""
        test_utils.create_markdown_file(temp_docs_dir, "general_docs.md", general_content)

        # Create an endpoint file
        endpoint_content = """### POST /api/test

**Test endpoint**

This endpoint creates a test resource.
"""
        test_utils.create_markdown_file(temp_docs_dir, "test.md", endpoint_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)

        # Mock the _load_general_docs method to raise an exception
        def mock_load_general_docs(docs_path):
            raise PermissionError("Permission denied")

        loader._load_general_docs = mock_load_general_docs

        # Should handle the error gracefully and continue without general docs
        # Suppress the expected warning during testing
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            documentation = loader.load_documentation()

        # Should still have endpoints
        assert len(documentation.endpoints) > 0

        # Check that endpoint description doesn't include general docs due to error
        endpoint = documentation.endpoints[0]
        description = endpoint.description or ""

        assert "Test endpoint" in description
        assert "# General Documentation" not in description

    def test_load_general_docs_method(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test the _load_general_docs method directly."""
        # Create general docs file
        general_content = """# General Documentation

This is general documentation.
"""
        test_utils.create_markdown_file(temp_docs_dir, "general_docs.md", general_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir))

        # Test loading general docs
        result = loader._load_general_docs(str(temp_docs_dir))

        assert result is not None
        assert "# General Documentation" in result
        assert "This is general documentation" in result

        # Test with nonexistent file
        result = loader._load_general_docs("/nonexistent/path")
        assert result is None

        # Test with custom file
        loader.general_docs_file = "general_docs.md"
        result = loader._load_general_docs(str(temp_docs_dir))
        assert result is not None
        assert "# General Documentation" in result

    def test_response_examples_multi_endpoint_bug_reproduction(self) -> None:
        """Test that reproduces the bug where response examples are not detected in multi-endpoint files."""
        loader = MarkdownDocumentationLoader()

        # Multi-endpoint content that reproduces the bug from the bug report
        multi_endpoint_content = """
### POST /v1/session

Login to the system and create a new session.

#### Response Examples

**Success (200 OK):**
```json
{
  "id": "user123",
  "username": "admin",
  "isOtpEnabled": false
}
```

**OTP Required (204 No Content):**
```
HTTP/1.1 204 No Content
Set-Cookie: temporary_session=temp_token_123; Path=/; HttpOnly; Secure
```

**Invalid Credentials (401 Unauthorized):**
```json
{
  "error": "Invalid credentials",
  "code": "INVALID_CREDENTIALS"
}
```

**Account Locked (423 Locked):**
```json
{
  "error": "Account is locked",
  "code": "ACCOUNT_LOCKED",
  "lockoutTime": "2024-01-15T10:30:00Z"
}
```

**Server Error (500 Internal Server Error):**
```json
{
  "error": "Internal server error",
  "code": "INTERNAL_ERROR"
}
```

---

### POST /v1/session:verifyOtp

Verify OTP and complete the authentication process.

#### Response Examples

**Success (200 OK):**
```json
{
  "id": "user123",
  "username": "admin",
  "recoveryCodes": ["recovery1", "recovery2", "recovery3"]
}
```

**Invalid OTP (401 Unauthorized):**
```json
{
  "error": "Invalid OTP code",
  "code": "INVALID_OTP"
}
```

**OTP Expired (401 Unauthorized):**
```json
{
  "error": "OTP code has expired",
  "code": "OTP_EXPIRED"
}
```

**Too Many Attempts (429 Too Many Requests):**
```json
{
  "error": "Too many OTP attempts",
  "code": "TOO_MANY_ATTEMPTS",
  "retryAfter": 300
}
```
"""

        # Extract endpoints from the multi-endpoint content
        endpoints = loader._extract_endpoints_from_content(multi_endpoint_content)

        # Should find 2 endpoints
        assert len(endpoints) == 2

        # First endpoint: POST /v1/session
        session_endpoint = endpoints[0]
        assert session_endpoint.path == "/v1/session"
        assert session_endpoint.method.value == "POST"

        # BUG: This should find 5 response examples but currently finds 0
        print(f"POST /v1/session response examples found: {len(session_endpoint.response_examples)}")
        assert (
            len(session_endpoint.response_examples) == 5
        ), f"Expected 5 response examples, found {len(session_endpoint.response_examples)}"

        # Second endpoint: POST /v1/session:verifyOtp
        verify_otp_endpoint = endpoints[1]
        assert verify_otp_endpoint.path == "/v1/session:verifyOtp"
        assert verify_otp_endpoint.method.value == "POST"

        # BUG: This should find 4 response examples but currently finds 0
        print(f"POST /v1/session:verifyOtp response examples found: {len(verify_otp_endpoint.response_examples)}")
        assert (
            len(verify_otp_endpoint.response_examples) == 4
        ), f"Expected 4 response examples, found {len(verify_otp_endpoint.response_examples)}"

    def test_response_examples_status_code_extraction(self) -> None:
        """Test that status codes are correctly extracted from response description lines."""
        loader = MarkdownDocumentationLoader()

        content_with_status_codes = """
### POST /v1/test

Test endpoint with various status codes.

#### Response Examples

**Success (200 OK):**
```json
{
  "id": "test123",
  "status": "success"
}
```

**Created (201 Created):**
```json
{
  "id": "test456",
  "status": "created"
}
```

**Bad Request (400 Bad Request):**
```json
{
  "error": "Invalid input",
  "code": "BAD_REQUEST"
}
```

**Unauthorized (401 Unauthorized):**
```json
{
  "error": "Authentication required",
  "code": "UNAUTHORIZED"
}
```

**Not Found (404 Not Found):**
```json
{
  "error": "Resource not found",
  "code": "NOT_FOUND"
}
```

**Server Error (500 Internal Server Error):**
```json
{
  "error": "Internal server error",
  "code": "INTERNAL_ERROR"
}
```
"""

        # Extract endpoints from the content
        endpoints = loader._extract_endpoints_from_content(content_with_status_codes)

        # Should find 1 endpoint
        assert len(endpoints) == 1

        endpoint = endpoints[0]
        assert endpoint.path == "/v1/test"
        assert endpoint.method.value == "POST"

        # Should find 6 response examples with correct status codes
        assert len(endpoint.response_examples) == 6

        # Verify status codes are extracted correctly
        expected_status_codes = [200, 201, 400, 401, 404, 500]
        expected_descriptions = ["Success", "Created", "Bad Request", "Unauthorized", "Not Found", "Server Error"]

        actual_status_codes = [example.status_code for example in endpoint.response_examples]
        actual_descriptions = [example.description for example in endpoint.response_examples]

        assert (
            actual_status_codes == expected_status_codes
        ), f"Expected {expected_status_codes}, got {actual_status_codes}"
        assert (
            actual_descriptions == expected_descriptions
        ), f"Expected {expected_descriptions}, got {actual_descriptions}"

        # Verify content is parsed correctly
        for i, example in enumerate(endpoint.response_examples):
            assert isinstance(example.content, dict)
            if i < 2:  # Success and Created responses
                assert "id" in example.content
                assert "status" in example.content
            else:  # Error responses
                assert "error" in example.content
                assert "code" in example.content

    def test_response_examples_complex_multi_endpoint_structure(self) -> None:
        """Test response examples detection in complex multi-endpoint files with extensive content."""
        loader = MarkdownDocumentationLoader()

        # Complex multi-endpoint content that closely matches syneto-doorman structure
        complex_content = """### POST /v1/session

**Create a new authentication session**

This endpoint authenticates users and creates a session. It supports multiple authentication methods:

1. **Username/Password Authentication**: Standard login for regular users
2. **PIN Authentication**: Quick access for support personnel

**Authentication Flow:**
- If OTP is disabled: Returns a session cookie immediately
- If OTP is enabled: Returns a temporary session cookie and requires OTP verification

**Response Scenarios:**
- `200 OK`: Session created successfully (OTP disabled)
- `203 Non-Authoritative Information`: OTP setup required (first-time OTP users)
- `204 No Content`: Temporary session created, OTP verification needed
- `401 Unauthorized`: Invalid credentials
- `429 Too Many Requests`: Rate limited by fail2ban

#### Code Examples

##### cURL
```bash
curl -X POST "{base_url}/v1/session" \\
  -H "Content-Type: application/json" \\
  -H "X-Real-IP: 192.168.1.100" \\
  -d '{
    "username": "admin",
    "password": "your_password"
  }'
```

##### Python
```python
import requests

url = "{base_url}/v1/session"
headers = {
    "Content-Type": "application/json",
    "X-Real-IP": "192.168.1.100"
}
data = {
    "username": "admin",
    "password": "your_password"
}

response = requests.post(url, headers=headers, json=data)
print(response.status_code)
print(response.cookies.get('session'))
```

#### Request Examples

**Username/Password Authentication:**
```json
{
  "username": "admin",
  "password": "your_password"
}
```

**PIN Authentication (Support Access):**
```json
{
  "pin": "123456"
}
```

#### Response Examples

**Success (200 OK) - Session created:**
```json
{
  "id": "user123",
  "username": "admin",
  "fullName": "Administrator",
  "role": "administrator",
  "isOtpEnabled": false
}
```

**OTP Required (204 No Content) - Temporary session created:**
```
HTTP/1.1 204 No Content
Set-Cookie: temporary_session=temp_token_123; Path=/; HttpOnly; Secure
Content-Length: 0
```

**OTP Setup Required (203 Non-Authoritative Information):**
```json
{
  "authenticatorLink": "otpauth://totp/Syneto:admin?secret=JBSWY3DPEHPK3PXP&issuer=Syneto",
  "secret": "JBSWY3DPEHPK3PXP"
}
```

**Authentication Failed (401 Unauthorized):**
```json
{
  "detail": "Invalid credentials"
}
```

**Rate Limited (429 Too Many Requests):**
```json
{
  "detail": "Too many authentication attempts. Please try again later."
}
```

---

### GET /v1/session

**Get current session information**

Retrieves details about the currently authenticated user based on the session cookie.

#### Response Example

**Success (200 OK):**
```json
{
  "id": "user123",
  "username": "admin",
  "fullName": "System Administrator",
  "role": "administrator"
}
```

---

### DELETE /v1/session

**Terminate current session and logout user**

Logs out the current user by invalidating their session cookie.

#### Response Examples

**Success (204 No Content):**
```
HTTP/1.1 204 No Content
Set-Cookie: session=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0
Content-Length: 0
```

### POST /v1/session:verifyOtp

**Verify One-Time Password (OTP)**

Completes the two-factor authentication process by verifying the OTP code.

**Supported Code Types:**
- **6-digit TOTP codes**: Time-based codes from authenticator apps
- **8-digit recovery codes**: Backup codes for account recovery

**Process:**
1. User provides temporary session token (from initial login)
2. User submits OTP code
3. System validates the code
4. If valid, issues a full session token
5. If first-time setup, provides recovery codes

**Security Features:**
- Rate limiting to prevent brute force attacks
- Automatic account lockout after multiple failures
- Recovery codes are single-use only

#### Code Examples

##### cURL
```bash
curl -X POST "{base_url}/v1/session:verifyOtp" \\
  -H "Content-Type: application/json" \\
  -H "Cookie: temporary_session=your_temp_token" \\
  -H "X-Real-IP: 192.168.1.100" \\
  -d '{
    "code": "123456"
  }'
```

##### Python
```python
import requests

url = "{base_url}/v1/session:verifyOtp"
headers = {
    "Content-Type": "application/json",
    "X-Real-IP": "192.168.1.100"
}
cookies = {"temporary_session": "your_temp_token"}
data = {"code": "123456"}

response = requests.post(url, headers=headers, cookies=cookies, json=data)
session_cookie = response.cookies.get('session')
print(f"Session established: {session_cookie}")
```

#### Request Examples

**OTP Code Verification:**
```json
{
  "code": "123456"
}
```

**Recovery Code Usage:**
```json
{
  "code": "12345678"
}
```

#### Response Examples

**OTP Verified with Recovery Codes (200 OK) - First-time setup:**
```json
{
  "recoveryCodes": [
    "12345678",
    "87654321",
    "11223344",
    "44332211",
    "55667788"
  ]
}
```

**OTP Verified (204 No Content):**
```
HTTP/1.1 204 No Content
Set-Cookie: session=full_session_token_456; Path=/; HttpOnly; Secure; SameSite=Strict
Content-Length: 0
```

**Invalid OTP Code (401 Unauthorized):**
```json
{
  "detail": "Invalid OTP code"
}
```

**Rate Limited (429 Too Many Requests):**
```json
{
  "detail": "Too many OTP verification attempts. Please try again later."
}
```
"""

        # Extract endpoints from the complex content
        endpoints = loader._extract_endpoints_from_content(complex_content)

        # Should find 4 endpoints
        assert len(endpoints) == 4

        # Verify each endpoint has the correct number of response examples
        post_session = next((ep for ep in endpoints if ep.path == "/v1/session" and ep.method.value == "POST"), None)
        get_session = next((ep for ep in endpoints if ep.path == "/v1/session" and ep.method.value == "GET"), None)
        delete_session = next(
            (ep for ep in endpoints if ep.path == "/v1/session" and ep.method.value == "DELETE"), None
        )
        post_verify = next(
            (ep for ep in endpoints if ep.path == "/v1/session:verifyOtp" and ep.method.value == "POST"), None
        )

        # POST /v1/session should have 5 response examples
        assert post_session is not None
        assert len(post_session.response_examples) == 5
        status_codes = [ex.status_code for ex in post_session.response_examples]
        assert 200 in status_codes
        assert 204 in status_codes
        assert 203 in status_codes
        assert 401 in status_codes
        assert 429 in status_codes

        # GET /v1/session should have 1 response example
        assert get_session is not None
        assert len(get_session.response_examples) == 1
        assert get_session.response_examples[0].status_code == 200

        # DELETE /v1/session should have 1 response example
        assert delete_session is not None
        assert len(delete_session.response_examples) == 1
        assert delete_session.response_examples[0].status_code == 204

        # POST /v1/session:verifyOtp should have 4 response examples
        assert post_verify is not None
        assert len(post_verify.response_examples) == 4
        verify_status_codes = [ex.status_code for ex in post_verify.response_examples]
        assert 200 in verify_status_codes
        assert 204 in verify_status_codes
        assert 401 in verify_status_codes
        assert 429 in verify_status_codes

    def test_response_examples_edge_cases(self) -> None:
        """Test response examples detection with various edge cases."""
        loader = MarkdownDocumentationLoader()

        # Test case 1: Response Examples section with no actual examples
        content_no_examples = """### POST /v1/test

Test endpoint.

#### Response Examples

This endpoint doesn't have any examples yet.
"""
        endpoints = loader._extract_endpoints_from_content(content_no_examples)
        assert len(endpoints) == 1
        assert len(endpoints[0].response_examples) == 0

        # Test case 2: Multiple Response Examples headers (should handle the first one)
        content_multiple_headers = """### POST /v1/test

Test endpoint.

#### Response Examples

**Success (200 OK):**
```json
{"status": "ok"}
```

#### More Response Examples

**Error (400 Bad Request):**
```json
{"error": "bad request"}
```
"""
        endpoints = loader._extract_endpoints_from_content(content_multiple_headers)
        assert len(endpoints) == 1
        # Should find only the first response example (the second is under a different header)
        assert len(endpoints[0].response_examples) == 1
        assert endpoints[0].response_examples[0].status_code == 200

        # Test case 3: Response Examples with mixed content types
        content_mixed_types = """### POST /v1/test

Test endpoint.

#### Response Examples

**JSON Response (200 OK):**
```json
{"data": "json"}
```

**Plain Text Response (200 OK):**
```
Plain text response
```

**XML Response (200 OK):**
```xml
<response>xml</response>
```

**Empty Response (204 No Content):**
```
HTTP/1.1 204 No Content
Content-Length: 0
```
"""
        endpoints = loader._extract_endpoints_from_content(content_mixed_types)
        assert len(endpoints) == 1
        assert len(endpoints[0].response_examples) == 4

        # Verify different content types are handled
        status_codes = [ex.status_code for ex in endpoints[0].response_examples]
        assert status_codes.count(200) == 3  # Three 200 responses
        assert status_codes.count(204) == 1  # One 204 response

        # Test case 4: Response Examples with complex status descriptions
        content_complex_descriptions = """### POST /v1/test

Test endpoint.

#### Response Examples

**Created Successfully with Additional Processing (201 Created) - Resource created and queued for processing:**
```json
{"id": "123", "status": "created"}
```

**Partial Content Returned Due to Size Limits (206 Partial Content) - Large dataset truncated:**
```json
{"data": [], "truncated": true}
```

**Authentication Required for Protected Resource (401 Unauthorized) - Invalid or missing token:**
```json
{"error": "authentication_required"}
```
"""
        endpoints = loader._extract_endpoints_from_content(content_complex_descriptions)
        assert len(endpoints) == 1
        assert len(endpoints[0].response_examples) == 3

        # Verify status codes are extracted correctly from complex descriptions
        status_codes = [ex.status_code for ex in endpoints[0].response_examples]
        assert 201 in status_codes
        assert 206 in status_codes
        assert 401 in status_codes

        # Test case 5: Response Examples interrupted by other sections
        content_interrupted = """### POST /v1/test

Test endpoint.

#### Response Examples

**Success (200 OK):**
```json
{"status": "ok"}
```

#### Parameters

- `param1` (string): A parameter

#### More Content

Some other content here.

**This should not be parsed as a response example (400 Bad Request):**
```json
{"error": "not parsed"}
```
"""
        endpoints = loader._extract_endpoints_from_content(content_interrupted)
        assert len(endpoints) == 1
        # Should only find the first response example before the interruption
        assert len(endpoints[0].response_examples) == 1
        assert endpoints[0].response_examples[0].status_code == 200

    def test_extract_endpoint_info_general_docs_only(self) -> None:
        """Test extract_endpoint_info with only general docs content."""

        # Content with no endpoints
        content = """
# General Documentation

This is general documentation content that applies to the whole API.

## Features

- Feature 1
- Feature 2
"""

        general_docs = "This is general documentation for the entire API."

        endpoint_info = extract_endpoint_info(content, general_docs)

        # Should not find any endpoint
        assert endpoint_info["path"] is None
        assert endpoint_info["method"] is None
        assert endpoint_info["summary"] is None

        # Should not have description when no endpoint is found and no overview
        assert endpoint_info["description"] is None

    def test_extract_tag_descriptions_from_content(self) -> None:
        """Test extraction of tag descriptions from markdown content with Overview sections."""
        loader = MarkdownDocumentationLoader()

        content_with_overview = """
# User Management API Documentation

## Overview

The **User Management API** provides comprehensive user account administration for SynetoOS, enabling centralized user lifecycle management with role-based access control and multi-factor authentication. This API supports enterprise-grade user provisioning, security policies, and audit capabilities.

### 👥 **User Management Features**

**Complete User Lifecycle**
- User account creation with customizable roles and permissions
- Profile management and account status control (enable/disable)
- Secure user deletion with data integrity protection

### 🛡️ **Security Features**

**Password Security**
- Configurable password complexity requirements and minimum length
- Secure password hashing with industry-standard algorithms
- No plain-text password storage or transmission

## Endpoints

### GET /users

**List all users**

Retrieves a complete list of all user accounts in the system.

Tags: users, list

### POST /users

**Create new user**

Creates a new user account with specified credentials and configuration.

Tags: users, create
"""

        tag_descriptions = loader._extract_tag_descriptions_from_content(content_with_overview)

        # Should extract tag descriptions for all tags in the file
        assert "users" in tag_descriptions
        assert "list" in tag_descriptions
        assert "create" in tag_descriptions

        # All tags should have the same overview description
        expected_description = tag_descriptions["users"]
        assert "User Management API" in expected_description
        assert "comprehensive user account administration" in expected_description
        assert "👥" in expected_description  # Should include emoji sections
        assert "🛡️" in expected_description

        # All tags from this file should have the same description
        assert tag_descriptions["list"] == expected_description
        assert tag_descriptions["create"] == expected_description

    def test_extract_tag_descriptions_no_overview(self) -> None:
        """Test tag description extraction when no Overview section exists."""
        loader = MarkdownDocumentationLoader()

        content_without_overview = """
# API Documentation

### GET /users

List all users.

Tags: users, list

### POST /users

Create a user.

Tags: users, create
"""

        tag_descriptions = loader._extract_tag_descriptions_from_content(content_without_overview)

        # Should return empty dict when no Overview section exists
        assert tag_descriptions == {}

    def test_extract_tag_descriptions_no_tags(self) -> None:
        """Test tag description extraction when no tags are present."""
        loader = MarkdownDocumentationLoader()

        content_with_overview_no_tags = """
# API Documentation

## Overview

This is an overview of the API with comprehensive documentation.

### GET /users

List all users.

### POST /users

Create a user.
"""

        tag_descriptions = loader._extract_tag_descriptions_from_content(content_with_overview_no_tags)

        # Should return empty dict when no tags are found
        assert tag_descriptions == {}

    def test_extract_overview_section(self) -> None:
        """Test extraction of Overview section content."""
        loader = MarkdownDocumentationLoader()

        content_with_overview = """
# API Documentation

## Overview

The **User Management API** provides comprehensive user account administration.

### Features

- Feature 1
- Feature 2

### Security

Security features are important.

## Endpoints

### GET /users

List users.
"""

        overview_content = loader._extract_overview_section(content_with_overview)

        assert overview_content is not None
        assert "User Management API" in overview_content
        assert "Feature 1" in overview_content
        assert "Security features are important" in overview_content
        # Should not include the "## Endpoints" section
        assert "## Endpoints" not in overview_content
        assert "List users" not in overview_content

    def test_extract_overview_section_not_found(self) -> None:
        """Test overview section extraction when section doesn't exist."""
        loader = MarkdownDocumentationLoader()

        content_without_overview = """
# API Documentation

## Introduction

This is just an introduction.

### GET /users

List users.
"""

        overview_content = loader._extract_overview_section(content_without_overview)

        assert overview_content is None

    def test_load_documentation_with_tag_descriptions(self, temp_docs_dir: Any, test_utils: Any) -> None:
        """Test that tag descriptions are properly collected during documentation loading."""
        users_content = """
# User Management API

## Overview

The **User Management API** provides comprehensive user account administration for SynetoOS, enabling centralized user lifecycle management with role-based access control and multi-factor authentication.

## Endpoints

### GET /users

List all users in the system.

Tags: users, list

### POST /users

Create a new user account.

Tags: users, create
"""

        auth_content = """
# Authentication API

## Overview

The **Authentication API** handles user login, session management, and security token operations for secure access to the system.

## Endpoints

### POST /auth/login

Authenticate a user and create a session.

Tags: authentication, login

### POST /auth/logout

Logout a user and invalidate the session.

Tags: authentication, logout
"""

        # Create markdown files
        test_utils.create_markdown_file(temp_docs_dir, "users.md", users_content)
        test_utils.create_markdown_file(temp_docs_dir, "auth.md", auth_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)
        documentation = loader.load_documentation()

        # Check that tag descriptions were collected
        assert hasattr(documentation, "tag_descriptions")
        assert len(documentation.tag_descriptions) > 0

        # Check specific tag descriptions
        assert "users" in documentation.tag_descriptions
        assert "authentication" in documentation.tag_descriptions

        users_desc = documentation.tag_descriptions["users"]
        auth_desc = documentation.tag_descriptions["authentication"]

        assert "User Management API" in users_desc
        assert "comprehensive user account administration" in users_desc

        assert "Authentication API" in auth_desc
        assert "user login, session management" in auth_desc

        # All tags from the same file should have the same description
        if "list" in documentation.tag_descriptions:
            assert documentation.tag_descriptions["list"] == users_desc
        if "create" in documentation.tag_descriptions:
            assert documentation.tag_descriptions["create"] == users_desc
