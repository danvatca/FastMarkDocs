"""
Unit tests for the CodeSampleGenerator class.

Tests the code sample generation for different programming languages and HTTP methods.
"""

from typing import Any
from unittest.mock import Mock

import pytest

from fastmarkdocs.code_samples import CodeSampleGenerator
from fastmarkdocs.exceptions import CodeSampleGenerationError
from fastmarkdocs.types import CodeLanguage, EndpointDocumentation, HTTPMethod


class TestCodeSampleGenerator:
    """Test the CodeSampleGenerator class."""

    def test_initialization_default_config(self) -> None:
        """Test generator initialization with default configuration."""
        generator = CodeSampleGenerator()

        assert generator.base_url == "https://api.example.com"
        assert len(generator.server_urls) > 0
        assert CodeLanguage.CURL in generator.code_sample_languages
        assert CodeLanguage.PYTHON in generator.code_sample_languages

    def test_initialization_custom_config(self, code_generator_config: Any) -> None:
        """Test generator initialization with custom configuration."""
        generator = CodeSampleGenerator(**code_generator_config)

        assert generator.base_url == "https://api.example.com"
        assert "https://staging.example.com" in generator.server_urls
        assert "TestApp/1.0" in generator.custom_headers["User-Agent"]

    def test_generate_curl_sample_get(self) -> None:
        """Test generating cURL sample for GET request."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_curl_sample(endpoint)

        assert sample.language == CodeLanguage.CURL
        assert "curl -X GET" in sample.code
        assert "/api/users" in sample.code
        assert sample.title == "cURL Request"

    def test_generate_curl_sample_post_with_body(self) -> None:
        """Test generating cURL sample for POST request with request body."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.POST, summary="Create user")

        sample = generator.generate_curl_sample(endpoint, request_body={"name": "John", "email": "john@example.com"})

        assert sample.language == CodeLanguage.CURL
        assert "curl -X POST" in sample.code
        assert "Content-Type: application/json" in sample.code
        assert '"name": "John"' in sample.code

    def test_generate_python_sample_get(self) -> None:
        """Test generating Python sample for GET request."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_python_sample(endpoint)

        assert sample.language == CodeLanguage.PYTHON
        assert "import requests" in sample.code
        assert "requests.get" in sample.code
        assert "/api/users" in sample.code

    def test_generate_python_sample_post_with_body(self) -> None:
        """Test generating Python sample for POST request with request body."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.POST, summary="Create user")

        request_body = {"name": "John", "email": "john@example.com"}
        sample = generator.generate_python_sample(endpoint, request_body=request_body)

        assert sample.language == CodeLanguage.PYTHON
        assert "requests.post" in sample.code
        assert "json=" in sample.code
        assert "john@example.com" in sample.code

    def test_generate_javascript_sample_get(self) -> None:
        """Test generating JavaScript sample for GET request."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_javascript_sample(endpoint)

        assert sample.language == CodeLanguage.JAVASCRIPT
        assert "fetch(" in sample.code
        assert "/api/users" in sample.code
        assert "method: 'GET'" in sample.code

    def test_generate_javascript_sample_post_with_body(self) -> None:
        """Test generating JavaScript sample for POST request with request body."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.POST, summary="Create user")

        request_body = {"name": "John", "email": "john@example.com"}
        sample = generator.generate_javascript_sample(endpoint, request_body=request_body)

        assert sample.language == CodeLanguage.JAVASCRIPT
        assert "method: 'POST'" in sample.code
        assert "JSON.stringify(" in sample.code
        assert "john@example.com" in sample.code

    def test_generate_samples_for_endpoint(self) -> None:
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

    def test_generate_samples_with_path_parameters(self) -> None:
        """Test generating samples with path parameters."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users/{user_id}", method=HTTPMethod.GET, summary="Get user by ID")

        path_params = {"user_id": 123}
        sample = generator.generate_curl_sample(endpoint, path_params=path_params)

        assert "/api/users/123" in sample.code

    def test_generate_samples_with_query_parameters(self) -> None:
        """Test generating samples with query parameters."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        query_params = {"limit": 50, "offset": 0}
        sample = generator.generate_curl_sample(endpoint, query_params=query_params)

        assert "limit=50" in sample.code
        assert "offset=0" in sample.code

    def test_generate_samples_with_custom_headers(self) -> None:
        """Test generating samples with custom headers."""
        generator = CodeSampleGenerator(custom_headers={"Authorization": "Bearer token123", "X-API-Key": "key456"})

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_curl_sample(endpoint)

        assert "Authorization: Bearer token123" in sample.code
        assert "X-API-Key: key456" in sample.code

    def test_generate_samples_with_authentication(self) -> None:
        """Test generating samples with authentication schemes."""
        generator = CodeSampleGenerator(authentication_schemes=["bearer"])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_python_sample(endpoint)

        assert "Authorization" in sample.code or "Bearer" in sample.code

    def test_generate_typescript_sample(self) -> None:
        """Test generating TypeScript sample."""
        generator = CodeSampleGenerator(code_sample_languages=[CodeLanguage.TYPESCRIPT])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_typescript_sample(endpoint)

        assert sample.language == CodeLanguage.TYPESCRIPT
        assert "fetch(" in sample.code
        assert "Promise<" in sample.code or "async" in sample.code

    def test_generate_go_sample(self) -> None:
        """Test generating Go sample."""
        generator = CodeSampleGenerator(code_sample_languages=[CodeLanguage.GO])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_go_sample(endpoint)

        assert sample.language == CodeLanguage.GO
        assert "http.Get(" in sample.code or "http.NewRequest(" in sample.code
        assert "package main" in sample.code

    def test_generate_java_sample(self) -> None:
        """Test generating Java sample."""
        generator = CodeSampleGenerator(code_sample_languages=[CodeLanguage.JAVA])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_java_sample(endpoint)

        assert sample.language == CodeLanguage.JAVA
        assert "HttpClient" in sample.code or "HttpURLConnection" in sample.code

    def test_generate_php_sample(self) -> None:
        """Test generating PHP sample."""
        generator = CodeSampleGenerator(code_sample_languages=[CodeLanguage.PHP])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_php_sample(endpoint)

        assert sample.language == CodeLanguage.PHP
        assert "<?php" in sample.code
        assert "curl_init(" in sample.code or "file_get_contents(" in sample.code

    def test_generate_ruby_sample(self) -> None:
        """Test generating Ruby sample."""
        generator = CodeSampleGenerator(code_sample_languages=[CodeLanguage.RUBY])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_ruby_sample(endpoint)

        assert sample.language == CodeLanguage.RUBY
        assert "require" in sample.code
        assert "Net::HTTP" in sample.code or "HTTParty" in sample.code

    def test_generate_csharp_sample(self) -> None:
        """Test generating C# sample."""
        generator = CodeSampleGenerator(code_sample_languages=[CodeLanguage.CSHARP])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_csharp_sample(endpoint)

        assert sample.language == CodeLanguage.CSHARP
        assert "HttpClient" in sample.code
        assert "using" in sample.code

    def test_url_building_with_base_url(self) -> None:
        """Test URL building with different base URLs."""
        generator = CodeSampleGenerator(base_url="https://custom.api.com")

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_curl_sample(endpoint)

        assert "https://custom.api.com/api/users" in sample.code

    def test_url_building_with_path_parameters(self) -> None:
        """Test URL building with path parameters."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(
            path="/api/users/{user_id}/posts/{post_id}", method=HTTPMethod.GET, summary="Get user post"
        )

        path_params = {"user_id": 123, "post_id": 456}
        url = generator._build_url(endpoint.path, path_params=path_params)

        assert "/api/users/123/posts/456" in url

    def test_url_building_with_query_parameters(self) -> None:
        """Test URL building with query parameters."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        query_params = {"limit": 50, "sort": "name", "active": True}
        url = generator._build_url(endpoint.path, query_params=query_params)

        assert "limit=50" in url
        assert "sort=name" in url
        assert "active=true" in url.lower()

    def test_error_handling_unsupported_language(self) -> None:
        """Test error handling for unsupported languages."""
        generator = CodeSampleGenerator()

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        with pytest.raises(CodeSampleGenerationError):
            generator._generate_sample_for_language(endpoint, "unsupported_language")

    def test_error_handling_invalid_endpoint(self) -> None:
        """Test error handling for invalid endpoint data."""
        generator = CodeSampleGenerator()

        # Test with None endpoint
        with pytest.raises((CodeSampleGenerationError, AttributeError)):
            generator.generate_curl_sample(None)  # type: ignore

        # Test that EndpointDocumentation validation works
        with pytest.raises(ValueError):
            EndpointDocumentation(
                path="",
                method=HTTPMethod.GET,
                summary="Invalid",  # Empty path should raise ValueError
            )

        # Test with valid endpoint but invalid method string (should be caught by type validation)
        with pytest.raises(TypeError):
            EndpointDocumentation(
                path="/api/test",
                method="INVALID",  # type: ignore
                summary="Test",  # Invalid method should raise TypeError
            )

    def test_template_customization(self) -> None:
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

    def test_multiple_server_urls(self) -> None:
        """Test handling multiple server URLs."""
        generator = CodeSampleGenerator(server_urls=["https://api.example.com", "https://staging.example.com"])

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        samples = generator.generate_samples_for_endpoint(endpoint)

        # Should generate samples for the primary server URL
        curl_sample = next(s for s in samples if s.language == CodeLanguage.CURL)
        assert "https://api.example.com" in curl_sample.code

    def test_request_body_serialization(self) -> None:
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

    def test_header_handling(self) -> None:
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

    def test_performance_with_large_endpoints(self) -> None:
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

    def test_caching_behavior(self) -> None:
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

    def test_curl_with_api_key_authentication(self) -> None:
        """Test cURL generation with API key authentication scheme."""
        generator = CodeSampleGenerator(authentication_schemes=["api_key"])
        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_curl_sample(endpoint)

        assert "X-API-Key: YOUR_API_KEY_HERE" in sample.code

    def test_curl_with_basic_authentication(self) -> None:
        """Test cURL generation with basic authentication scheme."""
        generator = CodeSampleGenerator(authentication_schemes=["basic"])
        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_curl_sample(endpoint)

        assert "Basic YOUR_CREDENTIALS_HERE" in sample.code

    def test_curl_with_string_request_body(self) -> None:
        """Test cURL generation with string request body."""
        generator = CodeSampleGenerator()
        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.POST, summary="Create user")

        sample = generator.generate_curl_sample(endpoint, request_body="plain text body")

        assert "-d 'plain text body'" in sample.code

    def test_python_with_custom_template(self) -> None:
        """Test Python generation with custom template."""
        custom_template = "# Custom Python template\nprint('Hello {method} {url}')"
        generator = CodeSampleGenerator(custom_templates={CodeLanguage.PYTHON: custom_template})
        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_python_sample(endpoint)

        assert "Custom Python template" in sample.code
        assert "Hello GET" in sample.code

    def test_python_with_string_request_body(self) -> None:
        """Test Python generation with string request body."""
        generator = CodeSampleGenerator()
        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.POST, summary="Create user")

        sample = generator.generate_python_sample(endpoint, request_body="plain text")

        assert 'data="plain text"' in sample.code

    def test_python_with_api_key_authentication(self) -> None:
        """Test Python generation with API key authentication."""
        generator = CodeSampleGenerator(authentication_schemes=["api_key"])
        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_python_sample(endpoint)

        assert "X-API-Key" in sample.code and "YOUR_API_KEY_HERE" in sample.code

    def test_python_with_basic_authentication(self) -> None:
        """Test Python generation with basic authentication."""
        generator = CodeSampleGenerator(authentication_schemes=["basic"])
        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        sample = generator.generate_python_sample(endpoint)

        assert "Basic YOUR_CREDENTIALS_HERE" in sample.code

    def test_javascript_with_string_request_body(self) -> None:
        """Test JavaScript generation with string request body."""
        generator = CodeSampleGenerator()
        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.POST, summary="Create user")

        sample = generator.generate_javascript_sample(endpoint, request_body="plain text")

        assert 'body: "plain text"' in sample.code

    def test_build_url_with_server_urls(self) -> None:
        """Test URL building with server URLs."""
        generator = CodeSampleGenerator(
            base_url="https://api.example.com",
            server_urls=["https://server1.example.com", "https://server2.example.com"],
        )

        url = generator._build_url("/test/path")

        assert url == "https://server1.example.com/test/path"

    def test_build_url_with_boolean_query_params(self) -> None:
        """Test URL building with boolean query parameters."""
        generator = CodeSampleGenerator()

        url = generator._build_url("/test", query_params={"active": True, "deleted": False})

        assert "active=true" in url
        assert "deleted=false" in url

    def test_custom_template_usage(self) -> None:
        """Test code sample generation using custom templates."""
        custom_template = """
# Custom template for {method} {path}
# Base URL: {base_url}
# Full URL: {url}
# Summary: {summary}

Custom code here for {method_lower} request
"""

        generator = CodeSampleGenerator(custom_templates={CodeLanguage.PYTHON: custom_template})

        endpoint = EndpointDocumentation(
            path="/api/test",
            method=HTTPMethod.GET,
            summary="Test endpoint for custom template",
            description="Test description",
            code_samples=[],
            response_examples=[],
            parameters=[],
        )

        sample = generator.generate_python_sample(endpoint)

        assert "Custom template" in sample.code
        assert "GET /api/test" in sample.code
        assert "https://api.example.com/api/test" in sample.code
        assert "Test endpoint for custom template" in sample.code
        assert "get request" in sample.code

    def test_custom_template_with_missing_variables(self) -> None:
        """Test custom template error handling when template variables are missing."""
        # Template with undefined variable
        bad_template = "Code for {undefined_variable}"

        generator = CodeSampleGenerator(custom_templates={CodeLanguage.PYTHON: bad_template})

        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        with pytest.raises(CodeSampleGenerationError) as exc_info:
            generator.generate_python_sample(endpoint)

        assert "Template variable not found" in str(exc_info.value)
        assert "undefined_variable" in str(exc_info.value)

    def test_unsupported_language_error_handling(self) -> None:
        """Test error handling for unsupported languages."""
        generator = CodeSampleGenerator()
        endpoint = EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")

        with pytest.raises(CodeSampleGenerationError) as exc_info:
            generator._generate_sample_for_language(endpoint, "unsupported_language")

        assert "Unsupported language: unsupported_language" in str(exc_info.value)

    def test_generate_samples_with_complex_error_scenarios(self) -> None:
        """Test error handling in generate_samples_for_endpoint with complex scenarios."""
        generator = CodeSampleGenerator()

        # Create an endpoint that will cause issues during generation
        problematic_endpoint = Mock()
        problematic_endpoint.method = HTTPMethod.GET
        problematic_endpoint.path = "/test"

        # Mock one of the generation methods to raise an exception
        def failing_curl_generation(*args, **kwargs):
            raise Exception("Curl generation failed")

        generator.generate_curl_sample = failing_curl_generation

        with pytest.raises(CodeSampleGenerationError) as exc_info:
            generator.generate_samples_for_endpoint(problematic_endpoint)

        assert "Failed to generate sample" in str(exc_info.value)
        assert "GET:/test" in str(exc_info.value)

    def test_endpoint_info_extraction_for_error_messages(self) -> None:
        """Test that endpoint info is properly extracted for error messages."""
        generator = CodeSampleGenerator()

        # Test with None endpoint
        with pytest.raises(CodeSampleGenerationError) as exc_info:
            generator.generate_samples_for_endpoint(None)  # type: ignore

        # Should handle None endpoint gracefully
        assert "unknown" in str(exc_info.value)
