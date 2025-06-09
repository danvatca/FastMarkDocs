"""
Unit tests for the OpenAPIEnhancer class.

Tests the OpenAPI schema enhancement functionality with markdown documentation.
"""

import copy

import pytest

from fastmarkdocs.exceptions import OpenAPIEnhancementError
from fastmarkdocs.openapi_enhancer import OpenAPIEnhancer, enhance_openapi_with_docs
from fastmarkdocs.types import (
    CodeLanguage,
    CodeSample,
    DocumentationData,
    EndpointDocumentation,
    HTTPMethod,
    ResponseExample,
)


class TestOpenAPIEnhancer:
    """Test the OpenAPIEnhancer class."""

    def test_initialization_default_config(self):
        """Test enhancer initialization with default configuration."""
        enhancer = OpenAPIEnhancer()

        assert enhancer.include_code_samples is True
        assert enhancer.include_response_examples is True
        assert enhancer.base_url == "https://api.example.com"
        assert CodeLanguage.CURL in enhancer.code_sample_languages

    def test_initialization_custom_config(self, openapi_enhancement_config):
        """Test enhancer initialization with custom configuration."""
        enhancer = OpenAPIEnhancer(**openapi_enhancement_config)

        assert enhancer.include_code_samples is True
        assert enhancer.include_response_examples is True
        assert enhancer.base_url == "https://api.example.com"
        assert "Authorization" in enhancer.custom_headers

    def test_enhance_openapi_schema_basic(self, sample_openapi_schema):
        """Test basic OpenAPI schema enhancement."""
        documentation_data = DocumentationData(
            endpoints=[
                EndpointDocumentation(
                    path="/api/users",
                    method=HTTPMethod.GET,
                    summary="List users",
                    description="Retrieve a list of users from the system",
                    code_samples=[
                        CodeSample(
                            language=CodeLanguage.CURL,
                            code='curl -X GET "https://api.example.com/api/users"',
                            title="cURL Request",
                        )
                    ],
                )
            ],
            metadata={},
        )

        enhancer = OpenAPIEnhancer()
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        assert enhanced_schema is not None
        assert "paths" in enhanced_schema
        assert "/api/users" in enhanced_schema["paths"]

        # Check that code samples were added
        get_operation = enhanced_schema["paths"]["/api/users"]["get"]
        assert "x-codeSamples" in get_operation
        assert len(get_operation["x-codeSamples"]) > 0

    def test_enhance_openapi_schema_with_response_examples(self, sample_openapi_schema):
        """Test OpenAPI schema enhancement with response examples."""
        documentation_data = DocumentationData(
            endpoints=[
                EndpointDocumentation(
                    path="/api/users",
                    method=HTTPMethod.GET,
                    summary="List users",
                    response_examples=[
                        ResponseExample(
                            status_code=200,
                            description="Successful response",
                            content=[{"id": 1, "name": "John", "email": "john@example.com"}],
                            headers={"Content-Type": "application/json"},
                        )
                    ],
                )
            ],
            metadata={},
        )

        enhancer = OpenAPIEnhancer(include_response_examples=True)
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        get_operation = enhanced_schema["paths"]["/api/users"]["get"]
        assert "responses" in get_operation
        assert "200" in get_operation["responses"]

        response_200 = get_operation["responses"]["200"]
        assert "content" in response_200
        assert "application/json" in response_200["content"]
        assert "examples" in response_200["content"]["application/json"]

    def test_enhance_openapi_schema_preserve_existing(self, sample_openapi_schema):
        """Test that existing OpenAPI schema content is preserved."""
        original_schema = copy.deepcopy(sample_openapi_schema)

        documentation_data = DocumentationData(endpoints=[], metadata={})

        enhancer = OpenAPIEnhancer()
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        # Original content should be preserved
        assert enhanced_schema["info"]["title"] == original_schema["info"]["title"]
        assert enhanced_schema["info"]["version"] == original_schema["info"]["version"]
        assert enhanced_schema["servers"] == original_schema["servers"]

    def test_enhance_openapi_schema_no_matching_endpoints(self, sample_openapi_schema):
        """Test enhancement when documentation has no matching endpoints."""
        documentation_data = DocumentationData(
            endpoints=[
                EndpointDocumentation(path="/api/nonexistent", method=HTTPMethod.GET, summary="Non-existent endpoint")
            ],
            metadata={},
        )

        enhancer = OpenAPIEnhancer()
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        # Schema should be unchanged for non-matching endpoints
        assert enhanced_schema == sample_openapi_schema

    def test_add_code_samples_to_operation(self):
        """Test adding code samples to an OpenAPI operation."""
        operation = {"summary": "List users", "responses": {"200": {"description": "Success"}}}

        code_samples = [
            CodeSample(
                language=CodeLanguage.CURL, code='curl -X GET "https://api.example.com/api/users"', title="cURL Request"
            ),
            CodeSample(
                language=CodeLanguage.PYTHON,
                code='import requests\nresponse = requests.get("/api/users")',
                title="Python Request",
            ),
        ]

        enhancer = OpenAPIEnhancer()
        enhancer._add_code_samples_to_operation(operation, code_samples)

        assert "x-codeSamples" in operation
        assert len(operation["x-codeSamples"]) == 2

        # Check structure of code samples
        curl_sample = next(s for s in operation["x-codeSamples"] if s["lang"] == "curl")
        python_sample = next(s for s in operation["x-codeSamples"] if s["lang"] == "python")

        assert "source" in curl_sample
        assert "label" in curl_sample
        assert "source" in python_sample
        assert "label" in python_sample

    def test_add_response_examples_to_operation(self):
        """Test adding response examples to an OpenAPI operation."""
        operation = {
            "summary": "List users",
            "responses": {
                "200": {"description": "Success", "content": {"application/json": {"schema": {"type": "array"}}}}
            },
        }

        response_examples = [
            ResponseExample(
                status_code=200,
                description="Successful response",
                content=[{"id": 1, "name": "John"}],
                headers={"Content-Type": "application/json"},
            )
        ]

        enhancer = OpenAPIEnhancer()
        enhancer._add_response_examples_to_operation(operation, response_examples)

        response_200 = operation["responses"]["200"]
        assert "content" in response_200
        assert "application/json" in response_200["content"]
        assert "examples" in response_200["content"]["application/json"]

        examples = response_200["content"]["application/json"]["examples"]
        assert "example_200" in examples
        assert examples["example_200"]["value"] == [{"id": 1, "name": "John"}]

    def test_merge_response_examples_with_existing(self):
        """Test merging response examples with existing OpenAPI responses."""
        operation = {
            "responses": {
                "200": {
                    "description": "Existing success response",
                    "content": {
                        "application/json": {
                            "schema": {"type": "array"},
                            "examples": {
                                "existing_example": {
                                    "summary": "Existing example",
                                    "value": [{"id": 2, "name": "Jane"}],
                                }
                            },
                        }
                    },
                }
            }
        }

        response_examples = [
            ResponseExample(status_code=200, description="New response example", content=[{"id": 1, "name": "John"}])
        ]

        enhancer = OpenAPIEnhancer()
        enhancer._add_response_examples_to_operation(operation, response_examples)

        examples = operation["responses"]["200"]["content"]["application/json"]["examples"]

        # Both existing and new examples should be present
        assert "existing_example" in examples
        assert "example_200" in examples
        assert examples["existing_example"]["value"] == [{"id": 2, "name": "Jane"}]
        assert examples["example_200"]["value"] == [{"id": 1, "name": "John"}]

    def test_enhance_operation_description(self):
        """Test enhancing operation descriptions."""
        operation = {"summary": "List users", "description": "Basic description"}

        endpoint_doc = EndpointDocumentation(
            path="/api/users",
            method=HTTPMethod.GET,
            summary="List users",
            description="Enhanced description with **markdown** formatting",
        )

        enhancer = OpenAPIEnhancer()
        enhancer._enhance_operation_description(operation, endpoint_doc)

        assert operation["description"] == "Enhanced description with **markdown** formatting"

    def test_path_matching_exact(self):
        """Test exact path matching between OpenAPI and documentation."""
        enhancer = OpenAPIEnhancer()

        assert enhancer._paths_match("/api/users", "/api/users") is True
        assert enhancer._paths_match("/api/users", "/api/posts") is False

    def test_path_matching_with_parameters(self):
        """Test path matching with parameters."""
        enhancer = OpenAPIEnhancer()

        # OpenAPI style parameters vs documentation style
        assert enhancer._paths_match("/api/users/{user_id}", "/api/users/{user_id}") is True
        assert enhancer._paths_match("/api/users/{id}", "/api/users/{user_id}") is True
        assert enhancer._paths_match("/api/users/{user_id}", "/api/users/123") is False

    def test_method_matching(self):
        """Test HTTP method matching."""
        enhancer = OpenAPIEnhancer()

        assert enhancer._methods_match("get", HTTPMethod.GET) is True
        assert enhancer._methods_match("GET", HTTPMethod.GET) is True
        assert enhancer._methods_match("post", HTTPMethod.POST) is True
        assert enhancer._methods_match("get", HTTPMethod.POST) is False

    def test_error_handling_invalid_schema(self):
        """Test error handling with invalid OpenAPI schema."""
        invalid_schema = {"invalid": "schema"}

        documentation_data = DocumentationData(endpoints=[], metadata={})

        enhancer = OpenAPIEnhancer()

        with pytest.raises(OpenAPIEnhancementError):
            enhancer.enhance_openapi_schema(invalid_schema, documentation_data)

    def test_error_handling_none_inputs(self):
        """Test error handling with None inputs."""
        enhancer = OpenAPIEnhancer()

        with pytest.raises((OpenAPIEnhancementError, TypeError)):
            enhancer.enhance_openapi_schema(None, None)

    def test_disable_code_samples(self, sample_openapi_schema):
        """Test disabling code sample enhancement."""
        documentation_data = DocumentationData(
            endpoints=[
                EndpointDocumentation(
                    path="/api/users",
                    method=HTTPMethod.GET,
                    summary="List users",
                    code_samples=[
                        CodeSample(language=CodeLanguage.CURL, code='curl -X GET "https://api.example.com/api/users"')
                    ],
                )
            ],
            metadata={},
        )

        enhancer = OpenAPIEnhancer(include_code_samples=False)
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        get_operation = enhanced_schema["paths"]["/api/users"]["get"]
        assert "x-codeSamples" not in get_operation

    def test_disable_response_examples(self, sample_openapi_schema):
        """Test disabling response example enhancement."""
        documentation_data = DocumentationData(
            endpoints=[
                EndpointDocumentation(
                    path="/api/users",
                    method=HTTPMethod.GET,
                    summary="List users",
                    response_examples=[
                        ResponseExample(status_code=200, description="Success", content=[{"id": 1, "name": "John"}])
                    ],
                )
            ],
            metadata={},
        )

        enhancer = OpenAPIEnhancer(include_response_examples=False)
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        # Response examples should not be added
        get_operation = enhanced_schema["paths"]["/api/users"]["get"]
        response_200 = get_operation["responses"]["200"]

        # Should not have examples added from documentation
        if "content" in response_200 and "application/json" in response_200["content"]:
            assert "examples" not in response_200["content"]["application/json"]

    def test_custom_headers_in_code_samples(self, sample_openapi_schema):
        """Test that custom headers are included in generated code samples."""
        documentation_data = DocumentationData(
            endpoints=[EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")],
            metadata={},
        )

        custom_headers = {"Authorization": "Bearer token123", "X-API-Key": "key456"}
        enhancer = OpenAPIEnhancer(custom_headers=custom_headers)
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        get_operation = enhanced_schema["paths"]["/api/users"]["get"]

        if "x-codeSamples" in get_operation:
            curl_sample = next((s for s in get_operation["x-codeSamples"] if s["lang"] == "curl"), None)

            if curl_sample:
                assert "Authorization: Bearer token123" in curl_sample["source"]
                assert "X-API-Key: key456" in curl_sample["source"]

    def test_multiple_content_types_in_responses(self):
        """Test handling multiple content types in response examples."""
        operation = {
            "responses": {
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {"schema": {"type": "object"}},
                        "application/xml": {"schema": {"type": "string"}},
                    },
                }
            }
        }

        response_examples = [
            ResponseExample(status_code=200, description="JSON response", content={"id": 1, "name": "John"})
        ]

        enhancer = OpenAPIEnhancer()
        enhancer._add_response_examples_to_operation(operation, response_examples)

        # Examples should be added to JSON content type
        json_content = operation["responses"]["200"]["content"]["application/json"]
        assert "examples" in json_content

        # XML content type should remain unchanged
        xml_content = operation["responses"]["200"]["content"]["application/xml"]
        assert "examples" not in xml_content

    def test_performance_with_large_schema(self):
        """Test performance with large OpenAPI schemas."""
        # Create a large schema with many paths
        large_schema = {"openapi": "3.0.2", "info": {"title": "Large API", "version": "1.0.0"}, "paths": {}}

        # Add 100 paths with multiple operations each
        for i in range(100):
            path = f"/api/endpoint{i}"
            large_schema["paths"][path] = {
                "get": {"summary": f"Get endpoint {i}", "responses": {"200": {"description": "Success"}}},
                "post": {"summary": f"Create endpoint {i}", "responses": {"201": {"description": "Created"}}},
                "put": {"summary": f"Update endpoint {i}", "responses": {"200": {"description": "Updated"}}},
                "delete": {"summary": f"Delete endpoint {i}", "responses": {"204": {"description": "Deleted"}}},
            }

        # Create documentation for some of the endpoints
        endpoints = []
        for i in range(0, 50, 5):  # Every 5th endpoint
            endpoints.append(
                EndpointDocumentation(
                    path=f"/api/endpoint{i}",
                    method=HTTPMethod.GET,
                    summary=f"Enhanced endpoint {i}",
                    code_samples=[
                        CodeSample(
                            language=CodeLanguage.CURL, code=f'curl -X GET "https://api.example.com/api/endpoint{i}"'
                        )
                    ],
                )
            )

        documentation_data = DocumentationData(endpoints=endpoints, metadata={})

        enhancer = OpenAPIEnhancer()
        enhanced_schema = enhancer.enhance_openapi_schema(large_schema, documentation_data)

        # Should handle large schemas efficiently
        assert enhanced_schema is not None
        assert len(enhanced_schema["paths"]) == 100

        # Check that some endpoints were enhanced
        enhanced_count = 0
        for _path, path_item in enhanced_schema["paths"].items():
            if "get" in path_item and "x-codeSamples" in path_item["get"]:
                enhanced_count += 1

        assert enhanced_count > 0


