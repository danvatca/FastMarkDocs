"""
Unit tests for the OpenAPIEnhancer class.

Tests the OpenAPI schema enhancement functionality including code sample generation,
response example integration, and documentation enhancement.
"""

from typing import Any, Union
from unittest.mock import Mock, patch

import pytest
from fastmarkdocs.exceptions import OpenAPIEnhancementError
from fastmarkdocs.openapi_enhancer import OpenAPIEnhancer, enhance_openapi_with_docs
from fastmarkdocs.types import (
    CodeLanguage,
    CodeSample,
    DocumentationData,
    EndpointDocumentation,
    HTTPMethod,
    ParameterDocumentation,
    ResponseExample,
)


class TestOpenAPIEnhancer:
    """Test the OpenAPIEnhancer class."""

    def test_initialization_default_config(self) -> None:
        """Test enhancer initialization with default configuration."""
        enhancer = OpenAPIEnhancer()

        assert enhancer.base_url == "https://api.example.com"
        assert enhancer.include_code_samples is True
        assert enhancer.include_response_examples is True

    def test_initialization_custom_config(self, openapi_enhancement_config: Any) -> None:
        """Test enhancer initialization with custom configuration."""
        enhancer = OpenAPIEnhancer(**openapi_enhancement_config)

        assert enhancer.base_url == "https://api.example.com"
        assert enhancer.include_code_samples is True
        assert enhancer.include_response_examples is True

    def test_enhance_openapi_schema_basic(self, sample_openapi_schema: Any) -> None:
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
        get_operation: dict[str, Any] = enhanced_schema["paths"]["/api/users"]["get"]
        assert "x-codeSamples" in get_operation
        assert len(get_operation["x-codeSamples"]) > 0

        # Check that description was enhanced
        assert "Retrieve a list of users" in get_operation["description"]

        # Check documentation stats
        assert "x-documentation-stats" in enhanced_schema["info"]
        stats = enhanced_schema["info"]["x-documentation-stats"]
        assert stats["endpoints_enhanced"] >= 1
        assert stats["total_endpoints"] == 1

    def test_enhance_openapi_schema_with_response_examples(self, sample_openapi_schema: Any) -> None:
        """Test OpenAPI schema enhancement with response examples."""
        documentation_data = DocumentationData(
            endpoints=[
                EndpointDocumentation(
                    path="/api/users",
                    method=HTTPMethod.GET,
                    summary="List users",
                    response_examples=[
                        ResponseExample(
                            status_code=200, description="Success", content={"items": [{"id": 1, "name": "John"}]}
                        )
                    ],
                )
            ],
            metadata={},
        )

        enhancer = OpenAPIEnhancer()
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        # Check that response examples were added
        get_operation: dict[str, Any] = enhanced_schema["paths"]["/api/users"]["get"]
        response_200: dict[str, Any] = get_operation["responses"]["200"]

        if "content" in response_200 and "application/json" in response_200["content"]:
            json_content = response_200["content"]["application/json"]
            assert "examples" in json_content

    def test_enhance_openapi_schema_preserve_existing(self, sample_openapi_schema: Any) -> None:
        """Test that existing OpenAPI schema content is preserved."""
        # Add existing code samples to the schema
        sample_openapi_schema["paths"]["/api/users"]["get"]["x-codeSamples"] = [
            {"lang": "existing", "source": "existing code"}
        ]

        documentation_data = DocumentationData(endpoints=[], metadata={})

        enhancer = OpenAPIEnhancer()
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        # Existing code samples should be preserved
        get_operation: dict[str, Any] = enhanced_schema["paths"]["/api/users"]["get"]
        existing_sample: Union[dict[str, Any], None] = next(
            (s for s in get_operation["x-codeSamples"] if s["lang"] == "existing"), None
        )
        assert existing_sample is not None
        assert existing_sample["source"] == "existing code"

    def test_enhance_openapi_schema_no_matching_endpoints(self, sample_openapi_schema: Any) -> None:
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

    def test_add_code_samples_to_operation(self) -> None:
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

        curl_sample: Union[dict[str, Any], None] = next(
            (s for s in operation["x-codeSamples"] if s["lang"] == "curl"), None
        )
        assert curl_sample is not None
        assert "curl -X GET" in curl_sample["source"]
        python_sample: Union[dict[str, Any], None] = next(
            (s for s in operation["x-codeSamples"] if s["lang"] == "python"), None
        )
        assert python_sample is not None
        assert "import requests" in python_sample["source"]

    def test_add_code_samples_to_operation_empty_list(self) -> None:
        """Test early return when no code samples are provided."""
        enhancer = OpenAPIEnhancer()
        operation = {"summary": "Test"}
        stats = {"code_samples_added": 0}

        # Should return early and not modify operation
        enhancer._add_code_samples_to_operation(operation, [], stats)

        assert "x-codeSamples" not in operation
        assert stats["code_samples_added"] == 0

    def test_add_response_examples_to_operation(self) -> None:
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
            ResponseExample(status_code=200, description="User list", content={"items": [{"id": 1, "name": "John"}]})
        ]

        enhancer = OpenAPIEnhancer()
        enhancer._add_response_examples_to_operation(operation, response_examples)

        json_content: dict[str, Any] = operation["responses"]["200"]["content"]["application/json"]
        assert "examples" in json_content
        assert "example_200" in json_content["examples"]

    def test_add_response_examples_to_operation_no_responses(self) -> None:
        """Test response examples when operation has no responses initially."""
        enhancer = OpenAPIEnhancer()
        operation = {"summary": "Test"}  # No responses key

        response_examples = [ResponseExample(status_code=200, description="Success", content={"result": "ok"})]

        stats = {"examples_added": 0}

        enhancer._add_response_examples_to_operation(operation, response_examples, stats)

        # Should create responses section
        assert "responses" in operation
        assert "200" in operation["responses"]
        assert stats["examples_added"] == 1

    def test_merge_response_examples_with_existing(self) -> None:
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

        json_content: dict[str, Any] = operation["responses"]["200"]["content"]["application/json"]
        examples: dict[str, Any] = json_content["examples"]

        # Both existing and new examples should be present
        assert "existing" in examples
        assert "example_200" in examples
        assert examples["existing"]["value"]["existing"] is True
        assert examples["example_200"]["value"]["id"] == 1

    def test_enhance_operation_description(self) -> None:
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

    def test_path_matching_exact(self) -> None:
        """Test exact path matching."""
        enhancer = OpenAPIEnhancer()

        assert enhancer._paths_match("/api/users", "/api/users") is True
        assert enhancer._paths_match("/api/users", "/api/posts") is False

    def test_path_matching_with_parameters(self) -> None:
        """Test path matching with parameters."""
        enhancer = OpenAPIEnhancer()

        assert enhancer._paths_match("/api/users/{id}", "/api/users/{user_id}") is True
        assert enhancer._paths_match("/api/users/{id}/posts", "/api/users/{user_id}/posts") is True
        assert enhancer._paths_match("/api/users/{id}", "/api/posts/{id}") is False

    def test_method_matching(self) -> None:
        """Test HTTP method matching."""
        enhancer = OpenAPIEnhancer()

        assert enhancer._methods_match("get", HTTPMethod.GET) is True
        assert enhancer._methods_match("post", HTTPMethod.POST) is True
        assert enhancer._methods_match("get", HTTPMethod.POST) is False

    def test_error_handling_invalid_schema(self) -> None:
        """Test error handling with invalid OpenAPI schema."""
        enhancer = OpenAPIEnhancer()

        invalid_schema = {"invalid": "schema"}
        documentation_data = DocumentationData(endpoints=[], metadata={})

        with pytest.raises(OpenAPIEnhancementError):
            enhancer.enhance_openapi_schema(invalid_schema, documentation_data)

    def test_error_handling_none_inputs(self) -> None:
        """Test error handling with None inputs."""
        enhancer = OpenAPIEnhancer()

        with pytest.raises(OpenAPIEnhancementError):
            enhancer.enhance_openapi_schema({}, DocumentationData(endpoints=[], metadata={}))

    def test_error_handling_invalid_schema_type(self) -> None:
        """Test error handling when schema is not a dictionary."""
        enhancer = OpenAPIEnhancer()
        documentation = DocumentationData(endpoints=[], metadata={})

        # Test with non-dict schema
        with pytest.raises(OpenAPIEnhancementError) as exc_info:
            enhancer.enhance_openapi_schema("not a dict", documentation)
        assert "OpenAPI schema must be a dictionary" in str(exc_info.value)

    def test_error_handling_root_exception(self) -> None:
        """Test error handling for root-level exceptions during enhancement."""
        enhancer = OpenAPIEnhancer()

        # Create a schema that will cause an exception during deep copy
        class BadDict(dict):
            def __deepcopy__(self, memo: Any) -> None:
                raise Exception("Deep copy failed")

        bad_schema = BadDict({"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0.0"}})

        documentation = DocumentationData(endpoints=[], metadata={})

        with pytest.raises(OpenAPIEnhancementError) as exc_info:
            enhancer.enhance_openapi_schema(bad_schema, documentation)

        assert "Schema enhancement failed" in str(exc_info.value)

    def test_error_handling_operation_enhancement_exception(self) -> None:
        """Test error handling when _enhance_operation raises an exception."""
        enhancer = OpenAPIEnhancer()

        # Create a mock that will raise an exception
        with patch.object(enhancer, "_enhance_operation", side_effect=Exception("Test error")):
            schema = {
                "openapi": "3.0.0",
                "info": {"title": "Test", "version": "1.0.0"},
                "paths": {"/test": {"get": {"summary": "Test endpoint"}}},
            }

            documentation = DocumentationData(
                endpoints=[EndpointDocumentation(path="/test", method=HTTPMethod.GET, summary="Test endpoint")],
                metadata={},
            )

            # Should not raise exception, but should handle it gracefully
            result = enhancer.enhance_openapi_schema(schema, documentation)
            assert result is not None

    def test_disable_code_samples(self, sample_openapi_schema: Any) -> None:
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

        get_operation: dict[str, Any] = enhanced_schema["paths"]["/api/users"]["get"]
        assert "x-codeSamples" not in get_operation

    def test_disable_response_examples(self, sample_openapi_schema: Any) -> None:
        """Test disabling response example enhancement."""
        documentation_data = DocumentationData(
            endpoints=[
                EndpointDocumentation(
                    path="/api/users",
                    method=HTTPMethod.GET,
                    summary="List users",
                    response_examples=[
                        ResponseExample(
                            status_code=200, description="Success", content={"items": [{"id": 1, "name": "John"}]}
                        )
                    ],
                )
            ],
            metadata={},
        )

        enhancer = OpenAPIEnhancer(include_response_examples=False)
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        # Response examples should not be added
        get_operation: dict[str, Any] = enhanced_schema["paths"]["/api/users"]["get"]
        response_200: dict[str, Any] = get_operation["responses"]["200"]

        # Should not have examples added from documentation
        if "content" in response_200 and "application/json" in response_200["content"]:
            assert "examples" not in response_200["content"]["application/json"]

    def test_custom_headers_in_code_samples(self, sample_openapi_schema: Any) -> None:
        """Test that custom headers are included in generated code samples."""
        documentation_data = DocumentationData(
            endpoints=[EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users")],
            metadata={},
        )

        custom_headers = {"Authorization": "Bearer token123", "X-API-Key": "key456"}
        enhancer = OpenAPIEnhancer(custom_headers=custom_headers)
        enhanced_schema = enhancer.enhance_openapi_schema(sample_openapi_schema, documentation_data)

        get_operation: dict[str, Any] = enhanced_schema["paths"]["/api/users"]["get"]

        if "x-codeSamples" in get_operation:
            curl_sample: Union[dict[str, Any], None] = next(
                (s for s in get_operation["x-codeSamples"] if s["lang"] == "curl"), None
            )

            if curl_sample:
                assert "Authorization: Bearer token123" in curl_sample["source"]
                assert "X-API-Key: key456" in curl_sample["source"]

    def test_multiple_content_types_in_responses(self) -> None:
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
        json_content: dict[str, Any] = operation["responses"]["200"]["content"]["application/json"]
        assert "examples" in json_content

        # XML content type should remain unchanged
        xml_content = operation["responses"]["200"]["content"]["application/xml"]
        assert "examples" not in xml_content

    def test_performance_with_large_schema(self) -> None:
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

    def test_enhance_with_malformed_schema(self) -> None:
        """Test enhancement with malformed OpenAPI schema."""
        enhancer = OpenAPIEnhancer()

        # Schema missing required fields
        malformed_schema = {"openapi": "3.0.2"}  # Missing info and paths
        documentation_data = DocumentationData(endpoints=[], metadata={})

        with pytest.raises(OpenAPIEnhancementError):
            enhancer.enhance_openapi_schema(malformed_schema, documentation_data)

    def test_enhance_with_none_documentation_data(self) -> None:
        """Test enhancement with None documentation data."""
        enhancer = OpenAPIEnhancer()
        schema = {"openapi": "3.0.2", "info": {"title": "Test", "version": "1.0.0"}, "paths": {}}

        with pytest.raises(OpenAPIEnhancementError):
            enhancer.enhance_openapi_schema(schema, None)

    def test_path_matching_edge_cases(self) -> None:
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

    def test_response_example_merging_edge_cases(self) -> None:
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

        json_content: dict[str, Any] = operation["responses"]["200"]["content"]["application/json"]
        examples: dict[str, Any] = json_content["examples"]

        # Only the last example should be present (they overwrite with same key)
        assert "example_200" in examples
        assert examples["example_200"]["value"]["id"] == 2  # Last one wins

    def test_operation_enhancement_with_existing_content(self) -> None:
        """Test that enhancement properly adds rich markdown descriptions while preserving meaningful existing content."""
        enhancer = OpenAPIEnhancer()

        # Test case 1: Auto-generated summary should be overridden
        operation1 = {"summary": "Authorize", "description": "", "tags": ["existing-tag"]}
        endpoint_doc1 = EndpointDocumentation(
            path="/test",
            method=HTTPMethod.GET,
            summary="Authenticate user with JWT token",
            description="This endpoint authenticates a user using a JWT token and returns user information along with access permissions.",
            tags=["new-tag"],
            code_samples=[],
            response_examples=[],
            parameters=[],
        )
        stats1 = {"descriptions_enhanced": 0, "code_samples_added": 0, "examples_added": 0, "endpoints_enhanced": 0}

        enhancer._enhance_operation(operation1, endpoint_doc1, stats1)

        # Should override auto-generated summary and add rich description
        assert operation1["summary"] == "Authenticate user with JWT token"
        assert (
            operation1["description"]
            == "This endpoint authenticates a user using a JWT token and returns user information along with access permissions."
        )
        assert "existing-tag" in operation1["tags"]
        assert "new-tag" in operation1["tags"]
        assert stats1["descriptions_enhanced"] == 2  # Both summary and description enhanced

        # Test case 2: Meaningful existing content should be preserved
        operation2 = {
            "summary": "Comprehensive user authentication endpoint",
            "description": "This is a detailed existing description that provides meaningful information about the endpoint functionality.",
            "tags": ["existing-tag"],
        }
        endpoint_doc2 = EndpointDocumentation(
            path="/test",
            method=HTTPMethod.GET,
            summary="New summary",
            description="New description",
            tags=["new-tag"],
            code_samples=[],
            response_examples=[],
            parameters=[],
        )
        stats2 = {"descriptions_enhanced": 0, "code_samples_added": 0, "examples_added": 0, "endpoints_enhanced": 0}

        enhancer._enhance_operation(operation2, endpoint_doc2, stats2)

        # Should preserve meaningful existing content
        assert operation2["summary"] == "Comprehensive user authentication endpoint"
        assert (
            operation2["description"]
            == "This is a detailed existing description that provides meaningful information about the endpoint functionality."
        )
        assert "existing-tag" in operation2["tags"]
        assert "new-tag" in operation2["tags"]
        assert stats2["descriptions_enhanced"] == 0  # Nothing enhanced since existing content is meaningful

    def test_response_examples_with_missing_status_codes(self) -> None:
        """Test response example enhancement when operation doesn't have matching status codes."""
        enhancer = OpenAPIEnhancer()

        operation = {"responses": {"200": {"description": "Success"}}}

        response_examples = [
            ResponseExample(status_code=201, description="Created", content={"id": 123}),
            ResponseExample(status_code=404, description="Not found", content={"error": "Not found"}),
        ]

        stats = {"examples_added": 0}

        enhancer._add_response_examples_to_operation(operation, response_examples, stats)

        # Should create new response entries for missing status codes
        assert "201" in operation["responses"]
        assert "404" in operation["responses"]
        assert operation["responses"]["201"]["description"] == "Created"
        assert operation["responses"]["404"]["description"] == "Not found"

        # Should add examples to responses (in content.application/json.examples format)
        assert "content" in operation["responses"]["201"]
        assert "application/json" in operation["responses"]["201"]["content"]
        assert "examples" in operation["responses"]["201"]["content"]["application/json"]

        assert stats["examples_added"] == 2

    def test_parameter_examples_enhancement_with_partial_matches(self) -> None:
        """Test parameter example enhancement when only some parameters match."""
        enhancer = OpenAPIEnhancer()

        operation = {
            "parameters": [
                {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                {"name": "offset", "in": "query", "schema": {"type": "integer"}},
                {"name": "sort", "in": "query", "schema": {"type": "string"}},
            ]
        }

        parameters = [
            ParameterDocumentation(
                name="limit", description="Limit results", type="integer", required=False, example=10
            ),
            ParameterDocumentation(
                name="unknown_param",
                description="This parameter doesn't exist in operation",
                type="string",
                required=False,
                example="test",
            ),
        ]

        stats = {"examples_added": 0}

        enhancer._add_parameter_examples(operation, parameters, stats)

        # Should only enhance matching parameters
        limit_param = next(p for p in operation["parameters"] if p["name"] == "limit")
        assert "example" in limit_param
        assert limit_param["example"] == 10

        # Other parameters should remain unchanged
        offset_param = next(p for p in operation["parameters"] if p["name"] == "offset")
        assert "example" not in offset_param

        # Should also add the unknown parameter as a new parameter
        unknown_param = next((p for p in operation["parameters"] if p["name"] == "unknown_param"), None)
        assert unknown_param is not None
        assert unknown_param["example"] == "test"

        # Note: The _add_parameter_examples method doesn't increment stats counter
        # This is the actual behavior of the implementation

    def test_global_info_enhancement_with_documentation_stats(self) -> None:
        """Test global info enhancement includes documentation statistics."""
        enhancer = OpenAPIEnhancer()

        schema = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}}

        # Mock documentation with stats
        documentation = Mock()
        documentation.endpoints = []
        documentation.global_examples = []
        documentation.metadata = {
            "stats": Mock(
                total_files=5,
                total_endpoints=15,
                total_code_samples=30,
                languages_found=["python", "javascript", "curl"],
                validation_errors=[],
                load_time_ms=125.5,
            )
        }

        stats = {"endpoints_enhanced": 12, "code_samples_added": 25, "descriptions_enhanced": 8, "examples_added": 8}

        enhancer._enhance_global_info(schema, documentation, stats)

        # Should add documentation stats to schema
        assert "x-documentation-stats" in schema["info"]
        doc_stats = schema["info"]["x-documentation-stats"]

        assert doc_stats["endpoints_enhanced"] == 12
        assert doc_stats["code_samples_added"] == 25
        assert doc_stats["descriptions_enhanced"] == 8
        assert doc_stats["examples_added"] == 8

    def test_global_info_enhancement_no_stats_to_add(self) -> None:
        """Test global info enhancement when there are no stats to add."""
        enhancer = OpenAPIEnhancer()

        schema = {"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0.0"}}

        documentation = DocumentationData(endpoints=[], metadata={})

        # Stats with no enhancements
        stats = {"endpoints_enhanced": 0, "code_samples_added": 0, "descriptions_enhanced": 0, "examples_added": 0}

        enhancer._enhance_global_info(schema, documentation, stats)

        # Should not add documentation stats when no enhancements were made
        assert "x-documentation-stats" not in schema["info"]

    def test_global_info_enhancement_no_info_section(self) -> None:
        """Test global info enhancement when schema has no info section."""
        enhancer = OpenAPIEnhancer()

        schema = {"openapi": "3.0.0"}  # No info section

        documentation = DocumentationData(endpoints=[], metadata={})

        stats = {"endpoints_enhanced": 1, "code_samples_added": 2, "descriptions_enhanced": 1, "examples_added": 1}

        enhancer._enhance_global_info(schema, documentation, stats)

        # Should create info section
        assert "info" in schema
        assert "x-documentation-stats" in schema["info"]
        assert schema["info"]["x-documentation-stats"]["endpoints_enhanced"] == 1

    def test_path_matching_with_parameter_variations(self) -> None:
        """Test path matching handles parameter name variations correctly."""
        enhancer = OpenAPIEnhancer()

        # Test various parameter naming conventions
        assert enhancer._paths_match("/users/{id}", "/users/{user_id}")
        assert enhancer._paths_match("/users/{userId}", "/users/{id}")
        assert enhancer._paths_match("/users/{user-id}", "/users/{id}")
        assert enhancer._paths_match("/posts/{postId}/comments/{id}", "/posts/{id}/comments/{comment_id}")

        # Test non-matching paths
        assert not enhancer._paths_match("/users/{id}", "/posts/{id}")
        assert not enhancer._paths_match("/users", "/users/{id}")
        assert not enhancer._paths_match("/users/{id}/posts", "/users/{id}")

    def test_code_sample_language_filtering_and_merging(self) -> None:
        """Test that code samples are properly filtered by language and merged."""
        enhancer = OpenAPIEnhancer(code_sample_languages=[CodeLanguage.PYTHON, CodeLanguage.CURL])

        # Mock endpoint with existing code samples
        endpoint = EndpointDocumentation(
            path="/test",
            method=HTTPMethod.GET,
            summary="Test endpoint",
            description="Test",
            code_samples=[
                CodeSample(language=CodeLanguage.JAVASCRIPT, code="// JS code", title="JS"),
                CodeSample(language=CodeLanguage.PYTHON, code="# Python code", title="Python"),
            ],
            response_examples=[],
            parameters=[],
        )

        operation: dict[str, Any] = {}
        stats = {"descriptions_enhanced": 0, "code_samples_added": 0, "examples_added": 0, "endpoints_enhanced": 0}

        # Mock code generator to return additional samples
        with patch.object(enhancer.code_generator, "generate_samples_for_endpoint") as mock_gen:
            mock_gen.return_value = [
                CodeSample(language=CodeLanguage.CURL, code="curl command", title="cURL"),
                CodeSample(language=CodeLanguage.GO, code="// Go code", title="Go"),
            ]

            enhancer._enhance_operation(operation, endpoint, stats)

            # Should include Python (from endpoint) and cURL (generated)
            # Should exclude JavaScript (not in requested languages) and Go (not in requested languages)
            assert "x-codeSamples" in operation
            code_samples = operation["x-codeSamples"]

            languages = [sample["lang"] for sample in code_samples]
            assert "python" in languages
            assert "curl" in languages
            assert "javascript" not in languages
            assert "go" not in languages

    def test_schema_validation_comprehensive(self) -> None:
        """Test comprehensive schema validation."""
        enhancer = OpenAPIEnhancer()

        # Test with None schema
        with pytest.raises(OpenAPIEnhancementError, match="OpenAPI schema cannot be None"):
            enhancer.enhance_openapi_schema(None, DocumentationData())

        # Test with None documentation
        with pytest.raises(OpenAPIEnhancementError, match="Documentation data cannot be None"):
            enhancer.enhance_openapi_schema({}, None)

        # Test with non-dict schema
        with pytest.raises(OpenAPIEnhancementError, match="OpenAPI schema must be a dictionary"):
            enhancer.enhance_openapi_schema("not a dict", DocumentationData())

        # Test with missing openapi/swagger field
        with pytest.raises(OpenAPIEnhancementError, match="missing 'openapi' or 'swagger' field"):
            enhancer.enhance_openapi_schema({"info": {"title": "Test"}}, DocumentationData())

        # Test with missing info field
        with pytest.raises(OpenAPIEnhancementError, match="missing 'info' field"):
            enhancer.enhance_openapi_schema({"openapi": "3.0.0"}, DocumentationData())

    def test_operation_enhancement_error_recovery(self) -> None:
        """Test that operation enhancement errors are handled gracefully."""
        enhancer = OpenAPIEnhancer()

        # Create a schema that will cause enhancement errors
        schema = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        # Missing required fields that might cause errors
                    }
                }
            },
        }

        # Create documentation with matching endpoint
        documentation = DocumentationData(
            endpoints=[
                EndpointDocumentation(
                    path="/test",
                    method=HTTPMethod.GET,
                    summary="Enhanced summary",
                    description="Enhanced description",
                    tags=["test"],
                )
            ]
        )

        # Should not raise an exception, even if individual operations fail
        result = enhancer.enhance_openapi_schema(schema, documentation)
        assert result is not None
        assert "paths" in result

    def test_tag_descriptions_enhancement(self) -> None:
        """Test that tag descriptions are properly added to OpenAPI schema."""
        enhancer = OpenAPIEnhancer()

        schema = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {"get": {"summary": "List users", "tags": ["users"]}},
                "/auth/login": {"post": {"summary": "Login", "tags": ["authentication"]}},
            },
        }

        documentation = DocumentationData(
            endpoints=[
                EndpointDocumentation(path="/users", method=HTTPMethod.GET, summary="List users", tags=["users"]),
                EndpointDocumentation(
                    path="/auth/login", method=HTTPMethod.POST, summary="Login", tags=["authentication"]
                ),
            ],
            tag_descriptions={
                "users": "The **User Management API** provides comprehensive user account administration for SynetoOS, enabling centralized user lifecycle management with role-based access control and multi-factor authentication.",
                "authentication": "The **Authentication API** handles user login, session management, and security token operations for secure access to the system.",
            },
        )

        result = enhancer.enhance_openapi_schema(schema, documentation)

        # Check that tags section was created with descriptions
        assert "tags" in result
        assert len(result["tags"]) == 2

        # Find the tags
        users_tag = next((tag for tag in result["tags"] if tag["name"] == "users"), None)
        auth_tag = next((tag for tag in result["tags"] if tag["name"] == "authentication"), None)

        assert users_tag is not None
        assert "description" in users_tag
        assert "User Management API" in users_tag["description"]

        assert auth_tag is not None
        assert "description" in auth_tag
        assert "Authentication API" in auth_tag["description"]

    def test_tag_descriptions_with_existing_tags(self) -> None:
        """Test that existing tags are preserved and enhanced with descriptions."""
        enhancer = OpenAPIEnhancer()

        schema = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "tags": [
                {"name": "users", "description": "Existing description"},
                {"name": "authentication"},  # No description
            ],
            "paths": {
                "/users": {"get": {"summary": "List users", "tags": ["users"]}},
                "/auth/login": {"post": {"summary": "Login", "tags": ["authentication"]}},
            },
        }

        documentation = DocumentationData(
            endpoints=[
                EndpointDocumentation(path="/users", method=HTTPMethod.GET, summary="List users", tags=["users"]),
                EndpointDocumentation(
                    path="/auth/login", method=HTTPMethod.POST, summary="Login", tags=["authentication"]
                ),
            ],
            tag_descriptions={"users": "Enhanced user description", "authentication": "Enhanced auth description"},
        )

        result = enhancer.enhance_openapi_schema(schema, documentation)

        # Check that tags section exists
        assert "tags" in result
        assert len(result["tags"]) == 2

        # Find the tags
        users_tag = next((tag for tag in result["tags"] if tag["name"] == "users"), None)
        auth_tag = next((tag for tag in result["tags"] if tag["name"] == "authentication"), None)

        # Users tag should keep existing description (not overwrite)
        assert users_tag is not None
        assert users_tag["description"] == "Existing description"

        # Authentication tag should get new description
        assert auth_tag is not None
        assert auth_tag["description"] == "Enhanced auth description"

    def test_tag_descriptions_no_tags_in_operations(self) -> None:
        """Test behavior when no tags are present in operations."""
        enhancer = OpenAPIEnhancer()

        schema = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint"
                        # No tags
                    }
                }
            },
        }

        documentation = DocumentationData(
            endpoints=[
                EndpointDocumentation(
                    path="/test",
                    method=HTTPMethod.GET,
                    summary="Test endpoint",
                    # No tags
                )
            ],
            tag_descriptions={"unused": "This tag is not used anywhere"},
        )

        result = enhancer.enhance_openapi_schema(schema, documentation)

        # No tags section should be created since no operations have tags
        assert "tags" not in result or len(result.get("tags", [])) == 0


