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

from pathvalidate import sanitize_filename as _pathvalidate_sanitize_filename

from .types import CodeLanguage, CodeSample, ValidationError


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.

    This function uses pathvalidate library with custom settings to maintain
    backward compatibility with the original implementation.

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename
    """
    # Use pathvalidate with custom settings to match original behavior
    result = _pathvalidate_sanitize_filename(
        filename,
        replacement_text="_",  # Replace invalid chars with underscore
        null_value_handler=lambda e: "unnamed",  # Return "unnamed" for empty strings
    )

    # Additional processing to match original behavior
    if result:
        # Remove leading/trailing whitespace and dots (like original implementation)
        result = result.strip(" .")

    # Handle the case where result is empty, whitespace-only, or only underscores
    if not result or result.isspace() or set(result) == {"_"}:
        return "unnamed"

    return result


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


def extract_endpoint_info(markdown_content: str, general_docs_content: Optional[str] = None) -> dict[str, Any]:
    """
    Extract comprehensive endpoint information from markdown content.

    Args:
        markdown_content: The markdown content to parse
        general_docs_content: Optional general documentation content (ignored - kept for compatibility)

    Returns:
        Dictionary containing endpoint information including endpoint-specific description
    """
    endpoint_info: dict[str, Any] = {"path": None, "method": None, "summary": None, "description": None, "tags": []}

    lines = markdown_content.split("\n")
    description_lines: list[str] = []
    in_description = False
    found_endpoint = False
    endpoint_header_level = 0
    overview_lines: list[str] = []
    in_overview = False

    for line in lines:
        # Check for Overview section
        if line.strip() == "## Overview":
            in_overview = True
            overview_lines.append(line)
            continue

        # Collect Overview content until next h2
        if in_overview:
            # Check if this is an endpoint header first
            endpoint_match = re.match(r"^(#{2,3})\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(.+)", line)
            if endpoint_match:
                # This is an endpoint header, stop overview collection
                in_overview = False
                # Don't continue, let this line be processed by the endpoint logic below
            else:
                header_match = re.match(r"^(#{1,})\s+", line)
                if header_match:
                    current_header_level = len(header_match.group(1))
                    # Stop overview collection if we hit another h2 or h1
                    if current_header_level <= 2:
                        in_overview = False
                        # Don't add this line to overview since it's the start of a new section
                        if current_header_level < 2:  # Only stop for h1, continue for other h2s
                            pass
                        else:
                            # This is another h2, stop overview collection
                            pass
                    else:
                        # This is h3, h4, etc. - include in overview
                        overview_lines.append(line)
                        continue
                else:
                    # Regular content line in overview
                    overview_lines.append(line)
                    continue

        # Extract endpoint from header (only take the first one found)
        endpoint_match = re.match(r"^(#{2,3})\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(.+)", line)
        if endpoint_match and not endpoint_info["method"]:
            endpoint_header_level = len(endpoint_match.group(1))  # Count the # characters
            endpoint_info["method"] = endpoint_match.group(2)
            endpoint_info["path"] = endpoint_match.group(3).strip()
            found_endpoint = True
            in_description = True  # Start collecting description after endpoint header
            continue

        # Collect description content (everything between endpoint header and next section)
        if in_description and found_endpoint:
            # Check if this line should stop description collection
            header_match = re.match(r"^(#{1,})\s+", line)
            if header_match:
                current_header_level = len(header_match.group(1))
                # Stop if we encounter a header at the same level or higher (fewer #'s)
                # This ensures we stop at the next endpoint (same level) or section (higher level)
                if current_header_level <= endpoint_header_level:
                    in_description = False
                    # Don't add this line to description since it's the start of a new section
                    continue

            # Skip empty lines at the start
            if not description_lines and not line.strip():
                continue

            # Add line to description
            description_lines.append(line)

            # Extract summary from first meaningful line (often bold text)
            if not endpoint_info["summary"] and line.strip() and not line.startswith("#"):
                # Clean up summary - remove markdown formatting for summary
                summary = line.strip()
                # Remove bold formatting for summary
                summary = re.sub(r"\*\*(.*?)\*\*", r"\1", summary)
                endpoint_info["summary"] = summary

        # Extract tags from metadata
        tag_match = re.match(r"^Tags?:\s*(.+)", line, re.IGNORECASE)
        if tag_match:
            tags = [tag.strip() for tag in tag_match.group(1).split(",")]
            endpoint_info["tags"] = tags

    # Build description from overview + endpoint content (no general docs)
    full_description_lines = []

    # Add overview content if we found any
    if overview_lines:
        full_description_lines.extend(overview_lines)
        # Add separator between overview and endpoint content
        if description_lines:
            full_description_lines.append("")
            full_description_lines.append("---")
            full_description_lines.append("")

    # Add endpoint-specific content
    if description_lines:
        full_description_lines.extend(description_lines)

    # Build final description
    if full_description_lines:
        # Remove trailing empty lines
        while full_description_lines and not full_description_lines[-1].strip():
            full_description_lines.pop()

        if full_description_lines:
            endpoint_info["description"] = "\n".join(full_description_lines).strip()

    return endpoint_info


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
