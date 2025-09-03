#!/usr/bin/env python3
"""
FastMarkDocs Linter CLI

Command-line interface for the FastMarkDocs documentation linter.
"""

import argparse
import json
import os
import re
import shlex
import subprocess  # nosec B404 - Used safely with shlex.split()
import sys
import time
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

from .linter import DocumentationLinter


class LinterConfig:
    """Configuration for the FastMarkDocs linter."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from file or defaults."""
        self.exclude_endpoints: list[dict[str, Any]] = []
        self.spec_generator: list[str] = []
        self.spec_generator_output: Optional[str] = None
        self.docs: list[str] = []
        self.openapi: Optional[str] = None
        self.recursive: bool = True
        self.base_url: str = "https://api.example.com"
        self.format: str = "text"
        self.output: Optional[str] = None

        if config_path:
            self.load_from_file(config_path)

    def load_from_file(self, config_path: str) -> None:
        """Load configuration from YAML file."""
        if not yaml:
            raise ImportError("PyYAML is required for configuration file support. Install with: pip install pyyaml")

        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        if not config_data:
            return

        # Load exclude patterns
        if "exclude" in config_data and "endpoints" in config_data["exclude"]:
            self.exclude_endpoints = config_data["exclude"]["endpoints"]

        # Load spec generator commands
        if "spec_generator" in config_data:
            spec_gen_config = config_data["spec_generator"]
            if isinstance(spec_gen_config, list):
                # Legacy format: list of commands
                self.spec_generator = spec_gen_config
            elif isinstance(spec_gen_config, dict):
                # New format: dict with commands and output_file
                self.spec_generator = spec_gen_config.get("commands", [])
                self.spec_generator_output = spec_gen_config.get("output_file")
            else:
                raise ValueError(
                    "spec_generator must be a list of commands or a dict with 'commands' and 'output_file'"
                )

        # Load docs directories
        if "docs" in config_data:
            self.docs = config_data["docs"]

        # Load OpenAPI file path
        if "openapi" in config_data:
            self.openapi = config_data["openapi"]

        # Load other options
        if "recursive" in config_data:
            self.recursive = config_data["recursive"]

        if "base_url" in config_data:
            self.base_url = config_data["base_url"]

        if "format" in config_data:
            self.format = config_data["format"]

        if "output" in config_data:
            self.output = config_data["output"]

    def should_exclude_endpoint(self, method: str, path: str) -> bool:
        """Check if an endpoint should be excluded based on configuration."""
        for exclude_rule in self.exclude_endpoints:
            if isinstance(exclude_rule, dict):
                # New format with path and methods
                path_pattern = exclude_rule.get("path", "")
                methods = exclude_rule.get("methods", [])

                # Check if path matches
                if path_pattern and re.search(path_pattern, path):
                    # Check if method matches
                    for method_pattern in methods:
                        if method_pattern == ".*" or re.search(method_pattern, method, re.IGNORECASE):
                            return True
            elif isinstance(exclude_rule, str):
                # Legacy format: "METHOD /path" or "/path"
                if " " in exclude_rule:
                    rule_method, rule_path = exclude_rule.split(" ", 1)
                    if rule_method.upper() == method.upper() and rule_path == path:
                        return True
                else:
                    # Just path
                    if exclude_rule == path:
                        return True

        return False


def find_config_file() -> Optional[str]:
    """Find configuration file in current directory or parent directories."""
    current_dir = Path.cwd()

    # Check current directory and parent directories
    for directory in [current_dir] + list(current_dir.parents):
        config_file = directory / ".fmd-lint.yaml"
        if config_file.exists():
            return str(config_file)

        # Also check for .yml extension
        config_file = directory / ".fmd-lint.yml"
        if config_file.exists():
            return str(config_file)

    return None


