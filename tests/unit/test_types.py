"""
Unit tests for the types module.

Tests the type definitions, enums, and data structures used throughout the library.
"""

import pytest

from fastmarkdocs.types import (
    CodeLanguage,
    CodeSample,
    DocumentationData,
    EndpointDocumentation,
    HTTPMethod,
    ParameterDocumentation,
    ResponseExample,
)


class TestCodeLanguage:
    """Test the CodeLanguage enum."""

    def test_code_language_values(self):
        """Test that all expected code languages are defined."""
        expected_languages = {"curl", "python", "javascript", "typescript", "go", "java", "php", "ruby", "csharp"}

        actual_languages = {lang.value for lang in CodeLanguage}
        assert actual_languages == expected_languages

    def test_code_language_string_representation(self):
        """Test string representation of code languages."""
        assert str(CodeLanguage.PYTHON) == "python"
        assert str(CodeLanguage.CURL) == "curl"
        assert str(CodeLanguage.JAVASCRIPT) == "javascript"

    def test_code_language_comparison(self):
        """Test comparison operations on code languages."""
        assert CodeLanguage.PYTHON == CodeLanguage.PYTHON
        assert CodeLanguage.PYTHON != CodeLanguage.CURL

        # Test comparison with strings
        assert CodeLanguage.PYTHON.value == "python"
        assert CodeLanguage.CURL.value == "curl"


class TestHTTPMethod:
    """Test the HTTPMethod enum."""

    def test_http_method_values(self):
        """Test that all expected HTTP methods are defined."""
        expected_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}

        actual_methods = {method.value for method in HTTPMethod}
        assert actual_methods == expected_methods

    def test_http_method_string_representation(self):
        """Test string representation of HTTP methods."""
        assert str(HTTPMethod.GET) == "GET"
        assert str(HTTPMethod.POST) == "POST"
        assert str(HTTPMethod.DELETE) == "DELETE"

    def test_http_method_case_sensitivity(self):
        """Test that HTTP methods maintain proper case."""
        assert HTTPMethod.GET.value == "GET"
        assert HTTPMethod.POST.value == "POST"
        assert HTTPMethod.PUT.value == "PUT"


class TestCodeSample:
    """Test the CodeSample data structure."""

    def test_code_sample_creation(self):
        """Test creating a CodeSample instance."""
        sample = CodeSample(
            language=CodeLanguage.PYTHON,
            code='import requests\nresponse = requests.get("/api/users")',
            description="Python example for listing users",
            title="List Users - Python",
        )

        assert sample.language == CodeLanguage.PYTHON
        assert "import requests" in sample.code
        assert sample.description == "Python example for listing users"
        assert sample.title == "List Users - Python"

    def test_code_sample_optional_fields(self):
        """Test CodeSample with optional fields."""
        # Test with minimal required fields
        sample = CodeSample(language=CodeLanguage.CURL, code='curl -X GET "https://api.example.com/users"')

        assert sample.language == CodeLanguage.CURL
        assert sample.code == 'curl -X GET "https://api.example.com/users"'
        assert sample.description is None
        assert sample.title is None

    def test_code_sample_validation(self):
        """Test CodeSample field validation."""
        # Test that empty code raises appropriate error
        with pytest.raises((ValueError, TypeError)):
            CodeSample(language=CodeLanguage.PYTHON, code="")


class TestResponseExample:
    """Test the ResponseExample data structure."""

    def test_response_example_creation(self):
        """Test creating a ResponseExample instance."""
        example = ResponseExample(
            status_code=200,
            description="Successful response",
            content={"users": [{"id": 1, "name": "John"}]},
            headers={"Content-Type": "application/json"},
        )

        assert example.status_code == 200
        assert example.description == "Successful response"
        assert "users" in example.content
        assert example.headers["Content-Type"] == "application/json"

    def test_response_example_optional_fields(self):
        """Test ResponseExample with optional fields."""
        example = ResponseExample(status_code=404, description="Not found")

        assert example.status_code == 404
        assert example.description == "Not found"
        assert example.content is None
        assert example.headers is None

    def test_response_example_status_codes(self):
        """Test various HTTP status codes."""
        status_codes = [200, 201, 400, 401, 403, 404, 500]

        for code in status_codes:
            example = ResponseExample(status_code=code, description=f"Status {code}")
            assert example.status_code == code


