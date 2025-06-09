---
layout: default
title: FastMarkDocs
description: Enhanced OpenAPI documentation generation from markdown files for FastAPI applications
nav_exclude: true
---

# FastMarkDocs

**Enhanced OpenAPI documentation generation from markdown files for FastAPI applications**

[![PyPI version](https://badge.fury.io/py/fastmarkdocs.svg)](https://badge.fury.io/py/fastmarkdocs)
[![Python Support](https://img.shields.io/pypi/pyversions/fastmarkdocs.svg)](https://pypi.org/project/fastmarkdocs/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/danvatca/fastmarkdocs/workflows/CI/badge.svg)](https://github.com/danvatca/fastmarkdocs/actions)
[![codecov](https://codecov.io/gh/danvatca/FastMarkDocs/branch/main/graph/badge.svg)](https://codecov.io/gh/danvatca/FastMarkDocs)

FastMarkDocs is a powerful library that transforms your API documentation workflow by allowing you to write beautiful, maintainable markdown files that automatically enhance your FastAPI OpenAPI schemas with rich content, multi-language code samples, and comprehensive examples.

## ✨ Key Features

- **📝 Markdown-First**: Write documentation in familiar markdown format
- **🔧 OpenAPI Enhancement**: Automatically enhance your OpenAPI/Swagger schemas
- **🌍 Multi-language Code Samples**: Generate code examples in Python, JavaScript, TypeScript, Go, Java, PHP, Ruby, C#, and cURL
- **🎨 Customizable Templates**: Use custom templates for code generation
- **⚡ High Performance**: Built-in caching and optimized processing
- **🧪 Well Tested**: Comprehensive test suite with 100+ tests
- **🔒 Production Ready**: Comprehensive error handling and validation

## 🚀 Quick Start

### Installation

```bash
pip install fastmarkdocs
```

### Basic Usage

```python
from fastapi import FastAPI
from fastmarkdocs import enhance_openapi_with_docs

app = FastAPI()

# Enhance your OpenAPI schema with markdown documentation
enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=app.openapi(),
    docs_directory="docs/api",
    base_url="https://api.example.com"
)

# Update your app's OpenAPI schema
app.openapi_schema = enhanced_schema
```

### Documentation Structure

Create markdown files in your docs directory:

```
docs/api/
├── users.md
├── authentication.md
└── orders.md
```

Example markdown file (`users.md`):

```markdown
# User Management API

## GET /users

Retrieve a list of all users in the system.

### Parameters
- `page` (integer, optional): Page number for pagination (default: 1)
- `limit` (integer, optional): Number of users per page (default: 10)

### Code Examples

```python
import requests
response = requests.get("https://api.example.com/users")
users = response.json()
```

```javascript
const response = await fetch('https://api.example.com/users');
const users = await response.json();
```
```

## 📚 Documentation

- **[Getting Started](getting-started.html)** - Installation and basic setup
- **[User Guide](user-guide.html)** - Comprehensive usage guide
- **[API Reference](api-reference.html)** - Complete API documentation
- **[Examples](examples.html)** - Real-world examples and tutorials
- **[Advanced Usage](advanced.html)** - Advanced features and customization

## 🎯 Use Cases

### API Documentation Teams
Transform your markdown documentation into rich, interactive API docs with automatic code sample generation.

### FastAPI Developers
Enhance your existing FastAPI applications with comprehensive documentation without changing your code structure.

### Technical Writers
Write documentation in markdown and automatically generate code samples in multiple programming languages.

### DevOps Teams
Integrate documentation generation into your CI/CD pipeline with automated testing and validation.

## 🌟 What Makes FastMarkDocs Special?

### Markdown-Driven Approach
Unlike other documentation tools that require you to learn new formats or DSLs, FastMarkDocs works with standard markdown files that your team already knows how to write.

### Automatic Code Generation
Generate code samples in 9+ programming languages automatically from your endpoint definitions, with support for custom templates and authentication schemes.

### FastAPI Integration
Seamlessly integrates with FastAPI's existing OpenAPI generation, enhancing rather than replacing your current documentation workflow.

### Production Ready
Built with enterprise needs in mind, featuring comprehensive error handling, caching, validation, and extensive test coverage.

## 🚀 Getting Started

Ready to enhance your API documentation? Check out our [Getting Started Guide](getting-started.html) for step-by-step instructions.

## 📖 Learn More

- [View on GitHub](https://github.com/danvatca/fastmarkdocs)
- [PyPI Package](https://pypi.org/project/fastmarkdocs/)
- [Report Issues](https://github.com/danvatca/fastmarkdocs/issues)
- [Contribute](https://github.com/danvatca/fastmarkdocs/blob/main/CONTRIBUTING.md)

## 📄 License

FastMarkDocs is released under the [MIT License](https://github.com/danvatca/fastmarkdocs/blob/main/LICENSE). 