"""
FastMarkDocs initialization tool for generating documentation scaffolding.

This module provides functionality to scan existing Python codebases for FastAPI
endpoints and generate boilerplate markdown documentation.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union


@dataclass
class EndpointInfo:
    """Information about a discovered API endpoint."""

    method: str
    path: str
    function_name: str
    file_path: str
    line_number: int
    docstring: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: Union[list[str], None] = None

    def __post_init__(self) -> None:
        if self.tags is None:
            self.tags = []


class FastAPIEndpointScanner:
    """Scanner for discovering FastAPI endpoints in Python source code."""

    def __init__(self, source_directory: str):
        """Initialize the scanner with a source directory."""
        self.source_directory = Path(source_directory)
        self.endpoints: list[EndpointInfo] = []

        # Common FastAPI decorators and their HTTP methods
        self.http_method_decorators = {
            "get": "GET",
            "post": "POST",
            "put": "PUT",
            "delete": "DELETE",
            "patch": "PATCH",
            "head": "HEAD",
            "options": "OPTIONS",
            "trace": "TRACE",
        }

    def scan_directory(self) -> list[EndpointInfo]:
        """Scan the source directory for FastAPI endpoints."""
        self.endpoints = []

        # Find all Python files recursively
        python_files = list(self.source_directory.rglob("*.py"))

        for file_path in python_files:
            try:
                self._scan_file(file_path)
            except Exception as e:
                print(f"Warning: Could not scan {file_path}: {e}")
                continue

        return self.endpoints

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single Python file for FastAPI endpoints."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Skip binary files
            return

        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Skip files with syntax errors
            return

        # Visit all nodes in the AST
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                endpoint_info = self._extract_endpoint_info(node, file_path, content)
                if endpoint_info:
                    self.endpoints.append(endpoint_info)

    def _extract_endpoint_info(
        self, func_node: ast.FunctionDef, file_path: Path, content: str
    ) -> Optional[EndpointInfo]:
        """Extract endpoint information from a function node."""
        # Look for FastAPI decorators
        for decorator in func_node.decorator_list:
            endpoint_info = self._parse_decorator(decorator, func_node, file_path, content)
            if endpoint_info:
                return endpoint_info

        return None

    def _parse_decorator(
        self, decorator: ast.AST, func_node: ast.FunctionDef, file_path: Path, content: str
    ) -> Optional[EndpointInfo]:
        """Parse a decorator to extract endpoint information."""
        method = None
        path = None

        # Handle different decorator patterns
        if isinstance(decorator, ast.Call):
            # @app.get("/path") or @router.get("/path")
            if isinstance(decorator.func, ast.Attribute):
                method_name = decorator.func.attr
                if method_name in self.http_method_decorators:
                    method = self.http_method_decorators[method_name]

                    # Extract path from first argument
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        path = decorator.args[0].value

        elif isinstance(decorator, ast.Attribute):
            # @app.get (without parentheses - less common)
            method_name = decorator.attr
            if method_name in self.http_method_decorators:
                method = self.http_method_decorators[method_name]

        if method and path:
            # Extract additional information
            docstring = ast.get_docstring(func_node)
            summary, description = self._parse_docstring(docstring)
            tags = self._extract_tags_from_decorator(decorator)

            return EndpointInfo(
                method=method,
                path=path,
                function_name=func_node.name,
                file_path=str(file_path.relative_to(self.source_directory)),
                line_number=func_node.lineno,
                docstring=docstring,
                summary=summary,
                description=description,
                tags=tags,
            )

        return None

    def _parse_docstring(self, docstring: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Parse docstring to extract summary and description."""
        if not docstring:
            return None, None

        lines = docstring.strip().split("\n")
        if not lines:
            return None, None

        # First line is typically the summary
        summary = lines[0].strip()

        # Rest is description (if any)
        if len(lines) > 1:
            description_lines = []
            for line in lines[1:]:
                stripped = line.strip()
                if stripped:  # Skip empty lines at the beginning
                    description_lines.extend(lines[lines.index(line) :])
                    break

            if description_lines:
                description = "\n".join(description_lines).strip()
                return summary, description

        return summary, None

    def _extract_tags_from_decorator(self, decorator: ast.AST) -> list[str]:
        """Extract tags from decorator arguments."""
        tags = []

        if isinstance(decorator, ast.Call):
            # Look for tags in keyword arguments
            for keyword in decorator.keywords:
                if keyword.arg == "tags":
                    if isinstance(keyword.value, ast.List):
                        for elt in keyword.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                tags.append(elt.value)

        return tags