class TestParameterDocumentation:
    """Test the ParameterDocumentation data structure."""

    def test_parameter_documentation_creation(self):
        """Test creating a ParameterDocumentation instance."""
        param = ParameterDocumentation(
            name="user_id", description="The unique identifier for the user", example=123, required=True, type="integer"
        )

        assert param.name == "user_id"
        assert "unique identifier" in param.description
        assert param.example == 123
        assert param.required is True
        assert param.type == "integer"

    def test_parameter_documentation_optional_fields(self):
        """Test ParameterDocumentation with optional fields."""
        param = ParameterDocumentation(name="limit", description="Maximum number of items to return")

        assert param.name == "limit"
        assert param.description == "Maximum number of items to return"
        assert param.example is None
        assert param.required is None
        assert param.type is None

    def test_parameter_documentation_types(self):
        """Test different parameter types."""
        types_and_examples = [
            ("string", "example_string"),
            ("integer", 42),
            ("boolean", True),
            ("array", [1, 2, 3]),
            ("object", {"key": "value"}),
        ]

        for param_type, example in types_and_examples:
            param = ParameterDocumentation(
                name=f"test_{param_type}", description=f"A {param_type} parameter", type=param_type, example=example
            )
            assert param.type == param_type
            assert param.example == example


class TestEndpointDocumentation:
    """Test the EndpointDocumentation data structure."""

    def test_endpoint_documentation_creation(self):
        """Test creating an EndpointDocumentation instance."""
        code_samples = [
            CodeSample(language=CodeLanguage.PYTHON, code='import requests\nresponse = requests.get("/api/users")')
        ]

        response_examples = [
            ResponseExample(status_code=200, description="Success", content=[{"id": 1, "name": "John"}])
        ]

        parameters = [ParameterDocumentation(name="limit", description="Maximum items", type="integer", example=50)]

        doc = EndpointDocumentation(
            path="/api/users",
            method=HTTPMethod.GET,
            summary="List users",
            description="Retrieve all users",
            code_samples=code_samples,
            response_examples=response_examples,
            parameters=parameters,
            tags=["users"],
            deprecated=False,
        )

        assert doc.path == "/api/users"
        assert doc.method == HTTPMethod.GET
        assert doc.summary == "List users"
        assert doc.description == "Retrieve all users"
        assert len(doc.code_samples) == 1
        assert len(doc.response_examples) == 1
        assert len(doc.parameters) == 1
        assert "users" in doc.tags
        assert doc.deprecated is False

    def test_endpoint_documentation_optional_fields(self):
        """Test EndpointDocumentation with minimal required fields."""
        doc = EndpointDocumentation(path="/api/health", method=HTTPMethod.GET, summary="Health check")

        assert doc.path == "/api/health"
        assert doc.method == HTTPMethod.GET
        assert doc.summary == "Health check"
        assert doc.description is None
        assert doc.code_samples is None or len(doc.code_samples) == 0
        assert doc.response_examples is None or len(doc.response_examples) == 0
        assert doc.parameters is None or len(doc.parameters) == 0
        assert doc.tags is None or len(doc.tags) == 0
        assert doc.deprecated is None or doc.deprecated is False

    def test_endpoint_documentation_validation(self):
        """Test EndpointDocumentation field validation."""
        # Test that invalid paths raise errors
        with pytest.raises((ValueError, TypeError)):
            EndpointDocumentation(path="", method=HTTPMethod.GET, summary="Test")  # Empty path should be invalid

        # Test that invalid methods raise errors
        with pytest.raises((ValueError, TypeError)):
            EndpointDocumentation(path="/api/test", method="INVALID", summary="Test")  # Invalid method


