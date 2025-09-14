"""
Tests for scaffolder file processing, section inference, and documentation generation.

This module tests how the scaffolder processes different types of Python files,
automatically infers appropriate sections for endpoints, and generates documentation.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from fastmarkdocs.scaffolder import (
    DocumentationInitializer,
    EndpointInfo,
    FastAPIEndpointScanner,
    MarkdownScaffoldGenerator,
    ParameterInfo,
)


class TestFileProcessingBehavior:
    """Test how the scanner processes different types of Python files during discovery."""

    def test_skips_files_with_invalid_python_syntax(self) -> None:
        """Scanner should gracefully skip files with syntax errors without crashing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file with syntax error
            bad_file = Path(temp_dir) / "bad_syntax.py"
            bad_file.write_text("def invalid_syntax(\n    # Missing closing parenthesis")

            scanner = FastAPIEndpointScanner(temp_dir)

            # Should not raise exception, just skip the file
            scanner._scan_file(bad_file)
            # Should have no endpoints from this file
            assert len(scanner.endpoints) == 0

    def test_skips_files_with_encoding_issues(self) -> None:
        """Scanner should gracefully skip files with invalid UTF-8 encoding."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file with invalid UTF-8
            bad_file = Path(temp_dir) / "bad_encoding.py"
            bad_file.write_bytes(b"\xff\xfe# Invalid UTF-8")

            scanner = FastAPIEndpointScanner(temp_dir)

            # Should not raise exception, just skip the file
            scanner._scan_file(bad_file)
            # Should have no endpoints from this file
            assert len(scanner.endpoints) == 0

    def test_handles_missing_files_gracefully(self) -> None:
        """Scanner should handle attempts to scan non-existent files without crashing."""
        scanner = FastAPIEndpointScanner(".")

        # Try to scan a non-existent file
        non_existent = Path("non_existent_file.py")

        # Should not raise exception
        scanner._scan_file(non_existent)
        assert len(scanner.endpoints) == 0

    def test_processes_mixed_file_types_in_directory(self) -> None:
        """Scanner should process valid Python files and skip problematic ones in a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create valid Python file
            valid_file = temp_path / "valid.py"
            valid_file.write_text(
                """
from fastapi import APIRouter
router = APIRouter(tags=["test"])

@router.get("/test")
def test_endpoint():
    return {"test": "data"}
"""
            )

            # Create invalid Python file
            invalid_file = temp_path / "invalid.py"
            invalid_file.write_text("def broken(\n    # syntax error")

            # Create non-Python file
            text_file = temp_path / "readme.txt"
            text_file.write_text("This is not Python")

            scanner = FastAPIEndpointScanner(temp_dir)

            with patch("builtins.print") as mock_print:
                endpoints = scanner.scan_directory()

            # Should find endpoints from valid file only
            assert len(endpoints) == 1
            assert endpoints[0].path == "/test"

            # Should print summary with skipped files
            mock_print.assert_called()

    def test_continues_scanning_after_file_processing_errors(self) -> None:
        """Scanner should continue processing other files even when individual files cause errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a file that will cause an exception
            problem_file = temp_path / "problem.py"
            problem_file.write_text(
                """
from fastapi import APIRouter
router = APIRouter()

@router.get("/test")
def test():
    pass
