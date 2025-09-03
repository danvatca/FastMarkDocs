"""
Integration tests for multi-format response example support.

This module tests the complete workflow from markdown parsing to OpenAPI enhancement
for various content types including Prometheus metrics, XML, YAML, etc.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from fastmarkdocs.documentation_loader import MarkdownDocumentationLoader
from fastmarkdocs.openapi_enhancer import OpenAPIEnhancer
from fastmarkdocs.types import OpenAPIEnhancementConfig


class TestMultiFormatIntegration:
    """Integration tests for multi-format response examples."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loader = MarkdownDocumentationLoader()
        self.enhancer = OpenAPIEnhancer()

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

Tags: metrics, prometheus, monitoring
"""

        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown_content)
            temp_file = Path(f.name)

        try:
            # Load documentation
            self.loader.docs_directory = temp_file.parent
            documentation = self.loader.load_documentation()

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
            assert 'syneto_chronos_jobs_total{status="completed"} 1247' in example.content

            # Test OpenAPI enhancement
            base_openapi = {
                "openapi": "3.0.0",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {
                    "/metrics": {"get": {"summary": "Get metrics", "responses": {"200": {"description": "Success"}}}}
                },
            }

            enhanced_schema = self.enhancer.enhance_openapi_schema(base_openapi, documentation)

            # Verify enhanced schema
            metrics_operation = enhanced_schema["paths"]["/metrics"]["get"]
            assert "responses" in metrics_operation
            assert "200" in metrics_operation["responses"]

            response_200 = metrics_operation["responses"]["200"]
            assert "content" in response_200
            assert "text/plain; version=0.0.4" in response_200["content"]

            prometheus_content = response_200["content"]["text/plain; version=0.0.4"]
            assert "examples" in prometheus_content
            assert "schema" in prometheus_content
            assert prometheus_content["schema"]["type"] == "string"

            example_value = prometheus_content["examples"]["example_200"]["value"]
            assert "# HELP syneto_chronos_jobs_total" in example_value

        finally:
            # Clean up
            temp_file.unlink()

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

Tags: data, multi-format
"""

        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown_content)
            temp_file = Path(f.name)

        try:
            # Load documentation
            self.loader.docs_directory = temp_file.parent
            documentation = self.loader.load_documentation()

            # Verify endpoint was parsed correctly
            assert len(documentation.endpoints) == 1
            endpoint = documentation.endpoints[0]
            assert endpoint.path == "/data"
            assert endpoint.method.value == "GET"

            # Verify response examples - should have both JSON and XML
            assert len(endpoint.response_examples) == 2

            # Find JSON and XML examples
            json_example = None
            xml_example = None
            for example in endpoint.response_examples:
                if example.content_type == "application/json":
                    json_example = example
                elif example.content_type == "application/xml":
                    xml_example = example

            assert json_example is not None
            assert xml_example is not None

            assert json_example.status_code == 200
            assert xml_example.status_code == 400

            assert isinstance(json_example.content, dict)
            assert json_example.content["status"] == "success"

            assert isinstance(xml_example.content, str)
            assert "<?xml version=" in xml_example.content

            # Test OpenAPI enhancement
            base_openapi = {
                "openapi": "3.0.0",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {"/data": {"get": {"summary": "Get data", "responses": {}}}},
            }

            enhanced_schema = self.enhancer.enhance_openapi_schema(base_openapi, documentation)

            # Verify enhanced schema has both content types
            data_operation = enhanced_schema["paths"]["/data"]["get"]
            responses = data_operation["responses"]

            assert "200" in responses
            assert "400" in responses

            # Check JSON response
            response_200 = responses["200"]
            assert "content" in response_200
            assert "application/json" in response_200["content"]

            json_content = response_200["content"]["application/json"]
            assert json_content["schema"]["type"] == "object"
            assert "examples" in json_content

            # Check XML response
            response_400 = responses["400"]
            assert "content" in response_400
            assert "application/xml" in response_400["content"]

            xml_content = response_400["content"]["application/xml"]
            assert xml_content["schema"]["type"] == "string"
            assert xml_content["schema"]["format"] == "xml"

        finally:
            # Clean up
            temp_file.unlink()

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

