"""Test general_docs.md generation functionality."""

import tempfile
from pathlib import Path

from fastmarkdocs.scaffolder import EndpointInfo, MarkdownScaffoldGenerator


class TestGeneralDocsGeneration:
    """Test the generation of general_docs.md file."""

    def test_general_docs_generated_with_no_endpoints(self):
        """Test that general_docs.md is generated even when no endpoints exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)
            result = generator.generate_scaffolding([])

            # Should create general_docs.md even with no endpoints
            assert len(result) == 1

            general_docs_path = Path(temp_dir) / "general_docs.md"
            assert general_docs_path.exists()
            assert str(general_docs_path) in result

    def test_general_docs_generated_with_endpoints(self):
        """Test that general_docs.md is generated alongside endpoint files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            endpoint = EndpointInfo(
                method="GET",
                path="/users",
                function_name="get_users",
                file_path="app.py",
                line_number=10,
                tags=["users"],
            )

            generator = MarkdownScaffoldGenerator(temp_dir)
            result = generator.generate_scaffolding([endpoint])

            # Should create both general_docs.md and endpoint file
            assert len(result) == 2

            general_docs_path = Path(temp_dir) / "general_docs.md"
            users_docs_path = Path(temp_dir) / "users.md"

            assert general_docs_path.exists()
            assert users_docs_path.exists()
            assert str(general_docs_path) in result
            assert str(users_docs_path) in result

    def test_general_docs_content_structure(self):
        """Test that general_docs.md contains all expected sections."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)
            generator.generate_scaffolding([])

            general_docs_path = Path(temp_dir) / "general_docs.md"
            content = general_docs_path.read_text()

            # Check for main sections
            expected_sections = [
                "# General API Documentation",
                "## Overview",
                "## Base URL",
                "## Authentication",
                "## Request and Response Format",
                "## Error Handling",
                "## Rate Limiting",
                "## Pagination",
                "## API Versioning",
                "## SDKs and Client Libraries",
                "## Testing",
                "## Support",
                "## Changelog",
            ]

            for section in expected_sections:
                assert section in content, f"Missing section: {section}"

    def test_general_docs_contains_todos(self):
        """Test that general_docs.md contains TODO items for users to complete."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)
            generator.generate_scaffolding([])

            general_docs_path = Path(temp_dir) / "general_docs.md"
            content = general_docs_path.read_text()

            # Should contain TODO items
            todo_count = content.count("TODO:")
            assert todo_count > 20, f"Expected many TODO items, found {todo_count}"

            # Check for specific TODO categories
            expected_todos = [
                "TODO: Add a brief overview",
                "TODO: Specify your API's base URL",
                "TODO: Document your authentication mechanism",
                "TODO: Document your error handling approach",
                "TODO: Document your rate limiting policy",
                "TODO: Document pagination for list endpoints",
                "TODO: Document your API versioning strategy",
            ]

            for todo_text in expected_todos:
                assert todo_text in content, f"Missing TODO: {todo_text}"

    def test_general_docs_has_proper_structure(self):
        """Test that general_docs.md has proper markdown structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)
            generator.generate_scaffolding([])

            general_docs_path = Path(temp_dir) / "general_docs.md"
            content = general_docs_path.read_text()

            # Should start with main title
            assert content.startswith("# General API Documentation")

            # Should contain code blocks
            assert "```bash" in content
            assert "```json" in content

            # Should contain tables
            assert "| Header | Required | Description |" in content
            assert "| Status Code | Meaning | Description |" in content

            # Should mention fmd-init generation
            assert "fmd-init" in content

    def test_general_docs_independent_of_endpoints(self):
        """Test that general_docs.md content is the same regardless of endpoints."""
        with tempfile.TemporaryDirectory() as temp_dir1, tempfile.TemporaryDirectory() as temp_dir2:

            # Generate with no endpoints
            generator1 = MarkdownScaffoldGenerator(temp_dir1)
            generator1.generate_scaffolding([])
            content1 = (Path(temp_dir1) / "general_docs.md").read_text()

            # Generate with endpoints
            endpoint = EndpointInfo(
                method="GET", path="/test", function_name="test", file_path="app.py", line_number=1, tags=["test"]
            )
            generator2 = MarkdownScaffoldGenerator(temp_dir2)
            generator2.generate_scaffolding([endpoint])
            content2 = (Path(temp_dir2) / "general_docs.md").read_text()

            # general_docs.md content should be identical
            assert content1 == content2

    def test_general_docs_markdown_validity(self):
        """Test that generated markdown is properly formatted."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)
            generator.generate_scaffolding([])

            general_docs_path = Path(temp_dir) / "general_docs.md"
            content = general_docs_path.read_text()

            lines = content.split("\n")

            # Check that headers are properly formatted
            h1_count = len([line for line in lines if line.startswith("# ")])
            h2_count = len([line for line in lines if line.startswith("## ")])
            h3_count = len([line for line in lines if line.startswith("### ")])

            assert h1_count == 1, "Should have exactly one H1 header"
            assert h2_count > 5, "Should have multiple H2 headers for main sections"
            assert h3_count > 5, "Should have multiple H3 headers for subsections"

            # Check that code blocks are properly closed
            code_block_starts = content.count("```")
            assert code_block_starts % 2 == 0, "All code blocks should be properly closed"
