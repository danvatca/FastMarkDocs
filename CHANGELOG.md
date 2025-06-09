# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of FastAPI Markdown Docs
- Markdown-based API documentation enhancement for FastAPI
- Multi-language code sample generation (Python, JavaScript, TypeScript, Go, Java, PHP, Ruby, C#, cURL)
- OpenAPI schema enhancement with documentation data
- Comprehensive test suite with 116 tests and 84% coverage
- GitHub Actions CI/CD pipeline
- Automated PyPI publishing on release

### Features
- `MarkdownDocumentationLoader` for parsing markdown documentation files
- `CodeSampleGenerator` for generating code samples in multiple languages
- `OpenAPIEnhancer` for enhancing OpenAPI schemas with documentation
- Support for custom templates and authentication schemes
- Caching system for improved performance
- Thread-safe operations
- Comprehensive error handling with custom exceptions

## [0.1.0] - 2024-12-19

### Added
- Initial project structure
- Core functionality implementation
- Test suite setup
- Documentation and examples
- Poetry configuration
- Development tooling (Black, Ruff, MyPy)

### Dependencies
- fastapi >= 0.68.0
- pydantic >= 1.8.0
- mistune >= 2.0.0
- pyyaml >= 5.4.0 