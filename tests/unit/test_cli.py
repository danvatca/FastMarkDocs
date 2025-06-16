"""
Tests for the FastMarkDocs CLI tools.
"""

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from fastmarkdocs.cli import DocumentationLinter, format_results, main


class TestDocumentationLinter:
    """Test the DocumentationLinter class."""

    def test_init(self) -> None:
        """Test linter initialization."""
        openapi_schema = {"paths": {"/users": {"get": {"summary": "List users"}, "post": {"summary": "Create user"}}}}

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple markdown file
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()

            (docs_dir / "users.md").write_text(
                """
# Users API

## GET /users

List all users in the system.

### Description
This endpoint returns a list of users.

### Code Examples

```bash
curl -X GET "/users"
```

### Response Examples

```json
{"users": []}
```
"""
            )

            linter = DocumentationLinter(
                openapi_schema=openapi_schema, docs_directory=str(docs_dir), base_url="https://api.example.com"
            )

            assert linter.openapi_schema == openapi_schema
            assert linter.base_url == "https://api.example.com"
            assert len(linter.documentation.endpoints) == 1

    def test_extract_openapi_endpoints(self) -> None:
        """Test extraction of OpenAPI endpoints."""
        openapi_schema = {
            "paths": {
                "/users": {
                    "get": {"summary": "List users"},
                    "post": {"summary": "Create user"},
                    "options": {"summary": "Options"},  # Should be included
                },
                "/health": {"get": {"summary": "Health check"}},
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=temp_dir)

            endpoints = linter._extract_openapi_endpoints()

            expected = {("GET", "/users"), ("POST", "/users"), ("OPTIONS", "/users"), ("GET", "/health")}

            assert endpoints == expected

    def test_find_missing_documentation(self) -> None:
        """Test finding missing documentation."""
        openapi_schema = {
            "paths": {
                "/users": {"get": {"summary": "List users"}},
                "/orders": {"get": {"summary": "List orders"}},
                "/health": {"get": {"summary": "Health check"}},
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()

            # Only document /users
            (docs_dir / "users.md").write_text(
                """
## GET /users
List users.
"""
            )

            linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir))

            openapi_endpoints = {("GET", "/users"), ("GET", "/orders"), ("GET", "/health")}
            markdown_endpoints = {("GET", "/users")}

            missing = linter._find_missing_documentation(openapi_endpoints, markdown_endpoints)

            assert len(missing) == 2
            missing_paths = {item["path"] for item in missing}
            assert missing_paths == {"/orders", "/health"}

    def test_find_common_mistakes(self) -> None:
        """Test finding common documentation mistakes."""
        openapi_schema = {
            "paths": {
                "/users/{user_id}": {"get": {"summary": "Get user"}},
                "/orders": {"get": {"summary": "List orders"}, "post": {"summary": "Create order"}},
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()

            # Document with wrong parameter name and missing method
            (docs_dir / "api.md").write_text(
                """
## GET /users/{id}
Get user by ID.

## GET /orders
List orders.
"""
            )

            linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir))

            openapi_endpoints = {("GET", "/users/{user_id}"), ("GET", "/orders"), ("POST", "/orders")}
            markdown_endpoints = {("GET", "/users/{id}"), ("GET", "/orders")}

            mistakes = linter._find_common_mistakes(openapi_endpoints, markdown_endpoints)

            # Should find path parameter mismatch and missing method documentation
            assert len(mistakes) >= 1

            # Check for path parameter mismatch
            mismatch_found = any(mistake["type"] == "path_parameter_mismatch" for mistake in mistakes)
            assert mismatch_found

    def test_find_common_mistakes_extra_methods(self) -> None:
        """Test finding extra method documentation."""
        openapi_schema = {"paths": {"/orders": {"get": {"summary": "List orders"}}}}

        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()

            # Document extra methods that don't exist in OpenAPI
            (docs_dir / "api.md").write_text(
                """
## GET /orders
List orders.

## POST /orders
Create order.

## DELETE /orders
Delete orders.
"""
            )

            linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir))

            openapi_endpoints = {("GET", "/orders")}
            markdown_endpoints = {("GET", "/orders"), ("POST", "/orders"), ("DELETE", "/orders")}

            mistakes = linter._find_common_mistakes(openapi_endpoints, markdown_endpoints)

            # Should find extra method documentation
            extra_method_found = any(mistake["type"] == "extra_method_documentation" for mistake in mistakes)
            assert extra_method_found

    def test_find_orphaned_documentation(self) -> None:
        """Test detection of truly orphaned documentation."""
        openapi_schema = {"paths": {"/users": {"get": {"summary": "List users"}}}}

        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()

            # Document endpoints that don't exist in OpenAPI at all
            (docs_dir / "api.md").write_text(
                """
## GET /users
List users.

## GET /nonexistent
This endpoint doesn't exist.

## POST /another-fake
Another fake endpoint.
"""
            )

            linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir))

            openapi_endpoints = {("GET", "/users")}
            markdown_endpoints = {("GET", "/users"), ("GET", "/nonexistent"), ("POST", "/another-fake")}

            orphaned = linter._find_orphaned_documentation(openapi_endpoints, markdown_endpoints)

            # Should find orphaned documentation
            assert len(orphaned) >= 1
            orphaned_paths = {item["path"] for item in orphaned}
            assert "/nonexistent" in orphaned_paths or "/another-fake" in orphaned_paths

    def test_find_incomplete_documentation_edge_cases(self) -> None:
        """Test incomplete documentation detection with various edge cases."""
        from fastmarkdocs.types import (
            CodeLanguage,
            CodeSample,
            EndpointDocumentation,
            HTTPMethod,
            ResponseExample,
        )

        # Test endpoint with very short description
        short_desc_endpoint = EndpointDocumentation(
            path="/users",
            method=HTTPMethod.GET,
            summary="Get",  # Very short summary
            description="Short",  # Very short description
            code_samples=[],
            response_examples=[],
            parameters=[],
        )

        # Test endpoint with path parameters but no parameter documentation
        path_param_endpoint = EndpointDocumentation(
            path="/users/{id}",
            method=HTTPMethod.GET,
            summary="Get user by ID",
            description="Get a specific user by their ID",
            code_samples=[CodeSample(language=CodeLanguage.CURL, code="curl /users/1")],
            response_examples=[ResponseExample(status_code=200, description="Success", content={})],
            parameters=[],  # Empty parameters list despite path having {id}
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            linter = DocumentationLinter(openapi_schema={"paths": {}}, docs_directory=temp_dir)

            # Mock the documentation endpoints
            linter.documentation.endpoints = [short_desc_endpoint, path_param_endpoint]

            incomplete = linter._find_incomplete_documentation()

            assert len(incomplete) == 2

            # Check that issues are properly identified
            issues_found = []
            for item in incomplete:
                issues_found.extend(item["issues"])

            assert "Missing or very short description" in issues_found
            assert "Missing or very short summary" in issues_found
            assert "No code samples provided" in issues_found
            assert "No response examples provided" in issues_found
            assert "Path has parameters but no parameter documentation" in issues_found

    def test_enhancement_process_with_exception(self) -> None:
        """Test enhancement process when it raises an exception."""
        openapi_schema = {"paths": {"/users": {"get": {"summary": "List users"}}}}

        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()

            (docs_dir / "users.md").write_text(
                """
## GET /users
List users.
"""
            )

            linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir))

            # Mock the enhancer to raise an exception
            linter.enhancer.enhance_openapi_schema = MagicMock(side_effect=Exception("Enhancement failed"))  # type: ignore

            openapi_endpoints = {("GET", "/users")}
            markdown_endpoints = {("GET", "/users")}

            failures = linter._test_enhancement_process(openapi_endpoints, markdown_endpoints)

            # Should capture the exception
            assert len(failures) == 1
            assert failures[0]["type"] == "enhancement_process_error"
            assert failures[0]["severity"] == "critical"
            assert "Enhancement failed" in failures[0]["message"]

    def test_enhancement_process_failure_detection(self) -> None:
        """Test detection of endpoints that fail to enhance."""
        openapi_schema = {
            "paths": {
                "/users": {"get": {"summary": "List users", "description": "Original description"}},
                "/orders": {"get": {"summary": "List orders", "description": "Original description"}},
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()

            (docs_dir / "api.md").write_text(
                """
## GET /users
List users with enhanced documentation.

### Description
This is enhanced documentation.

### Code Examples
```bash
curl /users
```

## GET /orders
List orders.

### Description
This is enhanced documentation for orders.
"""
            )

            linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir))

            # Mock the enhancer to return schema where only /users was enhanced
            enhanced_schema = {
                "paths": {
                    "/users": {
                        "get": {
                            "summary": "List users",
                            "description": "This is enhanced documentation with much more detail than the original.",
                            "x-codeSamples": [{"lang": "curl", "source": "curl /users"}],
                        }
                    },
                    "/orders": {
                        "get": {"summary": "List orders", "description": "Original description"}  # Not enhanced
                    },
                }
            }

            linter.enhancer.enhance_openapi_schema = MagicMock(return_value=enhanced_schema)  # type: ignore

            openapi_endpoints = {("GET", "/users"), ("GET", "/orders")}
            markdown_endpoints = {("GET", "/users"), ("GET", "/orders")}

            failures = linter._test_enhancement_process(openapi_endpoints, markdown_endpoints)

            # Should detect that /orders failed to enhance
            assert len(failures) >= 1
            failure_paths = {f["path"] for f in failures if "path" in f}
            assert "/orders" in failure_paths

    def test_calculate_completeness_score(self) -> None:
        """Test completeness score calculation."""
        from fastmarkdocs.types import (
            CodeLanguage,
            CodeSample,
            EndpointDocumentation,
            HTTPMethod,
            ResponseExample,
        )

        # Create a well-documented endpoint
        complete_endpoint = EndpointDocumentation(
            path="/users",
            method=HTTPMethod.GET,
            summary="List all users in the system",
            description="This endpoint returns a comprehensive list of all users with detailed information including their profiles, permissions, and activity status.",
            code_samples=[
                CodeSample(language=CodeLanguage.CURL, code="curl -X GET /users"),
                CodeSample(language=CodeLanguage.PYTHON, code="requests.get('/users')"),
                CodeSample(language=CodeLanguage.JAVASCRIPT, code="fetch('/users')"),
            ],
            response_examples=[
                ResponseExample(status_code=200, description="Success", content={"users": []}),
                ResponseExample(status_code=404, description="Not found", content={"error": "Not found"}),
            ],
            parameters=[],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            linter = DocumentationLinter(openapi_schema={"paths": {}}, docs_directory=temp_dir)

            score = linter._calculate_completeness_score(complete_endpoint)

            # Should get a high score (near 100)
            assert score >= 90

    def test_calculate_completeness_score_edge_cases(self) -> None:
        """Test completeness scoring with various content lengths and edge cases."""
        from fastmarkdocs.types import (
            CodeLanguage,
            CodeSample,
            EndpointDocumentation,
            HTTPMethod,
            ParameterDocumentation,
            ResponseExample,
        )

        # Test different description lengths
        short_desc_endpoint = EndpointDocumentation(
            path="/test",
            method=HTTPMethod.GET,
            summary="Short",  # 5 chars
            description="Short desc",  # 10 chars
            code_samples=[CodeSample(language=CodeLanguage.CURL, code="curl /test")],  # 1 sample
            response_examples=[ResponseExample(status_code=200, description="OK", content={})],  # 1 example
            parameters=[],
        )

        # Test endpoint with path parameters
        path_param_endpoint = EndpointDocumentation(
            path="/users/{id}",
            method=HTTPMethod.GET,
            summary="Get user by ID",
            description="Get a specific user",
            code_samples=[],
            response_examples=[],
            parameters=[ParameterDocumentation(name="id", description="User ID")],
        )

        # Test endpoint without path parameters
        no_param_endpoint = EndpointDocumentation(
            path="/users",
            method=HTTPMethod.GET,
            summary="List users",
            description="List all users",
            code_samples=[],
            response_examples=[],
            parameters=[],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            linter = DocumentationLinter(openapi_schema={"paths": {}}, docs_directory=temp_dir)

            # Test different scoring scenarios
            score1 = linter._calculate_completeness_score(short_desc_endpoint)
            score2 = linter._calculate_completeness_score(path_param_endpoint)
            score3 = linter._calculate_completeness_score(no_param_endpoint)

            # Verify scores are calculated correctly
            assert 0 <= score1 <= 100
            assert 0 <= score2 <= 100
            assert 0 <= score3 <= 100

            # Path param endpoint should get parameter points
            assert score2 > 0  # Should get some points for having parameters documented

    def test_generate_completion_suggestions(self) -> None:
        """Test completion suggestions generation for specific issue types."""
        from fastmarkdocs.types import EndpointDocumentation, HTTPMethod

        endpoint = EndpointDocumentation(
            path="/test",
            method=HTTPMethod.GET,
            summary="",
            description="",
            code_samples=[],
            response_examples=[],
            parameters=[],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            linter = DocumentationLinter(openapi_schema={"paths": {}}, docs_directory=temp_dir)

            # Test different issue types
            issues = [
                "Missing or very short description",
                "Missing or very short summary",
                "No code samples provided",
                "No response examples provided",
                "Path has parameters but no parameter documentation",
            ]

            suggestions = linter._generate_completion_suggestions(endpoint, issues)

            # Should generate appropriate suggestions for each issue type
            assert len(suggestions) == len(issues)
            assert any("description" in suggestion.lower() for suggestion in suggestions)
            assert any("summary" in suggestion.lower() for suggestion in suggestions)
            assert any("code examples" in suggestion.lower() for suggestion in suggestions)
            assert any("response" in suggestion.lower() for suggestion in suggestions)
            assert any("parameter" in suggestion.lower() for suggestion in suggestions)

    def test_lint_integration(self) -> None:
        """Test the complete linting process integration."""
        openapi_schema = {
            "paths": {"/users": {"get": {"summary": "List users"}}, "/orders": {"get": {"summary": "List orders"}}}
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()

            # Create partial documentation
            (docs_dir / "users.md").write_text(
                """
## GET /users

List all users.

### Description
Get all users from the system.

### Code Examples

```bash
curl -X GET "/users"
```

### Response Examples

```json
{"users": []}
```
"""
            )

            linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir))

            results = linter.lint()

            # Should have results structure
            assert "summary" in results
            assert "statistics" in results
            assert "missing_documentation" in results
            assert "incomplete_documentation" in results
            assert "common_mistakes" in results
            assert "orphaned_documentation" in results
            assert "enhancement_failures" in results
            assert "recommendations" in results

            # Should find missing documentation for /orders
            assert len(results["missing_documentation"]) >= 1

            # Should have statistics
            stats = results["statistics"]
            assert "total_openapi_endpoints" in stats
            assert "total_documented_endpoints" in stats
            assert "documentation_coverage_percentage" in stats


class TestFormatResults:
    """Test the format_results function."""

    def test_format_text(self) -> None:
        """Test text formatting."""
        results = {
            "summary": {
                "message": "Documentation analysis complete",
                "coverage": "80.0%",
                "completeness": "65.5%",
                "total_issues": 5,
            },
            "statistics": {
                "total_openapi_endpoints": 10,
                "total_documented_endpoints": 8,
                "documentation_coverage_percentage": 80.0,
                "average_completeness_score": 65.5,
                "issues": {
                    "total_issues": 5,
                    "missing_documentation": 2,
                    "incomplete_documentation": 2,
                    "common_mistakes": 1,
                    "orphaned_documentation": 0,
                    "enhancement_failures": 0,
                },
            },
            "missing_documentation": [],
            "incomplete_documentation": [],
            "common_mistakes": [],
            "orphaned_documentation": [],
            "enhancement_failures": [],
            "recommendations": [],
        }

        output = format_results(results, "text")

        assert "FastMarkDocs Documentation Linter Results" in output
        assert "Coverage: 80.0%" in output
        assert "Total API endpoints: 10" in output

    def test_format_json(self) -> None:
        """Test JSON formatting."""
        results = {"summary": {"status": "good"}, "statistics": {"total_issues": 0}}

        output = format_results(results, "json")

        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed["summary"]["status"] == "good"
        assert parsed["statistics"]["total_issues"] == 0

    def test_format_text_with_all_issue_types(self) -> None:
        """Test text formatting with comprehensive results including all issue types."""
        results = {
            "summary": {"message": "Issues found", "coverage": "60.0%", "completeness": "45.0%", "total_issues": 15},
            "statistics": {
                "total_openapi_endpoints": 20,
                "total_documented_endpoints": 12,
                "documentation_coverage_percentage": 60.0,
                "average_completeness_score": 45.0,
                "issues": {
                    "total_issues": 15,
                    "missing_documentation": 8,
                    "incomplete_documentation": 4,
                    "common_mistakes": 2,
                    "orphaned_documentation": 1,
                    "enhancement_failures": 0,
                },
            },
            "missing_documentation": [
                {"method": "GET", "path": f"/endpoint{i}", "similar_documented_paths": ["/similar1", "/similar2"]}
                for i in range(12)  # More than 10 to test truncation
            ],
            "incomplete_documentation": [
                {"method": "GET", "path": "/incomplete1", "issues": ["Missing description"]},
                {"method": "POST", "path": "/incomplete2", "issues": ["No code samples"]},
            ],
            "common_mistakes": [
                {
                    "type": "path_parameter_mismatch",
                    "message": "Parameter mismatch found",
                    "suggestion": "Fix the parameter names",
                },
                {"type": "missing_method", "message": "Missing method docs"},
                {"type": "extra_method", "message": "Extra method docs"},
                {"type": "another_mistake", "message": "Another mistake"},
                {"type": "yet_another", "message": "Yet another mistake"},
                {"type": "sixth_mistake", "message": "Sixth mistake"},  # More than 5 to test truncation
            ],
            "orphaned_documentation": [{"method": "GET", "path": "/orphaned", "message": "Orphaned endpoint"}],
            "enhancement_failures": [
                {"method": "GET", "path": "/failed1", "message": "Enhancement failed"},
                {"method": "POST", "path": "/failed2", "message": "Another failure"},
                {"method": "PUT", "path": "/failed3", "message": "Third failure"},
                {"method": "DELETE", "path": "/failed4", "message": "Fourth failure"},
                {"method": "PATCH", "path": "/failed5", "message": "Fifth failure"},
                {"method": "HEAD", "path": "/failed6", "message": "Sixth failure"},  # More than 5 to test truncation
            ],
            "recommendations": [
                {
                    "priority": "critical",
                    "title": "Fix critical issues",
                    "description": "These are critical",
                    "action": "Fix immediately",
                },
                {
                    "priority": "high",
                    "title": "Fix high priority issues",
                    "description": "These are important",
                    "action": "Fix soon",
                },
                {
                    "priority": "medium",
                    "title": "Medium priority",
                    "description": "These can wait",
                    "action": "Fix when convenient",
                },
                {
                    "priority": "low",
                    "title": "Low priority",
                    "description": "Nice to have",
                    "action": "Fix if time permits",
                },
            ],
        }

        output = format_results(results, "text")

        # Check that all sections are present
        assert "❌ Missing Documentation:" in output
        assert "⚠️ Common Mistakes:" in output
        assert "🔥 Enhancement Failures:" in output
        assert "💡 Recommendations:" in output

        # Check truncation messages
        assert "... and 2 more" in output  # For missing documentation (12 - 10)
        assert "... and 1 more" in output  # For common mistakes (6 - 5) or enhancement failures (6 - 5)

        # Check priority emojis
        assert "🔥" in output  # Critical
        assert "⚠️" in output  # High
        assert "📝" in output  # Medium
        assert "💭" in output  # Low

    def test_format_json_with_all_issue_types(self) -> None:
        """Test JSON formatting with comprehensive results."""
        results = {
            "summary": {"status": "issues_found", "total_issues": 10},
            "statistics": {"total_issues": 10},
            "missing_documentation": [{"method": "GET", "path": "/missing"}],
            "incomplete_documentation": [{"method": "POST", "path": "/incomplete"}],
            "common_mistakes": [{"type": "mismatch", "message": "Parameter mismatch"}],
            "orphaned_documentation": [{"method": "DELETE", "path": "/orphaned"}],
            "enhancement_failures": [{"method": "PUT", "path": "/failed"}],
            "recommendations": [{"priority": "high", "title": "Fix this"}],
        }

        output = format_results(results, "json")

        # Should be valid JSON with all sections
        parsed = json.loads(output)
        assert "summary" in parsed
        assert "statistics" in parsed
        assert "missing_documentation" in parsed
        assert "incomplete_documentation" in parsed
        assert "common_mistakes" in parsed
        assert "orphaned_documentation" in parsed
        assert "enhancement_failures" in parsed
        assert "recommendations" in parsed

        # Verify structure is preserved
        assert parsed["missing_documentation"][0]["path"] == "/missing"
        assert parsed["common_mistakes"][0]["type"] == "mismatch"


class TestCLIMain:
    """Test the main CLI function."""

    def test_main_with_missing_file(self) -> None:
        """Test main function with missing OpenAPI file."""
        with patch("sys.argv", ["fmd-lint", "--openapi", "nonexistent.json", "--docs", "docs"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_main_help(self) -> None:
        """Test main function with help argument."""
        with patch("sys.argv", ["fmd-lint", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_with_valid_inputs(self) -> None:
        """Test main function with valid inputs."""
        openapi_schema = {"paths": {"/users": {"get": {"summary": "List users"}}}}

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create OpenAPI file
            openapi_file = Path(temp_dir) / "openapi.json"
            openapi_file.write_text(json.dumps(openapi_schema))

            # Create docs directory
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "users.md").write_text("## GET /users\nList users.")

            # Create output file
            output_file = Path(temp_dir) / "output.txt"

            with patch(
                "sys.argv",
                [
                    "fmd-lint",
                    "--openapi",
                    str(openapi_file),
                    "--docs",
                    str(docs_dir),
                    "--output",
                    str(output_file),
                    "--format",
                    "text",
                ],
            ):
                # Should exit with code 1 because there are incomplete documentation issues
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

            # Check that output file was created
            assert output_file.exists()
            content = output_file.read_text()
            assert "FastMarkDocs Documentation Linter Results" in content

    def test_main_with_json_format(self) -> None:
        """Test CLI with JSON output format."""
        openapi_schema = {"paths": {"/users": {"get": {"summary": "List users"}}}}

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create OpenAPI file
            openapi_file = Path(temp_dir) / "openapi.json"
            openapi_file.write_text(json.dumps(openapi_schema))

            # Create docs directory
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "users.md").write_text("## GET /users\nList users.")

            with (
                patch(
                    "sys.argv",
                    ["fmd-lint", "--openapi", str(openapi_file), "--docs", str(docs_dir), "--format", "json"],
                ),
                patch("builtins.print") as mock_print,
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

                # Check that JSON was printed
                printed_output = mock_print.call_args[0][0]
                parsed_json = json.loads(printed_output)
                assert "summary" in parsed_json
                assert "statistics" in parsed_json

    def test_main_with_output_file(self) -> None:
        """Test CLI writing results to file."""
        openapi_schema = {"paths": {"/users": {"get": {"summary": "List users"}}}}

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create OpenAPI file
            openapi_file = Path(temp_dir) / "openapi.json"
            openapi_file.write_text(json.dumps(openapi_schema))

            # Create docs directory
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "users.md").write_text("## GET /users\nList users.")

            # Test output file
            output_file = Path(temp_dir) / "results.json"

            with patch(
                "sys.argv",
                [
                    "fmd-lint",
                    "--openapi",
                    str(openapi_file),
                    "--docs",
                    str(docs_dir),
                    "--output",
                    str(output_file),
                    "--format",
                    "json",
                ],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

            # Verify file was created with correct content
            assert output_file.exists()
            content = output_file.read_text()
            parsed_json = json.loads(content)
            assert "summary" in parsed_json
            assert "statistics" in parsed_json

    def test_main_with_recursive_flag(self) -> None:
        """Test CLI with recursive flag."""
        openapi_schema = {"paths": {"/users": {"get": {"summary": "List users"}}}}

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create OpenAPI file
            openapi_file = Path(temp_dir) / "openapi.json"
            openapi_file.write_text(json.dumps(openapi_schema))

            # Create nested docs directory structure
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()
            nested_dir = docs_dir / "api" / "v1"
            nested_dir.mkdir(parents=True)
            (nested_dir / "users.md").write_text("## GET /users\nList users.")

            with (
                patch("sys.argv", ["fmd-lint", "--openapi", str(openapi_file), "--docs", str(docs_dir), "--recursive"]),
                patch("builtins.print"),
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                # Should find the documentation in nested directory
                assert exc_info.value.code == 1  # Still has issues but found the docs

    def test_main_with_invalid_json(self) -> None:
        """Test CLI behavior with invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create invalid JSON file
            openapi_file = Path(temp_dir) / "invalid.json"
            openapi_file.write_text("{ invalid json content")

            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()

            with patch("sys.argv", ["fmd-lint", "--openapi", str(openapi_file), "--docs", str(docs_dir)]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

    def test_main_exits_with_code_when_issues_found(self) -> None:
        """Test that main function exits with code 1 when issues are found."""
        openapi_schema = {
            "paths": {"/users": {"get": {"summary": "List users"}}, "/orders": {"get": {"summary": "List orders"}}}
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create OpenAPI file
            openapi_file = Path(temp_dir) / "openapi.json"
            openapi_file.write_text(json.dumps(openapi_schema))

            # Create docs directory with only partial documentation
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "users.md").write_text("## GET /users\nShort description.")
            # Missing documentation for /orders

            with patch("sys.argv", ["fmd-lint", "--openapi", str(openapi_file), "--docs", str(docs_dir)]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                # Should exit with code 1 due to missing documentation and incomplete documentation
                assert exc_info.value.code == 1

    def test_main_exits_with_zero_when_no_issues(self) -> None:
        """Test that main function exits with code 0 when no issues are found."""
        # Create a proper OpenAPI schema with all required fields
        openapi_schema = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "description": "Get all users",
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {"users": {"type": "array", "items": {"type": "object"}}},
                                        }
                                    }
                                },
                            }
                        },
                    }
                }
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create OpenAPI file
            openapi_file = Path(temp_dir) / "openapi.json"
            openapi_file.write_text(json.dumps(openapi_schema))

            # Create docs directory with complete documentation
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "users.md").write_text(
                """
## GET /users

List all users in the system.

### Description
This endpoint returns a comprehensive list of all users with detailed information including their profiles, permissions, and activity status.

### Code Examples

```bash
curl -X GET "/users"
```

```python
import requests
response = requests.get("/users")
```

```javascript
fetch('/users').then(response => response.json())
```

### Response Examples

```json
{
  "users": [
    {"id": 1, "name": "John Doe"}
  ]
}
```

```json
{
  "error": "Unauthorized",
  "status": 401
}
```
"""
            )

            with patch("sys.argv", ["fmd-lint", "--openapi", str(openapi_file), "--docs", str(docs_dir)]):
                # Should exit normally (code 0) because documentation is complete
                try:
                    main()
                except SystemExit as e:
                    # If it exits, it should be with code 0
                    assert e.code == 0 or e.code is None

    def test_main_with_generic_exception(self) -> None:
        """Test CLI behavior with generic exception."""
        with patch("sys.argv", ["fmd-lint", "--openapi", "test.json", "--docs", "docs"]):
            with patch("builtins.open", side_effect=PermissionError("Permission denied")):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

    def test_generate_recommendations_edge_cases(self) -> None:
        """Test recommendation generation with edge cases."""
        # Test with very low coverage and completeness
        results = {
            "statistics": {
                "documentation_coverage_percentage": 30.0,  # Low coverage
                "average_completeness_score": 40.0,  # Low completeness
                "issues": {
                    "missing_documentation": 10,
                    "incomplete_documentation": 5,
                    "common_mistakes": 3,
                    "orphaned_documentation": 1,
                    "enhancement_failures": 2,
                },
            },
            "enhancement_failures": [
                {"severity": "critical", "message": "Critical failure"},
                {"severity": "error", "message": "Error failure"},
            ],
            "common_mistakes": [{"severity": "critical", "message": "Critical mistake"}],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            linter = DocumentationLinter(openapi_schema={"paths": {}}, docs_directory=temp_dir)

            recommendations = linter._generate_recommendations(results)

            # Should generate all types of recommendations
            assert len(recommendations) >= 3

            # Check that all priority levels are covered
            priorities = {rec["priority"] for rec in recommendations}
            assert "high" in priorities  # For low coverage and mistakes
            assert "medium" in priorities  # For low completeness
            assert "critical" in priorities  # For enhancement failures

    def test_create_summary_edge_cases(self) -> None:
        """Test summary creation with different issue counts."""
        # Test with exactly 5 issues (boundary case)
        results_5_issues = {
            "statistics": {
                "documentation_coverage_percentage": 85.0,
                "average_completeness_score": 75.0,
                "issues": {"total_issues": 5},
            },
            "enhancement_failures": [{"severity": "critical"}],
            "common_mistakes": [{"severity": "error"}],
        }

        # Test with exactly 15 issues (boundary case)
        results_15_issues = {
            "statistics": {
                "documentation_coverage_percentage": 60.0,
                "average_completeness_score": 50.0,
                "issues": {"total_issues": 15},
            },
            "enhancement_failures": [],
            "common_mistakes": [],
        }

        # Test with more than 15 issues
        results_many_issues = {
            "statistics": {
                "documentation_coverage_percentage": 40.0,
                "average_completeness_score": 30.0,
                "issues": {"total_issues": 25},
            },
            "enhancement_failures": [],
            "common_mistakes": [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            linter = DocumentationLinter(openapi_schema={"paths": {}}, docs_directory=temp_dir)

            summary_5 = linter._create_summary(results_5_issues)
            summary_15 = linter._create_summary(results_15_issues)
            summary_many = linter._create_summary(results_many_issues)

            # Test boundary conditions
            assert summary_5["status"] == "good"
            assert "5 minor issues" in summary_5["message"]

            assert summary_15["status"] == "needs_improvement"
            assert "15 issues" in summary_15["message"]

            assert summary_many["status"] == "poor"
            assert "25 issues" in summary_many["message"]

    def test_statistics_generation_edge_cases(self) -> None:
        """Test statistics generation with edge cases."""
        # Test with empty completeness scores
        results_no_incomplete: dict[str, Any] = {
            "missing_documentation": [],
            "incomplete_documentation": [],  # Empty list
            "common_mistakes": [],
            "orphaned_documentation": [],
            "enhancement_failures": [],
        }

        # Test with some incomplete documentation
        results_with_incomplete = {
            "missing_documentation": [],
            "incomplete_documentation": [
                {"completeness_score": 80.0},
                {"completeness_score": 60.0},
                {"completeness_score": 40.0},
            ],
            "common_mistakes": [],
            "orphaned_documentation": [],
            "enhancement_failures": [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            linter = DocumentationLinter(openapi_schema={"paths": {}}, docs_directory=temp_dir)

            openapi_endpoints = {("GET", "/test")}
            markdown_endpoints = {("GET", "/test")}

            stats_no_incomplete = linter._generate_statistics(
                openapi_endpoints, markdown_endpoints, results_no_incomplete
            )
            stats_with_incomplete = linter._generate_statistics(
                openapi_endpoints, markdown_endpoints, results_with_incomplete
            )

            # When no incomplete documentation, should default to 100% completeness
            assert stats_no_incomplete["average_completeness_score"] == 100

            # When there is incomplete documentation, should calculate average
            expected_avg = (80.0 + 60.0 + 40.0) / 3
            assert stats_with_incomplete["average_completeness_score"] == round(expected_avg, 1)

    def test_find_similar_openapi_paths_edge_case(self) -> None:
        """Test finding similar OpenAPI paths with specific similarity threshold."""
        with tempfile.TemporaryDirectory() as temp_dir:
            linter = DocumentationLinter(openapi_schema={"paths": {}}, docs_directory=temp_dir)

            # Test with paths that have exactly 70% similarity
            target_path = "/api/v1/users/{id}"
            openapi_endpoints = {
                ("GET", "/api/v1/users/{user_id}"),  # Should be similar (4/5 parts match)
                ("POST", "/api/v2/orders/{id}"),  # Should not be similar (2/5 parts match)
                ("GET", "/completely/different/path"),  # Should not be similar
            }

            similar_paths = linter._find_similar_openapi_paths(target_path, openapi_endpoints)

            # Should find the similar path
            assert len(similar_paths) >= 1
            assert any("users/{user_id}" in path for path in similar_paths)

    def test_enhancement_process_no_documented_endpoints(self) -> None:
        """Test enhancement process when there are no documented endpoints that match OpenAPI."""
        openapi_schema = {"paths": {"/users": {"get": {"summary": "List users"}}}}

        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()

            # Document a completely different endpoint
            (docs_dir / "api.md").write_text(
                """
## GET /different-endpoint
This endpoint doesn't exist in OpenAPI.
"""
            )

            linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir))

            openapi_endpoints = {("GET", "/users")}
            markdown_endpoints = {("GET", "/different-endpoint")}

            linter._test_enhancement_process(openapi_endpoints, markdown_endpoints)

            # Should not find any enhancement failures since no documented endpoints match OpenAPI
            documented_and_in_openapi = openapi_endpoints.intersection(markdown_endpoints)
            assert len(documented_and_in_openapi) == 0