class TestDocumentationData:
    """Test the DocumentationData data structure."""

    def test_documentation_data_creation(self):
        """Test creating a DocumentationData instance."""
        endpoints = [
            EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users"),
            EndpointDocumentation(path="/api/users", method=HTTPMethod.POST, summary="Create user"),
        ]

        metadata = {"title": "Test API", "version": "1.0.0", "description": "A test API"}

        data = DocumentationData(
            endpoints={f"{ep.method.value}:{ep.path}": ep for ep in endpoints}, global_examples=[], metadata=metadata
        )

        assert len(data["endpoints"]) == 2
        assert data.metadata["title"] == "Test API"
        assert data.metadata["version"] == "1.0.0"

    def test_documentation_data_empty(self):
        """Test DocumentationData with empty collections."""
        data = DocumentationData(endpoints=[], metadata={})

        assert len(data.endpoints) == 0
        assert len(data.metadata) == 0

    def test_documentation_data_filtering(self):
        """Test filtering endpoints by various criteria."""
        endpoints = [
            EndpointDocumentation(path="/api/users", method=HTTPMethod.GET, summary="List users", tags=["users"]),
            EndpointDocumentation(path="/api/auth/login", method=HTTPMethod.POST, summary="Login", tags=["auth"]),
            EndpointDocumentation(
                path="/api/users/{id}", method=HTTPMethod.DELETE, summary="Delete user", tags=["users"], deprecated=True
            ),
        ]

        data = DocumentationData(endpoints=endpoints, metadata={})

        # Filter by tag
        user_endpoints = [ep for ep in data.endpoints if ep.tags and "users" in ep.tags]
        assert len(user_endpoints) == 2

        # Filter by method
        get_endpoints = [ep for ep in data.endpoints if ep.method == HTTPMethod.GET]
        assert len(get_endpoints) == 1

        # Filter by deprecated status
        active_endpoints = [ep for ep in data.endpoints if not ep.deprecated]
        assert len(active_endpoints) == 2


class TestTypeIntegration:
    """Test integration between different type definitions."""

    def test_complete_endpoint_with_all_types(self):
        """Test creating a complete endpoint with all type components."""
        # Create code samples
        code_samples = [
            CodeSample(
                language=CodeLanguage.CURL,
                code='curl -X GET "https://api.example.com/api/users"',
                description="cURL example",
                title="cURL Request",
            ),
            CodeSample(
                language=CodeLanguage.PYTHON,
                code='import requests\nresponse = requests.get("/api/users")',
                description="Python example",
                title="Python Request",
            ),
        ]

        # Create response examples
        response_examples = [
            ResponseExample(
                status_code=200,
                description="Successful response",
                content=[{"id": 1, "name": "John", "email": "john@example.com"}],
                headers={"Content-Type": "application/json"},
            ),
            ResponseExample(
                status_code=400,
                description="Bad request",
                content={"error": "Invalid parameters"},
                headers={"Content-Type": "application/json"},
            ),
        ]

        # Create parameters
        parameters = [
            ParameterDocumentation(
                name="limit",
                description="Maximum number of users to return",
                example=50,
                required=False,
                type="integer",
            ),
            ParameterDocumentation(
                name="offset", description="Number of users to skip", example=0, required=False, type="integer"
            ),
        ]

        # Create endpoint documentation
        endpoint = EndpointDocumentation(
            path="/api/users",
            method=HTTPMethod.GET,
            summary="List all users",
            description="Retrieve a paginated list of users from the system",
            code_samples=code_samples,
            response_examples=response_examples,
            parameters=parameters,
            tags=["users", "list"],
            deprecated=False,
        )

        # Create documentation data
        documentation = DocumentationData(
            endpoints=[endpoint],
            metadata={"title": "User Management API", "version": "1.0.0", "description": "API for managing users"},
        )

        # Verify all components are properly integrated
        assert len(documentation.endpoints) == 1

        ep = documentation.endpoints[0]
        assert ep.path == "/api/users"
        assert ep.method == HTTPMethod.GET
        assert len(ep.code_samples) == 2
        assert len(ep.response_examples) == 2
        assert len(ep.parameters) == 2
        assert len(ep.tags) == 2

        # Verify code samples
        curl_sample = next(s for s in ep.code_samples if s.language == CodeLanguage.CURL)
        python_sample = next(s for s in ep.code_samples if s.language == CodeLanguage.PYTHON)

        assert "curl -X GET" in curl_sample.code
        assert "import requests" in python_sample.code

        # Verify response examples
        success_response = next(r for r in ep.response_examples if r.status_code == 200)
        error_response = next(r for r in ep.response_examples if r.status_code == 400)

        assert success_response.description == "Successful response"
        assert error_response.description == "Bad request"

        # Verify parameters
        limit_param = next(p for p in ep.parameters if p.name == "limit")
        offset_param = next(p for p in ep.parameters if p.name == "offset")

        assert limit_param.type == "integer"
        assert offset_param.example == 0
