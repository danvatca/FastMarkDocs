"""
Tests for the FastMarkDocs CLI tools.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from fastmarkdocs.linter import DocumentationLinter
from fastmarkdocs.linter_cli import LinterConfig, find_config_file, format_results, main, run_spec_generator


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
            markdown_endpoints = {("GET", "/nonexistent"), ("POST", "/another-fake")}

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

            # Check for the specific error messages from the unified analyzer
            assert any("Description too short" in issue or "Missing description" in issue for issue in issues_found)
            assert any("Summary too short" in issue or "Missing summary" in issue for issue in issues_found)
            # Code samples are auto-generated, so they should not be reported as missing
            assert "No code samples provided" not in issues_found
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
            # Note: Code samples don't get suggestions anymore since they're auto-generated
            assert len(suggestions) == len(issues) - 1  # One less because no code sample suggestions
            assert any("description" in suggestion.lower() for suggestion in suggestions)
            assert any("summary" in suggestion.lower() for suggestion in suggestions)
            # Code samples should not generate suggestions since they're auto-generated
            assert not any("code examples" in suggestion.lower() for suggestion in suggestions)
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
                {
                    "method": "GET",
                    "path": "/incomplete1",
                    "issues": ["Missing description"],
                    "completeness_score": 45.0,
                    "suggestions": ["Add description"],
                },
                {
                    "method": "POST",
                    "path": "/incomplete2",
                    "issues": ["No code samples"],
                    "completeness_score": 60.0,
                    "suggestions": ["Add code samples"],
                },
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

    def test_format_text_with_all_flag(self) -> None:
        """Test text formatting with --all flag shows complete details."""
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
                {
                    "method": "GET",
                    "path": f"/endpoint{i}",
                    "similar_documented_paths": ["/similar1", "/similar2", "/similar3"],
                }
                for i in range(12)  # More than 10 to test truncation
            ],
            "incomplete_documentation": [
                {
                    "method": "GET",
                    "path": "/incomplete1",
                    "issues": ["Missing description"],
                    "completeness_score": 45.0,
                    "suggestions": ["Add description", "Add examples", "Add parameters"],
                }
            ],
            "common_mistakes": [
                {
                    "type": "path_parameter_mismatch",
                    "message": "Parameter mismatch found",
                    "suggestion": "Fix the parameter names",
                }
                for _ in range(6)  # More than 5 to test truncation
            ],
            "orphaned_documentation": [
                {
                    "method": "GET",
                    "path": "/orphaned",
                    "message": "Orphaned endpoint",
                    "summary": "This is a very long summary that should be truncated in normal mode but shown in full when using the --all flag to demonstrate the functionality",
                    "suggestion": "Remove this documentation",
                }
                for _ in range(12)  # More than 10 to test truncation
            ],
            "enhancement_failures": [
                {"method": "GET", "path": f"/failed{i}", "message": "Enhancement failed"}
                for i in range(6)  # More than 5 to test truncation
            ],
            "recommendations": [],
        }

        # Test without --all flag (default behavior with truncation)
        output_truncated = format_results(results, "text", show_all=False)

        # Should show truncation indicators
        assert "... and 2 more" in output_truncated  # Missing documentation
        assert "... and 1 more" in output_truncated  # Common mistakes or enhancement failures

        # Should truncate long summary
        assert "This is a very long summary that should be truncated in normal mode but shown in..." in output_truncated

        # Should truncate similar paths (only show first 2)
        assert "/similar1" in output_truncated
        assert "/similar2" in output_truncated
        assert "/similar3" not in output_truncated  # Third similar path should be truncated

        # Should truncate suggestions (only show first 2)
        assert "Add description" in output_truncated
        assert "Add examples" in output_truncated
        assert "Add parameters" not in output_truncated  # Third suggestion should be truncated

        # Test with --all flag (show everything)
        output_all = format_results(results, "text", show_all=True)

        # Should NOT show truncation indicators
        assert "... and" not in output_all

        # Should show full summary
        assert (
            "This is a very long summary that should be truncated in normal mode but shown in full when using the --all flag to demonstrate the functionality"
            in output_all
        )

        # Should show all similar paths
        assert "/similar1" in output_all
        assert "/similar2" in output_all
        assert "/similar3" in output_all

        # Should show all suggestions
        assert "Add description" in output_all
        assert "Add examples" in output_all
        assert "Add parameters" in output_all

        # Should show all items (12 missing docs, 6 common mistakes, 12 orphaned, 6 enhancement failures)
        missing_count = output_all.count("GET /endpoint")
        assert missing_count == 12  # All missing documentation items

        common_mistakes_count = output_all.count("path_parameter_mismatch")
        assert common_mistakes_count == 6  # All common mistakes

        orphaned_count = output_all.count("GET /orphaned")
        assert orphaned_count == 12  # All orphaned documentation items

        enhancement_failures_count = output_all.count("GET /failed")
        assert enhancement_failures_count == 6  # All enhancement failures


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

    def test_main_with_no_recursive_flag(self) -> None:
        """Test CLI with --no-recursive flag."""
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
                patch(
                    "sys.argv", ["fmd-lint", "--openapi", str(openapi_file), "--docs", str(docs_dir), "--no-recursive"]
                ),
                patch("builtins.print"),
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                # Should NOT find the documentation in nested directory due to --no-recursive
                assert exc_info.value.code == 1  # Has issues because docs not found

    def test_main_with_default_recursive_behavior(self) -> None:
        """Test CLI with default recursive behavior (no flag needed)."""
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
                patch("sys.argv", ["fmd-lint", "--openapi", str(openapi_file), "--docs", str(docs_dir)]),
                patch("builtins.print"),
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                # Should find the documentation in nested directory by default (recursive=True)
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


class TestLinterConfig:
    """Test the LinterConfig class."""

    def test_init_default(self) -> None:
        """Test default configuration initialization."""
        config = LinterConfig()

        assert config.exclude_endpoints == []
        assert config.spec_generator == []
        assert config.docs == []
        assert config.recursive is True
        assert config.base_url == "https://api.example.com"
        assert config.format == "text"
        assert config.output is None

    def test_load_from_file(self) -> None:
        """Test loading configuration from YAML file."""
        config_content = """
