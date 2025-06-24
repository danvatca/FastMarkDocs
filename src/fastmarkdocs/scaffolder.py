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
class ParameterInfo:
    """Information about a function parameter."""

    name: str
    type_hint: Optional[str] = None
    default_value: Optional[str] = None
    is_required: bool = True
    parameter_type: str = "query"  # "path", "query", "body"


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
    parameters: Union[list[ParameterInfo], None] = None

    def __post_init__(self) -> None:
        if self.tags is None:
            self.tags = []
        if self.parameters is None:
            self.parameters = []


@dataclass
class RouterInfo:
    """Information about a discovered APIRouter."""

    name: str
    tags: list[str]
    prefix: Optional[str] = None
    line_number: Optional[int] = None


class FastAPIEndpointScanner:
    """Scanner for discovering FastAPI endpoints in Python source code."""

    def __init__(self, source_directory: str):
        """Initialize the scanner with a source directory."""
        self.source_directory = Path(source_directory)
        self.endpoints: list[EndpointInfo] = []
        self.http_method_decorators = {
            "get": "GET",
            "post": "POST",
            "put": "PUT",
            "patch": "PATCH",
            "delete": "DELETE",
            "head": "HEAD",
            "options": "OPTIONS",
            "trace": "TRACE",
        }

    def scan_directory(self) -> list[EndpointInfo]:
        """Scan the directory recursively for FastAPI endpoints."""
        self.endpoints = []
        scanned_files = 0
        skipped_files = 0

        print(f"🔍 Scanning {self.source_directory} recursively for Python files...")

        # Get all Python files recursively
        python_files = list(self.source_directory.rglob("*.py"))

        # Filter out common directories that typically don't contain API endpoints
        excluded_patterns = [
            "__pycache__",
            ".git",
            ".pytest_cache",
            "htmlcov",
            ".venv",
            "venv",
            "node_modules",
            ".tox",
            "build",
            "dist",
            "tests/",  # Exclude test directories
            "test_",  # Exclude test files
        ]

        filtered_files = []
        for file_path in python_files:
            # Check if file is in an excluded directory
            if any(pattern in str(file_path) for pattern in excluded_patterns):
                continue
            filtered_files.append(file_path)

        print(f"📁 Found {len(python_files)} Python files ({len(filtered_files)} after filtering)")

        if not filtered_files:
            print("⚠️  No Python files found to scan")
            return self.endpoints

        # Scan each file
        for file_path in filtered_files:
            try:
                endpoints_before = len(self.endpoints)
                self._scan_file(file_path)
                endpoints_after = len(self.endpoints)

                scanned_files += 1

                # Show progress for files that contain endpoints
                if endpoints_after > endpoints_before:
                    new_endpoints = endpoints_after - endpoints_before
                    relative_path = file_path.relative_to(self.source_directory)
                    print(f"  ✅ {relative_path} → {new_endpoints} endpoint{'s' if new_endpoints != 1 else ''}")

            except (SyntaxError, UnicodeDecodeError):
                skipped_files += 1
                relative_path = file_path.relative_to(self.source_directory)
                print(f"  ⚠️  Skipped {relative_path} (syntax/encoding error)")
                continue
            except Exception as e:
                skipped_files += 1
                relative_path = file_path.relative_to(self.source_directory)
                print(f"  ⚠️  Skipped {relative_path} (error: {type(e).__name__})")
                continue

        # Summary
        if scanned_files > 0:
            print(f"📊 Scan complete: {scanned_files} files processed, {skipped_files} skipped")

        return self.endpoints

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single Python file for endpoints."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # First pass: discover routers and their tags
            routers = self._discover_routers(tree)

            # Second pass: discover endpoints and associate with router tags
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    endpoint_infos = self._extract_endpoint_info(node, file_path, content, routers)
                    if endpoint_infos:
                        self.endpoints.extend(endpoint_infos)

        except (SyntaxError, UnicodeDecodeError, OSError):
            # Skip files with syntax errors, encoding issues, or file access problems
            # These are expected when scanning directories with non-Python files or invalid Python code
            return

    def _discover_routers(self, tree: ast.AST) -> dict[str, RouterInfo]:
        """Discover APIRouter definitions and extract their tags."""
        routers: dict[str, RouterInfo] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Look for router = APIRouter(...) assignments
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        router_name = target.id

                        if isinstance(node.value, ast.Call):
                            # Check if it's an APIRouter call
                            if self._is_api_router_call(node.value):
                                router_info = self._extract_router_info(node.value, router_name, node.lineno)
                                if router_info:
                                    routers[router_name] = router_info

        return routers

    def _is_api_router_call(self, call_node: ast.Call) -> bool:
        """Check if a call node is creating an APIRouter."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id == "APIRouter"
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr == "APIRouter"
        return False

    def _extract_router_info(self, call_node: ast.Call, router_name: str, line_number: int) -> Optional[RouterInfo]:
        """Extract information from an APIRouter constructor call."""
        tags = []
        prefix = None

        # Extract tags and prefix from keyword arguments
        for keyword in call_node.keywords:
            if keyword.arg == "tags":
                if isinstance(keyword.value, ast.List):
                    for elt in keyword.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            tags.append(elt.value)
            elif keyword.arg == "prefix":
                if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                    prefix = keyword.value.value

        if tags:  # Only create RouterInfo if tags are found
            return RouterInfo(name=router_name, tags=tags, prefix=prefix, line_number=line_number)

        return None

    def _extract_endpoint_info(
        self,
        func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        file_path: Path,
        content: str,
        routers: dict[str, RouterInfo],
    ) -> list[EndpointInfo]:
        """Extract endpoint information from a function definition. Returns a list since one function can have multiple HTTP method decorators."""
        endpoints = []

        for decorator in func_node.decorator_list:
            endpoint_info = self._parse_decorator(decorator, func_node, file_path, content, routers)
            if endpoint_info:
                endpoints.append(endpoint_info)

        return endpoints

    def _parse_decorator(
        self,
        decorator: ast.AST,
        func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        file_path: Path,
        content: str,
        routers: dict[str, RouterInfo],
    ) -> Optional[EndpointInfo]:
        """Parse a decorator to extract endpoint information."""
        method = None
        path = None
        router_tags = []
        include_in_schema = True  # Default to True

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

                    # Check for include_in_schema parameter
                    for keyword in decorator.keywords:
                        if keyword.arg == "include_in_schema":
                            if isinstance(keyword.value, ast.Constant):
                                include_in_schema = keyword.value.value

                    # Skip endpoints excluded from schema (error handlers)
                    if not include_in_schema:
                        return None

                    # Check if this is a router-based endpoint
                    if isinstance(decorator.func.value, ast.Name):
                        router_name = decorator.func.value.id
                        if router_name in routers:
                            router_info = routers[router_name]
                            router_tags = router_info.tags.copy()

                            # Combine router prefix with endpoint path
                            if router_info.prefix:
                                # Handle prefix combination
                                prefix = router_info.prefix.rstrip("/")
                                endpoint_path = path.lstrip("/") if path else ""
                                if endpoint_path:
                                    # Special handling for colon-based paths (e.g., ":verifyOtp")
                                    if endpoint_path.startswith(":"):
                                        path = f"{prefix}{endpoint_path}"
                                    else:
                                        path = f"{prefix}/{endpoint_path}"
                                else:
                                    path = prefix

        elif isinstance(decorator, ast.Attribute):
            # @app.get (without parentheses - less common)
            method_name = decorator.attr
            if method_name in self.http_method_decorators:
                method = self.http_method_decorators[method_name]

        if method and path is not None:
            # Extract additional information
            docstring = ast.get_docstring(func_node)
            summary, description = self._parse_docstring(docstring)
            endpoint_tags = self._extract_tags_from_decorator(decorator)

            # Normalize path to match OpenAPI schema format (remove type annotations)
            normalized_path = self._normalize_path_for_openapi(path)
            parameters = self._extract_parameters(func_node, normalized_path, method)

            # Combine router tags with endpoint tags (endpoint tags take precedence)
            combined_tags = router_tags + [tag for tag in endpoint_tags if tag not in router_tags]

            return EndpointInfo(
                method=method,
                path=normalized_path,  # Use normalized path
                function_name=func_node.name,
                file_path=str(file_path.relative_to(self.source_directory)),
                line_number=func_node.lineno,
                docstring=docstring,
                summary=summary,
                description=description,
                tags=combined_tags,
                parameters=parameters,
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

    def _extract_parameters(
        self, func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef], path: str, method: str
    ) -> list[ParameterInfo]:
        """Extract parameter information from function definition."""
        parameters = []

        # Extract path parameters from the path string
        path_params = self._extract_path_parameters(path)

        # Analyze function arguments
        for arg in func_node.args.args:
            param_name = arg.arg

            # Skip common FastAPI framework parameters
            if param_name in ["request", "response", "background_tasks"]:
                continue

            # Skip dependency injection parameters (those with Depends())
            if self._is_dependency_parameter(func_node, param_name):
                continue

            # Determine parameter type and requirements
            type_hint = self._get_type_hint(arg)
            default_value = self._get_default_value(func_node, param_name)
            is_required = default_value is None

            # Determine parameter location (path, query, or body)
            if param_name in path_params:
                param_type = "path"
                is_required = True  # Path parameters are always required
            elif method.upper() in ["POST", "PUT", "PATCH"] and self._is_body_parameter(arg, type_hint):
                param_type = "body"
            else:
                param_type = "query"

            parameters.append(
                ParameterInfo(
                    name=param_name,
                    type_hint=type_hint,
                    default_value=default_value,
                    is_required=is_required,
                    parameter_type=param_type,
                )
            )

        return parameters

    def _extract_path_parameters(self, path: str) -> set[str]:
        """Extract parameter names from path string like '/users/{user_id}/posts/{post_id}'."""
        import re

        path_param_pattern = r"\{([^}:]+)(?::[^}]*)?\}"  # Handle {param} and {param:type} formats
        matches = re.findall(path_param_pattern, path)
        return set(matches)

    def _normalize_path_for_openapi(self, path: str) -> str:
        """
        Normalize path to match OpenAPI schema format.

        FastAPI routes can use {param:type} but OpenAPI schema uses {param}.
        This method converts {path:path} to {path}, {user_id:int} to {user_id}, etc.
        """
        import re

        # Replace {param:type} with {param}
        normalized_path = re.sub(r"\{([^}:]+):[^}]*\}", r"{\1}", path)
        return normalized_path

    def _is_dependency_parameter(
        self, func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef], param_name: str
    ) -> bool:
        """Check if a parameter uses FastAPI's Depends() for dependency injection."""
        # Look for default values that are Depends() calls
        defaults = func_node.args.defaults
        args = func_node.args.args

        # Find the parameter index
        param_index = None
        for i, arg in enumerate(args):
            if arg.arg == param_name:
                param_index = i
                break

        if param_index is None:
            return False

        # Check if this parameter has a default value
        defaults_offset = len(args) - len(defaults)
        if param_index < defaults_offset:
            return False

        default_index = param_index - defaults_offset
        if default_index >= len(defaults):
            return False

        default_value = defaults[default_index]

        # Check if the default is a Depends() call
        if isinstance(default_value, ast.Call):
            if isinstance(default_value.func, ast.Name) and default_value.func.id == "Depends":
                return True
            elif isinstance(default_value.func, ast.Attribute) and default_value.func.attr == "Depends":
                return True

        return False

    def _get_type_hint(self, arg: ast.arg) -> Optional[str]:
        """Extract type hint from function argument."""
        if arg.annotation:
            return ast.unparse(arg.annotation)
        return None

    def _get_default_value(
        self, func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef], param_name: str
    ) -> Optional[str]:
        """Get the default value for a parameter if it exists."""
        args = func_node.args.args
        defaults = func_node.args.defaults

        # Find parameter index
        param_index = None
        for i, arg in enumerate(args):
            if arg.arg == param_name:
                param_index = i
                break

        if param_index is None:
            return None

        # Check if this parameter has a default value
        defaults_offset = len(args) - len(defaults)
        if param_index < defaults_offset:
            return None

        default_index = param_index - defaults_offset
        if default_index >= len(defaults):
            return None

        default_value = defaults[default_index]

        # Skip Depends() calls
        if isinstance(default_value, ast.Call):
            if isinstance(default_value.func, ast.Name) and default_value.func.id == "Depends":
                return None
            elif isinstance(default_value.func, ast.Attribute) and default_value.func.attr == "Depends":
                return None

        try:
            return ast.unparse(default_value)
        except Exception:
            return "..."

    def _is_body_parameter(self, arg: ast.arg, type_hint: Optional[str]) -> bool:
        """Determine if a parameter should be treated as a request body."""
        if not type_hint:
            return False

        # Common patterns for request body parameters
        body_indicators = ["Model", "Schema", "Request", "Create", "Update", "Add", "Spec", "BaseModel", "Pydantic"]

        return any(indicator in type_hint for indicator in body_indicators)


