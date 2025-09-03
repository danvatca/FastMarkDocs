"""
FastMarkDocs Unified Endpoint Analyzer

This module provides unified analysis capabilities for OpenAPI endpoints and documentation,
eliminating duplication between the linter and enhancer components.
"""

from dataclasses import dataclass
from typing import Any, Optional

from .code_samples import CodeSampleGenerator, generate_code_samples_for_endpoint
from .exceptions import CodeSampleGenerationError
from .types import CodeLanguage, CodeSample, EndpointDocumentation


@dataclass
class EndpointMatch:
    """Represents a match between OpenAPI and documentation endpoints."""

    openapi_method: str
    openapi_path: str
    doc_method: str
    doc_path: str
    endpoint_doc: Optional[EndpointDocumentation]
    openapi_operation: dict[str, Any]
    match_confidence: float  # 0.0 to 1.0
    match_type: str  # "exact", "parameter_mismatch", "similar", "no_match"


@dataclass
class EndpointAnalysis:
    """Complete analysis of an endpoint's documentation state."""

    endpoint_doc: EndpointDocumentation
    openapi_operation: Optional[dict[str, Any]]
    completeness_score: float
    missing_elements: list[str]
    quality_issues: list[str]
    enhancement_opportunities: list[str]
    can_be_enhanced: bool