Tags: config, yaml
"""

        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown_content)
            temp_file = Path(f.name)

        try:
            # Load documentation
            self.loader.docs_directory = temp_file.parent
            documentation = self.loader.load_documentation()

            # Verify YAML content type detection
            assert len(documentation.endpoints) == 1
            endpoint = documentation.endpoints[0]
            assert len(endpoint.response_examples) == 1

            example = endpoint.response_examples[0]
            assert example.content_type == "application/yaml"
            assert "server:" in example.raw_content

        finally:
            # Clean up
            temp_file.unlink()

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

Tags: reports, csv
"""

        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown_content)
            temp_file = Path(f.name)

        try:
            # Load documentation
            self.loader.docs_directory = temp_file.parent
            documentation = self.loader.load_documentation()

            # Verify CSV content type detection
            assert len(documentation.endpoints) == 1
            endpoint = documentation.endpoints[0]
            assert len(endpoint.response_examples) == 1

            example = endpoint.response_examples[0]
            assert example.content_type == "text/csv"
            assert "name,age,department,salary" in example.content

        finally:
            # Clean up
            temp_file.unlink()

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

Tags: logs, text
"""

        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown_content)
            temp_file = Path(f.name)

        try:
            # Load documentation
            self.loader.docs_directory = temp_file.parent
            documentation = self.loader.load_documentation()

            # Verify plain text fallback
            assert len(documentation.endpoints) == 1
            endpoint = documentation.endpoints[0]
            assert len(endpoint.response_examples) == 1

            example = endpoint.response_examples[0]
            assert example.content_type == "text/plain"
            assert "2024-01-15 10:30:00 INFO Starting application" in example.content

        finally:
            # Clean up
            temp_file.unlink()

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

Tags: error, malformed
"""

        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown_content)
            temp_file = Path(f.name)

        try:
            # Load documentation
            self.loader.docs_directory = temp_file.parent
            documentation = self.loader.load_documentation()

            # Verify fallback to plain text for malformed JSON
            assert len(documentation.endpoints) == 1
            endpoint = documentation.endpoints[0]
            assert len(endpoint.response_examples) == 1

            example = endpoint.response_examples[0]
            # Should fall back to plain text due to malformed JSON
            assert example.content_type == "text/plain"
            assert '"error": "Something went wrong"' in example.content

        finally:
            # Clean up
            temp_file.unlink()

    @patch("yaml.safe_load")
    def test_yaml_parsing_with_pyyaml_available(self, mock_yaml_load):
        """Test YAML parsing when PyYAML library is available."""
        mock_yaml_load.return_value = {"server": {"host": "localhost", "port": 8080}, "features": ["auth", "logging"]}

        markdown_content = """
# Config API

## GET /config

### Response Examples

```yaml
server:
  host: localhost
  port: 8080
features:
  - auth
  - logging
```

Tags: config
"""

        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown_content)
            temp_file = Path(f.name)

        try:
            # Load documentation
            self.loader.docs_directory = temp_file.parent
            documentation = self.loader.load_documentation()

            # Verify YAML was parsed as dict
            endpoint = documentation.endpoints[0]
            example = endpoint.response_examples[0]

            assert example.content_type == "application/yaml"
            assert isinstance(example.content, dict)
            # YAML parsing happens twice: once in ResponseExample.__post_init__ and once in documentation_loader
            assert mock_yaml_load.call_count == 2

        finally:
            # Clean up
            temp_file.unlink()

    def test_configuration_content_type_filtering(self):
        """Test that configuration can filter supported content types."""
        config = OpenAPIEnhancementConfig(
            supported_content_types=["application/json", "text/plain"], content_type_detection=True
        )

        # Verify configuration
        assert "application/json" in config.supported_content_types
        assert "text/plain" in config.supported_content_types
        assert "application/xml" not in config.supported_content_types
        assert config.content_type_detection is True


if __name__ == "__main__":
    pytest.main([__file__])