def run_spec_generator(commands: list[str], output_file: Optional[str] = None) -> str:
    """Run spec generator commands and return the path to generated OpenAPI file."""
    if not commands:
        raise ValueError("No spec generator commands provided")

    for command in commands:
        try:
            print(f"🔧 Running spec generator: {command}", file=sys.stderr)

            # Check if command contains shell features (redirection, pipes, etc.)
            shell_features = [">", "<", "|", "&", ";", "&&", "||", "$(", "`"]
            needs_shell = any(feature in command for feature in shell_features)

            if needs_shell:
                # Use shell for commands with shell features, but validate command first
                # Only allow commands that start with safe executables
                safe_prefixes = ["echo", "python", "poetry", "pip", "curl", "wget", "cat", "mkdir", "touch"]
                command_start = command.strip().split()[0]
                if not any(command_start.startswith(prefix) for prefix in safe_prefixes):
                    raise ValueError(f"Unsafe command detected: {command_start}")

                # Use shell but with limited environment for safety
                result = subprocess.run(  # nosec B602 - Command is validated for safety
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True,
                    env={"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "")},
                )
            else:
                # Parse command safely using shlex to avoid shell injection
                parsed_command = shlex.split(command)

                # Validate command even for non-shell execution
                safe_prefixes = ["echo", "python", "poetry", "pip", "curl", "wget", "cat", "mkdir", "touch"]
                command_start = parsed_command[0] if parsed_command else ""
                if not any(command_start.startswith(prefix) for prefix in safe_prefixes):
                    raise ValueError(f"Unsafe command detected: {command_start}")

                result = subprocess.run(
                    parsed_command, capture_output=True, text=True, check=True
                )  # nosec B603 - Command is parsed safely with shlex

            if result.stdout:
                print(result.stdout, file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"❌ Spec generator failed: {e}", file=sys.stderr)
            if e.stderr:
                print(e.stderr, file=sys.stderr)
            raise

    # Try to find the generated OpenAPI file
    if output_file:
        # Use specified output file
        if Path(output_file).exists():
            return output_file
        else:
            raise FileNotFoundError(f"Specified output file not found: {output_file}")
    else:
        # Use default file names
        common_names = ["openapi.json", "openapi_complete.json", "openapi_enhanced.json", "swagger.json"]
        for name in common_names:
            if Path(name).exists():
                return name

        raise FileNotFoundError("Could not find generated OpenAPI file. Expected one of: " + ", ".join(common_names))


def format_results(results: dict[str, Any], format_type: str = "text", show_all: bool = False) -> str:
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
    if "docs_directory" in results.get("metadata", {}):
        output.append(f"   • Documentation directory: {results['metadata']['docs_directory']}")
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
        if issues.get("duplicate_endpoints", 0) > 0:
            output.append(f"   • Duplicate endpoints: {issues['duplicate_endpoints']}")
        if issues["orphaned_documentation"] > 0:
            output.append(f"   • Orphaned documentation: {issues['orphaned_documentation']}")
        if issues["enhancement_failures"] > 0:
            output.append(f"   • Enhancement failures: {issues['enhancement_failures']}")
        if issues.get("todo_entries", 0) > 0:
            output.append(f"   • TODO entries: {issues['todo_entries']}")
        output.append("")

    # Detailed issues
    if results["missing_documentation"]:
        output.append("❌ Missing Documentation:")
        items_to_show = results["missing_documentation"] if show_all else results["missing_documentation"][:10]
        for item in items_to_show:
            output.append(f"   • {item['method']} {item['path']}")
            if item.get("similar_documented_paths"):
                similar_paths = item["similar_documented_paths"] if show_all else item["similar_documented_paths"][:2]
                output.append(f"     Similar documented: {', '.join(similar_paths)}")
        if not show_all and len(results["missing_documentation"]) > 10:
            output.append(f"   ... and {len(results['missing_documentation']) - 10} more")
        output.append("")

    if results["incomplete_documentation"]:
        output.append("📝 Incomplete Documentation:")
        output.append("   📁 Look for these endpoints in your documentation files:")
        items_to_show = results["incomplete_documentation"] if show_all else results["incomplete_documentation"][:10]
        for item in items_to_show:
            output.append(f"   • {item['method']} {item['path']} (Score: {item['completeness_score']:.1f}%)")
            for issue in item["issues"]:
                output.append(f"     - {issue}")
            if item.get("suggestions"):
                suggestions = item["suggestions"] if show_all else item["suggestions"][:2]
                output.append(f"     💡 Suggestions: {', '.join(suggestions)}")
        if not show_all and len(results["incomplete_documentation"]) > 10:
            output.append(f"   ... and {len(results['incomplete_documentation']) - 10} more")
        output.append("")

    if results["common_mistakes"]:
        output.append("⚠️ Common Mistakes:")
        items_to_show = results["common_mistakes"] if show_all else results["common_mistakes"][:5]
        for item in items_to_show:
            output.append(f"   • {item['type']}: {item['message']}")
            if item.get("suggestion"):
                output.append(f"     💡 {item['suggestion']}")
        if not show_all and len(results["common_mistakes"]) > 5:
            output.append(f"   ... and {len(results['common_mistakes']) - 5} more")
        output.append("")

    if results.get("duplicate_endpoints"):
        output.append("🔄 Duplicate Endpoints:")
        output.append("   📁 These endpoints are documented multiple times:")
        items_to_show = results["duplicate_endpoints"] if show_all else results["duplicate_endpoints"][:5]
        for item in items_to_show:
            output.append(f"   • {item['method']} {item['path']} ({len(item['occurrences'])} times)")
            output.append(f"     📄 Files: {', '.join(item['files'])}")
            if item.get("suggestion"):
                output.append(f"     💡 {item['suggestion']}")
        if not show_all and len(results["duplicate_endpoints"]) > 5:
            output.append(f"   ... and {len(results['duplicate_endpoints']) - 5} more")
        output.append("")

    if results["orphaned_documentation"]:
        output.append("👻 Orphaned Documentation:")
        output.append("   📁 These endpoints are documented but don't exist in your API:")
        items_to_show = results["orphaned_documentation"] if show_all else results["orphaned_documentation"][:10]
        for item in items_to_show:
            output.append(f"   • {item['method']} {item['path']}")
            if item.get("summary"):
                if show_all:
                    summary = item["summary"]
                else:
                    summary = item["summary"][:80] + "..." if len(item["summary"]) > 80 else item["summary"]
                output.append(f"     📝 Summary: {summary}")

            details = []
            if item.get("description_length", 0) > 0:
                details.append(f"Description: {item['description_length']} chars")
            if item.get("has_code_samples"):
                details.append("Has code samples")
            if item.get("has_response_examples"):
                details.append("Has response examples")
            if item.get("has_parameters"):
                details.append("Has parameters")

            if details:
                output.append(f"     📊 Details: {', '.join(details)}")

            if item.get("documentation_file") and item["documentation_file"] != "Unknown file":
                output.append(f"     📂 File: {item['documentation_file']}")

            if item.get("suggestion"):
                output.append(f"     💡 {item['suggestion']}")
        if not show_all and len(results["orphaned_documentation"]) > 10:
            output.append(f"   ... and {len(results['orphaned_documentation']) - 10} more")
        output.append("")

    if results["enhancement_failures"]:
        output.append("🔥 Enhancement Failures:")
        items_to_show = results["enhancement_failures"] if show_all else results["enhancement_failures"][:5]
        for item in items_to_show:
            if "method" in item and "path" in item:
                output.append(f"   • {item['method']} {item['path']}: {item['message']}")
            else:
                output.append(f"   • {item['message']}")
        if not show_all and len(results["enhancement_failures"]) > 5:
            output.append(f"   ... and {len(results['enhancement_failures']) - 5} more")
        output.append("")

    if results.get("todo_entries"):
        output.append("📝 TODO Entries:")
        output.append("   📁 These TODO items need to be addressed:")
        items_to_show = results["todo_entries"] if show_all else results["todo_entries"][:10]
        for item in items_to_show:
            output.append(f"   • {item['file']}:{item['line']}")
            output.append(f"     📝 {item['todo_text']}")
            if item.get("context") and item["context"] != "in documentation":
                output.append(f"     📍 Location: {item['context']}")
            # Show a truncated version of the content for context
            content = item["content"]
            if not show_all and len(content) > 80:
                content = content[:77] + "..."
            output.append(f"     📄 Line: {content}")
        if not show_all and len(results["todo_entries"]) > 10:
            output.append(f"   ... and {len(results['todo_entries']) - 10} more")
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
  fmd-lint --openapi openapi.json --docs docs/api --all
  fmd-lint --openapi openapi.json --docs docs/api --no-recursive --base-url https://api.example.com
  fmd-lint --config .fmd-lint.yaml

Configuration file (.fmd-lint.yaml):
  exclude:
    endpoints:
      - path: "^/static/.*"
        methods:
          - "GET"
      - path: "^/login"
        methods:
          - ".*"
  openapi: "./openapi.json"
  docs:
    - "./src/doorman/api"
  recursive: true
  base_url: "https://api.example.com"

  # Alternative: Use spec_generator instead of openapi
  spec_generator:
    commands:
      - "poetry run python ./generate_openapi.py"
    output_file: "./my-custom-schema.json"

Note: The tool exits with code 1 if any issues are found, making it suitable for CI/CD pipelines.
      Recursive directory scanning is enabled by default. Use --no-recursive to disable.
        """,
    )

    parser.add_argument("--config", help="Path to configuration file (.fmd-lint.yaml)")

    parser.add_argument("--openapi", help="Path to OpenAPI JSON schema file")

    parser.add_argument("--docs", help="Path to documentation directory")

    parser.add_argument("--format", choices=["text", "json"], help="Output format")

    parser.add_argument("--output", help="Output file path (default: stdout)")

    parser.add_argument("--base-url", help="Base URL for the API")

    parser.add_argument(
        "--no-recursive", action="store_true", help="Disable recursive search of documentation directory"
    )

    parser.add_argument("--all", action="store_true", help="Show all details and suggestions without truncation")

    args = parser.parse_args()

    try:
        # Load configuration
        config_file = args.config or find_config_file()
        config = LinterConfig(config_file) if config_file else LinterConfig()

        if config_file:
            print(f"📋 Using configuration file: {config_file}", file=sys.stderr)

        # Override config with command line arguments
        if args.openapi:
            openapi_path = args.openapi
        elif config.openapi:
            openapi_path = config.openapi
        elif config.spec_generator:
            # Run spec generator
            openapi_path = run_spec_generator(config.spec_generator, config.spec_generator_output)
        else:
            parser.error(
                "Either --openapi must be provided, openapi must be configured, or spec_generator must be configured"
            )

        if args.docs:
            docs_path = args.docs
        elif config.docs:
            docs_path = config.docs[0]  # Use first docs directory for now
        else:
            parser.error("Either --docs must be provided or docs must be configured")

        format_type = args.format or config.format
        output_path = args.output or config.output
        base_url = args.base_url or config.base_url
        recursive = not args.no_recursive if args.no_recursive else config.recursive

        # Load OpenAPI schema
        with open(openapi_path, encoding="utf-8") as f:
            openapi_schema = json.load(f)

        # Create linter
        linter = DocumentationLinter(
            openapi_schema=openapi_schema, docs_directory=docs_path, base_url=base_url, recursive=recursive
        )

        # Apply exclusions if configured
        if config.exclude_endpoints:
            linter.config = config

        # Run linting
        print("🔍 Analyzing documentation...", file=sys.stderr)
        start_time = time.time()
        results = linter.lint()
        end_time = time.time()

        print(f"✅ Analysis completed in {end_time - start_time:.2f}s", file=sys.stderr)

        # Format results
        formatted_output = format_results(results, format_type, show_all=args.all)

        # Output results
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted_output)
            print(f"📄 Results written to {output_path}", file=sys.stderr)
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
    except ImportError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