class MarkdownScaffoldGenerator:
    """Generator for creating markdown documentation scaffolding."""

    def __init__(self, output_directory: str = "docs"):
        """Initialize the generator with an output directory."""
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(exist_ok=True)

    def generate_scaffolding(self, endpoints: list[EndpointInfo]) -> dict[str, str]:
        """Generate markdown scaffolding for discovered endpoints."""
        if not endpoints:
            return {}

        # Group endpoints by tags or create a general file
        grouped_endpoints = self._group_endpoints(endpoints)
        generated_files = {}

        for group_name, group_endpoints in grouped_endpoints.items():
            file_content = self._generate_markdown_content(group_name, group_endpoints)
            file_path = self.output_directory / f"{group_name}.md"

            # Write the file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)

            generated_files[str(file_path)] = file_content

        return generated_files

    def _group_endpoints(self, endpoints: list[EndpointInfo]) -> dict[str, list[EndpointInfo]]:
        """Group endpoints by tags or other criteria."""
        groups: dict[str, list[EndpointInfo]] = {}

        for endpoint in endpoints:
            # Use the first tag as the group, or 'api' as default
            group_name = endpoint.tags[0] if endpoint.tags else "api"

            # Sanitize group name for filename
            group_name = re.sub(r"[^\w\-_]", "_", group_name.lower())

            if group_name not in groups:
                groups[group_name] = []

            groups[group_name].append(endpoint)

        return groups

    def _generate_markdown_content(self, group_name: str, endpoints: list[EndpointInfo]) -> str:
        """Generate markdown content for a group of endpoints."""
        content = []

        # Header
        title = group_name.replace("_", " ").title()
        content.append(f"# {title} API Documentation\n")
        content.append("This documentation was generated automatically by fmd-init.\n")
        content.append("Please review and enhance the content below.\n\n")

        # Sort endpoints by path and method
        sorted_endpoints = sorted(endpoints, key=lambda e: (e.path, e.method))

        for endpoint in sorted_endpoints:
            content.append(self._generate_endpoint_section(endpoint))

        return "\n".join(content)

    def _generate_endpoint_section(self, endpoint: EndpointInfo) -> str:
        """Generate markdown section for a single endpoint."""
        lines = []

        # Endpoint header
        lines.append(f"## {endpoint.method} {endpoint.path}")
        lines.append("")

        # Summary (from docstring or generated)
        summary = endpoint.summary or f"{endpoint.method.title()} {endpoint.path}"
        lines.append(f"**Summary:** {summary}")
        lines.append("")

        # Description
        if endpoint.description:
            lines.append("### Description")
            lines.append("")
            lines.append(endpoint.description)
            lines.append("")
        else:
            lines.append("### Description")
            lines.append("")
            lines.append("TODO: Add detailed description of this endpoint.")
            lines.append("")

        # Source information
        lines.append("### Implementation Details")
        lines.append("")
        lines.append(f"- **Function:** `{endpoint.function_name}`")
        lines.append(f"- **File:** `{endpoint.file_path}:{endpoint.line_number}`")
        if endpoint.tags:
            lines.append(f"- **Tags:** {', '.join(endpoint.tags)}")
        lines.append("")

        # Placeholder sections
        lines.append("### Parameters")
        lines.append("")
        lines.append("TODO: Document path parameters, query parameters, and request body.")
        lines.append("")

        lines.append("### Response Examples")
        lines.append("")
        lines.append("TODO: Add response examples for different status codes.")
        lines.append("")
        lines.append("```json")
        lines.append("{")
        lines.append('  "example": "response"')
        lines.append("}")
        lines.append("```")
        lines.append("")

        lines.append("### Code Examples")
        lines.append("")
        lines.append("TODO: Add code examples will be generated automatically.")
        lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)


class DocumentationInitializer:
    """Main class for initializing documentation scaffolding."""

    def __init__(self, source_directory: str, output_directory: str = "docs"):
        """Initialize the documentation initializer."""
        self.source_directory = source_directory
        self.output_directory = output_directory
        self.scanner = FastAPIEndpointScanner(source_directory)
        self.generator = MarkdownScaffoldGenerator(output_directory)

    def initialize(self) -> dict[str, Any]:
        """Initialize documentation scaffolding."""
        print(f"Scanning {self.source_directory} for FastAPI endpoints...")

        # Scan for endpoints
        endpoints = self.scanner.scan_directory()

        if not endpoints:
            print("No FastAPI endpoints found.")
            return {"endpoints_found": 0, "files_generated": {}, "summary": "No endpoints discovered"}

        print(f"Found {len(endpoints)} endpoints")

        # Generate scaffolding
        print(f"Generating documentation scaffolding in {self.output_directory}...")
        generated_files = self.generator.generate_scaffolding(endpoints)

        # Create summary
        summary = self._create_summary(endpoints, generated_files)

        print(f"Generated {len(generated_files)} documentation files")
        print("\nSummary:")
        print(summary)

        return {
            "endpoints_found": len(endpoints),
            "files_generated": generated_files,
            "summary": summary,
            "endpoints": endpoints,
        }

    def _create_summary(self, endpoints: list[EndpointInfo], generated_files: dict[str, str]) -> str:
        """Create a summary of the initialization process."""
        lines = []

        lines.append("📊 **Documentation Initialization Complete**")
        lines.append(f"- **Endpoints discovered:** {len(endpoints)}")
        lines.append(f"- **Files generated:** {len(generated_files)}")
        lines.append("")

        # Group by HTTP method
        method_counts: dict[str, int] = {}
        for endpoint in endpoints:
            method_counts[endpoint.method] = method_counts.get(endpoint.method, 0) + 1

        lines.append("**Endpoints by method:**")
        for method, count in sorted(method_counts.items()):
            lines.append(f"- {method}: {count}")
        lines.append("")

        # List generated files
        lines.append("**Generated files:**")
        for file_path in sorted(generated_files.keys()):
            lines.append(f"- {file_path}")
        lines.append("")

        lines.append("**Next steps:**")
        lines.append("1. Review the generated documentation files")
        lines.append("2. Fill in TODO sections with detailed information")
        lines.append("3. Add parameter documentation and response examples")
        lines.append("4. Run `fmd-lint` to check documentation completeness")

        return "\n".join(lines)
