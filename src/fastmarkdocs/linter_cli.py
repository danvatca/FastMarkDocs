#!/usr/bin/env python3
"""
FastMarkDocs Linter CLI

Command-line interface for the FastMarkDocs documentation linter.
"""

import argparse
import json
import sys
import time
from typing import Any

from .linter import DocumentationLinter


def format_results(results: dict[str, Any], format_type: str = "text") -> str:
    """Format linting results for display."""
    if format_type == "json":
        return json.dumps(results, indent=2, ensure_ascii=False)

    # Text format
    output = []
    summary = results["summary"]
    stats = results["statistics"]

    # Header
    output.append("=" * 60)
    output.append("🔍 FastMarkDocs Documentation Linter Results")
    output.append("=" * 60)
    output.append("")

    # Summary
    output.append(f"📊 {summary['message']}")
    output.append(
        f"📈 Coverage: {summary['coverage']} | Completeness: {summary['completeness']} | Issues: {summary['total_issues']}"
    )
    output.append("")

    # Statistics
    output.append("📈 Statistics:")
    output.append(f"   • Total API endpoints: {stats['total_openapi_endpoints']}")
    output.append(f"   • Documented endpoints: {stats['total_documented_endpoints']}")
    output.append(f"   • Documentation coverage: {stats['documentation_coverage_percentage']}%")
    output.append(f"   • Average completeness: {stats['average_completeness_score']}%")
    output.append("")

    # Issues breakdown
    if stats["issues"]["total_issues"] > 0:
        output.append("🚨 Issues Found:")
        issues = stats["issues"]
        if issues["missing_documentation"] > 0:
            output.append(f"   • Missing documentation: {issues['missing_documentation']}")
        if issues["incomplete_documentation"] > 0:
            output.append(f"   • Incomplete documentation: {issues['incomplete_documentation']}")
        if issues["common_mistakes"] > 0:
            output.append(f"   • Common mistakes: {issues['common_mistakes']}")
        if issues["orphaned_documentation"] > 0:
            output.append(f"   • Orphaned documentation: {issues['orphaned_documentation']}")
        if issues["enhancement_failures"] > 0:
            output.append(f"   • Enhancement failures: {issues['enhancement_failures']}")
        output.append("")

    # Detailed issues
    if results["missing_documentation"]:
        output.append("❌ Missing Documentation:")
        for item in results["missing_documentation"][:10]:  # Show first 10
            output.append(f"   • {item['method']} {item['path']}")
            if item.get("similar_documented_paths"):
                output.append(f"     Similar documented: {', '.join(item['similar_documented_paths'][:2])}")
        if len(results["missing_documentation"]) > 10:
            output.append(f"   ... and {len(results['missing_documentation']) - 10} more")
        output.append("")

    if results["common_mistakes"]:
        output.append("⚠️ Common Mistakes:")
        for item in results["common_mistakes"][:5]:  # Show first 5
            output.append(f"   • {item['type']}: {item['message']}")
            if item.get("suggestion"):
                output.append(f"     💡 {item['suggestion']}")
        if len(results["common_mistakes"]) > 5:
            output.append(f"   ... and {len(results['common_mistakes']) - 5} more")
        output.append("")

    if results["enhancement_failures"]:
        output.append("🔥 Enhancement Failures:")
        for item in results["enhancement_failures"][:5]:  # Show first 5
            if "method" in item and "path" in item:
                output.append(f"   • {item['method']} {item['path']}: {item['message']}")
            else:
                output.append(f"   • {item['message']}")
        if len(results["enhancement_failures"]) > 5:
            output.append(f"   ... and {len(results['enhancement_failures']) - 5} more")
        output.append("")

    # Recommendations
    if results["recommendations"]:
        output.append("💡 Recommendations:")
        for rec in results["recommendations"]:
            priority_emoji = {"critical": "🔥", "high": "⚠️", "medium": "📝", "low": "💭"}
            emoji = priority_emoji.get(rec["priority"], "📝")
            output.append(f"   {emoji} {rec['title']}")
            output.append(f"     {rec['description']}")
            output.append(f"     Action: {rec['action']}")
        output.append("")

    output.append("=" * 60)

    return "\n".join(output)


def main() -> None:
    """Main CLI entry point for fmd-lint."""
    parser = argparse.ArgumentParser(
        description="FastMarkDocs Documentation Linter - Analyze and improve your API documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fmd-lint --openapi openapi.json --docs docs/api
  fmd-lint --openapi openapi.json --docs docs/api --format json
  fmd-lint --openapi openapi.json --docs docs/api --output report.txt
  fmd-lint --openapi openapi.json --docs docs/api --recursive --base-url https://api.example.com

Note: The tool exits with code 1 if any issues are found, making it suitable for CI/CD pipelines.
        """,
    )

    parser.add_argument("--openapi", required=True, help="Path to OpenAPI JSON schema file")

    parser.add_argument("--docs", required=True, help="Path to documentation directory")

    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format (default: text)")

    parser.add_argument("--output", help="Output file path (default: stdout)")

    parser.add_argument(
        "--base-url", default="https://api.example.com", help="Base URL for the API (default: https://api.example.com)"
    )

    parser.add_argument("--recursive", action="store_true", help="Search documentation directory recursively")

    args = parser.parse_args()

    try:
        # Load OpenAPI schema
        with open(args.openapi, encoding="utf-8") as f:
            openapi_schema = json.load(f)

        # Create linter
        linter = DocumentationLinter(
            openapi_schema=openapi_schema, docs_directory=args.docs, base_url=args.base_url, recursive=args.recursive
        )

        # Run linting
        print("🔍 Analyzing documentation...", file=sys.stderr)
        start_time = time.time()
        results = linter.lint()
        end_time = time.time()

        print(f"✅ Analysis completed in {end_time - start_time:.2f}s", file=sys.stderr)

        # Format results
        formatted_output = format_results(results, args.format)

        # Output results
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(formatted_output)
            print(f"📄 Results written to {args.output}", file=sys.stderr)
        else:
            print(formatted_output)

        # Exit with appropriate code
        if results["statistics"]["issues"]["total_issues"] > 0:
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in OpenAPI file - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