class MarkdownScaffoldGenerator:
    """Generator for creating markdown documentation scaffolding."""

    def __init__(self, output_directory: str = "docs"):
        """Initialize the generator with an output directory."""
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(exist_ok=True)

    def generate_scaffolding(self, endpoints: list[EndpointInfo]) -> dict[str, str]:
        """Generate markdown scaffolding for discovered endpoints."""
        generated_files = {}

        # Always generate general_docs.md
        general_docs_content = self._generate_general_docs()
        general_docs_path = self.output_directory / "general_docs.md"

        # Write general docs file
        with open(general_docs_path, "w", encoding="utf-8") as f:
            f.write(general_docs_content)

        generated_files[str(general_docs_path)] = general_docs_content

        # Generate endpoint-specific documentation if endpoints exist
        if endpoints:
            # Group endpoints by tags or create a general file
            grouped_endpoints = self._group_endpoints(endpoints)

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

        # Parameters section
        if endpoint.parameters:
            self._add_parameters_section(lines, endpoint.parameters)
        else:
            lines.append("### Parameters")
            lines.append("")
            lines.append("No parameters detected.")
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
        lines.append("#### cURL")
        lines.append("```bash")

        # Generate cURL example
        curl_example = self._generate_curl_example(endpoint)
        lines.append(curl_example)
        lines.append("```")
        lines.append("")

        lines.append("#### Python")
        lines.append("```python")
        lines.append("import requests")
        lines.append("")
        lines.append(f"# TODO: Add Python example for {endpoint.method} {endpoint.path}")
        lines.append(f"response = requests.{endpoint.method.lower()}(")
        lines.append(f'    url="{{base_url}}{endpoint.path}",')
        lines.append('    headers={"Authorization": "Bearer your_token"}')
        if endpoint.method.upper() in ["POST", "PUT", "PATCH"]:
            lines.append('    json={"TODO": "Add request data"}')
        lines.append(")")
        lines.append("print(response.json())")
        lines.append("```")
        lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _generate_general_docs(self) -> str:
        """Generate general API documentation with TODO items for important sections."""
        lines = []

        # Header
        lines.append("# General API Documentation")
        lines.append("")
        lines.append("This document contains general information about the API that applies to all endpoints.")
        lines.append("This documentation was generated automatically by fmd-init.")
        lines.append("Please review and enhance the content below.")
        lines.append("")

        # Overview section
        lines.append("## Overview")
        lines.append("")
        lines.append("TODO: Add a brief overview of your API, its purpose, and main functionality.")
        lines.append("")
        lines.append("### Key Features")
        lines.append("")
        lines.append("TODO: List the main features and capabilities of your API:")
        lines.append("- Feature 1")
        lines.append("- Feature 2")
        lines.append("- Feature 3")
        lines.append("")

        # Base URL section
        lines.append("## Base URL")
        lines.append("")
        lines.append("TODO: Specify your API's base URL(s):")
        lines.append("")
        lines.append("```")
        lines.append("Production: https://api.example.com")
        lines.append("Staging: https://staging-api.example.com")
        lines.append("Development: http://localhost:8000")
        lines.append("```")
        lines.append("")

        # Authentication section
        lines.append("## Authentication")
        lines.append("")
        lines.append("TODO: Document your authentication mechanism. Common approaches include:")
        lines.append("")
        lines.append("### API Keys")
        lines.append("")
        lines.append("TODO: If using API keys, document how to obtain and use them:")
        lines.append("")
        lines.append("```bash")
        lines.append('curl -H "X-API-Key: your_api_key" https://api.example.com/endpoint')
        lines.append("```")
        lines.append("")
        lines.append("### Bearer Tokens")
        lines.append("")
        lines.append("TODO: If using bearer tokens (JWT, OAuth), document the authentication flow:")
        lines.append("")
        lines.append("```bash")
        lines.append('curl -H "Authorization: Bearer your_token" https://api.example.com/endpoint')
        lines.append("```")
        lines.append("")
        lines.append("### Authentication Endpoints")
        lines.append("")
        lines.append("TODO: Document authentication-related endpoints:")
        lines.append("- Login/token generation")
        lines.append("- Token refresh")
        lines.append("- Logout/token revocation")
        lines.append("")

        # Request/Response Format section
        lines.append("## Request and Response Format")
        lines.append("")
        lines.append("### Content Types")
        lines.append("")
        lines.append("TODO: Document supported content types:")
        lines.append("")
        lines.append("- **Request Content-Type**: `application/json`")
        lines.append("- **Response Content-Type**: `application/json`")
        lines.append("")
        lines.append("### Request Headers")
        lines.append("")
        lines.append("TODO: Document required and optional headers:")
        lines.append("")
        lines.append("| Header | Required | Description |")
        lines.append("|--------|----------|-------------|")
        lines.append("| `Content-Type` | Yes | Must be `application/json` for POST/PUT requests |")
        lines.append("| `Authorization` | Yes | Authentication token |")
        lines.append("| `X-Request-ID` | No | Unique request identifier for tracing |")
        lines.append("")
        lines.append("### Response Structure")
        lines.append("")
        lines.append("TODO: Document your standard response structure:")
        lines.append("")
        lines.append("```json")
        lines.append("{")
        lines.append('  "data": {},')
        lines.append('  "meta": {')
        lines.append('    "timestamp": "2024-01-01T00:00:00Z",')
        lines.append('    "request_id": "uuid"')
        lines.append("  }")
        lines.append("}")
        lines.append("```")
        lines.append("")

        # Error Handling section
        lines.append("## Error Handling")
        lines.append("")
        lines.append("TODO: Document your error handling approach and standard error responses.")
        lines.append("")
        lines.append("### HTTP Status Codes")
        lines.append("")
        lines.append("TODO: List the HTTP status codes your API uses:")
        lines.append("")
        lines.append("| Status Code | Meaning | Description |")
        lines.append("|-------------|---------|-------------|")
        lines.append("| 200 | OK | Request successful |")
        lines.append("| 201 | Created | Resource created successfully |")
        lines.append("| 400 | Bad Request | Invalid request data |")
        lines.append("| 401 | Unauthorized | Authentication required |")
        lines.append("| 403 | Forbidden | Insufficient permissions |")
        lines.append("| 404 | Not Found | Resource not found |")
        lines.append("| 422 | Unprocessable Entity | Validation errors |")
        lines.append("| 429 | Too Many Requests | Rate limit exceeded |")
        lines.append("| 500 | Internal Server Error | Server error |")
        lines.append("")
        lines.append("### Error Response Format")
        lines.append("")
        lines.append("TODO: Document your standard error response structure:")
        lines.append("")
        lines.append("```json")
        lines.append("{")
        lines.append('  "error": {')
        lines.append('    "code": "VALIDATION_ERROR",')
        lines.append('    "message": "The request data is invalid",')
        lines.append('    "details": [')
        lines.append("      {")
        lines.append('        "field": "email",')
        lines.append('        "message": "Invalid email format"')
        lines.append("      }")
        lines.append("    ]")
        lines.append("  },")
        lines.append('  "meta": {')
        lines.append('    "timestamp": "2024-01-01T00:00:00Z",')
        lines.append('    "request_id": "uuid"')
        lines.append("  }")
        lines.append("}")
        lines.append("```")
        lines.append("")

        # Rate Limiting section
        lines.append("## Rate Limiting")
        lines.append("")
        lines.append("TODO: Document your rate limiting policy:")
        lines.append("")
        lines.append("### Limits")
        lines.append("")
        lines.append("TODO: Specify rate limits for different types of requests:")
        lines.append("")
        lines.append("- **Authenticated requests**: 1000 requests per hour")
        lines.append("- **Unauthenticated requests**: 100 requests per hour")
        lines.append("- **Specific endpoints**: Custom limits as documented")
        lines.append("")
        lines.append("### Rate Limit Headers")
        lines.append("")
        lines.append("TODO: Document rate limit response headers:")
        lines.append("")
        lines.append("| Header | Description |")
        lines.append("|--------|-------------|")
        lines.append("| `X-RateLimit-Limit` | Total number of requests allowed |")
        lines.append("| `X-RateLimit-Remaining` | Number of requests remaining |")
        lines.append("| `X-RateLimit-Reset` | Time when the rate limit resets |")
        lines.append("")

        # Pagination section
        lines.append("## Pagination")
        lines.append("")
        lines.append("TODO: Document pagination for list endpoints:")
        lines.append("")
        lines.append("### Query Parameters")
        lines.append("")
        lines.append("TODO: Document pagination parameters:")
        lines.append("")
        lines.append("| Parameter | Type | Default | Description |")
        lines.append("|-----------|------|---------|-------------|")
        lines.append("| `page` | integer | 1 | Page number |")
        lines.append("| `per_page` | integer | 20 | Items per page (max 100) |")
        lines.append("| `sort` | string | - | Sort field |")
        lines.append("| `order` | string | asc | Sort order (asc/desc) |")
        lines.append("")
        lines.append("### Response Format")
        lines.append("")
        lines.append("TODO: Document paginated response structure:")
        lines.append("")
        lines.append("```json")
        lines.append("{")
        lines.append('  "data": [...],')
        lines.append('  "pagination": {')
        lines.append('    "current_page": 1,')
        lines.append('    "per_page": 20,')
        lines.append('    "total_pages": 5,')
        lines.append('    "total_items": 100,')
        lines.append('    "has_next": true,')
        lines.append('    "has_prev": false')
        lines.append("  }")
        lines.append("}")
        lines.append("```")
        lines.append("")

        # Versioning section
        lines.append("## API Versioning")
        lines.append("")
        lines.append("TODO: Document your API versioning strategy:")
        lines.append("")
        lines.append("### Version Format")
        lines.append("")
        lines.append("TODO: Specify how versions are indicated (URL path, headers, etc.):")
        lines.append("")
        lines.append("- **URL Path**: `/v1/users`, `/v2/users`")
        lines.append("- **Header**: `Accept: application/vnd.api+json;version=1`")
        lines.append("- **Query Parameter**: `?version=1`")
        lines.append("")
        lines.append("### Current Version")
        lines.append("")
        lines.append("TODO: Specify the current API version and deprecation policy:")
        lines.append("")
        lines.append("- **Current Version**: v1")
        lines.append("- **Supported Versions**: v1")
        lines.append("- **Deprecation Notice**: Version deprecation will be announced 6 months in advance")
        lines.append("")

        # SDKs and Libraries section
        lines.append("## SDKs and Client Libraries")
        lines.append("")
        lines.append("TODO: Document available SDKs and client libraries:")
        lines.append("")
        lines.append("### Official SDKs")
        lines.append("")
        lines.append("TODO: List official SDKs if available:")
        lines.append("")
        lines.append("- **Python**: `pip install your-api-sdk`")
        lines.append("- **JavaScript**: `npm install your-api-sdk`")
        lines.append("- **Go**: `go get github.com/yourorg/api-sdk`")
        lines.append("")
        lines.append("### Community Libraries")
        lines.append("")
        lines.append("TODO: List community-maintained libraries:")
        lines.append("")
        lines.append("- Link to community resources")
        lines.append("")

        # Testing section
        lines.append("## Testing")
        lines.append("")
        lines.append("### Sandbox Environment")
        lines.append("")
        lines.append("TODO: Document testing/sandbox environment if available:")
        lines.append("")
        lines.append("- **Sandbox URL**: `https://sandbox-api.example.com`")
        lines.append("- **Test Credentials**: How to obtain test API keys")
        lines.append("- **Test Data**: Available test data sets")
        lines.append("")
        lines.append("### Postman Collection")
        lines.append("")
        lines.append("TODO: Provide link to Postman collection if available:")
        lines.append("")
        lines.append(
            "[![Run in Postman](https://run.pstmn.io/button.svg)](https://app.getpostman.com/run-collection/your-collection-id)"
        )
        lines.append("")

        # Support section
        lines.append("## Support")
        lines.append("")
        lines.append("TODO: Document support channels and resources:")
        lines.append("")
        lines.append("### Documentation")
        lines.append("")
        lines.append("- **API Reference**: Link to detailed API reference")
        lines.append("- **Guides**: Link to integration guides")
        lines.append("- **Changelog**: Link to API changelog")
        lines.append("")
        lines.append("### Contact")
        lines.append("")
        lines.append("TODO: Provide contact information for API support:")
        lines.append("")
        lines.append("- **Email**: api-support@example.com")
        lines.append("- **Documentation Issues**: Link to documentation repository")
        lines.append("- **Status Page**: Link to API status page")
        lines.append("")

        # Changelog section
        lines.append("## Changelog")
        lines.append("")
        lines.append("TODO: Maintain a changelog of API changes:")
        lines.append("")
        lines.append("### Version 1.0.0 (2024-01-01)")
        lines.append("")
        lines.append("- Initial API release")
        lines.append("- Added core endpoints")
        lines.append("")
        lines.append("### Future Versions")
        lines.append("")
        lines.append("TODO: Document planned changes and new features")
        lines.append("")

        return "\n".join(lines)

    def _add_parameters_section(self, lines: list[str], parameters: list[ParameterInfo]) -> None:
        """Add parameter documentation sections to the markdown."""
        # Group parameters by type
        path_params = [p for p in parameters if p.parameter_type == "path"]
        query_params = [p for p in parameters if p.parameter_type == "query"]
        body_params = [p for p in parameters if p.parameter_type == "body"]

        # Path Parameters
        if path_params:
            lines.append("### Path Parameters")
            lines.append("")
            for param in path_params:
                type_str = self._format_type_hint(param.type_hint)
                lines.append(f"- `{param.name}` ({type_str}, required): TODO: Add description")
            lines.append("")

        # Query Parameters
        if query_params:
            lines.append("### Query Parameters")
            lines.append("")
            for param in query_params:
                type_str = self._format_type_hint(param.type_hint)
                required_str = "required" if param.is_required else "optional"
                default_info = f", default: {param.default_value}" if param.default_value else ""
                lines.append(f"- `{param.name}` ({type_str}, {required_str}{default_info}): TODO: Add description")
            lines.append("")

        # Request Body
        if body_params:
            lines.append("### Request Body")
            lines.append("")
            for param in body_params:
                type_str = self._format_type_hint(param.type_hint)
                required_str = "required" if param.is_required else "optional"
                lines.append(f"- `{param.name}` ({type_str}, {required_str}): TODO: Add description and schema details")
            lines.append("")
            lines.append("**Example:**")
            lines.append("```json")
            lines.append("TODO: Add request body example")
            lines.append("```")
            lines.append("")

    def _format_type_hint(self, type_hint: Optional[str]) -> str:
        """Format type hint for documentation."""
        if not type_hint:
            return "string"

        # Handle Optional types first (before generic replacements)
        if "Optional[" in type_hint:
            # Extract the inner type from Optional[Type]
            import re

            match = re.search(r"Optional\[([^\]]+)\]", type_hint)
            if match:
                inner_type = match.group(1)
                return self._format_type_hint(inner_type)

        # Simplify common type hints
        type_mappings = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
            "List": "array",
            "Dict": "object",
        }

        # Apply simple mappings
        for old_type, new_type in type_mappings.items():
            if old_type in type_hint:
                type_hint = type_hint.replace(old_type, new_type)

        # Remove module prefixes and clean up
        type_hint = type_hint.split(".")[-1]  # Remove module prefixes
        type_hint = type_hint.replace("[", "<").replace("]", ">")  # Replace brackets

        return type_hint

    def _generate_curl_example(self, endpoint: EndpointInfo) -> str:
        """Generate a realistic cURL example for the endpoint."""
        lines = []

        # Base curl command
        lines.append(f'curl -X {endpoint.method} "{{base_url}}{endpoint.path}" \\')

        # Add headers
        lines.append('  -H "Authorization: Bearer your_token"')

        # Add content-type for POST/PUT/PATCH
        if endpoint.method.upper() in ["POST", "PUT", "PATCH"]:
            lines.append('  -H "Content-Type: application/json" \\')

        # Add request body for POST/PUT/PATCH
        body_params = [p for p in (endpoint.parameters or []) if p.parameter_type == "body"]
        if body_params and endpoint.method.upper() in ["POST", "PUT", "PATCH"]:
            lines.append('  -d \'{"TODO": "Add request body"}\'')

        # Remove trailing backslash from last line
        if lines[-1].endswith(" \\"):
            lines[-1] = lines[-1][:-2]

        return "\n".join(lines)


