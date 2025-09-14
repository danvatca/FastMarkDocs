# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2025-09-15

### Breaking Changes
- **Section-Based Documentation**: Complete transition from `Tags:` to `Section:` approach
  - **Deprecated**: `Tags:` lines in markdown documentation (still supported but deprecated)
  - **New**: `Section:` lines for organizing endpoints into documentation sections
  - **Router Tags**: Now serve as "scaffolding hints" only, ignored at runtime
  - **Single Source of Truth**: Only `Section:` lines in markdown control documentation organization

### Added
- **Intelligent Section Inference**: Automatic section assignment for endpoints during scaffolding
  - **6-Step Fallback Chain**: Endpoint tags → Router tags → Path patterns → File names → Function names → "API" default
  - **Smart Pattern Recognition**: Recognizes common patterns like `/health`, `/metrics`, `/auth`, etc.
  - **File-Based Inference**: Infers sections from file names like `health.py`, `users.py`, `metrics.py`
  - **Function-Based Inference**: Analyzes function names for patterns like `health_check`, `get_users`, etc.
- **Enhanced Linting**: New validation rules for Section-based approach
  - **Section Validation**: Ensures all documented endpoints have `Section:` defined
  - **Missing Section Detection**: Reports endpoints without proper section assignment
  - **Helpful Suggestions**: Provides recommendations for missing sections based on inference
- **Comprehensive Migration Support**
  - **Migration Guide**: Detailed documentation for transitioning from Tags to Sections
  - **Automated Scripts**: sed and Python scripts for bulk migration
  - **Backward Compatibility**: Existing `Tags:` continue to work during transition period
- **Smart Section Descriptions**: Enhanced OpenAPI schema generation
  - **Section Mapping**: Maps markdown sections to OpenAPI tags with descriptions
  - **Intelligent Grouping**: Groups related endpoints under descriptive section headers
  - **Improved Organization**: Better RapiDoc section organization and ordering

### Enhanced
- **Scaffolding (`fmd-init`)**: Dramatically improved initial documentation generation
  - **Intelligent Defaults**: Automatically suggests appropriate sections for new endpoints
  - **Context-Aware**: Uses multiple hints (path, file, function) to determine best sections
  - **Reduced Manual Work**: Minimizes need for manual section assignment
- **Documentation Loader**: Updated to process Section-based markdown
  - **Dual Support**: Handles both `Tags:` (deprecated) and `Section:` formats
  - **Enhanced Parsing**: Improved regex patterns and content processing
  - **Better Error Handling**: More robust parsing with helpful error messages
- **Testing & Quality**: Comprehensive test coverage improvements
  - **91% Test Coverage**: Significantly improved from 88.55% baseline
  - **459 Tests**: All tests passing with comprehensive behavior coverage
  - **Robust File Processing**: Tests for various file types, encoding issues, and error conditions
  - **Section Assignment Testing**: Comprehensive tests for intelligent section inference

### Technical Improvements
- **Type System**: Updated data structures for Section-based approach
  - **DocumentationData**: `tag_descriptions` → `section_descriptions`
  - **EndpointDocumentation**: `tags` → `sections` field
  - **Enhanced Type Safety**: Better type hints and validation
- **OpenAPI Enhancement**: Improved schema generation and organization
  - **Section Descriptions**: Maps sections to OpenAPI tag descriptions
  - **Better Grouping**: More logical endpoint organization in generated docs
  - **Maintained Compatibility**: OpenAPI spec still uses standard "tags" format
- **Configuration**: Prepared for `tag_order` → `sections_order` transition
  - **Future-Ready**: Infrastructure ready for configuration parameter rename
  - **Backward Compatible**: Current `tag_order` continues to work

### Documentation
- **Updated Examples**: All documentation examples now use Section-based approach
- **Migration Guide**: Comprehensive guide for transitioning existing projects
- **Enhanced README**: Updated feature descriptions and examples
- **User Guide**: Refreshed documentation with Section-focused explanations