"""
            )

            scanner = FastAPIEndpointScanner(temp_dir)

            # Mock _scan_file to raise an exception
            original_scan_file = scanner._scan_file

            def mock_scan_file(file_path):
                if file_path.name == "problem.py":
                    raise ValueError("Test exception")
                return original_scan_file(file_path)

            scanner._scan_file = mock_scan_file

            with patch("builtins.print") as mock_print:
                endpoints = scanner.scan_directory()

            # Should handle exception gracefully
            assert len(endpoints) == 0
            mock_print.assert_called()


class TestAutomaticSectionAssignment:
    """Test how the scaffolder automatically assigns sections to endpoints based on various hints."""

    def test_assigns_sections_based_on_endpoint_paths(self) -> None:
        """Should assign appropriate sections when endpoint paths match common patterns."""
        scanner = FastAPIEndpointScanner(".")

        # Test health patterns
        assert scanner._infer_section_from_path("/health") == "Health"
        assert scanner._infer_section_from_path("/api/health/check") == "Health"
        # Note: ping and alive are not in the path patterns, only in function patterns

        # Test metrics patterns
        assert scanner._infer_section_from_path("/metrics") == "Metrics"
        # Note: stats and monitoring are not in the path patterns
        # Only exact matches from the path_to_section dict work

        # Test auth patterns
        assert scanner._infer_section_from_path("/auth/login") == "Authentication"
        # Note: token is not in the path patterns, only auth is

        # Test user patterns
        assert scanner._infer_section_from_path("/users") == "User Management"
        # Note: accounts is not in the path patterns, only users is

        # Test settings patterns
        assert scanner._infer_section_from_path("/settings") == "Settings"
        # Note: config maps to Configuration, not Settings
        assert scanner._infer_section_from_path("/config") == "Configuration"

        # Test system patterns
        assert scanner._infer_section_from_path("/system") == "System"
        # Note: status maps to Status, not System
        assert scanner._infer_section_from_path("/status") == "Status"

        # Test unknown pattern
        assert scanner._infer_section_from_path("/unknown/endpoint") is None

    def test_assigns_sections_based_on_file_names(self) -> None:
        """Should assign appropriate sections when Python file names match common patterns."""
        scanner = FastAPIEndpointScanner(".")

        # Test exact matches
        assert scanner._infer_section_from_file(Path("health.py")) == "Health"
        assert scanner._infer_section_from_file(Path("metrics.py")) == "Metrics"
        # Note: auth.py maps to Authorization, not Authentication
        assert scanner._infer_section_from_file(Path("authorization.py")) == "Authorization"
        assert scanner._infer_section_from_file(Path("users.py")) == "User Management"
        assert scanner._infer_section_from_file(Path("settings.py")) == "Settings"
        assert scanner._infer_section_from_file(Path("system.py")) == "System"

        # Test partial matches - these work because the logic checks if key in filename
        assert scanner._infer_section_from_file(Path("health_check.py")) == "Health"
        # Note: user_management.py doesn't match because "users" is not in "user_management"

        # Test unknown file
        assert scanner._infer_section_from_file(Path("unknown.py")) is None
        assert scanner._infer_section_from_file(Path("main.py")) is None

    def test_assigns_sections_based_on_function_names(self) -> None:
        """Should assign appropriate sections when function names match common patterns."""
        scanner = FastAPIEndpointScanner(".")

        # Test health patterns
        assert scanner._infer_section_from_function("health_check") == "Health"
        assert scanner._infer_section_from_function("ping_server") == "Health"
        assert scanner._infer_section_from_function("is_alive") == "Health"

        # Test metrics patterns
        assert scanner._infer_section_from_function("get_metrics") == "Metrics"
        assert scanner._infer_section_from_function("system_stats") == "Metrics"
        assert scanner._infer_section_from_function("monitor_status") == "Metrics"

        # Test auth patterns
        assert scanner._infer_section_from_function("login_user") == "Authentication"
        assert scanner._infer_section_from_function("authenticate") == "Authentication"
        assert scanner._infer_section_from_function("get_token") == "Authentication"
        assert scanner._infer_section_from_function("logout") == "Authentication"

        # Test session patterns
        assert scanner._infer_section_from_function("create_session") == "Session Management"
        assert scanner._infer_section_from_function("session_info") == "Session Management"

        # Test user patterns
        assert scanner._infer_section_from_function("get_user") == "User Management"
        assert scanner._infer_section_from_function("create_account") == "User Management"

        # Test settings patterns
        assert scanner._infer_section_from_function("get_settings") == "Settings"
        assert scanner._infer_section_from_function("update_config") == "Settings"

        # Test certificate patterns
        assert scanner._infer_section_from_function("get_cert") == "Certificate Authority"
        assert scanner._infer_section_from_function("ca_info") == "Certificate Authority"
        assert scanner._infer_section_from_function("certificate_status") == "Certificate Authority"

        # Test API key patterns
        assert scanner._infer_section_from_function("create_key") == "API Keys"
        assert scanner._infer_section_from_function("api_key_info") == "API Keys"

        # Test node patterns
        assert scanner._infer_section_from_function("get_node") == "Node Management"
        assert scanner._infer_section_from_function("remote_status") == "Node Management"

        # Test system patterns
        assert scanner._infer_section_from_function("system_info") == "System"
        assert scanner._infer_section_from_function("get_status") == "System"

        # Test log patterns
        assert scanner._infer_section_from_function("get_logs") == "Logs"
        assert scanner._infer_section_from_function("log_info") == "Logs"

        # Test backup patterns
        assert scanner._infer_section_from_function("create_backup") == "Backup"
        # Note: backup_status contains "status" which matches System pattern first

        # Test restore patterns
        assert scanner._infer_section_from_function("restore_data") == "Restore"
        # Note: restore_backup contains "backup" which matches first, so returns "Backup"

        # Test cluster patterns
        assert scanner._infer_section_from_function("cluster_info") == "Cluster Management"
        # Note: cluster_status contains "status" which matches System pattern first

        # Test unknown function
        assert scanner._infer_section_from_function("unknown_function") is None

    def test_prioritizes_multiple_section_hints_by_specificity(self) -> None:
        """Should use the most specific available hint when multiple section sources are available."""
        scanner = FastAPIEndpointScanner(".")

        # Test endpoint tags take precedence
        section = scanner._determine_section_for_endpoint(
            path="/unknown",
            function_name="unknown_func",
            file_path=Path("unknown.py"),
            router_tags=["router_tag"],
            endpoint_tags=["endpoint_tag"],
        )
        assert section == "endpoint_tag"

        # Test router tags as fallback
        section = scanner._determine_section_for_endpoint(
            path="/unknown",
            function_name="unknown_func",
            file_path=Path("unknown.py"),
            router_tags=["router_tag"],
            endpoint_tags=[],
        )
        assert section == "router_tag"

        # Test path-based inference
        section = scanner._determine_section_for_endpoint(
            path="/health", function_name="unknown_func", file_path=Path("unknown.py"), router_tags=[], endpoint_tags=[]
        )
        assert section == "Health"

        # Test file-based inference
        section = scanner._determine_section_for_endpoint(
            path="/unknown",
            function_name="unknown_func",
            file_path=Path("metrics.py"),
            router_tags=[],
            endpoint_tags=[],
        )
        assert section == "Metrics"

        # Test function-based inference
        section = scanner._determine_section_for_endpoint(
            path="/unknown", function_name="get_user", file_path=Path("unknown.py"), router_tags=[], endpoint_tags=[]
        )
        assert section == "User Management"

        # Test ultimate fallback
        section = scanner._determine_section_for_endpoint(
            path="/unknown",
            function_name="unknown_func",
            file_path=Path("unknown.py"),
            router_tags=[],
            endpoint_tags=[],
        )
        assert section == "API"


class TestMarkdownScaffoldGeneration:
    """Test how the markdown generator handles various endpoint configurations."""

    def test_generates_documentation_for_endpoints_with_multiple_parameter_types(self) -> None:
        """Should create comprehensive documentation for endpoints with path, query, and body parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)

            # Create endpoint with complex parameters
            endpoint = EndpointInfo(
                method="POST",
                path="/complex/{path_param}",
                function_name="complex_endpoint",
                file_path="api.py",
                line_number=10,
                summary="Complex endpoint",
                description="An endpoint with complex parameters",
                sections=["API"],
                parameters=[
                    ParameterInfo(name="path_param", type_hint="int", is_required=True, parameter_type="path"),
                    ParameterInfo(
                        name="query_param",
                        type_hint="Optional[str]",
                        default_value="None",
                        is_required=False,
                        parameter_type="query",
                    ),
                    ParameterInfo(name="body_param", type_hint="dict", is_required=True, parameter_type="body"),
                ],
            )

            section = generator._generate_endpoint_section(endpoint)

            # Should contain parameter information
            assert "path_param" in section
            assert "query_param" in section
            assert "body_param" in section
            assert "Path Parameters" in section
            assert "Query Parameters" in section
            assert "Request Body" in section

    def test_generates_documentation_for_simple_endpoints_without_parameters(self) -> None:
        """Should create appropriate documentation for endpoints that don't require parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)

            endpoint = EndpointInfo(
                method="GET",
                path="/simple",
                function_name="simple_endpoint",
                file_path="api.py",
                line_number=5,
                sections=["API"],
                parameters=[],
            )

            section = generator._generate_endpoint_section(endpoint)

            # Should indicate no parameters
            assert "No parameters detected" in section

    def test_generates_documentation_for_endpoints_without_predefined_sections(self) -> None:
        """Should create valid documentation even when endpoints don't have sections assigned."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)

            endpoint = EndpointInfo(
                method="GET",
                path="/test",
                function_name="test_endpoint",
                file_path="api.py",
                line_number=1,
                sections=[],
            )

            section = generator._generate_endpoint_section(endpoint)

            # Should still generate valid markdown
            assert "## GET /test" in section
            assert "Section:" in section

    def test_organizes_endpoints_into_logical_groups_by_section(self) -> None:
        """Should group related endpoints together based on their assigned sections."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)

            endpoints = [
                EndpointInfo("GET", "/health", "health", "api.py", 1, sections=["Health"]),
                EndpointInfo("GET", "/metrics", "metrics", "api.py", 2, sections=["Metrics"]),
                EndpointInfo("GET", "/status", "status", "api.py", 3, sections=["Health"]),
                EndpointInfo("GET", "/users", "users", "api.py", 4, sections=["Users"]),
            ]

            grouped = generator._group_endpoints(endpoints)

            # Group names are sanitized to lowercase
            assert "health" in grouped
            assert "metrics" in grouped
            assert "users" in grouped
            assert len(grouped["health"]) == 2
            assert len(grouped["metrics"]) == 1
            assert len(grouped["users"]) == 1


class TestDocumentationInitialization:
    """Test the complete documentation initialization process under various conditions."""

    def test_creates_basic_documentation_structure_when_no_endpoints_exist(self) -> None:
        """Should create general documentation files even when no API endpoints are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty Python file
            empty_file = Path(temp_dir) / "empty.py"
            empty_file.write_text("# Empty file")

            initializer = DocumentationInitializer(temp_dir)
            result = initializer.initialize()

            assert len(result["endpoints"]) == 0
            # A general_docs.md file is always created
            assert len(result["files"]) >= 1
            # Check that the summary mentions 0 endpoints discovered
            assert "Endpoints discovered:** 0" in result["summary"]

    def test_creates_output_directory_automatically_when_missing(self) -> None:
        """Should automatically create the specified output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source with endpoint
            source_file = temp_path / "api.py"
            source_file.write_text(
                """
