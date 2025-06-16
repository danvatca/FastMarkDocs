"""
FastMarkDocs Documentation Linter

Core linting functionality for analyzing FastAPI documentation completeness and accuracy.
"""

from pathlib import Path
from typing import Any

from .documentation_loader import MarkdownDocumentationLoader
from .openapi_enhancer import OpenAPIEnhancer
from .types import EndpointDocumentation


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

        # Load documentation
        self.loader = MarkdownDocumentationLoader(docs_directory=str(docs_directory), recursive=recursive)
        self.documentation = self.loader.load_documentation()

        # Create enhancer for testing
        self.enhancer = OpenAPIEnhancer(include_code_samples=True, include_response_examples=True, base_url=base_url)

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

        # Generate statistics
        results["statistics"] = self._generate_statistics(openapi_endpoints, markdown_endpoints, results)

        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)

        # Create summary
        results["summary"] = self._create_summary(results)

        return results

    def _extract_openapi_endpoints(self) -> set[tuple[str, str]]:
        """Extract all endpoints from OpenAPI schema."""
        endpoints = set()

        for path, methods in self.openapi_schema.get("paths", {}).items():
            for method in methods.keys():
                if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]:
                    endpoints.add((method.upper(), path))

        return endpoints

    def _extract_markdown_endpoints(self) -> set[tuple[str, str]]:
        """Extract all endpoints from markdown documentation."""
        endpoints = set()

        for endpoint in self.documentation.endpoints:
            endpoints.add((endpoint.method.value, endpoint.path))

        return endpoints

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
            issues = []

            # Check for missing description
            if not endpoint.description or len(endpoint.description.strip()) < 10:
                issues.append("Missing or very short description")

            # Check for missing summary
            if not endpoint.summary or len(endpoint.summary.strip()) < 5:
                issues.append("Missing or very short summary")

            # Check for missing code samples
            if not endpoint.code_samples:
                issues.append("No code samples provided")

            # Check for missing response examples
            if not endpoint.response_examples:
                issues.append("No response examples provided")

            # Check for missing parameters documentation
            if endpoint.parameters is None or len(endpoint.parameters) == 0:
                # Check if the path has parameters
                if "{" in endpoint.path and "}" in endpoint.path:
                    issues.append("Path has parameters but no parameter documentation")

            if issues:
                incomplete.append(
                    {
                        "method": endpoint.method.value,
                        "path": endpoint.path,
                        "severity": "warning",
                        "issues": issues,
                        "completeness_score": self._calculate_completeness_score(endpoint),
                        "suggestions": self._generate_completion_suggestions(endpoint, issues),
                    }
                )

        return incomplete

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
                    orphaned.append(
                        {
                            "method": method,
                            "path": path,
                            "severity": "warning",
                            "message": f"Documentation exists for non-existent endpoint {method} {path}",
                            "suggestion": "Remove this documentation or implement the endpoint in your FastAPI application",
                        }
                    )

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

    def _find_similar_paths(self, target_path: str, endpoints: set[tuple[str, str]]) -> list[str]:
        """Find similar paths in a set of endpoints."""
        similar = []
        target_parts = target_path.split("/")

        for _, path in endpoints:
            path_parts = path.split("/")

            # Check if paths have similar structure
            if len(path_parts) == len(target_parts):
                similarity = sum(
                    1 for a, b in zip(target_parts, path_parts) if a == b or (a.startswith("{") and b.startswith("{"))
                )
                if similarity >= len(target_parts) * 0.7:  # 70% similarity
                    similar.append(path)

        return similar[:3]  # Return top 3 similar paths

    def _find_similar_openapi_paths(self, target_path: str, openapi_endpoints: set[tuple[str, str]]) -> list[str]:
        """Find similar paths in OpenAPI endpoints."""
        similar = []
        target_parts = target_path.split("/")

        for method, path in openapi_endpoints:
            path_parts = path.split("/")

            # Check if paths have similar structure
            if len(path_parts) == len(target_parts):
                similarity = sum(
                    1 for a, b in zip(target_parts, path_parts) if a == b or (a.startswith("{") and b.startswith("{"))
                )
                if similarity >= len(target_parts) * 0.7:  # 70% similarity
                    similar.append(f"{method} {path}")

        return similar[:3]  # Return top 3 similar paths

    def _get_openapi_operation(self, method: str, path: str) -> dict[str, Any]:
        """Get OpenAPI operation details for an endpoint."""
        paths = self.openapi_schema.get("paths", {})
        if not isinstance(paths, dict):
            return {}

        path_item = paths.get(path, {})
        if not isinstance(path_item, dict):
            return {}

        operation = path_item.get(method.lower(), {})
        if not isinstance(operation, dict):
            return {}

        return operation

    def _calculate_completeness_score(self, endpoint: EndpointDocumentation) -> float:
        """Calculate a completeness score (0-100) for an endpoint."""
        score = 0

        # Description (30 points)
        if endpoint.description and len(endpoint.description.strip()) >= 50:
            score += 30
        elif endpoint.description and len(endpoint.description.strip()) >= 10:
            score += 15

        # Summary (20 points)
        if endpoint.summary and len(endpoint.summary.strip()) >= 10:
            score += 20
        elif endpoint.summary and len(endpoint.summary.strip()) >= 5:
            score += 10

        # Code samples (25 points)
        if endpoint.code_samples and len(endpoint.code_samples) >= 3:
            score += 25
        elif endpoint.code_samples and len(endpoint.code_samples) >= 1:
            score += 15

        # Response examples (20 points)
        if endpoint.response_examples and len(endpoint.response_examples) >= 2:
            score += 20
        elif endpoint.response_examples and len(endpoint.response_examples) >= 1:
            score += 10

        # Parameters documentation (5 points)
        if "{" in endpoint.path and "}" in endpoint.path:
            if endpoint.parameters and len(endpoint.parameters) > 0:
                score += 5
        else:
            score += 5  # No parameters needed

        return round(score, 1)

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
                suggestions.append("Add code examples in popular languages (cURL, Python, JavaScript)")
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