class UnifiedEndpointAnalyzer:
    """
    Unified analyzer for OpenAPI endpoints and documentation.

    This class consolidates the common logic used by both the linter and enhancer,
    providing a single source of truth for endpoint analysis, matching, and assessment.
    """

    def __init__(
        self,
        openapi_schema: dict[str, Any],
        base_url: str = "https://api.example.com",
    ):
        """
        Initialize the unified endpoint analyzer.

        Args:
            openapi_schema: The OpenAPI schema to analyze
            base_url: Base URL for code sample generation
        """
        self.openapi_schema = openapi_schema
        self.base_url = base_url
        self.code_generator = CodeSampleGenerator(base_url=base_url)

    def extract_openapi_endpoints(self, exclusions: Optional[set[tuple[str, str]]] = None) -> set[tuple[str, str]]:
        """
        Extract all endpoints from OpenAPI schema.

        Args:
            exclusions: Set of (method, path) tuples to exclude

        Returns:
            Set of (method, path) tuples from OpenAPI schema
        """
        endpoints = set()
        exclusions = exclusions or set()

        for path, methods in self.openapi_schema.get("paths", {}).items():
            for method in methods.keys():
                if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]:
                    method_upper = method.upper()

                    # Skip excluded endpoints
                    if (method_upper, path) in exclusions:
                        continue

                    endpoints.add((method_upper, path))

        return endpoints

    def extract_documentation_endpoints(self, endpoints: list[EndpointDocumentation]) -> set[tuple[str, str]]:
        """
        Extract all endpoints from documentation.

        Args:
            endpoints: List of endpoint documentation

        Returns:
            Set of (method, path) tuples from documentation
        """
        return {(endpoint.method.value, endpoint.path) for endpoint in endpoints}

    def match_endpoints(
        self, openapi_endpoints: set[tuple[str, str]], doc_endpoints: list[EndpointDocumentation]
    ) -> list[EndpointMatch]:
        """
        Match OpenAPI endpoints with documentation endpoints.

        Args:
            openapi_endpoints: Set of OpenAPI endpoints
            doc_endpoints: List of documentation endpoints

        Returns:
            List of endpoint matches with confidence scores
        """
        matches = []
        doc_endpoint_map = {(ep.method.value, ep.path): ep for ep in doc_endpoints}

        # Create matches for all combinations
        for oa_method, oa_path in openapi_endpoints:
            best_match = None
            best_confidence = 0.0

            for doc_method, doc_path in doc_endpoint_map.keys():
                confidence = self._calculate_match_confidence(oa_method, oa_path, doc_method, doc_path)

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = (doc_method, doc_path)

            # Determine match type
            if best_confidence >= 1.0:
                match_type = "exact"
            elif best_confidence >= 0.8:
                match_type = "parameter_mismatch"
            elif best_confidence >= 0.5:
                match_type = "similar"
            else:
                match_type = "no_match"

            # Get OpenAPI operation
            openapi_operation = self.get_openapi_operation(oa_method, oa_path)

            # Get documentation endpoint if matched
            endpoint_doc = None
            if best_match and best_confidence >= 0.5:
                endpoint_doc = doc_endpoint_map[best_match]

            matches.append(
                EndpointMatch(
                    openapi_method=oa_method,
                    openapi_path=oa_path,
                    doc_method=best_match[0] if best_match else "",
                    doc_path=best_match[1] if best_match else "",
                    endpoint_doc=endpoint_doc,
                    openapi_operation=openapi_operation,
                    match_confidence=best_confidence,
                    match_type=match_type,
                )
            )

        return matches

    def analyze_endpoint(
        self, endpoint_doc: EndpointDocumentation, openapi_operation: Optional[dict[str, Any]] = None
    ) -> EndpointAnalysis:
        """
        Perform comprehensive analysis of an endpoint's documentation.

        Args:
            endpoint_doc: The endpoint documentation to analyze
            openapi_operation: Corresponding OpenAPI operation (if any)

        Returns:
            Complete endpoint analysis
        """
        missing_elements = []
        quality_issues = []
        enhancement_opportunities = []

        # Analyze description
        if not endpoint_doc.description or len(endpoint_doc.description.strip()) < 10:
            missing_elements.append("description")
            if not endpoint_doc.description:
                quality_issues.append("Missing description")
            else:
                quality_issues.append("Description too short (less than 10 characters)")

        # Analyze summary
        if not endpoint_doc.summary or len(endpoint_doc.summary.strip()) < 5:
            missing_elements.append("summary")
            if not endpoint_doc.summary:
                quality_issues.append("Missing summary")
            else:
                quality_issues.append("Summary too short (less than 5 characters)")

        # Analyze code samples
        if not endpoint_doc.code_samples:
            missing_elements.append("code_samples")
            enhancement_opportunities.append("Auto-generate code samples")

        # Analyze response examples with enhanced multi-format support
        if not endpoint_doc.response_examples:
            missing_elements.append("response_examples")
            quality_issues.append("No response examples provided")
        else:
            # Check for valid content in any format
            valid_examples = []
            for example in endpoint_doc.response_examples:
                if example.content is not None or example.raw_content or hasattr(example, "content_type"):
                    valid_examples.append(example)

            if not valid_examples:
                quality_issues.append("Response examples found but no valid content detected")
            elif len(valid_examples) < 2:
                enhancement_opportunities.append("Add more response examples (success and error cases)")

            # Check for success response (2xx)
            success_examples = [ex for ex in valid_examples if 200 <= ex.status_code < 300]
            if not success_examples:
                quality_issues.append("No success response examples (2xx status codes)")

            # Check for different content types representation
            content_types = set()
            for example in valid_examples:
                if hasattr(example, "content_type"):
                    content_types.add(example.content_type)

            if len(content_types) > 1:
                enhancement_opportunities.append(f"Multiple content types documented: {', '.join(content_types)}")

        # Analyze parameters
        if "{" in endpoint_doc.path and "}" in endpoint_doc.path:
            if not endpoint_doc.parameters or len(endpoint_doc.parameters) == 0:
                missing_elements.append("parameters")
                quality_issues.append("Path has parameters but no parameter documentation")

        # Calculate completeness score
        completeness_score = self._calculate_completeness_score(endpoint_doc, missing_elements, quality_issues)

        # Determine if endpoint can be enhanced
        can_be_enhanced = openapi_operation is not None and (
            len(missing_elements) > 0 or len(enhancement_opportunities) > 0
        )

        return EndpointAnalysis(
            endpoint_doc=endpoint_doc,
            openapi_operation=openapi_operation,
            completeness_score=completeness_score,
            missing_elements=missing_elements,
            quality_issues=quality_issues,
            enhancement_opportunities=enhancement_opportunities,
            can_be_enhanced=can_be_enhanced,
        )

    def get_openapi_operation(self, method: str, path: str) -> dict[str, Any]:
        """
        Get OpenAPI operation for a specific method and path.

        Args:
            method: HTTP method
            path: API path

        Returns:
            OpenAPI operation dictionary or empty dict if not found
        """
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

    def find_similar_paths(self, target_path: str, candidate_paths: list[str]) -> list[str]:
        """
        Find paths similar to the target path.

        Args:
            target_path: Path to find similarities for
            candidate_paths: List of candidate paths to compare against

        Returns:
            List of similar paths, sorted by similarity
        """
        similarities = []

        for candidate in candidate_paths:
            confidence = self._calculate_path_similarity(target_path, candidate)
            if confidence > 0.5:  # Only include reasonably similar paths
                similarities.append((candidate, confidence))

        # Sort by confidence descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [path for path, _ in similarities]

    def generate_code_samples(
        self,
        endpoint_doc: EndpointDocumentation,
        openapi_operation: dict[str, Any],
        languages: Optional[list[CodeLanguage]] = None,
    ) -> list[CodeSample]:
        """
        Generate code samples for an endpoint.

        Args:
            endpoint_doc: Endpoint documentation
            openapi_operation: OpenAPI operation
            languages: List of languages to generate samples for

        Returns:
            List of generated code samples
        """
        if languages is None:
            languages = [CodeLanguage.CURL, CodeLanguage.PYTHON]

        try:
            return generate_code_samples_for_endpoint(
                method=endpoint_doc.method.value,
                path=endpoint_doc.path,
                operation=openapi_operation,
                base_url=self.base_url,
                languages=languages,
            )
        except CodeSampleGenerationError:
            return []

    def _calculate_match_confidence(self, oa_method: str, oa_path: str, doc_method: str, doc_path: str) -> float:
        """Calculate confidence score for endpoint matching."""
        # Method must match exactly
        if oa_method.upper() != doc_method.upper():
            return 0.0

        # Calculate path similarity
        return self._calculate_path_similarity(oa_path, doc_path)

    def _calculate_path_similarity(self, path1: str, path2: str) -> float:
        """Calculate similarity between two paths."""
        # Exact match
        if path1 == path2:
            return 1.0

        # Normalize paths
        path1_norm = path1.strip("/")
        path2_norm = path2.strip("/")

        if path1_norm == path2_norm:
            return 1.0

        # Split into parts
        parts1 = path1_norm.split("/")
        parts2 = path2_norm.split("/")

        # Different number of parts = low similarity
        if len(parts1) != len(parts2):
            return max(0.0, 1.0 - abs(len(parts1) - len(parts2)) * 0.3)

        # Compare parts
        matching_parts = 0
        parameter_matches = 0

        for p1, p2 in zip(parts1, parts2):
            if p1 == p2:
                matching_parts += 1
            elif p1.startswith("{") and p1.endswith("}") and p2.startswith("{") and p2.endswith("}"):
                # Both are parameters - count as partial match
                parameter_matches += 1

        total_parts = len(parts1)
        if total_parts == 0:
            return 1.0

        # Calculate similarity score
        exact_score = matching_parts / total_parts
        param_score = parameter_matches / total_parts * 0.8  # Parameters are slightly less confident

        return min(1.0, exact_score + param_score)

    def _calculate_completeness_score(
        self, endpoint_doc: EndpointDocumentation, missing_elements: list[str], quality_issues: list[str]
    ) -> float:
        """Calculate completeness score for an endpoint."""
        score = 0.0

        # Description (40 points)
        if "description" not in missing_elements:
            description_text = endpoint_doc.description or ""
            if len(description_text.strip()) >= 50:
                score += 40
            else:
                score += 20

        # Summary (25 points)
        if "summary" not in missing_elements:
            summary_text = endpoint_doc.summary or ""
            if len(summary_text.strip()) >= 10:
                score += 25
            else:
                score += 15

        # Response examples (25 points)
        if "response_examples" not in missing_elements:
            if len(endpoint_doc.response_examples) >= 2:
                score += 25
            else:
                score += 15

        # Parameters (10 points)
        if "parameters" not in missing_elements:
            score += 10
        elif "{" not in endpoint_doc.path or "}" not in endpoint_doc.path:
            # No parameters needed
            score += 10

        return round(score, 1)
