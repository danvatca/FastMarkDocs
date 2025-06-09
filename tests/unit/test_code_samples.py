"""
Unit tests for the CodeSampleGenerator class.

Tests the code sample generation for different programming languages and HTTP methods.
"""

import pytest

from fastmarkdocs.code_samples import CodeSampleGenerator
from fastmarkdocs.exceptions import CodeSampleGenerationError
from fastmarkdocs.types import CodeLanguage, EndpointDocumentation, HTTPMethod


class TestCodeSampleGenerator:
    """Test the CodeSampleGenerator class."""

    def test_initialization_default_config(self):
        """Test generator initialization with default configuration."""
        generator = CodeSampleGenerator()

        assert generator.base_url == "https://api.example.com"
        assert len(generator.server_urls) > 0
        assert CodeLanguage.CURL in generator.code_sample_languages
        assert CodeLanguage.PYTHON in generator.code_sample_languages

    def test_initialization_custom_config(self, code_generator_config):
        """Test generator initialization with custom configuration."""
        generator = CodeSampleGenerator(**code_generator_config)

        assert generator.base_url == "https://api.example.com"
        assert "https://staging.example.com" in generator.server_urls
        assert "TestApp/1.0" in generator.custom_headers["User-Agent"]

    def test_generate_curl_sample_get(self):
        """Test generating cURL sample for GET request."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_curl_sample(endpoint)

        assert sample.language == CodeLanguage.CURL
        assert "curl -X GET" in sample.code
        assert "/api/users" in sample.code
        assert sample.title == "cURL Request"

    def test_generate_curl_sample_post_with_body(self):
        """Test generating cURL sample for POST request with request body."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.POST, summary="Create user")

        sample = generator.generate_curl_sample(endpoint, request_body={"name": "John", "email": "john@example.com"})

        assert sample.language == CodeLanguage.CURL
        assert "curl -X POST" in sample.code
        assert "Content-Type: application/json" in sample.code
        assert '"name": "John"' in sample.code

    def test_generate_python_sample_get(self):
        """Test generating Python sample for GET request."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_python_sample(endpoint)

        assert sample.language == CodeLanguage.PYTHON
        assert "import requests" in sample.code
        assert "requests.get" in sample.code
        assert "/api/users" in sample.code

    def test_generate_python_sample_post_with_body(self):
        """Test generating Python sample for POST request with request body."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.POST, summary="Create user")

        request_body = {"name": "John", "email": "john@example.com"}
        sample = generator.generate_python_sample(endpoint, request_body=request_body)

        assert sample.language == CodeLanguage.PYTHON
        assert "requests.post" in sample.code
        assert "json=" in sample.code
        assert "john@example.com" in sample.code

    def test_generate_javascript_sample_get(self):
        """Test generating JavaScript sample for GET request."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_javascript_sample(endpoint)

        assert sample.language == CodeLanguage.JAVASCRIPT
        assert "fetch(" in sample.code
        assert "/api/users" in sample.code
        assert "method: 'GET'" in sample.code

    def test_generate_javascript_sample_post_with_body(self):
        """Test generating JavaScript sample for POST request with request body."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.POST, summary="Create user")

        request_body = {"name": "John", "email": "john@example.com"}
        sample = generator.generate_javascript_sample(endpoint, request_body=request_body)

        assert sample.language == CodeLanguage.JAVASCRIPT
        assert "method: 'POST'" in sample.code
        assert "JSON.stringify(" in sample.code
        assert "john@example.com" in sample.code

    def test_generate_samples_for_endpoint(self):
        """Test generating all configured samples for an endpoint."""
        generator = CodeSampleGenerator(
            code_sample_languages=[CodeLanguage.CURL, CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT]
        )

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        samples = generator.generate_samples_for_endpoint(endpoint)

        assert len(samples) == 3
        languages = [sample.language for sample in samples]
        assert CodeLanguage.CURL in languages
        assert CodeLanguage.PYTHON in languages
        assert CodeLanguage.JAVASCRIPT in languages

    def test_generate_samples_with_path_parameters(self):
        """Test generating samples with path parameters."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users/{user_id}", method=HTTPMethod.GET, summary="Get user by ID")

        path_params = {"user_id": 123}
        sample = generator.generate_curl_sample(endpoint, path_params=path_params)

        assert "/api/users/123" in sample.code

    def test_generate_samples_with_query_parameters(self):
        """Test generating samples with query parameters."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        query_params = {"limit": 50, "offset": 0}
        sample = generator.generate_curl_sample(endpoint, query_params=query_params)

        assert "limit=50" in sample.code
        assert "offset=0" in sample.code

    def test_generate_samples_with_custom_headers(self):
        """Test generating samples with custom headers."""
        generator = CodeSampleGenerator(custom_headers={"Authorization": "Bearer token123", "X-API-Key": "key456"})

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_curl_sample(endpoint)

        assert "Authorization: Bearer token123" in sample.code
        assert "X-API-Key: key456" in sample.code

    def test_generate_samples_with_authentication(self):
        """Test generating samples with authentication schemes."""
        generator = CodeSampleGenerator(authentication_schemes=["bearer"])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_python_sample(endpoint)

        assert "Authorization" in sample.code or "Bearer" in sample.code

    def test_generate_typescript_sample(self):
        """Test generating TypeScript sample."""
        generator = CodeSampleGenerator(code_sample_languages=[CodeLanguage.TYPESCRIPT])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_typescript_sample(endpoint)

        assert sample.language == CodeLanguage.TYPESCRIPT
        assert "fetch(" in sample.code
        assert "Promise<" in sample.code or "async" in sample.code

    def test_generate_go_sample(self):
        """Test generating Go sample."""
        generator = CodeSampleGenerator(code_sample_languages=[CodeLanguage.GO])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_go_sample(endpoint)

        assert sample.language == CodeLanguage.GO
        assert "http.Get(" in sample.code or "http.NewRequest(" in sample.code
        assert "package main" in sample.code

    def test_generate_java_sample(self):
        """Test generating Java sample."""
        generator = CodeSampleGenerator(code_sample_languages=[CodeLanguage.JAVA])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_java_sample(endpoint)

        assert sample.language == CodeLanguage.JAVA
        assert "HttpClient" in sample.code or "HttpURLConnection" in sample.code

    def test_generate_php_sample(self):
        """Test generating PHP sample."""
        generator = CodeSampleGenerator(code_sample_languages=[CodeLanguage.PHP])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_php_sample(endpoint)

        assert sample.language == CodeLanguage.PHP
        assert "<?php" in sample.code
        assert "curl_init(" in sample.code or "file_get_contents(" in sample.code

    def test_generate_ruby_sample(self):
        """Test generating Ruby sample."""
        generator = CodeSampleGenerator(code_sample_languages=[CodeLanguage.RUBY])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_ruby_sample(endpoint)

        assert sample.language == CodeLanguage.RUBY
        assert "require" in sample.code
        assert "Net::HTTP" in sample.code or "HTTParty" in sample.code

    def test_generate_csharp_sample(self):
        """Test generating C# sample."""
        generator = CodeSampleGenerator(code_sample_languages=[CodeLanguage.CSHARP])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_csharp_sample(endpoint)

        assert sample.language == CodeLanguage.CSHARP
        assert "HttpClient" in sample.code
        assert "using" in sample.code

    def test_url_building_with_base_url(self):
        """Test URL building with different base URLs."""
        generator = CodeSampleGenerator(base_url="https://custom.api.com")

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_curl_sample(endpoint)

        assert "https://custom.api.com/api/users" in sample.code

    def test_url_building_with_path_parameters(self):
        """Test URL building with path parameters."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(
            path="/api/users/{user_id}/posts/{post_id}", method=HTTPMethod.GET, summary="Get user post"
        )

        path_params = {"user_id": 123, "post_id": 456}
        url = generator._build_url(endpoint.path, path_params=path_params)

        assert "/api/users/123/posts/456" in url

    def test_url_building_with_query_parameters(self):
        """Test URL building with query parameters."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        query_params = {"limit": 50, "sort": "name", "active": True}
        url = generator._build_url(endpoint.path, query_params=query_params)

        assert "limit=50" in url
        assert "sort=name" in url
        assert "active=true" in url.lower()

    def test_error_handling_unsupported_language(self):
        """Test error handling for unsupported languages."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        with pytest.raises(CodeSampleGenerationError):
            generator._generate_sample_for_language(endpoint, "unsupported_language")

    def test_error_handling_invalid_endpoint(self):
        """Test error handling for invalid endpoint data."""
        generator = CodeSampleGenerator()

        # Test with None endpoint
        with pytest.raises((CodeSampleGenerationError, AttributeError)):
            generator.generate_curl_sample(None)

        # Test that EndpointDocumentation validation works
        with pytest.raises(ValueError):
            EndpointDocumentation(
                path="", method=HTTPMethod.GET, summary="Invalid"  # Empty path should raise ValueError
            )

        # Test with valid endpoint but invalid method string (should be caught by type validation)
        with pytest.raises(TypeError):
            EndpointDocumentation(
                path="/api/test", method="INVALID", summary="Test"  # Invalid method should raise TypeError
            )

    def test_template_customization(self):
        """Test customization of code generation templates."""
        custom_templates = {
            CodeLanguage.PYTHON: """
