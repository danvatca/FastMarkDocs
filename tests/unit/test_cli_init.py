#!/usr/bin/env python3
"""Unit tests for the fmd-init CLI interface."""

import argparse
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from fastmarkdocs.scaffolder import EndpointInfo
from fastmarkdocs.scaffolder_cli import (
    create_parser,
    format_json_output,
    format_text_output,
    main,
    validate_arguments,
)


class TestCreateParser:
    """Test the argument parser creation."""

    def test_create_parser(self) -> None:
        """Test creating the argument parser."""
        parser = create_parser()

        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == "fmd-init"
        assert "Initialize FastAPI documentation scaffolding" in parser.description

    def test_parser_required_arguments(self) -> None:
        """Test parser with required arguments."""
        parser = create_parser()

        # Test with valid arguments
        args = parser.parse_args(["src/"])
        assert args.source_directory == "src/"
        assert args.output_dir == "docs"  # default
        assert args.format == "text"  # default

    def test_parser_optional_arguments(self) -> None:
        """Test parser with optional arguments."""
        parser = create_parser()

        args = parser.parse_args(
            ["src/", "--output-dir", "api-docs", "--format", "json", "--dry-run", "--overwrite", "--verbose"]
        )

        assert args.source_directory == "src/"
        assert args.output_dir == "api-docs"
        assert args.format == "json"
        assert args.dry_run is True
        assert args.overwrite is True
        assert args.verbose is True

    def test_parser_short_arguments(self) -> None:
        """Test parser with short arguments."""
        parser = create_parser()

        args = parser.parse_args(["src/", "-o", "api-docs", "-f", "json", "-n", "-v"])

        assert args.source_directory == "src/"
        assert args.output_dir == "api-docs"
        assert args.format == "json"
        assert args.dry_run is True
        assert args.verbose is True

    def test_parser_no_config_flag(self) -> None:
        """Test parser with --no-config flag."""
        parser = create_parser()

        args = parser.parse_args(["src/", "--no-config"])
        assert args.source_directory == "src/"
        assert args.no_config is True

        # Test default behavior
        args = parser.parse_args(["src/"])
        assert args.no_config is False

    def test_parser_invalid_format(self) -> None:
        """Test parser with invalid format."""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["src/", "--format", "invalid"])


class TestValidateArguments:
    """Test the argument validation."""

    def test_validate_arguments_valid_directory(self) -> None:
        """Test validation with valid directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            args = argparse.Namespace(
                source_directory=temp_dir,
                output_dir=str(output_dir),
                overwrite=False,
                dry_run=False,
            )

            # Should not raise any exception
            validate_arguments(args)

    def test_validate_arguments_nonexistent_directory(self) -> None:
        """Test validation with non-existent directory."""
        args = argparse.Namespace(
            source_directory="/nonexistent/directory",
            output_dir="docs",
            overwrite=False,
            dry_run=False,
        )

        with pytest.raises(SystemExit):
            validate_arguments(args)

    def test_validate_arguments_file_not_directory(self) -> None:
        """Test validation with file instead of directory."""
        with tempfile.NamedTemporaryFile() as temp_file:
            args = argparse.Namespace(
                source_directory=temp_file.name,
                output_dir="docs",
                overwrite=False,
                dry_run=False,
            )

            with pytest.raises(SystemExit):
                validate_arguments(args)

    def test_validate_arguments_existing_output_files(self) -> None:
        """Test validation with existing output files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Create existing markdown file
            (output_dir / "existing.md").write_text("existing content")

            args = argparse.Namespace(
                source_directory=str(source_dir),
                output_dir=str(output_dir),
                overwrite=False,
                dry_run=False,
            )

            with pytest.raises(SystemExit):
                validate_arguments(args)

    def test_validate_arguments_existing_files_with_overwrite(self) -> None:
        """Test validation with existing files but overwrite enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Create existing markdown file
            (output_dir / "existing.md").write_text("existing content")

            args = argparse.Namespace(
                source_directory=str(source_dir),
                output_dir=str(output_dir),
                overwrite=True,
                dry_run=False,
            )

            # Should not raise any exception
            validate_arguments(args)

    def test_validate_arguments_existing_files_with_dry_run(self) -> None:
        """Test validation with existing files but dry run enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Create existing markdown file
            (output_dir / "existing.md").write_text("existing content")

            args = argparse.Namespace(
                source_directory=str(source_dir),
                output_dir=str(output_dir),
                overwrite=False,
                dry_run=True,
            )

            # Should not raise any exception
            validate_arguments(args)