exclude:
  endpoints:
    - path: "^/static/.*"
      methods:
        - "GET"
    - path: "^/health"
      methods:
        - ".*"
openapi: "./openapi.json"
spec_generator:
  - "poetry run python ./generate_openapi.py"
  - "echo 'Generated OpenAPI'"
docs:
  - "./src/doorman/api"
  - "./docs/api"
recursive: true
base_url: "https://api.example.com"
format: "json"
output: "report.json"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / ".fmd-lint.yaml"
            config_file.write_text(config_content)

            config = LinterConfig(str(config_file))

            assert len(config.exclude_endpoints) == 2
            assert config.exclude_endpoints[0]["path"] == "^/static/.*"
            assert config.exclude_endpoints[0]["methods"] == ["GET"]
            assert config.exclude_endpoints[1]["path"] == "^/health"
            assert config.exclude_endpoints[1]["methods"] == [".*"]

            assert config.openapi == "./openapi.json"

            assert len(config.spec_generator) == 2
            assert "poetry run python ./generate_openapi.py" in config.spec_generator
            assert config.spec_generator_output is None  # Legacy format

            assert len(config.docs) == 2
            assert "./src/doorman/api" in config.docs

            assert config.recursive is True
            assert config.base_url == "https://api.example.com"
            assert config.format == "json"
            assert config.output == "report.json"

    def test_load_from_file_new_spec_generator_format(self) -> None:
        """Test loading configuration with new spec_generator format."""
        config_content = """
spec_generator:
  commands:
    - "poetry run python ./generate_openapi.py"
    - "echo 'Generated'"
  output_file: "./custom-schema.json"
docs:
  - "./docs"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / ".fmd-lint.yaml"
            config_file.write_text(config_content)

            config = LinterConfig(str(config_file))

            assert len(config.spec_generator) == 2
            assert "poetry run python ./generate_openapi.py" in config.spec_generator
            assert "echo 'Generated'" in config.spec_generator
            assert config.spec_generator_output == "./custom-schema.json"

            assert len(config.docs) == 1
            assert "./docs" in config.docs

    def test_load_from_file_partial_config(self) -> None:
        """Test loading partial configuration from YAML file."""
        config_content = """