from fastapi import APIRouter
router = APIRouter(tags=["test"])

@router.get("/test")
def test_endpoint():
    return {"test": "data"}
"""
            )

            # Use non-existent output directory (single level)
            output_dir = temp_path / "docs"

            initializer = DocumentationInitializer(source_directory=str(temp_path), output_directory=str(output_dir))

            result = initializer.initialize()

            # Should create the output directory
            assert output_dir.exists()
            assert len(result["endpoints"]) == 1

    def test_provides_comprehensive_summary_of_initialization_results(self) -> None:
        """Should generate informative summaries showing what was discovered and created."""
        initializer = DocumentationInitializer(".")

        endpoints = [
            EndpointInfo("GET", "/health", "health", "api.py", 1, sections=["Health"]),
            EndpointInfo("GET", "/test", "test", "api.py", 2, sections=["API"]),  # Default section
            EndpointInfo("GET", "/users", "users", "api.py", 3, sections=["Users"]),
        ]

        summary = initializer._create_summary(endpoints, {"docs/health.md": "content", "docs/users.md": "content"})

        # Should mention endpoint and file counts
        assert "Endpoints discovered:** 3" in summary
        assert "Files generated:** 2" in summary

    def test_reports_accurate_statistics_when_no_files_generated(self) -> None:
        """Should provide accurate reporting even when no documentation files are generated."""
        initializer = DocumentationInitializer(".")

        endpoints = [
            EndpointInfo("GET", "/test", "test", "api.py", 1, sections=["API"]),
        ]

        summary = initializer._create_summary(endpoints, {})

        # Should indicate 0 files were generated
        assert "Files generated:** 0" in summary
