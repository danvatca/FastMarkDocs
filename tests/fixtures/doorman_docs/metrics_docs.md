# Metrics and Monitoring API Documentation

## Overview

The **Metrics and Monitoring API** provides comprehensive system telemetry and performance metrics for SynetoOS Authentication Service. This API exposes metrics in Prometheus format, enabling integration with modern monitoring and alerting systems.

### 📊 **Key Metrics Categories**

**Authentication Metrics**
- Login success/failure rates and response times
- Session creation, validation, and expiration statistics
- Multi-factor authentication usage and success rates

**API Usage Metrics**
- Request rates per endpoint with HTTP status code breakdowns
- API key usage patterns and rate limiting statistics
- Bearer token validation and refresh patterns

**System Performance Metrics**
- Database connection pool utilization and query performance
- Memory usage, CPU utilization, and garbage collection statistics
- Cache hit/miss ratios for session and user data

**Security Metrics**
- Failed authentication attempts and potential security threats
- Rate limiting activations and IP blocking events
- Certificate validation and TLS handshake statistics

### 🔍 **Monitoring Integration**

The metrics endpoint is designed for seamless integration with:
- **Prometheus**: Native format support with automatic service discovery
- **Grafana**: Pre-built dashboards for authentication service monitoring
- **AlertManager**: Configurable alerts for security and performance thresholds
- **Custom Monitoring**: Standard Prometheus format for any monitoring solution

## Endpoints

### GET /metrics

**Retrieve system metrics in Prometheus format**

This endpoint exposes comprehensive system metrics in the standard Prometheus exposition format. The metrics include authentication statistics, API usage patterns, system performance indicators, and security events.

**Key Features:**
- **Standard Prometheus Format**: Compatible with all Prometheus-based monitoring tools
- **Real-time Data**: Metrics are updated in real-time as events occur
- **Comprehensive Coverage**: Includes authentication, API, system, and security metrics
- **High Performance**: Optimized for frequent scraping with minimal system impact

**Security Considerations:**
- This endpoint may expose sensitive operational information
- Access should be restricted to monitoring systems and authorized personnel
- Consider network-level restrictions for production deployments

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `advanced` | boolean | No | Include advanced system metrics (default: false) |

**Response Format:**
- **Content-Type**: `text/plain; version=0.0.4; charset=utf-8`
- **Format**: Prometheus exposition format with metric families

#### Response Examples

**Success (200 OK):**