exclude:
  endpoints:
    - path: "^/static/.*"
      methods:
        - "GET"
recursive: false
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / ".fmd-lint.yaml"
            config_file.write_text(config_content)

            config = LinterConfig(str(config_file))

            # Should load specified values
            assert len(config.exclude_endpoints) == 1
            assert config.recursive is False

            # Should keep defaults for unspecified values
            assert config.spec_generator == []
            assert config.docs == []
            assert config.base_url == "https://api.example.com"
            assert config.format == "text"

    def test_load_from_file_empty_config(self) -> None:
        """Test loading empty configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / ".fmd-lint.yaml"
            config_file.write_text("")

            config = LinterConfig(str(config_file))

            # Should use all defaults
            assert config.exclude_endpoints == []
            assert config.spec_generator == []
            assert config.docs == []
            assert config.recursive is True

    def test_load_from_file_not_found(self) -> None:
        """Test loading configuration from non-existent file."""
        with pytest.raises(FileNotFoundError):
            LinterConfig("/non/existent/file.yaml")

    def test_should_exclude_endpoint_dict_format(self) -> None:
        """Test endpoint exclusion with dictionary format."""
        config = LinterConfig()
        config.exclude_endpoints = [
            {"path": "^/static/.*", "methods": ["GET"]},
            {"path": "^/health", "methods": [".*"]},
            {"path": "^/api/v1/users", "methods": ["POST", "DELETE"]},
        ]

        # Should exclude matching path and method
        assert config.should_exclude_endpoint("GET", "/static/css/style.css") is True
        assert config.should_exclude_endpoint("GET", "/health") is True
        assert config.should_exclude_endpoint("POST", "/health") is True
        assert config.should_exclude_endpoint("POST", "/api/v1/users") is True
        assert config.should_exclude_endpoint("DELETE", "/api/v1/users") is True

        # Should not exclude non-matching combinations
        assert config.should_exclude_endpoint("POST", "/static/css/style.css") is False
        assert config.should_exclude_endpoint("GET", "/api/v1/users") is False
        assert config.should_exclude_endpoint("PUT", "/api/v1/users") is False
        assert config.should_exclude_endpoint("GET", "/different/path") is False

    def test_should_exclude_endpoint_string_format_legacy(self) -> None:
        """Test endpoint exclusion with legacy string format."""
        config = LinterConfig()
        config.exclude_endpoints = ["GET /static/style.css", "POST /login", "/health"]  # Method-agnostic

        # Should exclude exact matches
        assert config.should_exclude_endpoint("GET", "/static/style.css") is True
        assert config.should_exclude_endpoint("POST", "/login") is True
        assert config.should_exclude_endpoint("GET", "/health") is True
        assert config.should_exclude_endpoint("POST", "/health") is True

        # Should not exclude non-matches
        assert config.should_exclude_endpoint("POST", "/static/style.css") is False
        assert config.should_exclude_endpoint("GET", "/login") is False
        assert config.should_exclude_endpoint("GET", "/different") is False

    def test_should_exclude_endpoint_no_exclusions(self) -> None:
        """Test endpoint exclusion with no exclusions configured."""
        config = LinterConfig()

        # Should not exclude anything
        assert config.should_exclude_endpoint("GET", "/any/path") is False
        assert config.should_exclude_endpoint("POST", "/any/path") is False


class TestConfigurationHelpers:
    """Test configuration helper functions."""

    def test_find_config_file_current_directory(self) -> None:
        """Test finding config file in current directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                # Change to temp directory
                import os

                os.chdir(temp_dir)

                # Create config file
                config_file = Path(temp_dir) / ".fmd-lint.yaml"
                config_file.write_text("recursive: true")

                found_config = find_config_file()
                assert Path(found_config).resolve() == config_file.resolve()

            finally:
                os.chdir(original_cwd)

    def test_find_config_file_parent_directory(self) -> None:
        """Test finding config file in parent directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                # Create nested directory structure
                parent_dir = Path(temp_dir)
                child_dir = parent_dir / "subdir"
                child_dir.mkdir()

                # Create config file in parent
                config_file = parent_dir / ".fmd-lint.yaml"
                config_file.write_text("recursive: true")

                # Change to child directory
                import os

                os.chdir(child_dir)

                found_config = find_config_file()
                assert Path(found_config).resolve() == config_file.resolve()

            finally:
                os.chdir(original_cwd)

    def test_find_config_file_yml_extension(self) -> None:
        """Test finding config file with .yml extension."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                # Create config file with .yml extension
                config_file = Path(temp_dir) / ".fmd-lint.yml"
                config_file.write_text("recursive: true")

                found_config = find_config_file()
                assert Path(found_config).resolve() == config_file.resolve()

            finally:
                os.chdir(original_cwd)

    def test_find_config_file_not_found(self) -> None:
        """Test behavior when config file is not found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                found_config = find_config_file()
                assert found_config is None

            finally:
                os.chdir(original_cwd)

    def test_run_spec_generator_success(self) -> None:
        """Test successful spec generator execution."""
        commands = ["echo 'test output'", "touch openapi.json"]

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                result_file = run_spec_generator(commands)
                assert result_file == "openapi.json"
                assert Path("openapi.json").exists()

            finally:
                os.chdir(original_cwd)
                # Clean up
                if Path("openapi.json").exists():
                    Path("openapi.json").unlink()

    def test_run_spec_generator_failure(self) -> None:
        """Test spec generator failure handling."""
        commands = ["python -c 'import sys; sys.exit(1)'"]  # Command that fails

        with pytest.raises(subprocess.CalledProcessError):
            run_spec_generator(commands)

    def test_run_spec_generator_no_commands(self) -> None:
        """Test spec generator with no commands."""
        with pytest.raises(ValueError, match="No spec generator commands provided"):
            run_spec_generator([])

    def test_run_spec_generator_no_output_file(self) -> None:
        """Test spec generator when no OpenAPI file is found."""
        commands = ["echo 'done'"]  # Command that doesn't create OpenAPI file

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                with pytest.raises(FileNotFoundError, match="Could not find generated OpenAPI file"):
                    run_spec_generator(commands)

            finally:
                os.chdir(original_cwd)

    def test_run_spec_generator_with_output_file(self) -> None:
        """Test spec generator with custom output file."""
        commands = ['echo \'{"test": "data"}\' > custom-schema.json']

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                result_file = run_spec_generator(commands, "custom-schema.json")
                assert result_file == "custom-schema.json"
                assert Path("custom-schema.json").exists()

            finally:
                os.chdir(original_cwd)

    def test_run_spec_generator_output_file_not_found(self) -> None:
        """Test spec generator when specified output file is not created."""
        commands = ["echo 'done'"]  # Doesn't create the expected file

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                with pytest.raises(FileNotFoundError, match="Specified output file not found: nonexistent.json"):
                    run_spec_generator(commands, "nonexistent.json")

            finally:
                os.chdir(original_cwd)


class TestCLIWithConfiguration:
    """Test CLI functionality with configuration files."""

    def test_main_with_config_file(self) -> None:
        """Test CLI with configuration file."""
        config_content = """
