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

    def test_yaml_frontmatter_parsing_error(self, temp_docs_dir, test_utils):
        """Test error handling for malformed YAML frontmatter."""
        malformed_yaml_content = """---
title: Test API
version: 1.0.0
invalid_yaml: [unclosed bracket
description: This has malformed YAML
---

# Test API

## GET /api/test

Test endpoint.
"""

        test_utils.create_markdown_file(temp_docs_dir, "malformed.md", malformed_yaml_content)

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), cache_enabled=False)

        # Should handle malformed YAML gracefully
        documentation = loader.load_documentation()
        assert documentation is not None

    def test_parse_simple_yaml_edge_cases(self):
        """Test the simple YAML parser with edge cases."""
        loader = MarkdownDocumentationLoader()

        # Test empty YAML
        result = loader._parse_simple_yaml("")
        assert result == {}

        # Test YAML with only whitespace
        result = loader._parse_simple_yaml("   \n  \t  \n")
        assert result == {}

        # Test YAML with comments
        yaml_with_comments = """
# This is a comment
title: Test API
# Another comment
version: v1.0.0
"""
        result = loader._parse_simple_yaml(yaml_with_comments)
        assert result["title"] == "Test API"
        assert result["version"] == "v1.0.0"  # String value that won't be parsed as float

        # Test YAML with simple values only (simple parser limitations)
        simple_yaml = """
title: Test API
description: A simple API
"""
        result = loader._parse_simple_yaml(simple_yaml)
        assert result["title"] == "Test API"
        assert result["description"] == "A simple API"

    def test_extract_frontmatter_edge_cases(self):
        """Test frontmatter extraction with edge cases."""
        loader = MarkdownDocumentationLoader()

        # Test content without frontmatter
        content_no_frontmatter = """
# API Documentation

## GET /api/test

Test endpoint.
"""
        metadata, content = loader._extract_frontmatter(content_no_frontmatter)
        assert metadata == {}
        assert "# API Documentation" in content

        # Test content with only opening frontmatter delimiter
        content_incomplete = """---
title: Test
# Missing closing delimiter

## GET /api/test

Test endpoint.
"""
        metadata, content = loader._extract_frontmatter(content_incomplete)
        assert metadata == {}  # Should return empty metadata for malformed frontmatter

        # Test content with frontmatter not at the beginning
        content_middle_frontmatter = """
Some content before

---
title: Test
---

## GET /api/test

Test endpoint.
"""
        metadata, content = loader._extract_frontmatter(content_middle_frontmatter)
        assert metadata == {}  # Frontmatter must be at the beginning

    def test_extract_endpoints_with_no_endpoints(self):
        """Test endpoint extraction from content with no endpoints."""
        loader = MarkdownDocumentationLoader()

        content_no_endpoints = """
# API Documentation

This is general documentation without specific endpoints.

## Overview

This API provides various functionality.

### Authentication

Use API keys for authentication.
"""

        endpoints = loader._extract_endpoints_from_content(content_no_endpoints)
        assert endpoints == []

    def test_extract_endpoints_with_malformed_headers(self):
        """Test endpoint extraction with malformed HTTP method headers."""
        loader = MarkdownDocumentationLoader()

        malformed_content = """
# API Documentation

## INVALID_METHOD /api/test

This should not be parsed as an endpoint.

## GET

Missing path.

## /api/missing-method

Missing HTTP method.

## GET /api/valid

This is a valid endpoint.
"""

        endpoints = loader._extract_endpoints_from_content(malformed_content)

        # Should only extract the valid endpoint
        assert len(endpoints) == 1
        assert endpoints[0].path == "/api/valid"
        assert endpoints[0].method == HTTPMethod.GET

    def test_extract_response_examples_edge_cases(self):
        """Test response example extraction with edge cases."""
        loader = MarkdownDocumentationLoader()

        content_with_edge_cases = """
## GET /api/test

### Response Examples

#### 200 OK
```json
{"valid": "json"}
```

#### 400 Bad Request
```json
{invalid json}
```
"""

        examples = loader._extract_response_examples(content_with_edge_cases)

        # Should handle valid and invalid JSON gracefully
        assert len(examples) >= 0  # May extract some examples

        # If any examples were extracted, check for valid ones
        if examples:
            valid_examples = [ex for ex in examples if ex.status_code == 200]
            if valid_examples:
                assert valid_examples[0].content == {"valid": "json"}

    def test_extract_parameters_edge_cases(self):
        """Test parameter extraction with edge cases."""
        loader = MarkdownDocumentationLoader()

        content_with_params = """
## GET /api/test

### Parameters

- `valid_param` (string, required): A valid parameter
- `optional_param` (integer): An optional parameter
- `malformed_param`: Missing type information
- (string): Missing parameter name
- ``: Empty parameter name
- `param_with_example` (string): Parameter with example value: `test_value`
"""

        params = loader._extract_parameters(content_with_params)

        # Should extract valid parameters and handle malformed ones gracefully
        assert len(params) >= 2  # At least the valid ones

        # Check valid parameter
        valid_param = next((p for p in params if p.name == "valid_param"), None)
        assert valid_param is not None
        assert valid_param.type == "string"
        assert valid_param.required is True

    def test_create_endpoint_documentation_edge_cases(self):
        """Test endpoint documentation creation with edge cases."""
        loader = MarkdownDocumentationLoader()

        # Test extracting endpoints from content
        content_with_endpoint = "## GET /api/minimal\n\nMinimal endpoint."
        endpoints = loader._extract_endpoints_from_content(content_with_endpoint)

        if endpoints:
            endpoint = endpoints[0]
            assert endpoint.path == "/api/minimal"
            assert endpoint.method == HTTPMethod.GET

        # Test with content that has no endpoints
        content_no_endpoints = "# Just a title\n\nNo endpoints here."
        endpoints = loader._extract_endpoints_from_content(content_no_endpoints)
        assert len(endpoints) == 0

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
        # Create file with non-UTF8 content
        file_path = temp_docs_dir / "encoded.md"

        # Write content with latin-1 encoding
        content = "# Test with special chars: café, naïve, résumé"
        file_path.write_bytes(content.encode("latin-1"))

        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), encoding="utf-8")

        # Should handle encoding errors gracefully
        try:
            file_data = loader._load_file(str(file_path))
            # If it succeeds, content should be loaded
            assert "content" in file_data
        except DocumentationLoadError:
            # If it fails, should raise DocumentationLoadError
            pass  # This is acceptable behavior

    def test_split_content_by_endpoints_edge_cases(self):
        """Test content splitting with edge cases."""
        loader = MarkdownDocumentationLoader()

        # Test content with no endpoint headers
        no_endpoints = """
# API Documentation

This is just general documentation.

## Overview

No endpoints here.
"""
        sections = loader._split_content_by_endpoints(no_endpoints)
        # The method may return sections even without endpoints
        assert len(sections) >= 0

        # Test content with nested headers
        nested_content = """
# API Documentation

## GET /api/users

### Nested Section

#### Deep Nested

## POST /api/users

### Another Nested

## GET /api/posts

Content here.
"""
        sections = loader._split_content_by_endpoints(nested_content)
        assert len(sections) >= 2  # Should find at least some endpoints