class TestFormatOutput:
    """Test output formatting functions."""

    def test_format_text_output_no_endpoints(self) -> None:
        """Test text formatting with no endpoints."""
        result = {"endpoints": [], "files": [], "summary": "No endpoints"}

        output = format_text_output(result)

        assert "🔍 No FastAPI endpoints found" in output
        assert "@app.get('/path')" in output

    def test_format_text_output_with_endpoints(self) -> None:
        """Test text formatting with endpoints."""
        result = {
            "endpoints": [Mock(), Mock()],
            "files": ["docs/api.md"],
            "summary": "Success summary with endpoints",
        }

        output = format_text_output(result)

        assert "✅ Documentation scaffolding generated successfully!" in output
        assert "Success summary with endpoints" in output

    def test_format_text_output_verbose(self) -> None:
        """Test text formatting with verbose flag."""
        endpoints = [
            EndpointInfo("GET", "/users", "get_users", "api.py", 10),
            EndpointInfo("POST", "/users", "create_user", "api.py", 20),
        ]
        result = {
            "endpoints": endpoints,
            "files": ["docs/api.md"],
            "summary": "Success summary",
        }

        output = format_text_output(result, verbose=True)

        assert "✅ Documentation scaffolding generated successfully!" in output
        assert "📋 **Discovered Endpoints:**" in output
        assert "GET    /users" in output
        assert "POST   /users" in output

    def test_format_json_output(self) -> None:
        """Test JSON formatting."""
        endpoint = EndpointInfo("GET", "/users", "get_users", "api.py", 10, summary="Get users", tags=["users"])
        result = {
            "endpoints": [endpoint],
            "files": ["docs/api.md"],
            "summary": "Success",
        }

        output = format_json_output(result)
        parsed = json.loads(output)

        assert len(parsed["endpoints"]) == 1
        endpoint_data = parsed["endpoints"][0]
        assert endpoint_data["method"] == "GET"
        assert endpoint_data["path"] == "/users"
        assert endpoint_data["function_name"] == "get_users"
        assert endpoint_data["summary"] == "Get users"
        assert endpoint_data["tags"] == ["users"]

    def test_format_json_output_no_endpoints(self) -> None:
        """Test JSON formatting with no endpoints."""
        result = {"endpoints": [], "files": [], "summary": "No endpoints"}

        output = format_json_output(result)
        parsed = json.loads(output)

        assert len(parsed["endpoints"]) == 0
        assert parsed["files"] == []