import requests

# Custom template for {method} {path}
response = requests.{method_lower}('{url}')
print(f'Status: {{response.status_code}}')
"""
        }

        generator = CodeSampleGenerator(custom_templates=custom_templates)

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_python_sample(endpoint)

        assert "Custom template for GET /api/users" in sample.code
        assert "Status: {response.status_code}" in sample.code

    def test_multiple_server_urls(self):
        """Test handling multiple server URLs."""
        generator = CodeSampleGenerator(server_urls=["https://api.example.com", "https://staging.example.com"])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        samples = generator.generate_samples_for_endpoint(endpoint)

        # Should generate samples for the primary server URL
        curl_sample = next(s for s in samples if s.language == CodeLanguage.CURL)
        assert "https://api.example.com" in curl_sample.code

    def test_request_body_serialization(self):
        """Test proper serialization of different request body types."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.POST, summary="Create user")

        # Test with dictionary
        dict_body = {"name": "John", "age": 30, "active": True}
        sample = generator.generate_python_sample(endpoint, request_body=dict_body)
        assert "json=" in sample.code

        # Test with list
        list_body = [{"name": "John"}, {"name": "Jane"}]
        sample = generator.generate_python_sample(endpoint, request_body=list_body)
        assert "json=" in sample.code

        # Test with string (should be treated as raw data)
        string_body = '{"name": "John"}'
        sample = generator.generate_python_sample(endpoint, request_body=string_body)
        assert "data=" in sample.code

    def test_header_handling(self):
        """Test proper handling of various header types."""
        generator = CodeSampleGenerator(
            custom_headers={
                "Authorization": "Bearer {token}",
                "Content-Type": "application/json",
                "X-Custom-Header": "custom-value",
            }
        )

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.POST, summary="Create user")

        sample = generator.generate_curl_sample(endpoint)

        assert "Authorization: Bearer {token}" in sample.code
        assert "Content-Type: application/json" in sample.code
        assert "X-Custom-Header: custom-value" in sample.code

    def test_performance_with_large_endpoints(self):
        """Test performance with large number of endpoints."""
        generator = CodeSampleGenerator()

        endpoints = []
        for i in range(100):
            endpoint = EndpointDocumentation(path=f"/api/endpoint{i}", method=HTTPMethod.GET, summary=f"Endpoint {i}")
            endpoints.append(endpoint)

        # Should handle large number of endpoints efficiently
        all_samples = []
        for endpoint in endpoints:
            samples = generator.generate_samples_for_endpoint(endpoint)
            all_samples.extend(samples)

        assert len(all_samples) == len(endpoints) * len(generator.code_sample_languages)

    def test_caching_behavior(self):
        """Test caching behavior for generated samples."""
        generator = CodeSampleGenerator(cache_enabled=True)

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        # Generate samples twice
        samples1 = generator.generate_samples_for_endpoint(endpoint)
        samples2 = generator.generate_samples_for_endpoint(endpoint)

        # Should return the same objects if caching is enabled
        assert len(samples1) == len(samples2)
        for s1, s2 in zip(samples1, samples2):
            assert s1.code == s2.code
            assert s1.language == s2.language
