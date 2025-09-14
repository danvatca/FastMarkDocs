"""
Integration tests for multi-format response examples.

These tests verify that the complete workflow works end-to-end for various
content types and response formats.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from fastmarkdocs.documentation_loader import MarkdownDocumentationLoader
from fastmarkdocs.openapi_enhancer import OpenAPIEnhancer


class TestMultiFormatIntegration:
    """Integration tests for multi-format response examples."""

    def setup_method(self):
        """Set up test fixtures."""
        self.enhancer = OpenAPIEnhancer()

    def _load_documentation_from_content(self, markdown_content: str):
        """Helper method to load documentation from markdown content in isolated temp directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "test.md"
            temp_file.write_text(markdown_content)

            loader = MarkdownDocumentationLoader(docs_directory=temp_dir, cache_enabled=False)
            return loader.load_documentation()

    def test_prometheus_metrics_end_to_end(self):
        """Test complete workflow for Prometheus metrics documentation."""
        markdown_content = """
# Metrics API

## GET /metrics

Retrieve Prometheus metrics for the service.

### Response Examples

**Success Response (200):**
```
# HELP syneto_chronos_jobs_total Total number of protection jobs
# TYPE syneto_chronos_jobs_total counter
syneto_chronos_jobs_total{status="completed"} 1247
syneto_chronos_jobs_total{status="failed"} 23
syneto_chronos_jobs_total{status="running"} 5

# HELP syneto_chronos_service_health Service health status
# TYPE syneto_chronos_service_health gauge
syneto_chronos_service_health 1
```

### Code Examples

```python
import requests
response = requests.get("http://localhost:8000/metrics")
print(response.text)
```

Section: metrics, prometheus, monitoring
"""

        # Load documentation using helper method
        documentation = self._load_documentation_from_content(markdown_content)

        # Verify endpoint was parsed correctly
        assert len(documentation.endpoints) == 1
        endpoint = documentation.endpoints[0]
        assert endpoint.path == "/metrics"
        assert endpoint.method.value == "GET"

        # Verify response examples
        assert len(endpoint.response_examples) == 1
        example = endpoint.response_examples[0]
        assert example.status_code == 200
        assert example.content_type == "text/plain; version=0.0.4"
        assert "# HELP syneto_chronos_jobs_total" in example.content

        # Verify code samples
        assert len(endpoint.code_samples) == 1
        code_sample = endpoint.code_samples[0]
        assert code_sample.language.value == "python"
        assert "import requests" in code_sample.code

        # Verify sections
        assert "metrics" in endpoint.sections
        assert "prometheus" in endpoint.sections
        assert "monitoring" in endpoint.sections

        # Test OpenAPI enhancement
        base_openapi = {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/metrics": {
                    "get": {
                        "summary": "Get metrics",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        enhanced = self.enhancer.enhance_openapi_schema(base_openapi, documentation)

        # Verify enhancement worked
        metrics_get = enhanced["paths"]["/metrics"]["get"]
        assert "x-codeSamples" in metrics_get
        assert len(metrics_get["x-codeSamples"]) >= 1
        # Check that python code sample is included
        python_samples = [sample for sample in metrics_get["x-codeSamples"] if sample["lang"] == "python"]
        assert len(python_samples) >= 1

    def test_mixed_content_types_end_to_end(self):
        """Test complete workflow with multiple content types in one endpoint."""
        markdown_content = """
# API Documentation

## GET /data

Get data in various formats.

### Response Examples

**Success Response (200):**
```json
{
  "status": "success",
  "data": {
    "items": [],
    "count": 0
  }
}
```

**Error Response (400):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<error>
  <code>400</code>
  <message>Bad Request</message>
</error>
```

### Code Examples

```python
import requests
response = requests.get("http://localhost:8000/data")
```

Section: data, multi-format
"""

        # Load documentation using helper method
        documentation = self._load_documentation_from_content(markdown_content)

        # Verify endpoint was parsed correctly
        assert len(documentation.endpoints) == 1
        endpoint = documentation.endpoints[0]
        assert endpoint.path == "/data"
        assert endpoint.method.value == "GET"

        # Verify multiple response examples with different content types
        assert len(endpoint.response_examples) == 2

        # Find JSON and XML examples
        json_example = next(ex for ex in endpoint.response_examples if ex.content_type == "application/json")
        xml_example = next(ex for ex in endpoint.response_examples if ex.content_type == "application/xml")

        # Verify JSON example
        assert json_example.status_code == 200
        assert json_example.description == "Success Response"
        assert isinstance(json_example.content, dict)
        assert json_example.content["status"] == "success"

        # Verify XML example
        assert xml_example.status_code == 400
        assert xml_example.description == "Error Response"
        assert isinstance(xml_example.content, str)
        assert "<?xml version" in xml_example.content
        assert "<error>" in xml_example.content

        # Verify sections
        assert "data" in endpoint.sections
        assert "multi-format" in endpoint.sections

    def test_yaml_content_integration(self):
        """Test YAML content type integration."""
        markdown_content = """
# Configuration API

## GET /config

Get configuration in YAML format.

### Response Examples

```yaml
server:
  host: localhost
  port: 8080
database:
  url: postgresql://localhost/mydb
  pool_size: 10
features:
  - authentication
  - logging
  - metrics
```

Section: config, yaml
"""

        # Load documentation using helper method
        documentation = self._load_documentation_from_content(markdown_content)

        # Verify YAML content type detection
        assert len(documentation.endpoints) == 1
        endpoint = documentation.endpoints[0]
        assert endpoint.path == "/config"

        # Verify YAML response example
        assert len(endpoint.response_examples) == 1
        example = endpoint.response_examples[0]
        assert example.content_type == "application/yaml"
        assert isinstance(example.content, dict)
        assert example.content["server"]["host"] == "localhost"
        assert example.content["server"]["port"] == 8080
        assert "authentication" in example.content["features"]

    def test_csv_content_integration(self):
        """Test CSV content type integration."""
        markdown_content = """
# Reports API

## GET /report

Get report data in CSV format.

### Response Examples

```csv
name,age,department,salary
John Doe,30,Engineering,75000
Jane Smith,28,Marketing,65000
Bob Johnson,35,Sales,70000
```

Section: reports, csv
"""

        # Load documentation using helper method
        documentation = self._load_documentation_from_content(markdown_content)

        # Verify CSV content type detection
        assert len(documentation.endpoints) == 1
        endpoint = documentation.endpoints[0]
        assert endpoint.path == "/report"

        # Verify CSV response example
        assert len(endpoint.response_examples) == 1
        example = endpoint.response_examples[0]
        assert example.content_type == "text/csv"
        assert isinstance(example.content, str)
        assert "name,age,department,salary" in example.content
        assert "John Doe,30,Engineering,75000" in example.content

    def test_plain_text_fallback_integration(self):
        """Test plain text fallback for unrecognized formats."""
        markdown_content = """
# Log API

## GET /logs

Get raw log data.

### Response Examples

```
2024-01-15 10:30:00 INFO Starting application
2024-01-15 10:30:01 INFO Database connection established
2024-01-15 10:30:02 WARN Configuration file not found, using defaults
2024-01-15 10:30:03 INFO Server listening on port 8080
```

Section: logs, text
"""

        # Load documentation using helper method
        documentation = self._load_documentation_from_content(markdown_content)

        # Verify plain text fallback
        assert len(documentation.endpoints) == 1
        endpoint = documentation.endpoints[0]
        assert endpoint.path == "/logs"

        # Verify plain text response example
        assert len(endpoint.response_examples) == 1
        example = endpoint.response_examples[0]
        assert example.content_type == "text/plain"
        assert isinstance(example.content, str)
        assert "2024-01-15 10:30:00 INFO Starting application" in example.content

    def test_malformed_json_fallback_integration(self):
        """Test fallback behavior for malformed JSON."""
        markdown_content = """
# Error API

## GET /error

Get error response with malformed JSON.

### Response Examples

```json
{
  "error": "Something went wrong",
  "details": {
    "code": 500,
    "message": "Internal server error"
    // Missing closing brace - malformed JSON
```

Section: error, malformed
"""

        # Load documentation using helper method
        documentation = self._load_documentation_from_content(markdown_content)

        # Verify fallback to plain text for malformed JSON
        assert len(documentation.endpoints) == 1
        endpoint = documentation.endpoints[0]
        assert endpoint.path == "/error"

        # Verify fallback response example
        assert len(endpoint.response_examples) == 1
        example = endpoint.response_examples[0]
        # Should fall back to plain text due to malformed JSON
        assert example.content_type == "text/plain"
        assert isinstance(example.content, str)
        assert "Something went wrong" in example.content

    @patch("yaml.safe_load")
    def test_yaml_parsing_with_pyyaml_available(self, mock_yaml_load):
        """Test YAML parsing when PyYAML is available."""
        mock_yaml_load.return_value = {"test": "data"}

        markdown_content = """
# Test API

## GET /test

Test YAML parsing.

### Response Examples

```yaml
test: data
```
"""

        # Load documentation using helper method
        documentation = self._load_documentation_from_content(markdown_content)

        # Verify YAML was parsed using PyYAML
        assert len(documentation.endpoints) == 1
        endpoint = documentation.endpoints[0]
        assert len(endpoint.response_examples) == 1
        example = endpoint.response_examples[0]
        assert example.content_type == "application/yaml"
        assert mock_yaml_load.call_count >= 1  # May be called multiple times during processing

    def test_configuration_content_type_filtering(self):
        """Test that content type filtering works correctly."""
        markdown_content = """
# Multi-format API

## POST /upload

Upload data in multiple formats.

### Response Examples

**JSON Response (200):**
```json
{"status": "success"}
```

**XML Response (200):**
```xml
<status>success</status>
```

**Plain Text Response (200):**
```
SUCCESS
```
"""

        # Load documentation using helper method
        documentation = self._load_documentation_from_content(markdown_content)

        # Verify all content types were detected
        assert len(documentation.endpoints) == 1
        endpoint = documentation.endpoints[0]
        assert len(endpoint.response_examples) == 3

        content_types = {ex.content_type for ex in endpoint.response_examples}
        assert "application/json" in content_types
        assert "application/xml" in content_types
        assert "text/plain" in content_types
