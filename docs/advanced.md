# Advanced Guide

This guide covers advanced usage patterns, performance optimization, custom implementations, and production deployment scenarios for FastMarkDocs.

## Table of Contents

- [Advanced Configuration](#advanced-configuration)
- [Custom Templates](#custom-templates)
- [Performance Optimization](#performance-optimization)
- [Error Handling](#error-handling)
- [Microservices Integration](#microservices-integration)
- [Production Deployment](#production-deployment)
- [Monitoring and Observability](#monitoring-and-observability)
- [Security Considerations](#security-considerations)
- [Extending FastMarkDocs](#extending-fastmarkdocs)

## Advanced Configuration

### Environment-Based Configuration

Create flexible configurations that adapt to different environments:

```python
import os
from typing import Dict, Any
from fastmarkdocs import (
    MarkdownDocumentationLoader,
    OpenAPIEnhancer,
    CodeLanguage
)

class DocumentationConfig:
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.docs_directory = os.getenv("DOCS_DIR", "docs/api")
        self.base_url = self._get_base_url()
        self.cache_enabled = self.environment == "production"
        self.cache_ttl = int(os.getenv("DOCS_CACHE_TTL", "3600"))
        
    def _get_base_url(self) -> str:
        env_urls = {
            "development": "http://localhost:8000",
            "staging": "https://staging-api.example.com",
            "production": "https://api.example.com"
        }
        return env_urls.get(self.environment, "https://api.example.com")
    
    def get_loader_config(self) -> Dict[str, Any]:
        return {
            "docs_directory": self.docs_directory,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "recursive": True,
            "supported_languages": [
                CodeLanguage.CURL,
                CodeLanguage.PYTHON,
                CodeLanguage.JAVASCRIPT
            ]
        }
    
    def get_enhancer_config(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url,
            "include_code_samples": True,
            "include_response_examples": True,
            "custom_headers": self._get_custom_headers()
        }
    
    def _get_custom_headers(self) -> Dict[str, str]:
        headers = {"User-Agent": "FastMarkDocs/1.0"}
        
        if api_key := os.getenv("API_KEY"):
            headers["X-API-Key"] = api_key
        
        if auth_token := os.getenv("AUTH_TOKEN"):
            headers["Authorization"] = f"Bearer {auth_token}"
            
        return headers

# Usage
config = DocumentationConfig()
loader = MarkdownDocumentationLoader(**config.get_loader_config())
enhancer = OpenAPIEnhancer(**config.get_enhancer_config())
```

### Multi-Language Documentation

Support multiple languages in your documentation:

```python
from fastmarkdocs import MarkdownDocumentationLoader
import os

class MultiLanguageDocumentationLoader:
    def __init__(self, base_docs_dir: str, default_language: str = "en"):
        self.base_docs_dir = base_docs_dir
        self.default_language = default_language
        self.loaders = {}
    
    def get_loader(self, language: str = None) -> MarkdownDocumentationLoader:
        lang = language or self.default_language
        
        if lang not in self.loaders:
            docs_dir = os.path.join(self.base_docs_dir, lang)
            self.loaders[lang] = MarkdownDocumentationLoader(
                docs_directory=docs_dir,
                cache_enabled=True,
                cache_ttl=3600
            )
        
        return self.loaders[lang]
    
    def load_documentation(self, language: str = None):
        loader = self.get_loader(language)
        return loader.load_documentation()

# Directory structure:
# docs/
# ├── en/
# │   ├── users.md
# │   └── auth.md
# ├── es/
# │   ├── users.md
# │   └── auth.md
# └── fr/
#     ├── users.md
#     └── auth.md

multi_loader = MultiLanguageDocumentationLoader("docs")
en_docs = multi_loader.load_documentation("en")
es_docs = multi_loader.load_documentation("es")
```

## Custom Templates

### Advanced Template System

Create sophisticated code generation templates:

```python
from fastmarkdocs import CodeSampleGenerator, CodeLanguage
from string import Template

class AdvancedCodeSampleGenerator(CodeSampleGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_templates = self._load_advanced_templates()
    
    def _load_advanced_templates(self):
        return {
            CodeLanguage.PYTHON: Template("""
# ${endpoint_description}
import httpx
import asyncio
from typing import Optional, Dict, Any

class ${service_name}Client:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.headers = {"User-Agent": "FastMarkDocs-Client/1.0"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    async def ${method_name}(self${parameters}) -> Dict[str, Any]:
        \"\"\"${endpoint_summary}\"\"\"
        async with httpx.AsyncClient() as client:
            response = await client.${http_method}(
                f"{self.base_url}${path}",
                headers=self.headers${request_body}
            )
            response.raise_for_status()
            return response.json()

# Usage example
async def main():
    client = ${service_name}Client("${base_url}", "your-api-key")
    result = await client.${method_name}(${example_params})
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
"""),
            
            CodeLanguage.TYPESCRIPT: Template("""
// ${endpoint_description}
interface ${response_type} {
  // Define your response type here
  [key: string]: any;
}

class ${service_name}Client {
  private baseUrl: string;
  private headers: Record<string, string>;

  constructor(baseUrl: string, apiKey?: string) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Content-Type': 'application/json',
      'User-Agent': 'FastMarkDocs-Client/1.0'
    };
    
    if (apiKey) {
      this.headers['Authorization'] = `Bearer $${apiKey}`;
    }
  }

  async ${method_name}(${parameters}): Promise<${response_type}> {
    const response = await fetch(`$${this.baseUrl}${path}`, {
      method: '${http_method_upper}',
      headers: this.headers${request_body}
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: $${response.status}`);
    }

    return response.json();
  }
}

// Usage example
const client = new ${service_name}Client('${base_url}', 'your-api-key');
client.${method_name}(${example_params})
  .then(result => console.log(result))
  .catch(error => console.error('Error:', error));
""")
        }
    
    def generate_advanced_sample(self, endpoint, language: CodeLanguage):
        template = self.custom_templates.get(language)
        if not template:
            return super().generate_samples_for_endpoint(endpoint)
        
        # Extract template variables from endpoint
        variables = self._extract_template_variables(endpoint)
        
        # Generate code from template
        code = template.safe_substitute(**variables)
        
        return [{
            'language': language,
            'code': code,
            'title': f'{language.value.title()} Client Example'
        }]
    
    def _extract_template_variables(self, endpoint):
        # Extract and process endpoint information for templates
        service_name = self._extract_service_name(endpoint.path)
        method_name = self._generate_method_name(endpoint)
        
        return {
            'endpoint_description': endpoint.description or endpoint.summary,
            'endpoint_summary': endpoint.summary or 'API endpoint',
            'service_name': service_name,
            'method_name': method_name,
            'http_method': endpoint.method.value.lower(),
            'http_method_upper': endpoint.method.value.upper(),
            'path': endpoint.path,
            'base_url': self.base_url,
            'parameters': self._generate_parameters(endpoint),
            'request_body': self._generate_request_body(endpoint),
            'example_params': self._generate_example_params(endpoint),
            'response_type': self._generate_response_type(endpoint)
        }
```

### Template Inheritance

Create a template inheritance system:

```python
class TemplateManager:
    def __init__(self):
        self.base_templates = self._load_base_templates()
        self.custom_templates = {}
    
    def register_template(self, language: CodeLanguage, template: str, extends: str = None):
        if extends and extends in self.base_templates:
            # Merge with base template
            base = self.base_templates[extends]
            merged = self._merge_templates(base, template)
            self.custom_templates[language] = merged
        else:
            self.custom_templates[language] = template
    
    def get_template(self, language: CodeLanguage) -> str:
        return self.custom_templates.get(language) or self.base_templates.get(language)
    
    def _merge_templates(self, base: str, custom: str) -> str:
        # Implement template merging logic
        pass
```

## Performance Optimization

### Caching Strategies

Implement advanced caching mechanisms:

```python
import redis
import pickle
import hashlib
from typing import Optional, Any
from fastmarkdocs import DocumentationData

class RedisDocumentationCache:
    def __init__(self, redis_url: str = "redis://localhost:6379", ttl: int = 3600):
        self.redis_client = redis.from_url(redis_url)
        self.ttl = ttl
    
    def _generate_key(self, docs_directory: str, config_hash: str) -> str:
        return f"fastmarkdocs:{hashlib.md5(f'{docs_directory}:{config_hash}'.encode()).hexdigest()}"
    
    def get(self, docs_directory: str, config_hash: str) -> Optional[DocumentationData]:
        key = self._generate_key(docs_directory, config_hash)
        cached_data = self.redis_client.get(key)
        
        if cached_data:
            return pickle.loads(cached_data)
        return None
    
    def set(self, docs_directory: str, config_hash: str, data: DocumentationData):
        key = self._generate_key(docs_directory, config_hash)
        serialized_data = pickle.dumps(data)
        self.redis_client.setex(key, self.ttl, serialized_data)
    
    def invalidate(self, docs_directory: str = None):
        if docs_directory:
            pattern = f"fastmarkdocs:*{docs_directory}*"
        else:
            pattern = "fastmarkdocs:*"
        
        for key in self.redis_client.scan_iter(match=pattern):
            self.redis_client.delete(key)

class CachedMarkdownDocumentationLoader(MarkdownDocumentationLoader):
    def __init__(self, *args, cache_backend=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_backend = cache_backend or RedisDocumentationCache()
    
    def load_documentation(self) -> DocumentationData:
        config_hash = self._generate_config_hash()
        
        # Try cache first
        cached_data = self.cache_backend.get(self.docs_directory, config_hash)
        if cached_data:
            return cached_data
        
        # Load and cache
        data = super().load_documentation()
        self.cache_backend.set(self.docs_directory, config_hash, data)
        
        return data
    
    def _generate_config_hash(self) -> str:
        config_str = f"{self.supported_languages}:{self.file_patterns}:{self.recursive}"
        return hashlib.md5(config_str.encode()).hexdigest()
```

### Lazy Loading

Implement lazy loading for large documentation sets:

```python
from typing import Dict, Iterator
import os
from pathlib import Path

class LazyDocumentationLoader:
    def __init__(self, docs_directory: str):
        self.docs_directory = Path(docs_directory)
        self._file_cache: Dict[str, Any] = {}
        self._loaded_files: set = set()
    
    def iter_endpoints(self) -> Iterator[EndpointDocumentation]:
        """Lazily yield endpoints as they're needed."""
        for md_file in self._discover_files():
            if md_file not in self._loaded_files:
                endpoints = self._load_file_endpoints(md_file)
                self._loaded_files.add(md_file)
                yield from endpoints
    
    def get_endpoint(self, method: str, path: str) -> Optional[EndpointDocumentation]:
        """Load a specific endpoint on demand."""
        endpoint_key = f"{method}:{path}"
        
        # Check if already loaded
        if endpoint_key in self._file_cache:
            return self._file_cache[endpoint_key]
        
        # Search through files
        for endpoint in self.iter_endpoints():
            key = f"{endpoint.method}:{endpoint.path}"
            self._file_cache[key] = endpoint
            
            if key == endpoint_key:
                return endpoint
        
        return None
    
    def _discover_files(self) -> List[Path]:
        """Discover markdown files without loading them."""
        return list(self.docs_directory.rglob("*.md"))
    
    def _load_file_endpoints(self, file_path: Path) -> List[EndpointDocumentation]:
        """Load endpoints from a specific file."""
        # Implementation for loading specific file
        pass
```

### Parallel Processing

Process multiple documentation files in parallel:

```python
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

class ParallelDocumentationLoader:
    def __init__(self, docs_directory: str, max_workers: int = 4):
        self.docs_directory = docs_directory
        self.max_workers = max_workers
    
    async def load_documentation_async(self) -> DocumentationData:
        """Load documentation using async/await for I/O operations."""
        files = self._discover_markdown_files()
        
        # Process files in parallel
        tasks = [self._process_file_async(file_path) for file_path in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_endpoints = []
        for result in results:
            if isinstance(result, Exception):
                print(f"Error processing file: {result}")
                continue
            all_endpoints.extend(result)
        
        return DocumentationData(endpoints=all_endpoints)
    
    async def _process_file_async(self, file_path: str) -> List[EndpointDocumentation]:
        """Process a single file asynchronously."""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Use thread pool for CPU-intensive parsing
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            endpoints = await loop.run_in_executor(
                executor, 
                self._parse_markdown_content, 
                content
            )
        
        return endpoints
    
    def _parse_markdown_content(self, content: str) -> List[EndpointDocumentation]:
        """Parse markdown content (CPU-intensive operation)."""
        # Implementation for parsing markdown
        pass
```

## Error Handling

### Comprehensive Error Handling

Implement robust error handling with detailed logging:

```python
import logging
from typing import Optional, Dict, Any
from fastmarkdocs import DocumentationLoadError
from fastmarkdocs.exceptions import FastAPIMarkdownDocsError

class RobustDocumentationLoader:
    def __init__(self, docs_directory: str, fallback_enabled: bool = True):
        self.docs_directory = docs_directory
        self.fallback_enabled = fallback_enabled
        self.logger = logging.getLogger(__name__)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def load_documentation_with_fallback(self) -> DocumentationData:
        """Load documentation with comprehensive error handling."""
        try:
            return self._load_documentation_safe()
        except DocumentationLoadError as e:
            self.logger.error(f"Documentation loading failed: {e}")
            if self.fallback_enabled:
                return self._create_fallback_documentation()
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during documentation loading: {e}")
            if self.fallback_enabled:
                return self._create_fallback_documentation()
            raise FastAPIMarkdownDocsError(f"Critical error: {e}")
    
    def _load_documentation_safe(self) -> DocumentationData:
        """Load documentation with detailed error tracking."""
        errors = []
        warnings = []
        endpoints = []
        
        try:
            files = self._discover_files()
            self.logger.info(f"Found {len(files)} documentation files")
            
            for file_path in files:
                try:
                    file_endpoints = self._process_file_safe(file_path)
                    endpoints.extend(file_endpoints)
                    self.logger.debug(f"Processed {file_path}: {len(file_endpoints)} endpoints")
                except Exception as e:
                    error_msg = f"Failed to process {file_path}: {e}"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)
            
            if not endpoints and errors:
                raise DocumentationLoadError(
                    self.docs_directory,
                    f"No endpoints loaded. Errors: {'; '.join(errors)}"
                )
            
            return DocumentationData(
                endpoints=endpoints,
                metadata={
                    'errors': errors,
                    'warnings': warnings,
                    'files_processed': len(files),
                    'endpoints_loaded': len(endpoints)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Critical error in documentation loading: {e}")
            raise
    
    def _create_fallback_documentation(self) -> DocumentationData:
        """Create minimal fallback documentation."""
        self.logger.info("Creating fallback documentation")
        return DocumentationData(
            endpoints=[],
            metadata={
                'fallback': True,
                'message': 'Documentation loading failed, using fallback'
            }
        )
```

### Validation and Recovery

Implement validation with automatic recovery:

```python
class ValidatingDocumentationLoader:
    def __init__(self, docs_directory: str, strict_mode: bool = False):
        self.docs_directory = docs_directory
        self.strict_mode = strict_mode
        self.validation_errors = []
    
    def load_and_validate(self) -> DocumentationData:
        """Load documentation with validation and recovery."""
        raw_data = self._load_raw_documentation()
        validated_data = self._validate_and_fix(raw_data)
        
        if self.strict_mode and self.validation_errors:
            raise ValidationError(
                "Validation failed in strict mode",
                details=self.validation_errors
            )
        
        return validated_data
    
    def _validate_and_fix(self, data: DocumentationData) -> DocumentationData:
        """Validate and attempt to fix common issues."""
        fixed_endpoints = []
        
        for endpoint in data.endpoints:
            try:
                fixed_endpoint = self._validate_endpoint(endpoint)
                fixed_endpoints.append(fixed_endpoint)
            except ValidationError as e:
                self.validation_errors.append(str(e))
                if not self.strict_mode:
                    # Attempt to fix the endpoint
                    fixed_endpoint = self._fix_endpoint(endpoint, e)
                    if fixed_endpoint:
                        fixed_endpoints.append(fixed_endpoint)
        
        return DocumentationData(
            endpoints=fixed_endpoints,
            metadata={
                **data.metadata,
                'validation_errors': self.validation_errors,
                'endpoints_fixed': len(data.endpoints) - len(fixed_endpoints)
            }
        )
    
    def _validate_endpoint(self, endpoint: EndpointDocumentation) -> EndpointDocumentation:
        """Validate a single endpoint."""
        if not endpoint.path:
            raise ValidationError("Endpoint path cannot be empty")
        
        if not endpoint.path.startswith('/'):
            raise ValidationError(f"Endpoint path must start with '/': {endpoint.path}")
        
        if not endpoint.method:
            raise ValidationError("Endpoint method cannot be empty")
        
        return endpoint
    
    def _fix_endpoint(self, endpoint: EndpointDocumentation, error: ValidationError) -> Optional[EndpointDocumentation]:
        """Attempt to fix common endpoint issues."""
        if "path must start with '/'" in str(error):
            endpoint.path = '/' + endpoint.path.lstrip('/')
            return endpoint
        
        if "method cannot be empty" in str(error):
            # Try to infer method from path or context
            endpoint.method = HTTPMethod.GET  # Default fallback
            return endpoint
        
        return None
```

## Microservices Integration

### Service Discovery Integration

Integrate with service discovery systems:

```python
import consul
from typing import Dict
from fastmarkdocs import enhance_openapi_with_docs

class ServiceDiscoveryDocumentationManager:
    def __init__(self, consul_host: str = "localhost", consul_port: int = 8500):
        self.consul = consul.Consul(host=consul_host, port=consul_port)
        self.service_docs = {}
    
    def register_service_docs(self, service_name: str, docs_directory: str, base_url: str):
        """Register documentation for a service."""
        self.service_docs[service_name] = {
            'docs_directory': docs_directory,
            'base_url': base_url
        }
        
        # Register with Consul
        self.consul.kv.put(f"docs/{service_name}/directory", docs_directory)
        self.consul.kv.put(f"docs/{service_name}/base_url", base_url)
    
    def discover_service_docs(self) -> Dict[str, Dict[str, str]]:
        """Discover documentation from all registered services."""
        services = {}
        
        # Get all documentation entries from Consul
        _, docs_data = self.consul.kv.get("docs/", recurse=True)
        
        if docs_data:
            for item in docs_data:
                key_parts = item['Key'].split('/')
                if len(key_parts) >= 3:
                    service_name = key_parts[1]
                    config_key = key_parts[2]
                    
                    if service_name not in services:
                        services[service_name] = {}
                    
                    services[service_name][config_key] = item['Value'].decode('utf-8')
        
        return services
    
    def enhance_gateway_schema(self, gateway_schema: Dict) -> Dict:
        """Enhance API gateway schema with documentation from all services."""
        services = self.discover_service_docs()
        
        for service_name, config in services.items():
            if 'directory' in config and 'base_url' in config:
                try:
                    service_schema = enhance_openapi_with_docs(
                        openapi_schema=gateway_schema,
                        docs_directory=config['directory'],
                        base_url=config['base_url']
                    )
                    gateway_schema = service_schema
                except Exception as e:
                    print(f"Failed to enhance docs for {service_name}: {e}")
        
        return gateway_schema
```

### Distributed Documentation

Manage documentation across multiple services:

```python
class DistributedDocumentationManager:
    def __init__(self):
        self.service_loaders = {}
        self.aggregated_docs = None
    
    def add_service(self, service_name: str, docs_config: Dict):
        """Add a service's documentation configuration."""
        self.service_loaders[service_name] = MarkdownDocumentationLoader(**docs_config)
    
    def load_all_documentation(self) -> Dict[str, DocumentationData]:
        """Load documentation from all registered services."""
        all_docs = {}
        
        for service_name, loader in self.service_loaders.items():
            try:
                docs = loader.load_documentation()
                all_docs[service_name] = docs
            except Exception as e:
                print(f"Failed to load docs for {service_name}: {e}")
                all_docs[service_name] = DocumentationData(endpoints=[])
        
        return all_docs
    
    def create_unified_schema(self, base_schemas: Dict[str, Dict]) -> Dict:
        """Create a unified OpenAPI schema from multiple services."""
        unified_schema = {
            "openapi": "3.0.2",
            "info": {
                "title": "Unified API Documentation",
                "version": "1.0.0"
            },
            "paths": {},
            "components": {"schemas": {}}
        }
        
        all_docs = self.load_all_documentation()
        
        for service_name, schema in base_schemas.items():
            if service_name in all_docs:
                enhanced_schema = enhance_openapi_with_docs(
                    openapi_schema=schema,
                    documentation=all_docs[service_name]
                )
                
                # Merge paths with service prefix
                for path, methods in enhanced_schema.get("paths", {}).items():
                    prefixed_path = f"/{service_name}{path}"
                    unified_schema["paths"][prefixed_path] = methods
                
                # Merge components
                if "components" in enhanced_schema:
                    for component_type, components in enhanced_schema["components"].items():
                        if component_type not in unified_schema["components"]:
                            unified_schema["components"][component_type] = {}
                        
                        for name, component in components.items():
                            prefixed_name = f"{service_name}_{name}"
                            unified_schema["components"][component_type][prefixed_name] = component
        
        return unified_schema
```

## Production Deployment

### Docker Integration

Create production-ready Docker configurations:

```dockerfile
# Dockerfile for FastMarkDocs-enhanced API
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy documentation
COPY docs/ /app/docs/

# Set environment variables
ENV DOCS_DIR=/app/docs
ENV DOCS_CACHE_TTL=7200
ENV ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment

Deploy with Kubernetes including documentation management:

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastmarkdocs-api
  labels:
    app: fastmarkdocs-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastmarkdocs-api
  template:
    metadata:
      labels:
        app: fastmarkdocs-api
    spec:
      containers:
      - name: api
        image: your-registry/fastmarkdocs-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DOCS_DIR
          value: "/app/docs"
        - name: DOCS_CACHE_TTL
          value: "7200"
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        volumeMounts:
        - name: docs-volume
          mountPath: /app/docs
          readOnly: true
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: docs-volume
        configMap:
          name: api-documentation

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-documentation
data:
  users.md: |
    # User Management API
    ## GET /api/users
    List all users in the system.
  auth.md: |
    # Authentication API
    ## POST /api/auth/login
    Authenticate a user.
```

### CI/CD Integration

Integrate documentation updates into your CI/CD pipeline:

```yaml
# .github/workflows/docs-update.yml
name: Update Documentation

on:
  push:
    paths:
      - 'docs/**'
      - 'src/**'
  pull_request:
    paths:
      - 'docs/**'

jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install fastmarkdocs
        pip install -r requirements-dev.txt
    
    - name: Validate documentation
      run: |
        python scripts/validate_docs.py
    
    - name: Test documentation loading
      run: |
        python scripts/test_docs_loading.py
    
    - name: Generate documentation preview
      run: |
        python scripts/generate_preview.py
    
    - name: Upload preview
      uses: actions/upload-artifact@v3
      with:
        name: docs-preview
        path: preview/

  deploy-docs:
    needs: validate-docs
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to production
      run: |
        # Update documentation in production environment
        kubectl rollout restart deployment/fastmarkdocs-api
```

## Monitoring and Observability

### Metrics Collection

Implement comprehensive metrics collection:

```python
import time
import logging
from prometheus_client import Counter, Histogram, Gauge
from fastmarkdocs import MarkdownDocumentationLoader

# Prometheus metrics
docs_load_duration = Histogram(
    'fastmarkdocs_load_duration_seconds',
    'Time spent loading documentation',
    ['docs_directory']
)

docs_load_counter = Counter(
    'fastmarkdocs_loads_total',
    'Total number of documentation loads',
    ['docs_directory', 'status']
)

docs_endpoints_gauge = Gauge(
    'fastmarkdocs_endpoints_total',
    'Total number of documented endpoints',
    ['docs_directory']
)

class MonitoredDocumentationLoader(MarkdownDocumentationLoader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
    
    def load_documentation(self) -> DocumentationData:
        start_time = time.time()
        
        try:
            with docs_load_duration.labels(docs_directory=self.docs_directory).time():
                data = super().load_documentation()
            
            # Record successful load
            docs_load_counter.labels(
                docs_directory=self.docs_directory,
                status='success'
            ).inc()
            
            # Update endpoint count
            docs_endpoints_gauge.labels(
                docs_directory=self.docs_directory
            ).set(len(data.endpoints))
            
            # Log performance metrics
            duration = time.time() - start_time
            self.logger.info(
                f"Documentation loaded successfully: "
                f"directory={self.docs_directory}, "
                f"endpoints={len(data.endpoints)}, "
                f"duration={duration:.2f}s"
            )
            
            return data
            
        except Exception as e:
            # Record failed load
            docs_load_counter.labels(
                docs_directory=self.docs_directory,
                status='error'
            ).inc()
            
            self.logger.error(
                f"Documentation loading failed: "
                f"directory={self.docs_directory}, "
                f"error={str(e)}"
            )
            
            raise
```

### Health Checks

Implement comprehensive health checks:

```python
from fastapi import FastAPI, HTTPException
from fastmarkdocs import MarkdownDocumentationLoader

app = FastAPI()

class HealthChecker:
    def __init__(self, docs_loader: MarkdownDocumentationLoader):
        self.docs_loader = docs_loader
    
    async def check_documentation_health(self) -> Dict[str, Any]:
        """Check if documentation can be loaded successfully."""
        try:
            start_time = time.time()
            docs = self.docs_loader.load_documentation()
            load_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "endpoints_count": len(docs.endpoints),
                "load_time_seconds": round(load_time, 3),
                "docs_directory": str(self.docs_loader.docs_directory),
                "cache_enabled": self.docs_loader.cache_enabled
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "docs_directory": str(self.docs_loader.docs_directory)
            }

health_checker = HealthChecker(MarkdownDocumentationLoader("docs"))

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "timestamp": time.time()}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including documentation status."""
    docs_health = await health_checker.check_documentation_health()
    
    overall_status = "healthy" if docs_health["status"] == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "components": {
            "documentation": docs_health
        }
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    docs_health = await health_checker.check_documentation_health()
    
    if docs_health["status"] != "healthy":
        raise HTTPException(status_code=503, detail="Documentation not ready")
    
    return {"status": "ready"}
```

---

*This advanced guide covers sophisticated usage patterns and production considerations for FastMarkDocs. For basic usage, see the [User Guide](user-guide.md).* 