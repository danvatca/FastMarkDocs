"""
CLI interface for the fmd-init tool.

This module provides the command-line interface for initializing FastAPI
documentation scaffolding from existing codebases.
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from .scaffolder import DocumentationInitializer, EndpointInfo


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for fmd-init."""
    parser = argparse.ArgumentParser(
        prog="fmd-init",
        description="Initialize FastAPI documentation scaffolding from existing code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fmd-init src/                          # Scan src/ directory, output to docs/
  fmd-init src/ --output-dir api-docs/   # Custom output directory
  fmd-init . --format json              # Output results as JSON
  fmd-init src/ --dry-run               # Preview what would be generated
  fmd-init src/ --overwrite             # Overwrite existing files

The tool will:
1. Recursively scan the source directory for Python files
2. Parse FastAPI decorators (@app.get, @router.post, etc.)
3. Extract endpoint information and docstrings
4. Generate markdown documentation scaffolding
5. Group endpoints by tags or create general API documentation

Generated files will contain TODO sections that you should fill in with:
- Detailed descriptions
- Parameter documentation
- Response examples
- Additional context
        """,
    )

    # Required arguments
    parser.add_argument("source_directory", help="Source directory to scan for FastAPI endpoints")

    # Optional arguments
    parser.add_argument(
        "--output-dir", "-o", default="docs", help="Output directory for generated documentation (default: docs)"
    )

    parser.add_argument(
        "--format", "-f", choices=["text", "json"], default="text", help="Output format (default: text)"
    )

    parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Preview what would be generated without creating files"
    )

    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing documentation files")

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    parser.add_argument(
        "--exclude", action="append", help="Exclude files/directories matching pattern (can be used multiple times)"
    )

    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    source_path = Path(args.source_directory)

    if not source_path.exists():
        print(f"Error: Source directory '{args.source_directory}' does not exist")
        sys.exit(1)

    if not source_path.is_dir():
        print(f"Error: '{args.source_directory}' is not a directory")
        sys.exit(1)

    # Check if output directory exists and has files (if not overwrite mode)
    output_path = Path(args.output_dir)
    if output_path.exists() and not args.overwrite and not args.dry_run:
        existing_md_files = list(output_path.glob("*.md"))
        if existing_md_files:
            print(f"Warning: Output directory '{args.output_dir}' contains existing .md files:")
            for file in existing_md_files[:5]:  # Show first 5
                print(f"  - {file.name}")
            if len(existing_md_files) > 5:
                print(f"  ... and {len(existing_md_files) - 5} more")
            print("\nUse --overwrite to replace existing files or choose a different output directory.")
            sys.exit(1)


def format_text_output(result: dict[str, Any], verbose: bool = False) -> str:
    """Format the result as human-readable text."""
    lines = []

    if result["endpoints_found"] == 0:
        lines.append("🔍 No FastAPI endpoints found in the source directory.")
        lines.append("\nMake sure your source directory contains Python files with FastAPI decorators like:")
        lines.append("  @app.get('/path')")
        lines.append("  @router.post('/path')")
        lines.append("  @api.put('/path')")
        return "\n".join(lines)

    # Success message
    lines.append("✅ Documentation scaffolding generated successfully!")
    lines.append("")
    lines.append(result["summary"])

    if verbose and "endpoints" in result:
        lines.append("\n📋 **Discovered Endpoints:**")
        for endpoint in result["endpoints"]:
            lines.append(f"  {endpoint.method:6} {endpoint.path:30} ({endpoint.file_path}:{endpoint.line_number})")

    return "\n".join(lines)


def format_json_output(result: dict[str, Any]) -> str:
    """Format the result as JSON."""
    # Convert EndpointInfo objects to dictionaries for JSON serialization
    if "endpoints" in result:
        endpoints_data = []
        for endpoint in result["endpoints"]:
            endpoints_data.append(
                {
                    "method": endpoint.method,
                    "path": endpoint.path,
                    "function_name": endpoint.function_name,
                    "file_path": endpoint.file_path,
                    "line_number": endpoint.line_number,
                    "summary": endpoint.summary,
                    "description": endpoint.description,
                    "tags": endpoint.tags,
                    "docstring": endpoint.docstring,
                }
            )
        result["endpoints"] = endpoints_data

    return json.dumps(result, indent=2)


def main() -> None:
    """Main entry point for fmd-init CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate arguments
    validate_arguments(args)

    if args.verbose:
        print(f"🔍 Scanning: {args.source_directory}")
        print(f"📁 Output: {args.output_dir}")
        if args.dry_run:
            print("🔬 Dry run mode: No files will be created")
        print()

    try:
        # Initialize the documentation generator
        if args.dry_run:
            # For dry run, use a secure temporary directory that we won't actually write to
            with tempfile.TemporaryDirectory(prefix="fmd-init-dry-run-") as temp_dir:
                initializer = DocumentationInitializer(args.source_directory, temp_dir)
                # Override the generator to not actually write files

                def dry_run_generate(endpoints: list[EndpointInfo]) -> dict[str, str]:
                    # Generate content but don't write files
                    if not endpoints:
                        return {}

                    grouped_endpoints = initializer.generator._group_endpoints(endpoints)
                    generated_files = {}

                    for group_name, group_endpoints in grouped_endpoints.items():
                        file_content = initializer.generator._generate_markdown_content(group_name, group_endpoints)
                        file_path = Path(args.output_dir) / f"{group_name}.md"
                        generated_files[str(file_path)] = file_content

                    return generated_files

                # Type ignore needed for monkey patching in dry run mode
                initializer.generator.generate_scaffolding = dry_run_generate  # type: ignore[method-assign]

                # Run the initialization
                result = initializer.initialize()
        else:
            initializer = DocumentationInitializer(args.source_directory, args.output_dir)
            # Run the initialization
            result = initializer.initialize()

        # Format and display output
        if args.format == "json":
            output = format_json_output(result)
        else:
            output = format_text_output(result, args.verbose)

        print(output)

        # Exit with appropriate code
        if result["endpoints_found"] == 0:
            sys.exit(1)  # No endpoints found
        else:
            sys.exit(0)  # Success

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