```prometheus
# HELP syneto_auth_login_attempts_total Total number of login attempts
# TYPE syneto_auth_login_attempts_total counter
syneto_auth_login_attempts_total{method="password",result="success"} 1247
syneto_auth_login_attempts_total{method="password",result="failure"} 23
syneto_auth_login_attempts_total{method="pin",result="success"} 89
syneto_auth_login_attempts_total{method="pin",result="failure"} 2

# HELP syneto_auth_sessions_active Current number of active sessions
# TYPE syneto_auth_sessions_active gauge
syneto_auth_sessions_active{type="user"} 42
syneto_auth_sessions_active{type="support"} 3

# HELP syneto_auth_session_duration_seconds Session duration in seconds
# TYPE syneto_auth_session_duration_seconds histogram
syneto_auth_session_duration_seconds_bucket{le="300"} 156
syneto_auth_session_duration_seconds_bucket{le="1800"} 892
syneto_auth_session_duration_seconds_bucket{le="3600"} 1456
syneto_auth_session_duration_seconds_bucket{le="7200"} 1678
syneto_auth_session_duration_seconds_bucket{le="14400"} 1789
syneto_auth_session_duration_seconds_bucket{le="+Inf"} 1834
syneto_auth_session_duration_seconds_sum 2847392.5
syneto_auth_session_duration_seconds_count 1834

# HELP syneto_auth_api_requests_total Total number of API requests
# TYPE syneto_auth_api_requests_total counter
syneto_auth_api_requests_total{endpoint="/v1/session",method="POST",status="200"} 1247
syneto_auth_api_requests_total{endpoint="/v1/session",method="POST",status="401"} 23
syneto_auth_api_requests_total{endpoint="/v1/session",method="DELETE",status="200"} 1156
syneto_auth_api_requests_total{endpoint="/users",method="GET",status="200"} 3456
syneto_auth_api_requests_total{endpoint="/users",method="POST",status="201"} 234

# HELP syneto_auth_api_request_duration_seconds API request duration in seconds
# TYPE syneto_auth_api_request_duration_seconds histogram
syneto_auth_api_request_duration_seconds_bucket{endpoint="/v1/session",method="POST",le="0.1"} 1089
syneto_auth_api_request_duration_seconds_bucket{endpoint="/v1/session",method="POST",le="0.5"} 1234
syneto_auth_api_request_duration_seconds_bucket{endpoint="/v1/session",method="POST",le="1.0"} 1267
syneto_auth_api_request_duration_seconds_bucket{endpoint="/v1/session",method="POST",le="+Inf"} 1270
syneto_auth_api_request_duration_seconds_sum{endpoint="/v1/session",method="POST"} 89.7
syneto_auth_api_request_duration_seconds_count{endpoint="/v1/session",method="POST"} 1270

# HELP syneto_auth_otp_verifications_total Total number of OTP verification attempts
# TYPE syneto_auth_otp_verifications_total counter
syneto_auth_otp_verifications_total{result="success"} 456
syneto_auth_otp_verifications_total{result="failure"} 12

# HELP syneto_auth_api_keys_active Current number of active API keys
# TYPE syneto_auth_api_keys_active gauge
syneto_auth_api_keys_active{scope="read"} 23
syneto_auth_api_keys_active{scope="write"} 8
syneto_auth_api_keys_active{scope="admin"} 3

# HELP syneto_auth_rate_limit_hits_total Total number of rate limit hits
# TYPE syneto_auth_rate_limit_hits_total counter
syneto_auth_rate_limit_hits_total{endpoint="/v1/session",limit_type="ip"} 45
syneto_auth_rate_limit_hits_total{endpoint="/v1/session",limit_type="user"} 12

# HELP syneto_auth_database_connections Current database connection pool usage
# TYPE syneto_auth_database_connections gauge
syneto_auth_database_connections{state="active"} 8
syneto_auth_database_connections{state="idle"} 12
syneto_auth_database_connections{state="waiting"} 0

# HELP syneto_auth_cache_operations_total Total number of cache operations
# TYPE syneto_auth_cache_operations_total counter
syneto_auth_cache_operations_total{operation="hit",cache="session"} 8934
syneto_auth_cache_operations_total{operation="miss",cache="session"} 234
syneto_auth_cache_operations_total{operation="hit",cache="user"} 5678
syneto_auth_cache_operations_total{operation="miss",cache="user"} 123

# HELP syneto_auth_memory_usage_bytes Current memory usage in bytes
# TYPE syneto_auth_memory_usage_bytes gauge
syneto_auth_memory_usage_bytes{type="heap"} 134217728
syneto_auth_memory_usage_bytes{type="stack"} 8388608
syneto_auth_memory_usage_bytes{type="cache"} 67108864
```

**Advanced Metrics (200 OK) - with advanced=true:**

```prometheus
# HELP syneto_auth_login_attempts_total Total number of login attempts
# TYPE syneto_auth_login_attempts_total counter
syneto_auth_login_attempts_total{method="password",result="success"} 1247
syneto_auth_login_attempts_total{method="password",result="failure"} 23
syneto_auth_login_attempts_total{method="pin",result="success"} 89
syneto_auth_login_attempts_total{method="pin",result="failure"} 2

# HELP syneto_auth_sessions_active Current number of active sessions
# TYPE syneto_auth_sessions_active gauge
syneto_auth_sessions_active{type="user"} 42
syneto_auth_sessions_active{type="support"} 3

# HELP syneto_auth_gc_duration_seconds Time spent in garbage collection
# TYPE syneto_auth_gc_duration_seconds histogram
syneto_auth_gc_duration_seconds_bucket{le="0.001"} 1234
syneto_auth_gc_duration_seconds_bucket{le="0.01"} 2345
syneto_auth_gc_duration_seconds_bucket{le="0.1"} 2456
syneto_auth_gc_duration_seconds_bucket{le="+Inf"} 2467
syneto_auth_gc_duration_seconds_sum 12.34
syneto_auth_gc_duration_seconds_count 2467

# HELP syneto_auth_thread_pool_active Current active threads in pool
# TYPE syneto_auth_thread_pool_active gauge
syneto_auth_thread_pool_active{pool="request_handler"} 16
syneto_auth_thread_pool_active{pool="background_tasks"} 4
syneto_auth_thread_pool_active{pool="database"} 8

# HELP syneto_auth_disk_io_bytes_total Total disk I/O in bytes
# TYPE syneto_auth_disk_io_bytes_total counter
syneto_auth_disk_io_bytes_total{operation="read"} 1073741824
syneto_auth_disk_io_bytes_total{operation="write"} 536870912

# HELP syneto_auth_network_bytes_total Total network traffic in bytes
# TYPE syneto_auth_network_bytes_total counter
syneto_auth_network_bytes_total{direction="in"} 2147483648
syneto_auth_network_bytes_total{direction="out"} 1073741824

# HELP syneto_auth_certificate_expiry_days Days until certificate expiry
# TYPE syneto_auth_certificate_expiry_days gauge
syneto_auth_certificate_expiry_days{cert_type="server",common_name="auth.syneto.local"} 89
syneto_auth_certificate_expiry_days{cert_type="ca",common_name="Syneto Root CA"} 1825
```

