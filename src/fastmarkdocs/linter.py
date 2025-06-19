"""
FastMarkDocs Documentation Linter

Core linting functionality for analyzing FastAPI documentation completeness and accuracy.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from .documentation_loader import MarkdownDocumentationLoader
from .endpoint_analyzer import UnifiedEndpointAnalyzer
from .openapi_enhancer import OpenAPIEnhancer
from .types import EndpointDocumentation

if TYPE_CHECKING:
    from .linter_cli import LinterConfig


class DocumentationLinter:
    """
    Lints FastAPI documentation for completeness and accuracy.

    Analyzes OpenAPI schemas and markdown documentation to identify:
    - Missing documentation for API endpoints
    - Incomplete documentation (missing descriptions, examples, etc.)
    - Common mistakes like path parameter mismatches
    - Orphaned documentation (documented endpoints that don't exist in code)
    """

    def __init__(
        self,
        openapi_schema: dict[str, Any],
        docs_directory: str,
        base_url: str = "https://api.example.com",
        recursive: bool = True,
    ):
        """
        Initialize the documentation linter.

        Args:
            openapi_schema: The OpenAPI schema from FastAPI
            docs_directory: Directory containing markdown documentation
            base_url: Base URL for the API
            recursive: Whether to search documentation recursively
        """
        self.openapi_schema = openapi_schema
        self.docs_directory = Path(docs_directory)
        self.base_url = base_url
        self.recursive = recursive
        self.config: Optional[LinterConfig] = None  # Will be set by CLI if configuration is provided

        # Load documentation
        self.loader = MarkdownDocumentationLoader(docs_directory=str(docs_directory), recursive=recursive)
        self.documentation = self.loader.load_documentation()

        # Create unified analyzer
        self.analyzer = UnifiedEndpointAnalyzer(openapi_schema, base_url=base_url)

        # Create enhancer for testing
        self.enhancer = OpenAPIEnhancer(include_code_samples=True, include_response_examples=True, base_url=base_url)

        # Build endpoint to file mapping for better reporting
        self._endpoint_file_mapping = self._build_endpoint_file_mapping()

    def _build_endpoint_file_mapping(self) -> dict[tuple[str, str], str]:
        """Build a mapping from (method, path) to source file for better error reporting."""
        mapping = {}

        # Find all markdown files in the documentation directory
        from .utils import find_markdown_files

        markdown_files = find_markdown_files(str(self.docs_directory), recursive=self.recursive)

        for file_path in markdown_files:
            try:
                # Parse each file to get its endpoints
                endpoints = self.loader._parse_markdown_file(Path(file_path))
                for endpoint in endpoints:
                    key = (endpoint.method.value, endpoint.path)
                    # Store relative path for cleaner display
                    relative_path = Path(file_path).relative_to(self.docs_directory)
                    mapping[key] = str(relative_path)
            except (FileNotFoundError, PermissionError, UnicodeDecodeError):
                # If we can't read a file due to file system issues, continue with others
                continue
            except (ValueError, KeyError, AttributeError):
                # If we can't parse a file due to content issues, continue with others
                continue

        return mapping

    def lint(self) -> dict[str, Any]:
        """
        Perform comprehensive documentation linting.

        Returns:
            Dictionary containing linting results with issues and statistics
        """
        results: dict[str, Any] = {
            "summary": {},
            "missing_documentation": [],
            "incomplete_documentation": [],
            "common_mistakes": [],
            "orphaned_documentation": [],
            "enhancement_failures": [],
            "todo_entries": [],
            "statistics": {},
            "recommendations": [],
        }

        # Extract endpoint information
        openapi_endpoints = self._extract_openapi_endpoints()
        markdown_endpoints = self._extract_markdown_endpoints()

        # Analyze missing documentation
        results["missing_documentation"] = self._find_missing_documentation(openapi_endpoints, markdown_endpoints)

        # Analyze incomplete documentation
        results["incomplete_documentation"] = self._find_incomplete_documentation()

        # Find common mistakes
        results["common_mistakes"] = self._find_common_mistakes(openapi_endpoints, markdown_endpoints)

        # Find orphaned documentation
        results["orphaned_documentation"] = self._find_orphaned_documentation(openapi_endpoints, markdown_endpoints)

        # Test enhancement process
        results["enhancement_failures"] = self._test_enhancement_process(openapi_endpoints, markdown_endpoints)

        # Find TODO entries
        results["todo_entries"] = self._find_todo_entries()

        # Generate statistics
        results["statistics"] = self._generate_statistics(openapi_endpoints, markdown_endpoints, results)

        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)

        # Create summary
        results["summary"] = self._create_summary(results)

        # Add metadata (convert non-serializable objects to dicts)
        metadata = {
            "docs_directory": self.docs_directory,
            "base_url": self.base_url,
            "recursive": self.recursive,
        }

        # Add documentation metadata, converting non-serializable objects
        for key, value in self.documentation.metadata.items():
            metadata[key] = self._make_json_serializable(value)

        results["metadata"] = metadata

        return results

    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format."""
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif hasattr(obj, "__dict__"):
            # Convert dataclass or object to dict
            return {key: self._make_json_serializable(value) for key, value in obj.__dict__.items()}
        elif hasattr(obj, "_asdict"):
            # Handle namedtuples
            return self._make_json_serializable(obj._asdict())
        else:
            # For other objects, convert to string representation
            return str(obj)

    def _extract_openapi_endpoints(self) -> set[tuple[str, str]]:
        """Extract all endpoints from OpenAPI schema, excluding configured exclusions."""
        # Get exclusions from config
        exclusions = set()
        if self.config:
            # Build exclusions set from config
            for path, methods in self.openapi_schema.get("paths", {}).items():
                for method in methods.keys():
                    if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]:
                        method_upper = method.upper()
                        if self.config.should_exclude_endpoint(method_upper, path):
                            exclusions.add((method_upper, path))

        return self.analyzer.extract_openapi_endpoints(exclusions)

    def _extract_markdown_endpoints(self) -> set[tuple[str, str]]:
        """Extract all endpoints from markdown documentation, excluding configured exclusions."""
        # Get all endpoints from documentation
        all_endpoints = self.analyzer.extract_documentation_endpoints(self.documentation.endpoints)

        # Apply exclusions if config is available
        if self.config:
            excluded_endpoints = set()
            for method, path in all_endpoints:
                if self.config.should_exclude_endpoint(method, path):
                    excluded_endpoints.add((method, path))

            # Return endpoints minus exclusions
            return all_endpoints - excluded_endpoints

        return all_endpoints

    def _find_missing_documentation(
        self, openapi_endpoints: set[tuple[str, str]], markdown_endpoints: set[tuple[str, str]]
    ) -> list[dict[str, Any]]:
        """Find API endpoints that have no documentation."""
        missing = []

        for method, path in openapi_endpoints:
            if (method, path) not in markdown_endpoints:
                # Check for similar paths (potential mismatches)
                similar_paths = self._find_similar_paths(path, markdown_endpoints)

                missing.append(
                    {
                        "method": method,
                        "path": path,
                        "severity": "error",
                        "message": f"No documentation found for {method} {path}",
                        "similar_documented_paths": similar_paths,
                        "openapi_operation": self._get_openapi_operation(method, path),
                    }
                )

        return missing

    def _find_incomplete_documentation(self) -> list[dict[str, Any]]:
        """Find documented endpoints with incomplete information."""
        incomplete = []

        for endpoint in self.documentation.endpoints:
            # Get OpenAPI operation for this endpoint
            openapi_operation = self.analyzer.get_openapi_operation(endpoint.method.value, endpoint.path)

            # Auto-generate code samples if missing
            if not endpoint.code_samples:
                self._auto_generate_code_samples(endpoint)

            # Analyze endpoint using unified analyzer
            analysis = self.analyzer.analyze_endpoint(endpoint, openapi_operation)

            if analysis.quality_issues:
                incomplete.append(
                    {
                        "method": endpoint.method.value,
                        "path": endpoint.path,
                        "severity": "warning",
                        "issues": analysis.quality_issues,
                        "completeness_score": analysis.completeness_score,
                        "suggestions": self._generate_completion_suggestions(endpoint, analysis.quality_issues),
                    }
                )

        return incomplete

    def _auto_generate_code_samples(self, endpoint: EndpointDocumentation) -> None:
        """Auto-generate code samples for an endpoint if missing."""
        from .code_samples import generate_code_samples_for_endpoint
        from .exceptions import CodeSampleGenerationError
        from .types import CodeLanguage

        try:
            # Get the OpenAPI operation for this endpoint
            operation = self._get_openapi_operation(endpoint.method.value, endpoint.path)
            if not operation:
                return

            # Generate code samples for popular languages
            languages = [CodeLanguage.CURL, CodeLanguage.PYTHON]
            generated_samples = generate_code_samples_for_endpoint(
                method=endpoint.method.value,
                path=endpoint.path,
                operation=operation,
                base_url=self.base_url,
                languages=languages,
            )

            # Add generated samples to the endpoint
            endpoint.code_samples.extend(generated_samples)

        except CodeSampleGenerationError:
            # If code sample generation fails, continue without breaking linting
            # The generate_code_samples_for_endpoint function already handles errors gracefully
            pass
        except (AttributeError, KeyError, ValueError):
            # Handle common errors that might occur during generation
            # These are typically due to malformed endpoint data or OpenAPI schema issues
            # Continue linting without code samples rather than failing entirely
            pass

    def _find_common_mistakes(
        self, openapi_endpoints: set[tuple[str, str]], markdown_endpoints: set[tuple[str, str]]
    ) -> list[dict[str, Any]]:
        """Find common documentation mistakes."""
        mistakes = []

        # Find path parameter mismatches
        for md_method, md_path in markdown_endpoints:
            if (md_method, md_path) not in openapi_endpoints:
                # Look for similar paths in OpenAPI
                similar_openapi = self._find_similar_openapi_paths(md_path, openapi_endpoints)

                if similar_openapi:
                    mistakes.append(
                        {
                            "type": "path_parameter_mismatch",
                            "severity": "error",
                            "documented_endpoint": f"{md_method} {md_path}",
                            "message": f"Documented endpoint {md_method} {md_path} not found in OpenAPI",
                            "similar_openapi_endpoints": similar_openapi,
                            "suggestion": "Check if path parameters match. Consider updating documentation to match OpenAPI schema.",
                            "likely_correct_path": similar_openapi[0] if similar_openapi else None,
                        }
                    )

        # Find method mismatches
        documented_paths = {path for _, path in markdown_endpoints}
        openapi_paths = {path for _, path in openapi_endpoints}

        for path in documented_paths.intersection(openapi_paths):
            md_methods = {method for method, p in markdown_endpoints if p == path}
            oa_methods = {method for method, p in openapi_endpoints if p == path}

            missing_methods = oa_methods - md_methods
            extra_methods = md_methods - oa_methods

            if missing_methods:
                mistakes.append(
                    {
                        "type": "missing_method_documentation",
                        "severity": "warning",
                        "path": path,
                        "message": f"Path {path} has undocumented methods: {', '.join(missing_methods)}",
                        "missing_methods": list(missing_methods),
                        "suggestion": "Add documentation for these HTTP methods",
                    }
                )

            if extra_methods:
                mistakes.append(
                    {
                        "type": "extra_method_documentation",
                        "severity": "warning",
                        "path": path,
                        "message": f"Path {path} has documentation for non-existent methods: {', '.join(extra_methods)}",
                        "extra_methods": list(extra_methods),
                        "suggestion": "Remove documentation for these methods or check if they should exist in the API",
                    }
                )

        return mistakes

    def _find_orphaned_documentation(
        self, openapi_endpoints: set[tuple[str, str]], markdown_endpoints: set[tuple[str, str]]
    ) -> list[dict[str, Any]]:
        """Find documentation for endpoints that don't exist in the API."""
        orphaned = []

        for method, path in markdown_endpoints:
            if (method, path) not in openapi_endpoints:
                # Check if this is already identified as a common mistake
                similar_openapi = self._find_similar_openapi_paths(path, openapi_endpoints)

                if not similar_openapi:  # Truly orphaned, not just a mismatch
                    # Find the corresponding documentation to get more details
                    endpoint_doc = next(
                        (ep for ep in self.documentation.endpoints if ep.method.value == method and ep.path == path),
                        None,
                    )

                    orphan_info: dict[str, Any] = {
                        "method": method,
                        "path": path,
                        "severity": "warning",
                        "message": f"Documentation exists for non-existent endpoint {method} {path}",
                        "suggestion": "Remove this documentation or implement the endpoint in your FastAPI application",
                    }

                    # Add documentation details if available
                    if endpoint_doc:
                        orphan_info.update(
                            {
                                "summary": endpoint_doc.summary or "No summary provided",
                                "description_length": len(endpoint_doc.description or ""),
                                "has_code_samples": len(endpoint_doc.code_samples) > 0,
                                "has_response_examples": len(endpoint_doc.response_examples) > 0,
                                "has_parameters": len(endpoint_doc.parameters) > 0,
                                "documentation_file": self._endpoint_file_mapping.get((method, path), "Unknown file"),
                            }
                        )
                    else:
                        orphan_info.update(
                            {
                                "summary": "Documentation found but details unavailable",
                                "description_length": 0,
                                "has_code_samples": False,
                                "has_response_examples": False,
                                "has_parameters": False,
                                "documentation_file": self._endpoint_file_mapping.get((method, path), "Unknown file"),
                            }
                        )

                    orphaned.append(orphan_info)

        return orphaned

    def _test_enhancement_process(
        self, openapi_endpoints: set[tuple[str, str]], markdown_endpoints: set[tuple[str, str]]
    ) -> list[dict[str, Any]]:
        """Test the enhancement process to find endpoints that fail to enhance."""
        failures = []

        try:
            # Run enhancement
            enhanced_schema = self.enhancer.enhance_openapi_schema(self.openapi_schema, self.documentation)

            # Check which endpoints were enhanced
            enhanced_endpoints = set()
            for path, methods in enhanced_schema.get("paths", {}).items():
                for method, operation in methods.items():
                    if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]:
                        original_op = self.openapi_schema.get("paths", {}).get(path, {}).get(method, {})

                        # Check if enhancement occurred
                        has_code_samples = "x-codeSamples" in operation or "x-code-samples" in operation
                        has_enhanced_desc = len(operation.get("description", "")) > len(
                            original_op.get("description", "")
                        )

                        if has_code_samples or has_enhanced_desc:
                            enhanced_endpoints.add((method.upper(), path))

            # Find documented endpoints that failed to enhance
            for method, path in markdown_endpoints:
                if (method, path) in openapi_endpoints and (method, path) not in enhanced_endpoints:
                    # Find the corresponding documentation
                    endpoint_doc = next(
                        (ep for ep in self.documentation.endpoints if ep.method.value == method and ep.path == path),
                        None,
                    )

                    if endpoint_doc:
                        failures.append(
                            {
                                "method": method,
                                "path": path,
                                "severity": "error",
                                "message": f"Enhancement failed for documented endpoint {method} {path}",
                                "possible_causes": [
                                    "Path parameter name mismatch",
                                    "HTTP method case sensitivity issue",
                                    "Documentation parsing error",
                                    "Enhancement logic bug",
                                ],
                                "documentation_summary": endpoint_doc.summary,
                                "has_description": bool(endpoint_doc.description),
                                "has_code_samples": bool(endpoint_doc.code_samples),
                                "has_response_examples": bool(endpoint_doc.response_examples),
                            }
                        )

        except Exception as e:
            failures.append(
                {
                    "type": "enhancement_process_error",
                    "severity": "critical",
                    "message": f"Enhancement process failed with error: {str(e)}",
                    "suggestion": "Check your OpenAPI schema and documentation format",
                }
            )

        return failures

    def _find_todo_entries(self) -> list[dict[str, Any]]:
        """
        Find all TODO entries in documentation files.

        Returns:
            List of TODO entries with file, line number, and content
        """
        import re

        from .utils import find_markdown_files

        todo_entries = []

        # Find all markdown files in the documentation directory
        markdown_files = find_markdown_files(str(self.docs_directory), recursive=self.recursive)

        # TODO pattern - matches "TODO" (case insensitive) followed by optional colon and text
        todo_pattern = re.compile(r"\bTODO\b\s*:?\s*(.*)", re.IGNORECASE)

        for file_path in markdown_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    lines = f.readlines()

                relative_path = Path(file_path).relative_to(self.docs_directory)

                for line_number, line in enumerate(lines, 1):
                    # Only process lines that actually contain TODO
                    if re.search(r"\bTODO\b", line, re.IGNORECASE):
                        match = todo_pattern.search(line)
                        if match:
                            todo_text = match.group(1).strip() if match.group(1) else "No description"
                            # Clean up the TODO text - only replace if truly empty
                            if not todo_text or todo_text == "":
                                todo_text = "No description provided"

                            todo_entries.append(
                                {
                                    "file": str(relative_path),
                                    "line": line_number,
                                    "content": line.strip(),
                                    "todo_text": todo_text,
                                    "context": self._extract_todo_context(lines, line_number - 1),
                                }
                            )

            except (FileNotFoundError, PermissionError, UnicodeDecodeError):
                # Skip files that can't be read
                continue

        return todo_entries

    def _extract_todo_context(self, lines: list[str], todo_line_index: int) -> str:
        """
        Extract context around a TODO entry to help identify what section it's in.

        Args:
            lines: All lines in the file
            todo_line_index: Zero-based index of the TODO line

        Returns:
            Context string (e.g., "in endpoint GET /users", "in Parameters section")
        """
        # Look backwards for headings and build context
        section_context = None
        endpoint_context = None

        for i in range(todo_line_index - 1, max(0, todo_line_index - 20), -1):
            line = lines[i].strip()

            # Check for endpoint headers (## GET /path)
            if line.startswith("##") and any(method in line for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]):
                # Extract method and path
                parts = line.split(" ", 2)
                if len(parts) >= 3:
                    method = parts[1]
                    path = parts[2]
                    endpoint_context = f"in endpoint {method} {path}"
                    break  # Found endpoint, stop looking

            # Check for section headers (capture the most recent one)
            elif (line.startswith("###") or line.startswith("####")) and section_context is None:
                if line.startswith("####"):
                    section = line.replace("####", "").strip()
                else:
                    section = line.replace("###", "").strip()
                section_context = f"in {section} section"

        # Return the most specific context available
        if endpoint_context:
            return endpoint_context
        elif section_context:
            return section_context
        else:
            return "in documentation"

    def _find_similar_paths(self, target_path: str, endpoints: set[tuple[str, str]]) -> list[str]:
        """Find similar paths in a set of endpoints."""
        candidate_paths = [path for _, path in endpoints]
        similar = self.analyzer.find_similar_paths(target_path, candidate_paths)
        return similar[:3]  # Return top 3 similar paths

    def _find_similar_openapi_paths(self, target_path: str, openapi_endpoints: set[tuple[str, str]]) -> list[str]:
        """Find similar paths in OpenAPI endpoints."""
        candidate_paths = [path for _, path in openapi_endpoints]
        similar_paths = self.analyzer.find_similar_paths(target_path, candidate_paths)

        # Format with method names for better reporting
        similar = []
        for similar_path in similar_paths[:3]:
            # Find the method for this path
            for method, path in openapi_endpoints:
                if path == similar_path:
                    similar.append(f"{method} {path}")
                    break

        return similar

    def _get_openapi_operation(self, method: str, path: str) -> dict[str, Any]:
        """Get OpenAPI operation details for an endpoint."""
        return self.analyzer.get_openapi_operation(method, path)

    def _calculate_completeness_score(self, endpoint: EndpointDocumentation) -> float:
        """Calculate a completeness score (0-100) for an endpoint."""
        # Use the unified analyzer for consistency
        analysis = self.analyzer.analyze_endpoint(endpoint)
        return analysis.completeness_score

    def _generate_completion_suggestions(self, endpoint: EndpointDocumentation, issues: list[str]) -> list[str]:
        """Generate suggestions for completing documentation."""
        suggestions = []

        for issue in issues:
            if "description" in issue.lower():
                suggestions.append(
                    "Add a detailed description explaining what this endpoint does, its use cases, and any important behavior"
                )
            elif "summary" in issue.lower():
                suggestions.append("Add a concise summary that clearly describes the endpoint's purpose")
            elif "code samples" in issue.lower():
                # Code samples are auto-generated, so we don't suggest adding them manually
                pass
            elif "response examples" in issue.lower():
                suggestions.append("Add example responses showing successful and error cases")
            elif "parameter" in issue.lower():
                suggestions.append("Document all path and query parameters with descriptions and types")

        return suggestions

    def _generate_statistics(
        self, openapi_endpoints: set[tuple[str, str]], markdown_endpoints: set[tuple[str, str]], results: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate comprehensive statistics."""
        total_openapi = len(openapi_endpoints)
        total_documented = len(markdown_endpoints)
        total_missing = len(results["missing_documentation"])
        total_incomplete = len(results["incomplete_documentation"])
        total_mistakes = len(results["common_mistakes"])
        total_orphaned = len(results["orphaned_documentation"])
        total_enhancement_failures = len(results["enhancement_failures"])
        total_todos = len(results.get("todo_entries", []))

        # Calculate documentation coverage
        documented_existing = len(openapi_endpoints.intersection(markdown_endpoints))
        coverage_percentage = (documented_existing / total_openapi * 100) if total_openapi > 0 else 0

        # Calculate average completeness score
        completeness_scores = [item.get("completeness_score", 0) for item in results["incomplete_documentation"]]
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 100

        return {
            "total_openapi_endpoints": total_openapi,
            "total_documented_endpoints": total_documented,
            "documented_existing_endpoints": documented_existing,
            "documentation_coverage_percentage": round(coverage_percentage, 1),
            "average_completeness_score": round(avg_completeness, 1),
            "issues": {
                "missing_documentation": total_missing,
                "incomplete_documentation": total_incomplete,
                "common_mistakes": total_mistakes,
                "orphaned_documentation": total_orphaned,
                "enhancement_failures": total_enhancement_failures,
                "todo_entries": total_todos,
                "total_issues": total_missing
                + total_incomplete
                + total_mistakes
                + total_orphaned
                + total_enhancement_failures,
            },
        }

    def _generate_recommendations(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate actionable recommendations based on linting results."""
        recommendations = []

        stats = results["statistics"]

        # Coverage recommendations
        if stats["documentation_coverage_percentage"] < 80:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "coverage",
                    "title": "Improve Documentation Coverage",
                    "description": f"Only {stats['documentation_coverage_percentage']}% of API endpoints are documented",
                    "action": f"Add documentation for {stats['issues']['missing_documentation']} missing endpoints",
                    "impact": "Users will have better understanding of your API",
                }
            )

        # Completeness recommendations
        if stats["average_completeness_score"] < 70:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "completeness",
                    "title": "Improve Documentation Quality",
                    "description": f"Average documentation completeness is {stats['average_completeness_score']}%",
                    "action": "Add missing descriptions, code samples, and response examples",
                    "impact": "Developers will have better examples and understanding",
                }
            )

        # Mistake recommendations
        if stats["issues"]["common_mistakes"] > 0:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "accuracy",
                    "title": "Fix Documentation Mistakes",
                    "description": f"Found {stats['issues']['common_mistakes']} common mistakes",
                    "action": "Review and fix path parameter mismatches and method inconsistencies",
                    "impact": "Documentation will accurately reflect your API",
                }
            )

        # Enhancement failure recommendations
        if stats["issues"]["enhancement_failures"] > 0:
            recommendations.append(
                {
                    "priority": "critical",
                    "category": "technical",
                    "title": "Fix Enhancement Failures",
                    "description": f"{stats['issues']['enhancement_failures']} documented endpoints failed to enhance",
                    "action": "Check for path parameter naming mismatches and documentation format issues",
                    "impact": "All documented endpoints will be properly enhanced in OpenAPI",
                }
            )

        # TODO entries recommendations
        if stats["issues"].get("todo_entries", 0) > 0:
            priority = "medium" if stats["issues"].get("todo_entries", 0) < 10 else "high"
            recommendations.append(
                {
                    "priority": priority,
                    "category": "completeness",
                    "title": "Address TODO Entries",
                    "description": f"Found {stats['issues'].get('todo_entries', 0)} TODO entries in documentation",
                    "action": "Review and complete all TODO items with proper descriptions, examples, and documentation",
                    "impact": "Documentation will be complete and ready for production use",
                }
            )

        return recommendations

    def _create_summary(self, results: dict[str, Any]) -> dict[str, Any]:
        """Create a summary of linting results."""
        stats = results["statistics"]
        total_issues = stats["issues"]["total_issues"]

        if total_issues == 0:
            status = "excellent"
            message = "🎉 Excellent! Your documentation is complete and accurate."
        elif total_issues <= 5:
            status = "good"
            message = f"✅ Good documentation with {total_issues} minor issues to address."
        elif total_issues <= 15:
            status = "needs_improvement"
            message = f"⚠️ Documentation needs improvement. Found {total_issues} issues."
        else:
            status = "poor"
            message = f"❌ Documentation needs significant work. Found {total_issues} issues."

        return {
            "status": status,
            "message": message,
            "coverage": f"{stats['documentation_coverage_percentage']}%",
            "completeness": f"{stats['average_completeness_score']}%",
            "total_issues": total_issues,
            "critical_issues": len(
                [
                    item
                    for item in results["enhancement_failures"] + results["common_mistakes"]
                    if item.get("severity") == "critical" or item.get("severity") == "error"
                ]
            ),
        }