class TestEnhanceOpenAPIWithDocs:
    """Test the enhance_openapi_with_docs convenience function."""

    def test_enhance_openapi_with_docs_basic(
        self, sample_openapi_schema, temp_docs_dir, sample_markdown_content, test_utils
    ):
        """Test the convenience function with basic usage."""
        # Create test documentation
        test_utils.create_markdown_file(temp_docs_dir, "api.md", sample_markdown_content)

        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=sample_openapi_schema, docs_directory=str(temp_docs_dir)
        )

        assert enhanced_schema is not None
        assert "paths" in enhanced_schema
        assert "/api/users" in enhanced_schema["paths"]

    def test_enhance_openapi_with_docs_custom_config(
        self, sample_openapi_schema, temp_docs_dir, sample_markdown_content, test_utils
    ):
        """Test the convenience function with custom configuration."""
        test_utils.create_markdown_file(temp_docs_dir, "api.md", sample_markdown_content)

        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=sample_openapi_schema,
            docs_directory=str(temp_docs_dir),
            base_url="https://custom.api.com",
            include_code_samples=True,
            include_response_examples=False,
            code_sample_languages=[CodeLanguage.CURL, CodeLanguage.PYTHON],
        )

        assert enhanced_schema is not None

        # Check that code samples were included but response examples were not
        get_operation = enhanced_schema["paths"]["/api/users"]["get"]
        assert "x-codeSamples" in get_operation

        # Check custom base URL in code samples
        curl_sample = next((s for s in get_operation["x-codeSamples"] if s["lang"] == "curl"), None)
        if curl_sample:
            assert "https://custom.api.com" in curl_sample["source"]

    def test_enhance_openapi_with_docs_error_handling(self, sample_openapi_schema):
        """Test error handling in the convenience function."""
        # Test with non-existent directory
        with pytest.raises((OpenAPIEnhancementError, FileNotFoundError)):
            enhance_openapi_with_docs(openapi_schema=sample_openapi_schema, docs_directory="/nonexistent/directory")

    def test_enhance_openapi_with_docs_fallback_on_error(self, sample_openapi_schema, temp_docs_dir):
        """Test that the function falls back gracefully on errors."""
        # Empty directory should not cause errors
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=sample_openapi_schema, docs_directory=str(temp_docs_dir)
        )

        # Should return the original schema if no documentation is found
        assert enhanced_schema == sample_openapi_schema
