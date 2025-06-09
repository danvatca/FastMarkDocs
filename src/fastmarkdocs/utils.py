"""
Copyright (c) 2025 Dan Vatca

Utility functions for FastMarkDocs.

This module provides various utility functions used throughout the library
for path normalization, code sample extraction, validation, and other
common operations.
"""

import os
import re
from pathlib import Path
from typing import Any, Optional

from .types import CodeLanguage, CodeSample, ValidationError


def normalize_path(path: str, base_path: Optional[str] = None) -> str:
    """
    Normalize a file path, making it absolute and resolving any relative components.

    Args:
        path: The path to normalize
        base_path: Optional base path to resolve relative paths against

    Returns:
        Normalized absolute path
    """
    if base_path:
        path = os.path.join(base_path, path)

    return os.path.abspath(os.path.expanduser(path))


def extract_code_samples(
    markdown_content: str, supported_languages: Optional[list[CodeLanguage]] = None
) -> list[CodeSample]:
    """
    Extract code samples from markdown content.

    Args:
        markdown_content: The markdown content to parse
        supported_languages: List of supported languages to filter by

    Returns:
        List of extracted code samples

    Raises:
        ValidationException: If code samples are malformed
    """
    code_samples = []

    # Pattern to match fenced code blocks with language specification
    # Captures: language, optional title on same line (space-separated), and code content
    pattern = r"```(\w+)(?: ([^\n]+))?\n(.*?)\n```"

    for match in re.finditer(pattern, markdown_content, re.DOTALL):
        language_str = match.group(1).lower()
        title = match.group(2)
        code = match.group(3).strip()

        # Map common language aliases to our supported languages
        language_mapping = {
            "bash": "curl",  # bash blocks containing curl commands
            "shell": "curl",  # shell blocks containing curl commands
            "sh": "curl",  # sh blocks containing curl commands
            "js": "javascript",  # js alias for javascript
            "ts": "typescript",  # ts alias for typescript
            "py": "python",  # py alias for python
            "c#": "csharp",  # c# alias for csharp
        }

        # Apply language mapping
        if language_str in language_mapping:
            language_str = language_mapping[language_str]

        # Validate language
        try:
            language = CodeLanguage(language_str)
        except ValueError:
            # Skip unsupported languages
            continue

        # Filter by supported languages if provided
        if supported_languages and language not in supported_languages:
            continue

        # Extract description from preceding text if available
        description = _extract_code_description(markdown_content, match.start())

        # Create CodeSample object
        code_sample = CodeSample(language=language, code=code, description=description, title=title)

        code_samples.append(code_sample)

    return code_samples


def validate_markdown_structure(markdown_content: str, file_path: Optional[str] = None) -> list[ValidationError]:
    """
    Validate the structure of markdown documentation.

    Args:
        markdown_content: The markdown content to validate
        file_path: Optional file path for error reporting

    Returns:
        List of validation errors found
    """
    errors = []
    lines = markdown_content.split("\n")

    # Check for required sections
    has_endpoint_header = False

    for i, line in enumerate(lines, 1):
        # Check for endpoint headers (## GET /path or ### POST /path)
        if re.match(r"^#{2,3}\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/", line):
            has_endpoint_header = True

        # Check for description sections
        if re.match(r"^#{3,4}\s+(Description|Summary)", line, re.IGNORECASE):
            pass

        # Check for example sections
        if re.match(r"^#{3,4}\s+(Example|Sample|Code)", line, re.IGNORECASE):
            pass

        # Validate code block syntax
        if line.strip().startswith("```"):
            if not _validate_code_block(lines, i - 1):
                errors.append(
                    ValidationError(
                        file_path=file_path or "unknown",
                        line_number=i,
                        error_type="syntax_error",
                        message="Malformed code block",
                        suggestion="Ensure code blocks have proper opening and closing ```",
                    )
                )

    # Add warnings for missing sections
    if not has_endpoint_header:
        errors.append(
            ValidationError(
                file_path=file_path or "unknown",
                line_number=None,
                error_type="missing_section",
                message="No endpoint headers found",
                suggestion='Add endpoint headers like "## GET /api/endpoint"',
            )
        )

    return errors


def extract_endpoint_info(markdown_content: str) -> dict[str, Any]:
    """
    Extract endpoint information from markdown content.

    Args:
        markdown_content: The markdown content to parse

    Returns:
        Dictionary containing endpoint information
    """
    endpoint_info: dict[str, Any] = {"path": None, "method": None, "summary": None, "description": None, "tags": []}

    lines = markdown_content.split("\n")

    for line in lines:
        # Extract endpoint from header (only take the first one found)
        endpoint_match = re.match(r"^#{2,3}\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(.+)", line)
        if endpoint_match and not endpoint_info["method"]:
            endpoint_info["method"] = endpoint_match.group(1)
            endpoint_info["path"] = endpoint_match.group(2).strip()

        # Extract summary from first paragraph
        if not endpoint_info["summary"] and line.strip() and not line.startswith("#"):
            endpoint_info["summary"] = line.strip()

        # Extract tags from metadata
        tag_match = re.match(r"^Tags?:\s*(.+)", line, re.IGNORECASE)
        if tag_match:
            tags = [tag.strip() for tag in tag_match.group(1).split(",")]
            endpoint_info["tags"] = tags

    return endpoint_info


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(" .")

    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed"

    return sanitized


def find_markdown_files(directory: str, patterns: Optional[list[str]] = None, recursive: bool = True) -> list[str]:
    """
    Find all markdown files in a directory.

    Args:
        directory: Directory to search in
        patterns: File patterns to match (default: ['*.md', '*.markdown'])
        recursive: Whether to search recursively

    Returns:
        List of markdown file paths
    """
    if patterns is None:
        patterns = ["*.md", "*.markdown"]

    directory_path = Path(directory)
    markdown_files: list[Path] = []

    for pattern in patterns:
        if recursive:
            markdown_files.extend(directory_path.rglob(pattern))
        else:
            markdown_files.extend(directory_path.glob(pattern))

    return [str(f) for f in markdown_files]


def _extract_code_description(content: str, code_start: int) -> Optional[str]:
    """
    Extract description text that precedes a code block.

    Args:
        content: Full markdown content
        code_start: Start position of the code block

    Returns:
        Description text if found
    """
    # Look backwards from code block to find preceding paragraph
    preceding_text = content[:code_start].strip()

    # Get the last paragraph before the code block
    paragraphs = preceding_text.split("\n\n")
    if paragraphs:
        last_paragraph = paragraphs[-1].strip()
        # Skip if it's a header or empty
        if last_paragraph and not last_paragraph.startswith("#"):
            return last_paragraph

    return None


def _validate_code_block(lines: list[str], start_index: int) -> bool:
    """
    Validate that a code block is properly formed.

    Args:
        lines: All lines in the document
        start_index: Index of the opening ``` line

    Returns:
        True if code block is valid
    """
    if start_index >= len(lines):
        return False

    # Find closing ```
    for i in range(start_index + 1, len(lines)):
        if lines[i].strip() == "```":
            return True

    return False