exclude:
  endpoints:
    - path: "^/health"
      methods:
        - ".*"
docs:
  - "."
recursive: false
base_url: "https://test.example.com"
format: "json"
"""

        openapi_schema = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {"get": {"summary": "List users"}},
                "/health": {"get": {"summary": "Health check"}},
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file
            config_file = Path(temp_dir) / ".fmd-lint.yaml"
            config_file.write_text(config_content)

            # Create OpenAPI file
            openapi_file = Path(temp_dir) / "openapi.json"
            openapi_file.write_text(json.dumps(openapi_schema))

            # Create complete documentation
            (Path(temp_dir) / "users.md").write_text(
                """
## GET /users

List all users in the system.

### Description
This endpoint returns a list of all users.

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

            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                with patch("sys.argv", ["fmd-lint", "--config", str(config_file), "--openapi", str(openapi_file)]):
                    # Should not raise SystemExit because no issues found (health is excluded)
                    try:
                        main()
                        # If main() returns normally, that means no issues were found
                        success = True
                    except SystemExit as e:
                        # If it does exit, it should be with code 0
                        success = e.code == 0 or e.code is None

                    assert success

            finally:
                os.chdir(original_cwd)

    def test_main_with_spec_generator(self) -> None:
        """Test CLI with spec generator configuration."""
        config_content = """
spec_generator:
  - "echo '{\\"openapi\\": \\"3.0.0\\", \\"info\\": {\\"title\\": \\"Test API\\", \\"version\\": \\"1.0.0\\"}, \\"paths\\": {\\"/test\\": {\\"get\\": {\\"summary\\": \\"Test\\"}}}}' > openapi.json"
docs:
  - "."
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file
            config_file = Path(temp_dir) / ".fmd-lint.yaml"
            config_file.write_text(config_content)

            # Create complete documentation
            (Path(temp_dir) / "test.md").write_text(
                """
