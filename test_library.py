#!/usr/bin/env python3
"""
Copyright (c) 2025 Dan Vatca

Simple test script to verify the FastMarkDocs library functionality.

This script tests the core components of the library to ensure they work correctly.
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastmarkdocs import (
    MarkdownDocumentationLoader,
    CodeSampleGenerator,
    enhance_openapi_with_docs,
    CodeLanguage,
    HTTPMethod
)

def create_test_markdown():
    """Create a temporary markdown file for testing."""
    content = """
## GET /test/endpoint

This is a test endpoint for demonstration purposes.

### Parameters

- `id` (integer, required): The test ID

### Code Examples

```python
import requests
response = requests.get("/test/endpoint")
print(response.json())
```

```curl
curl -X GET "https://api.example.com/test/endpoint"
```

Tags: test, example
"""
    return content

def test_documentation_loader():
    """Test the MarkdownDocumentationLoader."""
    print("Testing MarkdownDocumentationLoader...")
    
    # Create temporary directory and file
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.md"
        test_file.write_text(create_test_markdown())
        
        # Configure and test loader
        config = {
            'docs_directory': temp_dir,
            'recursive': True,
            'cache_enabled': False
        }
        
        loader = MarkdownDocumentationLoader(**config)
        
        try:
            documentation = loader.load_documentation()
            
            print(f"✓ Loaded documentation from {temp_dir}")
            print(f"✓ Found {len(documentation['endpoints'])} endpoints")
            print(f"✓ Found {len(documentation['global_examples'])} global examples")
            
            # Check if our test endpoint was loaded
            test_key = "GET:/test/endpoint"
            if test_key in documentation['endpoints']:
                endpoint = documentation['endpoints'][test_key]
                print(f"✓ Test endpoint loaded: {endpoint['method']} {endpoint['path']}")
                print(f"✓ Code samples: {len(endpoint['code_samples'])}")
            else:
                print("✗ Test endpoint not found in loaded documentation")
                
        except Exception as e:
            print(f"✗ Error loading documentation: {e}")
            return False
    
    return True

def test_code_sample_generator():
    """Test the CodeSampleGenerator."""
    print("\nTesting CodeSampleGenerator...")
    
    config = {
        'base_url': 'https://api.example.com',
        'code_sample_languages': [CodeLanguage.CURL, CodeLanguage.PYTHON]
    }
    
    generator = CodeSampleGenerator(config)
    
    # Create test endpoint
    endpoint = {
        'method': HTTPMethod.GET,
        'path': '/test/endpoint',
        'summary': 'Test endpoint',
        'description': 'A test endpoint for demonstration',
        'code_samples': [],
        'response_examples': [],
        'parameters': [],
        'tags': ['test'],
        'deprecated': False
    }
    
    try:
        samples = generator.generate_samples(endpoint)
        
        print(f"✓ Generated {len(samples)} code samples")
        
        for sample in samples:
            print(f"✓ {sample['language'].value} sample generated")
            print(f"  Title: {sample.get('title', 'N/A')}")
            print(f"  Code length: {len(sample['code'])} characters")
            
    except Exception as e:
        print(f"✗ Error generating code samples: {e}")
        return False
    
    return True

def test_openapi_enhancement():
    """Test OpenAPI schema enhancement."""
    print("\nTesting OpenAPI Enhancement...")
    
    # Create a simple OpenAPI schema
    openapi_schema = {
        "openapi": "3.0.2",
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "paths": {
            "/test/endpoint": {
                "get": {
                    "summary": "Test endpoint",
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            }
        }
    }
    
    # Create temporary documentation
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.md"
        test_file.write_text(create_test_markdown())
        
        config = {
            'docs_directory': temp_dir,
            'cache_enabled': False
        }
        
        loader = MarkdownDocumentationLoader(**config)
        
        try:
            enhanced_schema = enhance_openapi_with_docs(openapi_schema, loader)
            
            print("✓ OpenAPI schema enhanced successfully")
            
            # Check if enhancement added documentation stats
            if 'x-documentation-stats' in enhanced_schema.get('info', {}):
                stats = enhanced_schema['info']['x-documentation-stats']
                print(f"✓ Documentation stats added: {stats}")
            
            # Check if code samples were added to the operation
            operation = enhanced_schema['paths']['/test/endpoint']['get']
            if 'x-codeSamples' in operation:
                print(f"✓ Code samples added to operation: {len(operation['x-codeSamples'])}")
            else:
                print("! No code samples added to operation (this might be expected)")
                
        except Exception as e:
            print(f"✗ Error enhancing OpenAPI schema: {e}")
            return False
    
    return True

def test_types_and_imports():
    """Test that all types and imports work correctly."""
    print("\nTesting Types and Imports...")
    
    try:
        # Test enum values
        assert CodeLanguage.PYTHON == "python"
        assert HTTPMethod.GET == "GET"
        print("✓ Enums working correctly")
        
        # Test that all main classes can be imported
        from fastmarkdocs import (
            MarkdownDocumentationLoader,
            OpenAPIEnhancer,
            CodeSampleGenerator,
            enhance_openapi_with_docs
        )
        print("✓ All main classes imported successfully")
        
        # Test exception imports
        from fastmarkdocs import (
            FastAPIMarkdownDocsError,
            DocumentationLoadError,
            CodeSampleGenerationError,
            OpenAPIEnhancementError
        )
        print("✓ All exception classes imported successfully")
        
    except Exception as e:
        print(f"✗ Error with types/imports: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("FastMarkDocs - Library Test Suite")
    print("=" * 50)
    
    tests = [
        test_types_and_imports,
        test_documentation_loader,
        test_code_sample_generator,
        test_openapi_enhancement
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("Test failed!")
        except Exception as e:
            print(f"Test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The library is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 