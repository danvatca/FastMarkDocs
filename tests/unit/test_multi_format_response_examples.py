"""
Unit tests for multi-format response example support in fastmarkdocs.

This module tests the enhanced ResponseExample type and related functionality
that supports multiple content types including JSON, Prometheus metrics, XML, YAML, etc.
"""

from unittest.mock import patch

import pytest
from fastmarkdocs.documentation_loader import MarkdownDocumentationLoader
from fastmarkdocs.openapi_enhancer import OpenAPIEnhancer
from fastmarkdocs.types import OpenAPIEnhancementConfig, ResponseExample


class TestResponseExampleContentTypeDetection:
    """Test content type auto-detection in ResponseExample."""

    def test_json_content_detection(self):
        """Test JSON content type detection."""
        json_content = '{"status": "success", "data": {"items": []}}'

        example = ResponseExample(status_code=200, description="Success response", raw_content=json_content)

        assert example.content_type == "application/json"
        assert isinstance(example.content, dict)
        assert example.content["status"] == "success"

    def test_prometheus_metrics_detection(self):
        """Test Prometheus metrics content type detection."""
        prometheus_content = """# HELP syneto_chronos_jobs_total Total number of protection jobs
# TYPE syneto_chronos_jobs_total counter
syneto_chronos_jobs_total{status="completed"} 1247
syneto_chronos_jobs_total{status="failed"} 23"""

        example = ResponseExample(status_code=200, description="Prometheus metrics", raw_content=prometheus_content)

        assert example.content_type == "text/plain; version=0.0.4"
        assert example.content == prometheus_content

    def test_xml_content_detection(self):
        """Test XML content type detection."""
        xml_content = '<?xml version="1.0" encoding="UTF-8"?><response><status>success</status></response>'

        example = ResponseExample(status_code=200, description="XML response", raw_content=xml_content)

        assert example.content_type == "application/xml"
        assert example.content == xml_content

    def test_yaml_content_detection(self):
        """Test YAML content type detection."""
        yaml_content = """status: success
data:
  items: []
  count: 0"""

        example = ResponseExample(status_code=200, description="YAML response", raw_content=yaml_content)

        assert example.content_type == "application/yaml"

    def test_html_content_detection(self):
        """Test HTML content type detection."""
        html_content = "<!DOCTYPE html><html><head><title>Test</title></head><body>Content</body></html>"

        example = ResponseExample(status_code=200, description="HTML response", raw_content=html_content)

        assert example.content_type == "text/html"

    def test_csv_content_detection(self):
        """Test CSV content type detection."""
        csv_content = """name,age,city
John,30,New York
Jane,25,Los Angeles"""

        example = ResponseExample(status_code=200, description="CSV response", raw_content=csv_content)

        assert example.content_type == "text/csv"

    def test_plain_text_fallback(self):
        """Test fallback to plain text for unknown formats."""
        plain_content = "This is just plain text content without any specific format."

        example = ResponseExample(status_code=200, description="Plain text response", raw_content=plain_content)

        assert example.content_type == "text/plain"
        assert example.content == plain_content

    def test_explicit_content_type_override(self):
        """Test that explicitly set content type is not overridden."""
        json_content = '{"status": "success"}'

        example = ResponseExample(
            status_code=200,
            description="Explicit content type",
            content_type="application/custom+json",
            raw_content=json_content,
        )

        # Should not auto-detect since content_type was explicitly set
        assert example.content_type == "application/custom+json"


