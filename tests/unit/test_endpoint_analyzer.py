"""
Tests for the unified endpoint analyzer.
"""

from src.fastmarkdocs.endpoint_analyzer import UnifiedEndpointAnalyzer
from src.fastmarkdocs.types import CodeLanguage, CodeSample, EndpointDocumentation, HTTPMethod, ResponseExample


class TestUnifiedEndpointAnalyzer:
    """Test cases for the UnifiedEndpointAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.openapi_schema = {
            "openapi": "3.0.2",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {"summary": "List users", "responses": {"200": {"description": "Success"}}},
                    "post": {"summary": "Create user", "responses": {"201": {"description": "Created"}}},
                },
                "/users/{id}": {
                    "get": {
                        "summary": "Get user",
                        "parameters": [{"name": "id", "in": "path", "required": True}],
                        "responses": {"200": {"description": "Success"}},
                    },
                    "put": {"summary": "Update user", "responses": {"200": {"description": "Updated"}}},
                },
            },
        }

        self.analyzer = UnifiedEndpointAnalyzer(self.openapi_schema)

    def test_extract_openapi_endpoints(self):
        """Test extraction of OpenAPI endpoints."""
        endpoints = self.analyzer.extract_openapi_endpoints()

        expected = {("GET", "/users"), ("POST", "/users"), ("GET", "/users/{id}"), ("PUT", "/users/{id}")}

        assert endpoints == expected

    def test_extract_openapi_endpoints_with_exclusions(self):
        """Test extraction with exclusions."""
        exclusions = {("POST", "/users")}
        endpoints = self.analyzer.extract_openapi_endpoints(exclusions)

        expected = {("GET", "/users"), ("GET", "/users/{id}"), ("PUT", "/users/{id}")}

        assert endpoints == expected

    def test_extract_documentation_endpoints(self):
        """Test extraction of documentation endpoints."""
        doc_endpoints = [
            EndpointDocumentation(
                method=HTTPMethod.GET,
                path="/users",
                summary="List users",
                description="Get all users",
                code_samples=[],
                response_examples=[],
                parameters=[],
            ),
            EndpointDocumentation(
                method=HTTPMethod.POST,
                path="/users",
                summary="Create user",
                description="Create a new user",
                code_samples=[],
                response_examples=[],
                parameters=[],
            ),
        ]

        endpoints = self.analyzer.extract_documentation_endpoints(doc_endpoints)
        expected = {("GET", "/users"), ("POST", "/users")}

        assert endpoints == expected

    def test_match_endpoints_exact_match(self):
        """Test exact endpoint matching."""
        openapi_endpoints = {("GET", "/users")}
        doc_endpoints = [
            EndpointDocumentation(
                method=HTTPMethod.GET,
                path="/users",
                summary="List users",
                description="Get all users",
                code_samples=[],
                response_examples=[],
                parameters=[],
            )
        ]

        matches = self.analyzer.match_endpoints(openapi_endpoints, doc_endpoints)

        assert len(matches) == 1
        match = matches[0]
        assert match.openapi_method == "GET"
        assert match.openapi_path == "/users"
        assert match.match_confidence == 1.0
        assert match.match_type == "exact"
        assert match.endpoint_doc is not None

    def test_match_endpoints_parameter_mismatch(self):
        """Test endpoint matching with parameter name differences."""
        openapi_endpoints = {("GET", "/users/{id}")}
        doc_endpoints = [
            EndpointDocumentation(
                method=HTTPMethod.GET,
                path="/users/{user_id}",
                summary="Get user",
                description="Get user by ID",
                code_samples=[],
                response_examples=[],
                parameters=[],
            )
        ]

        matches = self.analyzer.match_endpoints(openapi_endpoints, doc_endpoints)

        assert len(matches) == 1
        match = matches[0]
        assert match.match_confidence >= 0.8
        assert match.match_type == "parameter_mismatch"

    def test_match_endpoints_no_match(self):
        """Test endpoint matching when no match exists."""
        openapi_endpoints = {("GET", "/users")}
        doc_endpoints = [
            EndpointDocumentation(
                method=HTTPMethod.GET,
                path="/products",
                summary="List products",
                description="Get all products",
                code_samples=[],
                response_examples=[],
                parameters=[],
            )
        ]

        matches = self.analyzer.match_endpoints(openapi_endpoints, doc_endpoints)

        assert len(matches) == 1
        match = matches[0]
        assert match.match_confidence < 0.5
        assert match.match_type == "no_match"
        assert match.endpoint_doc is None

    def test_analyze_endpoint_complete(self):
        """Test analysis of a complete endpoint."""
        endpoint_doc = EndpointDocumentation(
            method=HTTPMethod.GET,
            path="/users",
            summary="List all users in the system",
            description="This endpoint returns a paginated list of all users in the system with their basic information",
            code_samples=[CodeSample(language=CodeLanguage.CURL, code="curl /users", description="Get users")],
            response_examples=[
                ResponseExample(status_code=200, description="Success", content={"users": []}),
                ResponseExample(status_code=400, description="Bad request", content={"error": "Invalid"}),
            ],
            parameters=[],
        )

        openapi_operation = {"summary": "List users", "responses": {"200": {"description": "Success"}}}

        analysis = self.analyzer.analyze_endpoint(endpoint_doc, openapi_operation)

        assert analysis.completeness_score == 100.0
        assert len(analysis.missing_elements) == 0
        assert len(analysis.quality_issues) == 0
        assert analysis.can_be_enhanced is False  # Complete endpoint with no missing elements or opportunities

    def test_analyze_endpoint_incomplete(self):
        """Test analysis of an incomplete endpoint."""
        endpoint_doc = EndpointDocumentation(
            method=HTTPMethod.GET,
            path="/users/{id}",
            summary="Get",  # Too short
            description="",  # Missing
            code_samples=[],  # Missing
            response_examples=[],  # Missing
            parameters=[],  # Missing for parameterized path
        )

        analysis = self.analyzer.analyze_endpoint(endpoint_doc)

        assert analysis.completeness_score < 50.0
        assert "description" in analysis.missing_elements
        assert "summary" in analysis.missing_elements
        assert "code_samples" in analysis.missing_elements
        assert "response_examples" in analysis.missing_elements
        assert "parameters" in analysis.missing_elements
        assert len(analysis.quality_issues) > 0

    def test_get_openapi_operation(self):
        """Test getting OpenAPI operation."""
        operation = self.analyzer.get_openapi_operation("GET", "/users")

        assert operation["summary"] == "List users"
        assert "200" in operation["responses"]

    def test_get_openapi_operation_not_found(self):
        """Test getting non-existent OpenAPI operation."""
        operation = self.analyzer.get_openapi_operation("DELETE", "/nonexistent")

        assert operation == {}

    def test_find_similar_paths(self):
        """Test finding similar paths."""
        target = "/users/{id}"
        candidates = ["/users/{user_id}", "/users/{userId}", "/products/{id}", "/users"]

        similar = self.analyzer.find_similar_paths(target, candidates)

        # Should return paths with parameter matches first
        assert "/users/{user_id}" in similar
        assert "/users/{userId}" in similar
        # Should not include very different paths
        assert "/products/{id}" not in similar or similar.index("/users/{user_id}") < similar.index("/products/{id}")

    def test_calculate_path_similarity_exact(self):
        """Test path similarity calculation for exact matches."""
        similarity = self.analyzer._calculate_path_similarity("/users", "/users")
        assert similarity == 1.0

    def test_calculate_path_similarity_parameter_match(self):
        """Test path similarity for parameter name differences."""
        similarity = self.analyzer._calculate_path_similarity("/users/{id}", "/users/{user_id}")
        assert similarity >= 0.8

    def test_calculate_path_similarity_different_paths(self):
        """Test path similarity for completely different paths."""
        similarity = self.analyzer._calculate_path_similarity("/users", "/products")
        assert similarity < 0.5

    def test_calculate_completeness_score_perfect(self):
        """Test completeness score calculation for perfect documentation."""
        endpoint_doc = EndpointDocumentation(
            method=HTTPMethod.GET,
            path="/users",
            summary="This is a detailed summary with more than 10 characters",
            description="This is a very detailed description that is definitely longer than 50 characters to get full points",
            code_samples=[],
            response_examples=[
                ResponseExample(status_code=200, description="Success", content={}),
                ResponseExample(status_code=400, description="Error", content={}),
            ],
            parameters=[],
        )

        score = self.analyzer._calculate_completeness_score(endpoint_doc, [], [])
        assert score == 100.0

    def test_calculate_completeness_score_with_parameters(self):
        """Test completeness score for endpoint with path parameters."""
        endpoint_doc = EndpointDocumentation(
            method=HTTPMethod.GET,
            path="/users/{id}",
            summary="Get user by ID",
            description="This endpoint retrieves a specific user by their unique identifier",
            code_samples=[],
            response_examples=[ResponseExample(status_code=200, description="Success", content={})],
            parameters=[],  # Missing parameters
        )

        missing_elements = ["parameters"]
        score = self.analyzer._calculate_completeness_score(endpoint_doc, missing_elements, [])
        assert score == 80.0  # Should lose 10 points for missing parameters, 15 points for single response example

    def test_generate_code_samples(self):
        """Test code sample generation."""
        endpoint_doc = EndpointDocumentation(
            method=HTTPMethod.GET,
            path="/users",
            summary="List users",
            description="Get all users",
            code_samples=[],
            response_examples=[],
            parameters=[],
        )

        openapi_operation = {"summary": "List users", "responses": {"200": {"description": "Success"}}}

        # Mock the code sample generation to avoid external dependencies
        from unittest.mock import patch

        with patch("src.fastmarkdocs.endpoint_analyzer.generate_code_samples_for_endpoint") as mock_gen:
            mock_gen.return_value = [
                CodeSample(language=CodeLanguage.CURL, code="curl /users", description="Get users")
            ]

            samples = self.analyzer.generate_code_samples(endpoint_doc, openapi_operation)

            assert len(samples) == 1
            assert samples[0].language == CodeLanguage.CURL
            mock_gen.assert_called_once()

    def test_calculate_match_confidence_method_mismatch(self):
        """Test match confidence with method mismatch."""
        confidence = self.analyzer._calculate_match_confidence("GET", "/users", "POST", "/users")
        assert confidence == 0.0

    def test_calculate_match_confidence_path_match(self):
        """Test match confidence with path match."""
        confidence = self.analyzer._calculate_match_confidence("GET", "/users", "GET", "/users")
        assert confidence == 1.0