class TestMainFunction:
    """Test the main CLI function."""

    @patch("fastmarkdocs.scaffolder_cli.DocumentationInitializer")
    def test_main_successful_execution(self, mock_initializer_class) -> None:
        """Test successful execution of main function."""
        # Mock the initializer
        mock_initializer = Mock()
        mock_initializer.initialize.return_value = {
            "endpoints": [Mock(), Mock()],
            "files": ["docs/api.md"],
            "summary": "Success summary",
        }
        mock_initializer_class.return_value = mock_initializer

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            with patch("sys.argv", ["fmd-init", temp_dir, "--output-dir", str(output_dir)]):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Should exit with code 0 (success)
                assert exc_info.value.code == 0

    @patch("fastmarkdocs.scaffolder_cli.DocumentationInitializer")
    def test_main_with_no_config_flag(self, mock_initializer_class) -> None:
        """Test main function with --no-config flag."""
        # Mock the initializer
        mock_initializer = Mock()
        mock_initializer.initialize.return_value = {
            "endpoints": [Mock(), Mock()],
            "files": ["docs/api.md"],
            "summary": "Success summary",
        }
        mock_initializer_class.return_value = mock_initializer

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            with patch("sys.argv", ["fmd-init", temp_dir, "--output-dir", str(output_dir), "--no-config"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Should exit with code 0 (success)
                assert exc_info.value.code == 0

                # Verify DocumentationInitializer was called with generate_config=False
                mock_initializer_class.assert_called_with(temp_dir, str(output_dir), generate_config=False)

    @patch("fastmarkdocs.scaffolder_cli.DocumentationInitializer")
    def test_main_with_config_generation_enabled(self, mock_initializer_class) -> None:
        """Test main function with config generation enabled (default)."""
        # Mock the initializer
        mock_initializer = Mock()
        mock_initializer.initialize.return_value = {
            "endpoints": [Mock(), Mock()],
            "files": ["docs/api.md"],
            "summary": "Success summary",
        }
        mock_initializer_class.return_value = mock_initializer

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            with patch("sys.argv", ["fmd-init", temp_dir, "--output-dir", str(output_dir)]):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Should exit with code 0 (success)
                assert exc_info.value.code == 0

                # Verify DocumentationInitializer was called with generate_config=True (default)
                mock_initializer_class.assert_called_with(temp_dir, str(output_dir), generate_config=True)

    @patch("fastmarkdocs.scaffolder_cli.DocumentationInitializer")
    def test_main_no_endpoints_found(self, mock_initializer_class) -> None:
        """Test main function when no endpoints are found."""
        # Mock the initializer
        mock_initializer = Mock()
        mock_initializer.initialize.return_value = {
            "endpoints": [],
            "files": [],
            "summary": "No endpoints discovered",
        }
        mock_initializer_class.return_value = mock_initializer

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("sys.argv", ["fmd-init", temp_dir]):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Should exit with code 1 (no endpoints found)
                assert exc_info.value.code == 1

    def test_main_invalid_directory(self) -> None:
        """Test main function with invalid directory."""
        with patch("sys.argv", ["fmd-init", "/nonexistent/directory"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with code 1 (validation error)
            assert exc_info.value.code == 1

    @patch("fastmarkdocs.scaffolder_cli.DocumentationInitializer")
    def test_main_with_json_format(self, mock_initializer_class) -> None:
        """Test main function with JSON output format."""
        # Mock the initializer
        mock_initializer = Mock()
        mock_initializer.initialize.return_value = {
            "endpoints": [EndpointInfo("GET", "/test", "test", "test.py", 1)],
            "files": ["docs/api.md"],
            "summary": "Success",
        }
        mock_initializer_class.return_value = mock_initializer

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            with patch("sys.argv", ["fmd-init", temp_dir, "--output-dir", str(output_dir), "--format", "json"]):
                with patch("builtins.print") as mock_print:
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    # Should exit with code 0
                    assert exc_info.value.code == 0

                    # Check that JSON was printed
                    printed_output = mock_print.call_args[0][0]
                    parsed = json.loads(printed_output)
                    assert len(parsed["endpoints"]) == 1

    @patch("fastmarkdocs.scaffolder_cli.DocumentationInitializer")
    def test_main_with_verbose_flag(self, mock_initializer_class) -> None:
        """Test main function with verbose flag."""
        # Mock the initializer
        mock_initializer = Mock()
        mock_initializer.initialize.return_value = {
            "endpoints": [EndpointInfo("GET", "/test", "test", "test.py", 1)],
            "files": ["docs/api.md"],
            "summary": "Success",
        }
        mock_initializer_class.return_value = mock_initializer

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            with patch("sys.argv", ["fmd-init", temp_dir, "--output-dir", str(output_dir), "--verbose"]):
                with patch("builtins.print") as mock_print:
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    # Should exit with code 0
                    assert exc_info.value.code == 0

                    # Check that verbose output was printed
                    print_calls = [str(call[0][0]) if call[0] else "" for call in mock_print.call_args_list]
                    verbose_output = "\n".join(print_calls)
                    assert "🔍 Scanning:" in verbose_output
                    assert "📁 Output:" in verbose_output

    @patch("fastmarkdocs.scaffolder_cli.FastAPIEndpointScanner")
    @patch("fastmarkdocs.scaffolder_cli.MarkdownScaffoldGenerator")
    @patch("fastmarkdocs.scaffolder_cli.DocumentationInitializer")
    def test_main_with_dry_run(self, mock_initializer_class, mock_generator_class, mock_scanner_class) -> None:
        """Test main function with dry run flag."""
        # Mock the scanner
        mock_scanner = Mock()
        mock_endpoint = EndpointInfo("GET", "/test", "test", "test.py", 1)
        mock_scanner.scan_directory.return_value = [mock_endpoint]
        mock_scanner_class.return_value = mock_scanner

        # Mock the generator
        mock_generator = Mock()
        mock_generator._group_endpoints.return_value = {"api": [mock_endpoint]}
        mock_generator._generate_markdown_content.return_value = "# Test content"
        mock_generator_class.return_value = mock_generator

        # Mock the initializer (for summary creation)
        mock_initializer = Mock()
        mock_initializer._create_summary.return_value = "Success summary"
        mock_initializer_class.return_value = mock_initializer

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            with patch("sys.argv", ["fmd-init", temp_dir, "--output-dir", str(output_dir), "--dry-run", "--verbose"]):
                with patch("builtins.print") as mock_print:
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    # Should exit with code 0
                    assert exc_info.value.code == 0

                    # Check that dry run was mentioned
                    print_calls = [str(call[0][0]) if call[0] else "" for call in mock_print.call_args_list]
                    verbose_output = "\n".join(print_calls)
                    assert "🔬 Dry run mode" in verbose_output

    @patch("fastmarkdocs.scaffolder_cli.DocumentationInitializer")
    def test_main_keyboard_interrupt(self, mock_initializer_class) -> None:
        """Test main function handling keyboard interrupt."""
        # Mock the initializer to raise KeyboardInterrupt
        mock_initializer_class.side_effect = KeyboardInterrupt()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            with patch("sys.argv", ["fmd-init", temp_dir, "--output-dir", str(output_dir)]):
                with patch("builtins.print") as mock_print:
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    # Should exit with code 130 (keyboard interrupt)
                    assert exc_info.value.code == 130

                    # Check that cancellation message was printed
                    mock_print.assert_called_with("\n⚠️  Operation cancelled by user")

    @patch("fastmarkdocs.scaffolder_cli.DocumentationInitializer")
    def test_main_generic_exception(self, mock_initializer_class) -> None:
        """Test main function handling generic exception."""
        # Mock the initializer to raise a generic exception
        mock_initializer_class.side_effect = Exception("Test error")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            with patch("sys.argv", ["fmd-init", temp_dir, "--output-dir", str(output_dir)]):
                with patch("builtins.print") as mock_print:
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    # Should exit with code 1 (error)
                    assert exc_info.value.code == 1

                    # Check that error message was printed
                    print_calls = [str(call[0][0]) if call[0] else "" for call in mock_print.call_args_list]
                    error_output = "\n".join(print_calls)
                    assert "❌ Error: Test error" in error_output
