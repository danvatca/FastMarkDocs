#!/usr/bin/env python3
"""
Example: Using fmd-lint programmatically

This example demonstrates how to use the FastMarkDocs documentation linter
programmatically to analyze API documentation quality.
"""

import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastmarkdocs.linter import DocumentationLinter
from fastmarkdocs.linter_cli import format_results

# Create a simple FastAPI app
app = FastAPI(title="Example API", version="1.0.0")


@app.get("/users")
async def list_users() -> dict[str, list[Any]]:
    """List all users."""
    return {"users": []}


@app.get("/users/{user_id}")
async def get_user(user_id: int) -> dict[str, dict[str, Any]]:
    """Get a specific user."""
    return {"user": {"id": user_id, "name": "John Doe"}}


@app.post("/users")
async def create_user() -> dict[str, dict[str, Any]]:
    """Create a new user."""
    return {"user": {"id": 1, "name": "New User"}}


def main() -> None:
    """Demonstrate fmd-lint usage."""

    # Generate OpenAPI schema
    openapi_schema = app.openapi()

    # Create temporary documentation
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_dir = Path(temp_dir) / "docs"
        docs_dir.mkdir()

        # Create partial documentation (missing some endpoints and details)
        (docs_dir / "users.md").write_text(
            """
# Users API

## GET /users

List all users in the system.

### Description
This endpoint returns a list of users.

## GET /users/{user_id}

Get user by ID.

Short description only.
"""
        )

        # Create linter
        linter = DocumentationLinter(
            openapi_schema=openapi_schema,
            docs_directory=str(docs_dir),
            base_url="https://api.example.com",
            recursive=True,
        )

        # Run analysis
        print("🔍 Running documentation analysis...")
        results = linter.lint()

        # Display results
        print("\n" + "=" * 60)
        print("📊 ANALYSIS RESULTS")
        print("=" * 60)

        # Summary
        summary = results["summary"]
        print(f"Status: {summary['status']}")
        print(f"Coverage: {summary['coverage']}")
        print(f"Completeness: {summary['completeness']}")
        print(f"Total Issues: {summary['total_issues']}")

        # Missing documentation
        if results["missing_documentation"]:
            print(f"\n❌ Missing Documentation ({len(results['missing_documentation'])} endpoints):")
            for item in results["missing_documentation"]:
                print(f"   • {item['method']} {item['path']}")

        # Incomplete documentation
        if results["incomplete_documentation"]:
            print(f"\n⚠️ Incomplete Documentation ({len(results['incomplete_documentation'])} endpoints):")
            for item in results["incomplete_documentation"][:3]:  # Show first 3
                print(f"   • {item['method']} {item['path']} (Score: {item['completeness_score']}%)")
                for issue in item["issues"][:2]:  # Show first 2 issues
                    print(f"     - {issue}")

        # Recommendations
        if results["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in results["recommendations"]:
                print(f"   • {rec['title']}")
                print(f"     {rec['description']}")
                print(f"     Action: {rec['action']}")

        print("\n" + "=" * 60)
        print("📄 Full Text Report:")
        print("=" * 60)
        print(format_results(results, "text"))

        print("\n" + "=" * 60)
        print("📋 JSON Output (first 500 chars):")
        print("=" * 60)
        json_output = format_results(results, "json")
        print(json_output[:500] + "..." if len(json_output) > 500 else json_output)


if __name__ == "__main__":
    main()