class DocumentationInitializer:
    """Main class for initializing documentation scaffolding."""

    def __init__(self, source_directory: str, output_directory: str = "docs"):
        """Initialize the documentation initializer."""
        self.source_directory = source_directory
        self.output_directory = output_directory

    def initialize(self) -> dict[str, Any]:
        """Initialize documentation scaffolding for the project."""
        print("🚀 Starting FastAPI documentation initialization...")
        print(f"📂 Source directory: {self.source_directory}")
        print(f"📝 Output directory: {self.output_directory}")
        print()

        # Scan for endpoints
        scanner = FastAPIEndpointScanner(self.source_directory)
        endpoints = scanner.scan_directory()

        print(f"\n🎯 Found {len(endpoints)} endpoints total")

        # Generate scaffolding (always generates general_docs.md, plus endpoint files if endpoints exist)
        print(f"\n📚 Generating documentation scaffolding in {self.output_directory}...")
        generator = MarkdownScaffoldGenerator(self.output_directory)
        generated_files = generator.generate_scaffolding(endpoints)

        print(f"✅ Generated {len(generated_files)} documentation files")

        if not endpoints:
            print("ℹ️  No FastAPI endpoints found, but general_docs.md was created with API documentation structure.")
            print("💡 Tip: Check that your Python files contain @app.get(), @router.post(), etc. decorators")

        # Create summary
        summary = self._create_summary(endpoints, generated_files)

        return {
            "endpoints": endpoints,
            "files": list(generated_files.keys()),
            "summary": summary,
        }

    def _create_summary(self, endpoints: list[EndpointInfo], generated_files: dict[str, str]) -> str:
        """Create a summary of the initialization process."""
        lines = []

        lines.append("📊 **Documentation Initialization Complete**")
        lines.append(f"- **Endpoints discovered:** {len(endpoints)}")
        lines.append(f"- **Files generated:** {len(generated_files)}")
        lines.append("")

        # Method breakdown
        method_counts: dict[str, int] = {}
        for endpoint in endpoints:
            method_counts[endpoint.method] = method_counts.get(endpoint.method, 0) + 1

        lines.append("**Endpoints by method:**")
        for method, count in sorted(method_counts.items()):
            lines.append(f"- {method}: {count}")
        lines.append("")

        # Generated files
        lines.append("**Generated files:**")
        general_docs_files = [f for f in generated_files.keys() if "general_docs.md" in f]
        endpoint_files = [f for f in generated_files.keys() if "general_docs.md" not in f]

        # Show general_docs.md first
        for file_path in sorted(general_docs_files):
            lines.append(f"- {file_path} (general API documentation)")

        # Then show endpoint-specific files
        for file_path in sorted(endpoint_files):
            lines.append(f"- {file_path}")
        lines.append("")

        # Check for untagged endpoints
        untagged_endpoints = [ep for ep in endpoints if not ep.tags]
        if untagged_endpoints:
            lines.append("⚠️  **Endpoints without tags (will be grouped in api.md):**")
            for endpoint in sorted(untagged_endpoints, key=lambda e: (e.file_path, e.line_number)):
                lines.append(f"- {endpoint.method} {endpoint.path} → `{endpoint.file_path}:{endpoint.line_number}`")
            lines.append("")
            lines.append("💡 **Tip:** Add tags to these endpoints for better organization:")
            lines.append("   ```python")
            lines.append("   # For individual endpoints:")
            lines.append("   @app.get('/path', tags=['tag_name'])")
            lines.append("   ")
            lines.append("   # For router-level tagging:")
            lines.append("   router = APIRouter(prefix='/prefix', tags=['tag_name'])")
            lines.append("   ```")
            lines.append("")

        # Next steps
        lines.append("**Next steps:**")
        lines.append("1. Review the generated documentation files")
        lines.append("2. **Complete all TODO items** - The linter will fail until all TODOs are addressed")
        lines.append("3. Fill in general API information in `general_docs.md` (authentication, rate limiting, etc.)")
        lines.append("4. Add detailed endpoint descriptions and response examples")
        if untagged_endpoints:
            lines.append("5. Consider adding tags to untagged endpoints for better organization")
            lines.append("6. Run `fmd-lint` to check documentation completeness and TODO status")
        else:
            lines.append("5. Run `fmd-lint` to check documentation completeness and TODO status")

        lines.append("")
        lines.append("⚠️  **Important**: The linter will fail if any TODO items remain. This ensures")
        lines.append("    complete documentation before deployment.")

        return "\n".join(lines)