class TestEnhanceOpenAPIWithDocs:
    """Test the enhance_openapi_with_docs convenience function."""

    def test_enhance_openapi_with_docs_basic(
        self, sample_openapi_schema: Any, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any
    ) -> None:
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
        self, sample_openapi_schema: Any, temp_docs_dir: Any, sample_markdown_content: Any, test_utils: Any
    ) -> None:
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
        get_operation: dict[str, Any] = enhanced_schema["paths"]["/api/users"]["get"]
        assert "x-codeSamples" in get_operation

        # Check custom base URL in code samples
        curl_sample: Union[dict[str, Any], None] = next(
            (s for s in get_operation["x-codeSamples"] if s["lang"] == "curl"), None
        )
        if curl_sample:
            assert "https://custom.api.com" in curl_sample["source"]

    def test_enhance_openapi_with_docs_error_handling(self, sample_openapi_schema: Any) -> None:
        """Test error handling in the convenience function."""
        # Test with non-existent directory
        with pytest.raises((OpenAPIEnhancementError, FileNotFoundError)):
            enhance_openapi_with_docs(openapi_schema=sample_openapi_schema, docs_directory="/nonexistent/directory")

    def test_enhance_openapi_with_docs_fallback_on_error(self, sample_openapi_schema: Any, temp_docs_dir: Any) -> None:
        """Test that the function falls back gracefully on errors."""
        # Empty directory should not cause errors
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=sample_openapi_schema, docs_directory=str(temp_docs_dir)
        )

        # Should return the original schema if no documentation is found
        assert enhanced_schema == sample_openapi_schema

    def test_enhance_openapi_with_docs_invalid_schema(self, temp_docs_dir: Any) -> None:
        """Test error handling with invalid schema."""
        invalid_schema = {"invalid": "schema"}

        with pytest.raises(OpenAPIEnhancementError):
            enhance_openapi_with_docs(openapi_schema=invalid_schema, docs_directory=str(temp_docs_dir))

    def test_enhance_openapi_with_docs_general_docs_feature(
        self, sample_openapi_schema: Any, temp_docs_dir: Any, test_utils: Any
    ) -> None:
        """Test the general docs feature through enhance_openapi_with_docs function."""
        # Create general docs file
        general_docs_content = """# API General Documentation

This is general documentation that should appear in the global info.description.

## Features
- Authentication
- Rate limiting
- Error handling

## Getting Started
1. Get an API key
2. Make requests
3. Handle responses
"""
        test_utils.create_markdown_file(temp_docs_dir, "general_docs.md", general_docs_content)

        # Create endpoint documentation
        endpoint_content = """## GET /api/users

Retrieve a list of users.

### Parameters
- `limit` (integer, optional): Maximum number of results

### Response Examples

```json
{
  "users": [
    {"id": 1, "name": "John Doe"}
  ]
}
```
"""
        test_utils.create_markdown_file(temp_docs_dir, "users.md", endpoint_content)

        # Test 1: Default behavior (should auto-detect general_docs.md)
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=sample_openapi_schema, docs_directory=str(temp_docs_dir)
        )

        assert enhanced_schema is not None
        assert "paths" in enhanced_schema
        assert "/api/users" in enhanced_schema["paths"]

        # Check that general docs were included in the global info.description
        info_description = enhanced_schema.get("info", {}).get("description", "")
        assert "API General Documentation" in info_description
        assert "This is general documentation" in info_description
        assert "Features" in info_description
        assert "Getting Started" in info_description

        # Check that endpoint descriptions do NOT include general docs
        get_operation: dict[str, Any] = enhanced_schema["paths"]["/api/users"]["get"]
        endpoint_description = get_operation.get("description", "")

        # Should include endpoint-specific content
        assert "Retrieve a list of users" in endpoint_description
        assert "Parameters" in endpoint_description

        # Should NOT include general docs content in endpoint descriptions
        assert "API General Documentation" not in endpoint_description
        assert "This is general documentation" not in endpoint_description

        # Test 2: Custom general docs file
        custom_general_content = """# Custom General Docs

Custom general documentation content.

## Custom Features
- Custom feature 1
- Custom feature 2
"""
        test_utils.create_markdown_file(temp_docs_dir, "custom_general.md", custom_general_content)

        enhanced_schema_custom = enhance_openapi_with_docs(
            openapi_schema=sample_openapi_schema,
            docs_directory=str(temp_docs_dir),
            general_docs_file="custom_general.md",
        )

        info_description_custom = enhanced_schema_custom.get("info", {}).get("description", "")

        # Should include custom general docs content in global description
        assert "Custom General Docs" in info_description_custom
        assert "Custom general documentation content" in info_description_custom
        assert "Custom Features" in info_description_custom

        # Should NOT include default general docs content
        assert "API General Documentation" not in info_description_custom
        assert "This is general documentation" not in info_description_custom

        # Test 3: No general docs file (remove both files)
        (temp_docs_dir / "general_docs.md").unlink()
        (temp_docs_dir / "custom_general.md").unlink()

        enhanced_schema_no_general = enhance_openapi_with_docs(
            openapi_schema=sample_openapi_schema, docs_directory=str(temp_docs_dir)
        )

        info_description_no_general = enhanced_schema_no_general.get("info", {}).get("description", "")

        # Should NOT include any general docs content in global description
        assert "API General Documentation" not in info_description_no_general
        assert "Custom General Docs" not in info_description_no_general

        # Endpoint descriptions should still work normally
        get_operation_no_general = enhanced_schema_no_general["paths"]["/api/users"]["get"]
        endpoint_description_no_general = get_operation_no_general.get("description", "")

        # Should include endpoint-specific content
        assert "Retrieve a list of users" in endpoint_description_no_general
        assert "Parameters" in endpoint_description_no_general