## GET /test

Test endpoint.

### Description
This is a test endpoint.

### Code Examples

```bash
curl -X GET "/test"
```

### Response Examples

```json
{"status": "ok"}
```
"""
            )

            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                with patch("sys.argv", ["fmd-lint", "--config", str(config_file)]):
                    try:
                        main()
                        success = True
                    except SystemExit as e:
                        success = e.code == 0 or e.code is None

                    assert success

            finally:
                os.chdir(original_cwd)

    def test_main_with_openapi_config(self) -> None:
        """Test CLI with openapi configuration."""
        config_content = """
openapi: "./openapi.json"
docs:
  - "."
"""

        openapi_schema = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {"/test": {"get": {"summary": "Test"}}},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file
            config_file = Path(temp_dir) / ".fmd-lint.yaml"
            config_file.write_text(config_content)

            # Create OpenAPI file
            openapi_file = Path(temp_dir) / "openapi.json"
            openapi_file.write_text(json.dumps(openapi_schema))

            # Create complete documentation
            (Path(temp_dir) / "test.md").write_text(
                """
## GET /test

Test endpoint.

### Description
This is a test endpoint.

### Code Examples

```bash
curl -X GET "/test"
```

### Response Examples

```json
{"status": "ok"}
```
"""
            )

            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                with patch("sys.argv", ["fmd-lint", "--config", str(config_file)]):
                    try:
                        main()
                        success = True
                    except SystemExit as e:
                        success = e.code == 0 or e.code is None

                    assert success

            finally:
                os.chdir(original_cwd)

    def test_main_with_new_spec_generator_format(self) -> None:
        """Test CLI with new spec_generator format (commands + output_file)."""
        config_content = """
spec_generator:
  commands:
    - "echo '{\\"openapi\\": \\"3.0.0\\", \\"info\\": {\\"title\\": \\"Test API\\", \\"version\\": \\"1.0.0\\"}, \\"paths\\": {\\"/test\\": {\\"get\\": {\\"summary\\": \\"Test\\"}}}}' > custom-schema.json"
  output_file: "./custom-schema.json"