class TestDocumentationLoaderEnhancements:
    """Test enhanced documentation loader functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loader = MarkdownDocumentationLoader()

    def test_finalize_json_response_example(self):
        """Test finalizing JSON response examples."""
        response_examples = []
        json_code = ['{"status": "success", "data": {"id": 123}}']

        self.loader._finalize_response_example(response_examples, json_code, 200, "Success response")

        assert len(response_examples) == 1
        example = response_examples[0]
        assert example.status_code == 200
        assert example.content_type == "application/json"
        assert isinstance(example.content, dict)
        assert example.content["status"] == "success"

    def test_finalize_prometheus_response_example(self):
        """Test finalizing Prometheus metrics response examples."""
        response_examples = []
        prometheus_code = [
            "# HELP syneto_jobs_total Total jobs",
            "# TYPE syneto_jobs_total counter",
            'syneto_jobs_total{status="completed"} 100',
        ]

        self.loader._finalize_response_example(response_examples, prometheus_code, 200, "Metrics response")

        assert len(response_examples) == 1
        example = response_examples[0]
        assert example.status_code == 200
        assert example.content_type == "text/plain; version=0.0.4"
        assert isinstance(example.content, str)
        assert "# HELP syneto_jobs_total" in example.content

    def test_finalize_xml_response_example(self):
        """Test finalizing XML response examples."""
        response_examples = []
        xml_code = ['<?xml version="1.0"?><response><status>success</status></response>']

        self.loader._finalize_response_example(response_examples, xml_code, 200, "XML response")

        assert len(response_examples) == 1
        example = response_examples[0]
        assert example.status_code == 200
        assert example.content_type == "application/xml"
        assert example.content == xml_code[0]

    @patch("yaml.safe_load")
    def test_finalize_yaml_response_example_with_yaml_library(self, mock_yaml_load):
        """Test finalizing YAML response examples when PyYAML is available."""
        mock_yaml_load.return_value = {"status": "success", "data": None}

        response_examples = []
        yaml_code = ["status: success", "data: null"]

        self.loader._finalize_response_example(response_examples, yaml_code, 200, "YAML response")

        assert len(response_examples) == 1
        example = response_examples[0]
        assert example.status_code == 200
        assert example.content_type == "application/yaml"
        assert isinstance(example.content, dict)
        # YAML parsing happens twice: once in ResponseExample.__post_init__ and once in documentation_loader
        assert mock_yaml_load.call_count == 2

    def test_finalize_yaml_response_example_without_yaml_library(self):
        """Test finalizing YAML response examples when PyYAML is not available."""
        yaml_code = ["status: success", "data: null"]

        # Create a ResponseExample directly to test YAML without PyYAML
        # This simulates what happens when PyYAML is not available
        yaml_content = "\n".join(yaml_code)

        # Mock the yaml import to raise ImportError
        with patch.dict("sys.modules", {"yaml": None}):
            example = ResponseExample(status_code=200, description="YAML response", raw_content=yaml_content)

        # Should detect as YAML but store content as string due to missing PyYAML
        assert example.status_code == 200
        assert example.content_type == "application/yaml"
        assert isinstance(example.content, str)
        assert example.content == yaml_content

    def test_finalize_invalid_json_fallback(self):
        """Test that invalid JSON falls back to plain text."""
        response_examples = []
        invalid_json_code = ['{"invalid": json content}']

        self.loader._finalize_response_example(response_examples, invalid_json_code, 400, "Invalid JSON")

        assert len(response_examples) == 1
        example = response_examples[0]
        assert example.status_code == 400
        assert example.content_type == "text/plain"
        assert example.content == invalid_json_code[0]

    def test_finalize_empty_code_block(self):
        """Test that empty code blocks are skipped."""
        response_examples = []
        empty_code = ["", "   ", ""]

        self.loader._finalize_response_example(response_examples, empty_code, 200, "Empty response")

        assert len(response_examples) == 0


class TestOpenAPIEnhancerMultiFormat:
    """Test enhanced OpenAPI enhancer with multi-format support."""

    def setup_method(self):
        """Set up test fixtures."""
        self.enhancer = OpenAPIEnhancer()

    def test_add_json_response_examples(self):
        """Test adding JSON response examples to OpenAPI operation."""
        operation = {"responses": {}}

        json_example = ResponseExample(
            status_code=200,
            description="Success response",
            content={"status": "success", "data": {"id": 123}},
            content_type="application/json",
        )

        self.enhancer._add_response_examples_to_operation(operation, [json_example])

        assert "200" in operation["responses"]
        response_200 = operation["responses"]["200"]
        assert "content" in response_200
        assert "application/json" in response_200["content"]

        json_content = response_200["content"]["application/json"]
        assert "examples" in json_content
        assert "schema" in json_content
        assert json_content["schema"]["type"] == "object"

        example = json_content["examples"]["example_200"]
        assert example["summary"] == "Success response"
        assert example["value"]["status"] == "success"

    def test_add_prometheus_response_examples(self):
        """Test adding Prometheus metrics response examples to OpenAPI operation."""
        operation = {"responses": {}}

        prometheus_content = "# HELP test_metric A test metric\ntest_metric 42"
        prometheus_example = ResponseExample(
            status_code=200,
            description="Prometheus metrics",
            content=prometheus_content,
            content_type="text/plain; version=0.0.4",
            raw_content=prometheus_content,
        )

        self.enhancer._add_response_examples_to_operation(operation, [prometheus_example])

        assert "200" in operation["responses"]
        response_200 = operation["responses"]["200"]
        assert "content" in response_200
        assert "text/plain; version=0.0.4" in response_200["content"]

        prometheus_response = response_200["content"]["text/plain; version=0.0.4"]
        assert "examples" in prometheus_response
        assert "schema" in prometheus_response
        assert prometheus_response["schema"]["type"] == "string"

        example = prometheus_response["examples"]["example_200"]
        assert example["summary"] == "Prometheus metrics"
        assert "# HELP test_metric" in example["value"]

    def test_add_xml_response_examples(self):
        """Test adding XML response examples to OpenAPI operation."""
        operation = {"responses": {}}

        xml_content = '<?xml version="1.0"?><response><status>success</status></response>'
        xml_example = ResponseExample(
            status_code=200,
            description="XML response",
            content=xml_content,
            content_type="application/xml",
            raw_content=xml_content,
        )

        self.enhancer._add_response_examples_to_operation(operation, [xml_example])

        assert "200" in operation["responses"]
        response_200 = operation["responses"]["200"]
        assert "content" in response_200
        assert "application/xml" in response_200["content"]

        xml_response = response_200["content"]["application/xml"]
        assert "examples" in xml_response
        assert "schema" in xml_response
        assert xml_response["schema"]["type"] == "string"
        assert xml_response["schema"]["format"] == "xml"

    def test_add_multiple_content_type_examples(self):
        """Test adding examples with different content types to the same operation."""
        operation = {"responses": {}}

        examples = [
            ResponseExample(
                status_code=200,
                description="JSON response",
                content={"status": "success"},
                content_type="application/json",
            ),
            ResponseExample(
                status_code=200,
                description="XML response",
                content="<response><status>success</status></response>",
                content_type="application/xml",
                raw_content="<response><status>success</status></response>",
            ),
        ]

        self.enhancer._add_response_examples_to_operation(operation, examples)

        assert "200" in operation["responses"]
        response_200 = operation["responses"]["200"]
        assert "content" in response_200
        assert "application/json" in response_200["content"]
        assert "application/xml" in response_200["content"]

        # Both content types should have their examples
        json_content = response_200["content"]["application/json"]
        xml_content = response_200["content"]["application/xml"]

        assert "examples" in json_content
        assert "examples" in xml_content
        assert json_content["examples"]["example_200"]["summary"] == "JSON response"
        assert xml_content["examples"]["example_200"]["summary"] == "XML response"

    def test_response_example_without_content(self):
        """Test handling response examples without content."""
        operation = {"responses": {}}

        empty_example = ResponseExample(status_code=204, description="No content response")

        self.enhancer._add_response_examples_to_operation(operation, [empty_example])

        assert "204" in operation["responses"]
        response_204 = operation["responses"]["204"]
        assert response_204["description"] == "No content response"
        # Should not have content section for empty responses
        assert "content" not in response_204


class TestOpenAPIEnhancementConfig:
    """Test enhanced OpenAPI enhancement configuration."""

    def test_default_supported_content_types(self):
        """Test default supported content types in configuration."""
        config = OpenAPIEnhancementConfig()

        expected_types = [
            "application/json",
            "text/plain",
            "text/plain; version=0.0.4",  # Prometheus
            "application/xml",
            "application/yaml",
            "text/html",
            "text/csv",
        ]

        assert config.supported_content_types == expected_types
        assert config.content_type_detection is True
        assert config.preserve_raw_content is True
        assert config.validate_content_format is True

    def test_custom_content_types_configuration(self):
        """Test custom content types configuration."""
        custom_types = ["application/json", "text/plain", "application/custom"]

        config = OpenAPIEnhancementConfig(supported_content_types=custom_types, content_type_detection=False)

        assert config.supported_content_types == custom_types
        assert config.content_type_detection is False


class TestResponseExampleValidation:
    """Test response example validation and error handling."""

    def test_invalid_status_code(self):
        """Test validation of invalid status codes."""
        with pytest.raises(ValueError, match="Status code must be a valid HTTP status code"):
            ResponseExample(status_code=99, description="Invalid status")  # Invalid status code

        with pytest.raises(ValueError, match="Status code must be a valid HTTP status code"):
            ResponseExample(status_code=600, description="Invalid status")  # Invalid status code

    def test_valid_status_codes(self):
        """Test validation of valid status codes."""
        # Test boundary values
        example_100 = ResponseExample(status_code=100, description="Continue")
        example_599 = ResponseExample(status_code=599, description="Network Connect Timeout Error")

        assert example_100.status_code == 100
        assert example_599.status_code == 599

    def test_content_type_detection_with_malformed_content(self):
        """Test content type detection with malformed content."""
        malformed_json = '{"incomplete": json'

        example = ResponseExample(status_code=400, description="Malformed JSON", raw_content=malformed_json)

        # Should fall back to plain text for malformed JSON
        assert example.content_type == "text/plain"
        assert example.content == malformed_json


if __name__ == "__main__":
    pytest.main([__file__])
