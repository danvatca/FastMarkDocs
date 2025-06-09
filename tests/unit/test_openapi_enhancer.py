"""
Unit tests for the OpenAPIEnhancer class.

Tests the OpenAPI schema enhancement functionality including code sample generation,
response example integration, and documentation enhancement.
"""

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

        assert enhancer.base_url == "https://api.example.com"
        assert enhancer.include_code_samples is True
        assert enhancer.include_response_examples is True

    def test_initialization_custom_config(self, openapi_enhancement_config):
        """Test enhancer initialization with custom configuration."""
        enhancer = OpenAPIEnhancer(**openapi_enhancement_config)

        assert enhancer.base_url == "https://api.example.com"
        assert enhancer.include_code_samples is True
        assert enhancer.include_response_examples is True

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
                        CodeSample(language=CodeLanguage.CURL, code='curl -X GET "https://api.example.com/api/users"')
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

        # Check that description was enhanced
        assert "Retrieve a list of users" in get_operation["description"]

        # Check documentation stats
        assert "x-documentation-stats" in enhanced_schema["info"]
        stats = enhanced_schema["info"]["x-documentation-stats"]
        assert stats["endpoints_enhanced"] >= 1
        assert stats["total_endpoints"] == 1

    def test_enhance_openapi_schema_with_response_examples(self, sample_openapi_schema):
        """Test OpenAPI schema enhancement with response examples."""
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

        enhancer = OpenAPIEnhancer()
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        # Check that response examples were added
        get_operation = enhanced_schema["paths"]["/api/users"]["get"]
        response_200 = get_operation["responses"]["200"]

        if "content" in response_200 and "application/json" in response_200["content"]:
            json_content = response_200["content"]["application/json"]
            assert "examples" in json_content

    def test_enhance_openapi_schema_preserve_existing(self, sample_openapi_schema):
        """Test that existing OpenAPI schema content is preserved."""
        # Add existing code samples to the schema
        sample_openapi_schema["paths"]["/api/users"]["get"]["x-codeSamples"] = [
            {"lang": "existing", "source": "existing code"}
        ]

        documentation_data = DocumentationData(endpoints=[], metadata={})

        enhancer = OpenAPIEnhancer()
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        # Existing code samples should be preserved
        get_operation = enhanced_schema["paths"]["/api/users"]["get"]
        existing_sample = next((s for s in get_operation["x-codeSamples"] if s["lang"] == "existing"), None)
        assert existing_sample is not None
        assert existing_sample["source"] == "existing code"

    def test_enhance_openapi_schema_no_matching_endpoints(self, sample_openapi_schema):
        """Test enhancement when no endpoints match the schema."""
        documentation_data = DocumentationData(
            endpoints=[
                EndpointDocumentation(path="/api/nonexistent", method=HTTPMethod.GET, summary="Non-existent endpoint")
            ],
            metadata={},
        )

        enhancer = OpenAPIEnhancer()
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        # Schema should be returned unchanged (except for stats)
        assert enhanced_schema["paths"] == sample_openapi_schema["paths"]

    def test_add_code_samples_to_operation(self):
        """Test adding code samples to an operation."""
        operation = {"summary": "Test operation", "responses": {"200": {"description": "Success"}}}

        code_samples = [
            CodeSample(language=CodeLanguage.CURL, code='curl -X GET "https://api.example.com/test"'),
            CodeSample(language=CodeLanguage.PYTHON, code="import requests\nresponse = requests.get('/test')"),
        ]

        enhancer = OpenAPIEnhancer()
        enhancer._add_code_samples_to_operation(operation, code_samples)

        assert "x-codeSamples" in operation
        assert len(operation["x-codeSamples"]) == 2

        curl_sample = next((s for s in operation["x-codeSamples"] if s["lang"] == "curl"), None)
        assert curl_sample is not None
        assert "curl -X GET" in curl_sample["source"]

        python_sample = next((s for s in operation["x-codeSamples"] if s["lang"] == "python"), None)
        assert python_sample is not None
        assert "import requests" in python_sample["source"]

    def test_add_response_examples_to_operation(self):
        """Test adding response examples to an operation."""
        operation = {
            "responses": {
                "200": {
                    "description": "Success",
                    "content": {"application/json": {"schema": {"type": "object"}}},
                }
            }
        }

        response_examples = [
            ResponseExample(status_code=200, description="User list", content=[{"id": 1, "name": "John"}])
        ]

        enhancer = OpenAPIEnhancer()
        enhancer._add_response_examples_to_operation(operation, response_examples)

        json_content = operation["responses"]["200"]["content"]["application/json"]
        assert "examples" in json_content
        assert "example_200" in json_content["examples"]

    def test_merge_response_examples_with_existing(self):
        """Test merging response examples with existing examples."""
        operation = {
            "responses": {
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"},
                            "examples": {"existing": {"summary": "Existing", "value": {"existing": True}}},
                        }
                    },
                }
            }
        }

        response_examples = [
            ResponseExample(status_code=200, description="New example", content={"id": 1, "name": "John"})
        ]

        enhancer = OpenAPIEnhancer()
        enhancer._add_response_examples_to_operation(operation, response_examples)

        json_content = operation["responses"]["200"]["content"]["application/json"]
        examples = json_content["examples"]

        # Both existing and new examples should be present
        assert "existing" in examples
        assert "example_200" in examples
        assert examples["existing"]["value"]["existing"] is True
        assert examples["example_200"]["value"]["id"] == 1

    def test_enhance_operation_description(self):
        """Test enhancing operation description."""
        operation = {"summary": "Original summary"}

        endpoint = EndpointDocumentation(
            path="/test", method=HTTPMethod.GET, summary="Enhanced summary", description="Enhanced description"
        )

        enhancer = OpenAPIEnhancer()
        enhancer._enhance_operation_description(operation, endpoint)

        # The method only sets description, not summary
        assert operation["summary"] == "Original summary"  # Unchanged
        assert operation["description"] == "Enhanced description"

    def test_path_matching_exact(self):
        """Test exact path matching."""
        enhancer = OpenAPIEnhancer()

        assert enhancer._paths_match("/api/users", "/api/users") is True
        assert enhancer._paths_match("/api/users", "/api/posts") is False

    def test_path_matching_with_parameters(self):
        """Test path matching with parameters."""
        enhancer = OpenAPIEnhancer()

        assert enhancer._paths_match("/api/users/{id}", "/api/users/{user_id}") is True
        assert enhancer._paths_match("/api/users/{id}/posts", "/api/users/{user_id}/posts") is True
        assert enhancer._paths_match("/api/users/{id}", "/api/posts/{id}") is False

    def test_method_matching(self):
        """Test HTTP method matching."""
        enhancer = OpenAPIEnhancer()

        assert enhancer._methods_match("get", HTTPMethod.GET) is True
        assert enhancer._methods_match("post", HTTPMethod.POST) is True
        assert enhancer._methods_match("get", HTTPMethod.POST) is False

    def test_error_handling_invalid_schema(self):
        """Test error handling with invalid OpenAPI schema."""
        enhancer = OpenAPIEnhancer()

        invalid_schema = {"invalid": "schema"}
        documentation_data = DocumentationData(endpoints=[], metadata={})

        with pytest.raises(OpenAPIEnhancementError):
            enhancer.enhance_openapi_schema(invalid_schema, documentation_data)

    def test_error_handling_none_inputs(self):
        """Test error handling with None inputs."""
        enhancer = OpenAPIEnhancer()

        with pytest.raises(OpenAPIEnhancementError):
            enhancer.enhance_openapi_schema(None, DocumentationData(endpoints=[], metadata={}))

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

    # New tests to cover missing lines

    def test_enhance_with_malformed_schema(self):
        """Test enhancement with malformed OpenAPI schema."""
        enhancer = OpenAPIEnhancer()

        # Schema missing required fields
        malformed_schema = {"openapi": "3.0.2"}  # Missing info and paths
        documentation_data = DocumentationData(endpoints=[], metadata={})

        with pytest.raises(OpenAPIEnhancementError):
            enhancer.enhance_openapi_schema(malformed_schema, documentation_data)

    def test_enhance_with_none_documentation_data(self):
        """Test enhancement with None documentation data."""
        enhancer = OpenAPIEnhancer()
        schema = {"openapi": "3.0.2", "info": {"title": "Test", "version": "1.0.0"}, "paths": {}}

        with pytest.raises(OpenAPIEnhancementError):
            enhancer.enhance_openapi_schema(schema, None)

    def test_path_matching_edge_cases(self):
        """Test path matching with edge cases."""
        enhancer = OpenAPIEnhancer()

        # Test with trailing slashes
        assert enhancer._paths_match("/api/users/", "/api/users") is True
        assert enhancer._paths_match("/api/users", "/api/users/") is True

        # Test with multiple parameters
        assert (
            enhancer._paths_match("/api/{org}/{repo}/issues/{id}", "/api/{organization}/{repository}/issues/{issue_id}")
            is True
        )

        # Test with no parameters vs parameters
        assert enhancer._paths_match("/api/users", "/api/{users}") is False

    def test_response_example_merging_edge_cases(self):
        """Test response example merging with edge cases."""
        operation = {
            "responses": {
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {"schema": {"type": "object"}}
                        # No existing examples
                    },
                }
            }
        }

        response_examples = [
            ResponseExample(status_code=200, description="First example", content={"id": 1}),
            ResponseExample(status_code=200, description="Second example", content={"id": 2}),
        ]

        enhancer = OpenAPIEnhancer()
        enhancer._add_response_examples_to_operation(operation, response_examples)

        json_content = operation["responses"]["200"]["content"]["application/json"]
        examples = json_content["examples"]

        # Only the last example should be present (they overwrite with same key)
        assert "example_200" in examples
        assert examples["example_200"]["value"]["id"] == 2  # Last one wins

    def test_operation_enhancement_with_none_values(self):
        """Test operation enhancement with None values."""
        operation = {"summary": "Original"}

        endpoint = EndpointDocumentation(
            path="/test", method=HTTPMethod.GET, summary=None, description=None  # None summary  # None description
        )

        enhancer = OpenAPIEnhancer()
        enhancer._enhance_operation_description(operation, endpoint)

        # Original summary should be preserved when endpoint summary is None
        assert operation["summary"] == "Original"
        # Description should not be added when None
        assert "description" not in operation or operation.get("description") is None


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

    def test_enhance_openapi_with_docs_invalid_schema(self, temp_docs_dir):
        """Test error handling with invalid schema."""
        invalid_schema = {"invalid": "schema"}

        with pytest.raises(OpenAPIEnhancementError):
            enhance_openapi_with_docs(openapi_schema=invalid_schema, docs_directory=str(temp_docs_dir))