**Error Responses:**

**Unauthorized (401 Unauthorized):**
```json
{
  "detail": "Authentication required to access metrics endpoint",
  "type": "authentication_error",
  "code": "METRICS_AUTH_REQUIRED"
}
```

**Forbidden (403 Forbidden):**
```json
{
  "detail": "Insufficient permissions to access system metrics",
  "type": "authorization_error", 
  "code": "METRICS_ACCESS_DENIED"
}
```

**Service Unavailable (503 Service Unavailable):**
```json
{
  "detail": "Metrics collection temporarily unavailable",
  "type": "service_error",
  "code": "METRICS_UNAVAILABLE"
}
```

### Code Examples

**Python - Basic Metrics Collection:**
```python
import requests

# Collect basic metrics
response = requests.get('https://auth.syneto.local/metrics')
if response.status_code == 200:
    metrics_data = response.text
    print("Metrics collected successfully")
    print(f"Content-Type: {response.headers['content-type']}")
else:
    print(f"Failed to collect metrics: {response.status_code}")
```

**Python - Advanced Metrics with Authentication:**
```python
import requests

# Collect advanced metrics with API key authentication
headers = {'X-API-Key': 'your-monitoring-api-key'}
params = {'advanced': 'true'}

response = requests.get(
    'https://auth.syneto.local/metrics',
    headers=headers,
    params=params
)

if response.status_code == 200:
    print("Advanced metrics collected")
    # Parse Prometheus format or forward to monitoring system
    with open('/tmp/syneto_auth_metrics.prom', 'w') as f:
        f.write(response.text)
else:
    print(f"Error: {response.json()}")
```

**cURL - Prometheus Scraping:**
```bash
#!/bin/bash

# Basic metrics scraping for Prometheus
curl -H "X-API-Key: monitoring-key" \
     -H "Accept: text/plain" \
     "https://auth.syneto.local/metrics" \
     -o /var/lib/prometheus/syneto_auth_metrics.prom

# Advanced metrics with query parameters
curl -H "X-API-Key: monitoring-key" \
     "https://auth.syneto.local/metrics?advanced=true" \
     -o /var/lib/prometheus/syneto_auth_advanced_metrics.prom
```

**Prometheus Configuration:**
```yaml
# prometheus.yml configuration for SynetoOS Auth Service
scrape_configs:
  - job_name: 'syneto-auth'
    static_configs:
      - targets: ['auth.syneto.local:443']
    scheme: https
    metrics_path: /metrics
    params:
      advanced: ['true']
    scrape_interval: 30s
    scrape_timeout: 10s
    headers:
      X-API-Key: 'your-monitoring-api-key'
```

### Monitoring Best Practices

**Scraping Frequency:**
- **Production**: 30-60 seconds for most metrics
- **Development**: 15-30 seconds for faster feedback
- **High-load systems**: Consider 60-120 seconds to reduce overhead

**Key Metrics to Alert On:**
- `syneto_auth_login_attempts_total{result="failure"}` - High failure rates
- `syneto_auth_sessions_active` - Unusual session count patterns  
- `syneto_auth_api_request_duration_seconds` - Performance degradation
- `syneto_auth_rate_limit_hits_total` - Potential security issues
- `syneto_auth_database_connections{state="waiting"}` - Database bottlenecks

**Grafana Dashboard Queries:**
```promql
# Login success rate over time
rate(syneto_auth_login_attempts_total{result="success"}[5m])

# Average API response time
rate(syneto_auth_api_request_duration_seconds_sum[5m]) / 
rate(syneto_auth_api_request_duration_seconds_count[5m])

# Cache hit ratio
rate(syneto_auth_cache_operations_total{operation="hit"}[5m]) / 
(rate(syneto_auth_cache_operations_total{operation="hit"}[5m]) + 
 rate(syneto_auth_cache_operations_total{operation="miss"}[5m]))
```
