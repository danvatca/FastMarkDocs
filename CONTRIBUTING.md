# Contributing to FastMarkDocs

Thank you for your interest in contributing to FastMarkDocs! This document provides guidelines and information for contributors.

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [dan@danvatca.com](mailto:dan@danvatca.com).

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Your environment (OS, Python version, library version)
- Code samples that demonstrate the issue

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- A clear and descriptive title
- A detailed description of the proposed enhancement
- Use cases and examples
- Any relevant mockups or code samples

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Install dependencies**: `poetry install`
3. **Make your changes** following the coding standards
4. **Add tests** for your changes
5. **Run the test suite**: `poetry run python -m pytest`
6. **Run linting**: `poetry run black . && poetry run ruff check .`
7. **Update documentation** if needed
8. **Commit your changes** with a clear commit message
9. **Push to your fork** and submit a pull request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Poetry for dependency management

### Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/fastmarkdocs.git
cd fastmarkdocs

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run tests
poetry run python -m pytest

# Run linting
poetry run black .
poetry run ruff check .
```

## Coding Standards

### Code Style

- Use [Black](https://black.readthedocs.io/) for code formatting
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use [Ruff](https://docs.astral.sh/ruff/) for linting
- Use type hints for all function parameters and return values

### Testing

- Write tests for all new functionality
- Maintain or improve test coverage
- Use descriptive test names
- Follow the existing test structure (unit tests in `tests/unit/`, integration tests in `tests/integration/`)

### Documentation

- Update docstrings for any modified functions/classes
- Update the README if adding new features
- Add examples for new functionality
- Keep documentation clear and concise

## Project Structure

```
fastmarkdocs/
├── src/fastmarkdocs/    # Main package
│   ├── __init__.py              # Public API
│   ├── documentation_loader.py  # Markdown parsing
│   ├── code_samples.py         # Code generation
│   ├── openapi_enhancer.py     # OpenAPI enhancement
│   ├── types.py                # Type definitions
│   ├── utils.py                # Utility functions
│   └── exceptions.py           # Custom exceptions
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test fixtures
├── examples/                   # Usage examples
└── docs/                       # Documentation
```

## Commit Message Guidelines

Use clear and meaningful commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Examples:
```
Add support for TypeScript code generation

Fix markdown parsing for nested code blocks

Update documentation for custom templates

Closes #123
```

## Release Process

Releases are automated through GitHub Actions:

1. Create a new release on GitHub with a semantic version tag (e.g., `v1.2.3`)
2. The CI/CD pipeline will automatically:
   - Run all tests
   - Build the package
   - Publish to PyPI
   - Update the changelog

## Getting Help

- Check the [documentation](https://github.com/danvatca/fastmarkdocs)
- Search existing [issues](https://github.com/danvatca/fastmarkdocs/issues)
- Create a new issue for bugs or feature requests
- Contact the maintainer: [dan@danvatca.com](mailto:dan@danvatca.com)

## Recognition

Contributors will be recognized in the project's README and release notes. Thank you for helping make FastMarkDocs better! 