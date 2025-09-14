# Multi-Format Response Examples

FastMarkDocs now supports response examples in multiple content types beyond JSON, including Prometheus metrics, XML, YAML, CSV, and plain text. This enhancement allows you to document APIs that return various data formats while maintaining proper OpenAPI schema generation.

## Supported Content Types

FastMarkDocs automatically detects and handles the following content types:

- **JSON** (`application/json`) - Default format with full parsing support
- **Prometheus Metrics** (`text/plain; version=0.0.4`) - Auto-detected from `# HELP` and `# TYPE` comments
- **XML** (`application/xml`) - Detected from XML declarations and tags
- **YAML** (`application/yaml`) - Detected from YAML structure patterns
- **HTML** (`text/html`) - Detected from HTML doctype and tags
- **CSV** (`text/csv`) - Detected from comma-separated value patterns
- **Plain Text** (`text/plain`) - Fallback for unrecognized formats

## Content Type Auto-Detection

FastMarkDocs automatically detects content types based on the structure and syntax of your response examples:

### JSON Detection
```markdown
### Response Examples

```json
{
  "status": "success",
  "data": {
    "items": [],
    "count": 0
  }
}
```
```

### Prometheus Metrics Detection
```markdown
### Response Examples

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
```

### XML Detection
```markdown
### Response Examples

```xml
<?xml version="1.0" encoding="UTF-8"?>
<response>
  <status>success</status>
  <data>
    <items></items>
    <count>0</count>
  </data>
</response>
```
```

### YAML Detection
```markdown
### Response Examples

```yaml
status: success
data:
  items: []
  count: 0
features:
  - authentication
  - logging
```
```

### CSV Detection
```markdown
### Response Examples

```csv
name,age,department,salary
John Doe,30,Engineering,75000
Jane Smith,28,Marketing,65000
Bob Johnson,35,Sales,70000
```
```

## Multiple Content Types

You can document multiple content types for the same endpoint by providing multiple response examples:

```markdown
## GET /data

Get data in various formats based on Accept header.

### Response Examples

**JSON Response (200 OK)**:
```json
{
  "status": "success",
  "data": {"items": [], "count": 0}
}
```

**XML Response (200 OK)**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<response>
  <status>success</status>
  <data>
    <items></items>
    <count>0</count>
  </data>
</response>
```

**Error Response (400 Bad Request)**:
```json
{
  "error": "Invalid request format",
  "code": 400
}
```
```

## OpenAPI Schema Generation

FastMarkDocs automatically generates appropriate OpenAPI schemas for different content types:

### JSON Content
- **Schema Type**: `object` or `array` based on content
- **Examples**: Full JSON structure preserved
- **Content-Type**: `application/json`

### Text-Based Content (Prometheus, Plain Text, CSV)
- **Schema Type**: `string`
- **Examples**: Raw text content preserved
- **Content-Type**: Specific MIME type (e.g., `text/plain; version=0.0.4` for Prometheus)

### XML Content
- **Schema Type**: `string` with `format: xml`
- **Examples**: Raw XML content preserved
- **Content-Type**: `application/xml`

### YAML Content
- **Schema Type**: `string` with `format: yaml`
- **Examples**: Raw YAML content preserved (or parsed structure if PyYAML available)
- **Content-Type**: `application/yaml`

## Configuration Options

You can configure multi-format support through `OpenAPIEnhancementConfig`:

```python
from fastmarkdocs.types import OpenAPIEnhancementConfig

config = OpenAPIEnhancementConfig(
    # Enable/disable content type auto-detection
    content_type_detection=True,
    
    # Preserve raw content alongside parsed content
    preserve_raw_content=True,
    
    # Validate content format during processing
    validate_content_format=True,
    
    # Specify supported content types
    supported_content_types=[
        "application/json",
        "text/plain",
        "text/plain; version=0.0.4",  # Prometheus
        "application/xml",
        "application/yaml",
        "text/html",
        "text/csv"
    ]
)
```

## Best Practices

### 1. Use Appropriate Code Block Languages
While FastMarkDocs auto-detects content types, using appropriate language specifiers in code blocks improves readability:

```markdown
```json
{"status": "success"}
```

```xml
<?xml version="1.0"?>
<response>...</response>
```

```yaml
status: success
```
```

### 2. Provide Multiple Examples
For endpoints that support multiple formats, document the most common ones:

```markdown
### Response Examples

**JSON Format**:
```json
{"data": [...]}
```

**CSV Format**:
```csv
name,value
item1,100
```
```

### 3. Include Error Examples
Document error responses in the same format as success responses:

```markdown
**Success Response (200 OK)**:
```json
{"status": "success", "data": {...}}
```

**Error Response (400 Bad Request)**:
```json
{"error": "Invalid input", "code": 400}
```
```

### 4. Prometheus Metrics Guidelines
For Prometheus metrics endpoints:
- Include `# HELP` and `# TYPE` comments
- Show realistic metric values
- Include multiple metric types (counters, gauges, histograms)

```markdown
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{method="GET",status="200"} 1234
api_requests_total{method="POST",status="201"} 567

# HELP api_request_duration_seconds Request duration
# TYPE api_request_duration_seconds histogram
api_request_duration_seconds_bucket{le="0.1"} 100
api_request_duration_seconds_bucket{le="0.5"} 200
api_request_duration_seconds_bucket{le="+Inf"} 250
```
```

## Troubleshooting

### Content Type Not Detected
If auto-detection fails:
1. Check the content format matches expected patterns
2. Ensure proper syntax (valid JSON, XML declarations, etc.)
3. Use explicit language specifiers in code blocks
4. Verify content isn't empty or malformed

### YAML Parsing Issues
For YAML content:
- Install PyYAML for full parsing support: `pip install PyYAML`
- Without PyYAML, content is stored as raw text
- Ensure proper YAML indentation and syntax

### Prometheus Metrics Not Recognized
Ensure metrics include:
- `# HELP` comments describing metrics
- `# TYPE` comments specifying metric types
- Proper metric naming and label syntax

## Migration from JSON-Only

Existing JSON-only documentation continues to work without changes. The enhanced system is backward compatible and only adds new capabilities for non-JSON content types.

To take advantage of multi-format support:
1. Add response examples in your desired formats
2. Use appropriate code block languages
3. Let FastMarkDocs auto-detect content types
4. Verify OpenAPI schema generation includes all formats

## Examples in Practice

### Metrics Endpoint
```markdown
## GET /metrics

Retrieve Prometheus-formatted metrics.

### Response Examples

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET"} 1027
http_requests_total{method="POST"} 3

# HELP http_request_duration_seconds HTTP request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 1000
http_request_duration_seconds_bucket{le="0.5"} 1020
http_request_duration_seconds_bucket{le="+Inf"} 1027
```

Section: Metrics
```

### Configuration Endpoint
```markdown
## GET /config

Get application configuration.

### Response Examples

**YAML Format**:
```yaml
server:
  host: localhost
  port: 8080
database:
  url: postgresql://localhost/mydb
  pool_size: 10
```

**JSON Format**:
```json
{
  "server": {
    "host": "localhost",
    "port": 8080
  },
  "database": {
    "url": "postgresql://localhost/mydb",
    "pool_size": 10
  }
}
```

Section: Configuration
```

This multi-format support makes FastMarkDocs suitable for documenting a wide variety of APIs beyond traditional REST JSON APIs, including metrics endpoints, configuration APIs, data export endpoints, and more.
