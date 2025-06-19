"""
Tests for TODO detection functionality in the documentation linter.
"""

import tempfile
from pathlib import Path

from fastmarkdocs.linter import DocumentationLinter


def test_todo_detection_basic():
    """Test basic TODO detection in markdown files."""
    # Create a temporary directory with test markdown files
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_dir = Path(temp_dir)

        # Create a test markdown file with various TODO patterns
        test_file = docs_dir / "test.md"
        test_file.write_text(
            """
# Test Documentation

## GET /users

TODO: Add detailed description of this endpoint.

### Parameters
- `user_id` (string, required): TODO: Add description

### Response Examples
TODO: Add response examples for different status codes.

## POST /users

This endpoint creates a new user.

# TODO: Add Python example for POST /users

### Request Body
- `name` (string, required): User's full name
- `email` (string, required): TODO Add email validation details

Some other content without any pending items.
"""
        )

        # Create a simple OpenAPI schema
        openapi_schema = {"paths": {"/users": {"get": {"summary": "Get users"}, "post": {"summary": "Create user"}}}}

        # Initialize linter
        linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir), recursive=False)

        # Run linting
        results = linter.lint()

        # Check TODO entries
        todo_entries = results["todo_entries"]
        assert len(todo_entries) == 5, f"Expected 5 TODO entries, got {len(todo_entries)}"

        # Check specific TODO entries
        todo_texts = [entry["todo_text"] for entry in todo_entries]
        assert "Add detailed description of this endpoint." in todo_texts
        assert "Add description" in todo_texts
        assert "Add response examples for different status codes." in todo_texts
        assert "Add Python example for POST /users" in todo_texts
        assert "Add email validation details" in todo_texts

        # Check file and line information
        for entry in todo_entries:
            assert entry["file"] == "test.md"
            assert isinstance(entry["line"], int)
            assert entry["line"] > 0
            assert "content" in entry
            assert "context" in entry


def test_todo_context_detection():
    """Test that TODO context detection works correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_dir = Path(temp_dir)

        test_file = docs_dir / "context_test.md"
        test_file.write_text(
            """
# API Documentation

## GET /users/{id}

This endpoint retrieves a user by ID.

### Parameters
TODO: Document the id parameter

### Response
TODO: Add response schema

## POST /users

### Request Body
TODO: Document request body structure

#### Validation Rules
TODO: Add validation details
"""
        )

        openapi_schema = {"paths": {}}
        linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir), recursive=False)

        results = linter.lint()
        todo_entries = results["todo_entries"]

        assert len(todo_entries) == 4

        # Check contexts - endpoint context should be preferred when available
        contexts = [entry["context"] for entry in todo_entries]

        # All TODOs should show endpoint context since they're all under endpoint headers
        assert contexts.count("in endpoint GET /users/{id}") == 2  # Parameters and Response TODOs
        assert contexts.count("in endpoint POST /users") == 2  # Request Body and Validation Rules TODOs


def test_todo_case_insensitive():
    """Test that TODO detection is case insensitive."""
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_dir = Path(temp_dir)

        test_file = docs_dir / "case_test.md"
        test_file.write_text(
            """
# Test Cases

TODO: Uppercase todo
todo: Lowercase todo
Todo: Mixed case todo
tOdO: Weird case todo
"""
        )

        openapi_schema = {"paths": {}}
        linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir), recursive=False)

        results = linter.lint()
        todo_entries = results["todo_entries"]

        assert len(todo_entries) == 4

        todo_texts = [entry["todo_text"] for entry in todo_entries]
        assert "Uppercase todo" in todo_texts
        assert "Lowercase todo" in todo_texts
        assert "Mixed case todo" in todo_texts
        assert "Weird case todo" in todo_texts


def test_todo_statistics():
    """Test that TODO entries are included in statistics."""
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_dir = Path(temp_dir)

        test_file = docs_dir / "stats_test.md"
        test_file.write_text(
            """
# Documentation

This is just documentation with pending items but no API endpoints.

TODO: First todo
TODO: Second todo
TODO: Third todo
"""
        )

        openapi_schema = {"paths": {}}
        linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir), recursive=False)

        results = linter.lint()

        # Check statistics
        stats = results["statistics"]
        assert stats["issues"]["todo_entries"] == 3

        # Check that TODO entries are tracked separately from regular issues
        # (total_issues might be > 0 due to other detection logic, but TODOs should be separate)

        # Check recommendations
        recommendations = results["recommendations"]
        todo_rec = next((r for r in recommendations if "TODO" in r["title"]), None)
        assert todo_rec is not None
        assert todo_rec["priority"] == "medium"  # < 10 TODOs
        assert "3 TODO entries" in todo_rec["description"]


def test_todo_high_priority_recommendation():
    """Test that many TODO entries trigger high priority recommendation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_dir = Path(temp_dir)

        test_file = docs_dir / "many_todos.md"
        # Create 15 TODO entries to trigger high priority
        todo_content = "\n".join([f"TODO: Item {i}" for i in range(15)])
        test_file.write_text(f"# Documentation\n\n{todo_content}")

        openapi_schema = {"paths": {}}
        linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir), recursive=False)

        results = linter.lint()

        # Check that we have 15 TODOs
        assert len(results["todo_entries"]) == 15

        # Check that recommendation is high priority
        recommendations = results["recommendations"]
        todo_rec = next((r for r in recommendations if "TODO" in r["title"]), None)
        assert todo_rec is not None
        assert todo_rec["priority"] == "high"  # >= 10 TODOs


def test_no_todos():
    """Test behavior when no TODO entries are found."""
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_dir = Path(temp_dir)

        test_file = docs_dir / "no_todos.md"
        test_file.write_text(
            """
# Clean Documentation

## GET /users

This endpoint returns a list of users.

### Parameters
- `limit` (integer, optional): Maximum number of users to return

### Response
Returns an array of user objects.
"""
        )

        openapi_schema = {"paths": {"/users": {"get": {"summary": "Get users"}}}}
        linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir), recursive=False)

        results = linter.lint()

        # Should have no TODO entries
        assert len(results["todo_entries"]) == 0
        assert results["statistics"]["issues"]["todo_entries"] == 0

        # Should not have TODO recommendation
        recommendations = results["recommendations"]
        todo_rec = next((r for r in recommendations if "TODO" in r["title"]), None)
        assert todo_rec is None


def test_recursive_todo_detection():
    """Test TODO detection in nested directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_dir = Path(temp_dir)

        # Create nested structure
        subdir = docs_dir / "api" / "v1"
        subdir.mkdir(parents=True)

        # File in root
        (docs_dir / "root.md").write_text("TODO: Root todo")

        # File in subdirectory
        (subdir / "nested.md").write_text("TODO: Nested todo")

        openapi_schema = {"paths": {}}
        linter = DocumentationLinter(openapi_schema=openapi_schema, docs_directory=str(docs_dir), recursive=True)

        results = linter.lint()

        # Should find both TODOs
        assert len(results["todo_entries"]) == 2

        files = [entry["file"] for entry in results["todo_entries"]]
        assert "root.md" in files
        assert str(Path("api") / "v1" / "nested.md") in files