### Benefits
- **Eliminated Duplication**: No more conflicts between router tags and documentation tags
- **Cleaner Architecture**: Clear separation between operational tags and documentation sections
- **Better Maintainability**: Single source of truth for documentation organization
- **Improved Developer Experience**: Intelligent defaults reduce manual configuration
- **Enhanced Flexibility**: Multiple fallback strategies for section determination

### Migration Path
1. Update to fastmarkdocs 0.5.0
2. Run migration scripts to convert `Tags:` to `Section:`
3. Update project configuration to use `sections_order` (when available)
4. Leverage intelligent section inference for new endpoints
5. Remove router tags used solely for documentation purposes

## [0.4.0] - 2025-01-27

### Added
- **Multi-Format Response Examples**: Comprehensive support for non-JSON response examples
  - **Automatic Content Type Detection**: Intelligently detects Prometheus metrics, XML, YAML, HTML, CSV, and plain text
  - **Prometheus Metrics Support**: Native support for `text/plain; version=0.0.4` Prometheus exposition format
  - **Enhanced ResponseExample Type**: New `content_type` and `raw_content` fields with auto-detection capabilities
  - **Flexible Content Parsing**: Handles malformed JSON gracefully with fallback to plain text
  - **OpenAPI Integration**: Generates appropriate schemas for different content types in OpenAPI spec
  - **Comprehensive Testing**: 25+ new unit tests and 8 integration tests covering all content types
  - **Backward Compatibility**: Existing JSON examples continue to work unchanged
  - **Documentation**: Complete documentation with examples for all supported formats
- **Enhanced Documentation Loader**: Improved markdown parsing with better code block handling
  - **Smart Section Splitting**: Prevents premature splitting of markdown sections within code blocks
  - **Flexible Status Code Detection**: More robust parsing of response status codes from markdown
  - **Multi-Format Processing**: Unified processing pipeline for all response content types
- **Sample Prometheus Metrics Documentation**: Added comprehensive `/metrics` endpoint example to doorman docs fixtures
  - **Realistic Prometheus Metrics**: Authentication, API usage, system performance, and security metrics
  - **Advanced Metrics Support**: Garbage collection, thread pools, disk I/O, network traffic examples
  - **Error Response Examples**: Complete 401, 403, and 503 error responses in JSON format
  - **Integration Testing**: Validates end-to-end multi-format response example processing

### Enhanced
- **Smart Tag Descriptions**: Automatically extract rich tag descriptions from markdown Overview sections
  - Parses `## Overview` sections from markdown files with full formatting support
  - Associates overview content with all tags used in the same file
  - Generates comprehensive OpenAPI tags section with rich descriptions
  - Preserves markdown formatting, emojis, and structured content
  - Works automatically with zero configuration required
  - Enhances API documentation discoverability and professional appearance
- **fmd-init**: Documentation scaffolding tool for existing FastAPI projects
  - Automatically scans Python files for FastAPI endpoints (`@app.get`, `@router.post`, etc.)
  - Extracts endpoint information including paths, methods, docstrings, and tags
  - Generates structured markdown documentation with TODO sections
  - Groups endpoints by tags or creates general API documentation
  - Supports dry-run mode, custom output directories, and JSON output
  - Includes comprehensive CLI with verbose mode and file exclusion patterns
  - Provides detailed reporting on discovered endpoints and generated files
  - Full programmatic API for integration with other tools
  - Comprehensive test suite with 48 test cases covering all functionality
  - Complete documentation with examples and best practices
- **fmd-lint**: Comprehensive documentation linter CLI tool
  - Analyzes API documentation completeness and accuracy
  - Identifies missing documentation for API endpoints
  - Detects common mistakes like path parameter mismatches
  - Finds orphaned documentation for non-existent endpoints
  - Tests enhancement process to ensure proper integration
  - Provides actionable recommendations for improvement
  - Supports both text and JSON output formats
  - Automatically exits with code 1 when issues are found (CI/CD ready)
- Initial release of FastMarkDocs
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