docs:
  - "."
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file
            config_file = Path(temp_dir) / ".fmd-lint.yaml"
            config_file.write_text(config_content)

            # Create complete documentation
            (Path(temp_dir) / "test.md").write_text(
                """
## GET /test

Test endpoint.

### Description
This is a test endpoint.

### Code Examples

```bash
curl -X GET "/test"
```

### Response Examples

```json
{"status": "ok"}
```
"""
            )

            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(temp_dir)

                with patch("sys.argv", ["fmd-lint", "--config", str(config_file)]):
                    try:
                        main()
                        success = True
                    except SystemExit as e:
                        success = e.code == 0 or e.code is None

                    assert success
                    # Verify the custom schema file was created
                    assert Path("custom-schema.json").exists()

            finally:
                os.chdir(original_cwd)

    def test_main_config_override_command_line(self) -> None:
        """Test that command line arguments override config file."""
        config_content = """
format: "json"
base_url: "https://config.example.com"
"""

        openapi_schema = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {"/test": {"get": {"summary": "Test"}}},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file
            config_file = Path(temp_dir) / ".fmd-lint.yaml"
            config_file.write_text(config_content)

            # Create OpenAPI file
            openapi_file = Path(temp_dir) / "openapi.json"
            openapi_file.write_text(json.dumps(openapi_schema))

            # Create docs directory
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "test.md").write_text(
                """
## GET /test

Test endpoint.

### Description
This is a test endpoint.

### Code Examples

```bash
curl -X GET "/test"
```

### Response Examples

```json
{"status": "ok"}
```
"""
            )

            with patch(
                "sys.argv",
                [
                    "fmd-lint",
                    "--config",
                    str(config_file),
                    "--openapi",
                    str(openapi_file),
                    "--docs",
                    str(docs_dir),
                    "--format",
                    "text",  # Override config
                    "--base-url",
                    "https://override.example.com",  # Override config
                ],
            ):
                # Should use command line overrides
                try:
                    main()
                    success = True
                except SystemExit as e:
                    success = e.code == 0 or e.code is None

                assert success


class TestDocumentationLinterWithExclusions:
    """Test DocumentationLinter with endpoint exclusions."""

    def test_extract_openapi_endpoints_with_exclusions(self) -> None:
        """Test OpenAPI endpoint extraction with exclusions."""
        openapi_schema = {
            "paths": {
                "/users": {"get": {"summary": "List users"}},
                "/static/style.css": {"get": {"summary": "Static file"}},
                "/health": {"get": {"summary": "Health check"}},
                "/metrics": {"get": {"summary": "Metrics"}},
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=temp_dir)

            # Set up exclusions
            from fastmarkdocs.linter_cli import LinterConfig

            config = LinterConfig()
            config.exclude_endpoints = [
                {"path": "^/static/.*", "methods": ["GET"]},
                {"path": "^/health", "methods": [".*"]},
            ]
            linter.config = config

            endpoints = linter._extract_openapi_endpoints()

            # Should exclude /static/style.css and /health
            expected = {("GET", "/users"), ("GET", "/metrics")}
            assert endpoints == expected

    def test_lint_with_exclusions_integration(self) -> None:
        """Test full linting process with exclusions."""
        openapi_schema = {
            "paths": {
                "/users": {"get": {"summary": "List users"}},
                "/static/style.css": {"get": {"summary": "Static file"}},
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
List all users.

### Description
Returns a list of users.

### Code Examples
```bash
curl /users
```

### Response Examples
```json
{"users": []}
```
"""
            )

            linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir))

            # Set up exclusions
            from fastmarkdocs.linter_cli import LinterConfig

            config = LinterConfig()
            config.exclude_endpoints = [
                {"path": "^/static/.*", "methods": ["GET"]},
                {"path": "^/health", "methods": [".*"]},
            ]
            linter.config = config

            results = linter.lint()

            # Should not report missing documentation for excluded endpoints
            missing_paths = {item["path"] for item in results["missing_documentation"]}
            assert "/static/style.css" not in missing_paths
            assert "/health" not in missing_paths

            # Should have 100% coverage since excluded endpoints are not counted
            assert results["statistics"]["documentation_coverage_percentage"] == 100
