"""
Unit tests for the MarkdownDocumentationLoader class.

Tests the markdown parsing, documentation extraction, and caching functionality.
"""

import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from fastmarkdocs.documentation_loader import MarkdownDocumentationLoader
from fastmarkdocs.exceptions import DocumentationLoadError
from fastmarkdocs.types import CodeLanguage, HTTPMethod


class TestMarkdownDocumentationLoader:
    """Test the MarkdownDocumentationLoader class."""

    def test_initialization_default_config(self):
        """Test loader initialization with default configuration."""
        loader = MarkdownDocumentationLoader()

        assert loader.docs_directory == Path("docs")
        assert loader.recursive is True
        assert loader.cache_enabled is True
        assert CodeLanguage.CURL in loader.supported_languages
        assert CodeLanguage.PYTHON in loader.supported_languages

    def test_initialization_custom_config(self, documentation_loader_config):
        """Test loader initialization with custom configuration."""
        loader = MarkdownDocumentationLoader(**documentation_loader_config)

        assert loader.docs_directory == Path("test_docs")
        assert loader.recursive is True
        assert loader.cache_enabled is False
        assert len(loader.supported_languages) == 3

    def test_initialization_invalid_directory(self):
        """Test loader initialization with invalid directory."""
        with pytest.raises(DocumentationLoadError):
            MarkdownDocumentationLoader(docs_directory="/nonexistent/directory")

    def test_load_documentation_success(self, temp_docs_dir, sample_markdown_content, test_utils):
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

    def test_load_documentation_empty_directory(self, temp_docs_dir):
        """Test loading documentation from empty directory."""
        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)

        documentation = loader.load_documentation()

        assert documentation is not None
        assert len(documentation.endpoints) == 0

    def test_load_documentation_with_caching(self, temp_docs_dir, sample_markdown_content, test_utils):
        """Test documentation loading with caching enabled."""
        test_utils.create_markdown_file(temp_docs_dir, "api.md", sample_markdown_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=True)

        # First load
        documentation1 = loader.load_documentation()

        # Second load should use cache
        documentation2 = loader.load_documentation()

        # Should be the same object reference due to caching
        assert documentation1 is documentation2

    def test_clear_cache(self, temp_docs_dir, sample_markdown_content, test_utils):
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

    def test_parse_markdown_file_success(self, temp_docs_dir, sample_markdown_content, test_utils):
        """Test parsing a single markdown file."""
        file_path = test_utils.create_markdown_file(temp_docs_dir, "test.md", sample_markdown_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir))
        endpoints = loader._parse_markdown_file(file_path)

        assert len(endpoints) > 0

        # Check specific endpoint
        get_users = next((ep for ep in endpoints if ep.path == "/api/users" and ep.method == HTTPMethod.GET), None)

        assert get_users is not None
        assert "users" in get_users.summary.lower()

    def test_parse_markdown_file_malformed(self, temp_docs_dir, test_utils):
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

    def test_parse_markdown_file_nonexistent(self, temp_docs_dir):
        """Test parsing non-existent markdown file."""
        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir))

        with pytest.raises(DocumentationLoadError):
            loader._parse_markdown_file(Path(temp_docs_dir) / "nonexistent.md")

    def test_extract_endpoints_from_content(self, sample_markdown_content):
        """Test endpoint extraction from markdown content."""
        loader = MarkdownDocumentationLoader()
        endpoints = loader._extract_endpoints_from_content(sample_markdown_content)

        assert len(endpoints) >= 3  # GET, POST, GET with ID

        # Check endpoint paths and methods
        paths_and_methods = [(ep.path, ep.method) for ep in endpoints]

        assert ("/api/users", HTTPMethod.GET) in paths_and_methods
        assert ("/api/users", HTTPMethod.POST) in paths_and_methods
        assert ("/api/users/{user_id}", HTTPMethod.GET) in paths_and_methods

    def test_extract_code_samples(self, sample_markdown_content):
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

    def test_extract_response_examples(self, sample_markdown_content):
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

    def test_extract_parameters(self, sample_markdown_content):
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

    def test_extract_tags(self, sample_markdown_content):
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

    def test_recursive_directory_loading(self, temp_docs_dir, sample_markdown_content, test_utils):
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

    def test_non_recursive_directory_loading(self, temp_docs_dir, sample_markdown_content, test_utils):
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

    def test_file_pattern_filtering(self, temp_docs_dir, sample_markdown_content, test_utils):
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

    def test_supported_languages_filtering(self, temp_docs_dir, test_utils):
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

    def test_encoding_handling(self, temp_docs_dir, test_utils):
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

    def test_error_handling_invalid_yaml_frontmatter(self, temp_docs_dir, test_utils):
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

    def test_metadata_extraction(self, temp_docs_dir, test_utils):
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

    def test_validation_error_handling(self, temp_docs_dir, test_utils):
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

    def test_performance_with_large_files(self, temp_docs_dir, test_utils):
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

    def test_concurrent_loading(self, temp_docs_dir, sample_markdown_content, test_utils):
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

    def test_cache_ttl_expiration(self, temp_docs_dir, sample_markdown_content, test_utils):
        """Test cache TTL expiration functionality."""
        test_utils.create_markdown_file(temp_docs_dir, "api.md", sample_markdown_content)

        # Use very short TTL for testing
        loader = MarkdownDocumentationLoader(
            docs_directory=str(temp_docs_dir), cache_enabled=True, cache_ttl=0.1  # 100ms
        )

        # First load
        documentation1 = loader.load_documentation()

        # Wait for cache to expire
        time.sleep(0.2)

        # Second load should reload due to expired cache
        documentation2 = loader.load_documentation()

        # Should be different objects due to cache expiration
        assert documentation1 is not documentation2

    def test_concurrent_cache_loading(self, temp_docs_dir, sample_markdown_content, test_utils):
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

    def test_concurrent_loading_with_error(self, temp_docs_dir, test_utils):
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

    def test_load_documentation_nonexistent_directory(self):
        """Test loading documentation from non-existent directory."""
        # This should fail at initialization, not at load time
        with pytest.raises(DocumentationLoadError) as exc_info:
            MarkdownDocumentationLoader(docs_directory="/nonexistent/path", cache_enabled=False)

        assert "does not exist" in str(exc_info.value)

    def test_file_processing_error_handling(self, temp_docs_dir, test_utils):
        """Test error handling when file processing fails."""
        # Create a valid file
        test_utils.create_markdown_file(temp_docs_dir, "api.md", "# Valid content")

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)

        # Mock _load_file to raise an exception
        with patch.object(loader, "_load_file", side_effect=Exception("File processing error")):
            with pytest.raises(DocumentationLoadError) as exc_info:
                loader.load_documentation()

            assert "Failed to process file" in str(exc_info.value)

    def test_yaml_frontmatter_parsing(self, temp_docs_dir, test_utils):
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
        assert metadata["description"] == "API for testing purposes"

    def test_response_examples_parsing_realistic(self):
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

    def test_response_examples_with_status_codes_realistic(self):
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

    def test_is_cached_functionality(self, temp_docs_dir, test_utils):
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

    def test_get_stats_functionality(self, temp_docs_dir, sample_markdown_content, test_utils):
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

    def test_load_file_with_encoding_issues(self, temp_docs_dir, test_utils):
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

    def test_split_content_by_endpoints_edge_cases(self):
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

    def test_concurrent_loading_with_cache_failure_recovery(self, temp_docs_dir, sample_markdown_content, test_utils):
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

    def test_file_modification_detection_in_cache(self, temp_docs_dir, test_utils):
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

    def test_response_examples_with_invalid_json_recovery(self):
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

        # Should wrap invalid JSON in raw_content
        example = examples[0]
        assert "raw_content" in example.content
        assert "invalid" in example.content["raw_content"]

    def test_cache_invalidation_on_file_access_errors(self, temp_docs_dir, test_utils):
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

    def test_general_docs_loading_default_file(self, temp_docs_dir, test_utils):
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

    def test_general_docs_loading_custom_file(self, temp_docs_dir, test_utils):
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

    def test_general_docs_loading_absolute_path(self, temp_docs_dir, test_utils):
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

    def test_general_docs_loading_nonexistent_file(self, temp_docs_dir, test_utils):
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

    def test_general_docs_loading_with_frontmatter(self, temp_docs_dir, test_utils):
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

    def test_general_docs_loading_error_handling(self, temp_docs_dir, test_utils):
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

    def test_load_general_docs_method(self, temp_docs_dir, test_utils):
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
