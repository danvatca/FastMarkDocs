"""
Copyright (c) 2025 Dan Vatca

Documentation loader for FastMarkDocs.

This module provides the MarkdownDocumentationLoader class for loading
and parsing markdown documentation files into structured data.
"""

import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Optional

import mistune
import yaml

from .exceptions import DocumentationLoadError
from .types import (
    CodeLanguage,
    CodeSample,
    DocumentationData,
    DocumentationStats,
    EndpointDocumentation,
    HTTPMethod,
    ParameterDocumentation,
    ResponseExample,
)
from .utils import (
    extract_code_samples,
    extract_endpoint_info,
    find_markdown_files,
    normalize_path,
    validate_markdown_structure,
)


class MarkdownDocumentationLoader:
    """
    Loads and parses markdown documentation files into structured data.

    This class handles the discovery, loading, and parsing of markdown files
    containing API documentation, extracting endpoint information, code samples,
    and other documentation elements.
    """

    def __init__(
        self,
        docs_directory: str = "docs",
        base_url_placeholder: str = "https://api.example.com",
        supported_languages: Optional[list[CodeLanguage]] = None,
        file_patterns: Optional[list[str]] = None,
        encoding: str = "utf-8",
        recursive: bool = True,
        cache_enabled: bool = True,
        cache_ttl: int = 3600,
        general_docs_file: Optional[str] = None,
    ):
        """
        Initialize the documentation loader.

        Args:
            docs_directory: Directory containing markdown files
            base_url_placeholder: Placeholder for base URL in documentation
            supported_languages: List of supported code sample languages
            file_patterns: File patterns to match
            encoding: File encoding
            recursive: Whether to search recursively
            cache_enabled: Whether to enable caching
            cache_ttl: Cache time-to-live in seconds
            general_docs_file: Path to general documentation file (defaults to "general_docs.md" if found)
        """
        self.docs_directory = Path(docs_directory)
        self.base_url_placeholder = base_url_placeholder
        self.supported_languages = supported_languages or list(CodeLanguage)
        self.file_patterns = file_patterns or ["*.md", "*.markdown"]
        self.encoding = encoding
        self.recursive = recursive
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.general_docs_file = general_docs_file

        # Validate directory exists during initialization (only for absolute paths)
        if self.docs_directory.is_absolute() and not self.docs_directory.exists():
            raise DocumentationLoadError(str(self.docs_directory), "Documentation directory does not exist")

        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_timestamps: dict[str, float] = {}
        self._documentation_cache: Optional[DocumentationData] = None
        self._documentation_cache_timestamp: Optional[float] = None
        self._cache_lock = threading.Lock()
        self._loading_event = threading.Event()
        self._is_loading = False
        self._markdown_parser = mistune.create_markdown(renderer="ast")
        self._general_docs_content: Optional[str] = None

    def load_documentation(self) -> DocumentationData:
        """
        Load all documentation from the configured directory.

        Returns:
            Structured documentation data

        Raises:
            DocumentationLoadError: If loading fails
        """
        if not self.cache_enabled:
            return self._load_documentation_internal()

        # Check cache first (fast path)
        if self._documentation_cache is not None and self._documentation_cache_timestamp:
            cache_age = time.time() - self._documentation_cache_timestamp
            if cache_age <= self.cache_ttl:
                return self._documentation_cache

        # Need to load documentation
        should_load = False

        with self._cache_lock:
            # Double-check cache after acquiring lock
            if self._documentation_cache is not None and self._documentation_cache_timestamp:
                cache_age = time.time() - self._documentation_cache_timestamp
                if cache_age <= self.cache_ttl:
                    return self._documentation_cache

            # Check if another thread is already loading
            if self._is_loading:
                # Another thread is loading, we'll wait
                should_load = False
            else:
                # We'll do the loading
                self._is_loading = True
                self._loading_event.clear()
                should_load = True

        if should_load:
            # We're the loading thread, do the work
            try:
                documentation = self._load_documentation_internal()

                # Cache the result
                with self._cache_lock:
                    self._documentation_cache = documentation
                    self._documentation_cache_timestamp = time.time()
                    self._is_loading = False
                    self._loading_event.set()  # Signal other threads

                return documentation
            except Exception:
                # Reset loading state on error
                with self._cache_lock:
                    self._is_loading = False
                    self._loading_event.set()
                raise
        else:
            # Wait for the loading thread to complete
            self._loading_event.wait()

            # Return the cached result
            if self._documentation_cache is not None:
                return self._documentation_cache
            else:
                # Loading failed, try loading ourselves
                return self._load_documentation_internal()

    def _load_documentation_internal(self) -> DocumentationData:
        """
        Internal method to load documentation (assumes caller handles locking if needed).

        Returns:
            Structured documentation data

        Raises:
            DocumentationLoadError: If loading fails
        """
        start_time = time.time()

        try:
            # Normalize the docs directory path
            docs_path = normalize_path(str(self.docs_directory))

            if not os.path.exists(docs_path):
                raise DocumentationLoadError(docs_path, "Documentation directory does not exist")

            # Load general documentation content if available
            try:
                self._general_docs_content = self._load_general_docs(docs_path)
            except Exception as e:
                # Log warning but don't fail - general docs are optional
                import warnings

                warnings.warn(f"Failed to load general docs: {str(e)}", stacklevel=2)
                self._general_docs_content = None

            # Find all markdown files
            markdown_files = find_markdown_files(docs_path, self.file_patterns, self.recursive)

            if not markdown_files:
                # Return empty documentation instead of raising error
                return DocumentationData(endpoints=[], global_examples=[], metadata={})

            # Load and parse each file
            endpoints = []
            global_examples = []
            validation_errors = []
            total_code_samples = 0
            languages_found = set()
            collected_metadata = {}
            collected_section_descriptions = {}

            for file_path in markdown_files:
                try:
                    file_data = self._load_file(file_path)

                    # Extract multiple endpoints from content
                    file_endpoints = self._extract_endpoints_from_content(file_data["content"])
                    endpoints.extend(file_endpoints)

                    # Collect global code samples
                    global_examples.extend(file_data["code_samples"])

                    # Extract section descriptions from this file
                    file_section_descriptions = self._extract_section_descriptions_from_content(file_data["content"])
                    collected_section_descriptions.update(file_section_descriptions)

                    # Update statistics
                    total_code_samples += len(file_data["code_samples"])
                    for sample in file_data["code_samples"]:
                        if hasattr(sample, "language"):
                            languages_found.add(sample.language)
                        elif isinstance(sample, dict) and "language" in sample:
                            languages_found.add(sample["language"])

                    # Collect validation errors
                    validation_errors.extend(file_data["validation_errors"])

                    # Collect metadata from frontmatter (excluding file-specific metadata)
                    file_metadata = file_data["metadata"]
                    for key, value in file_metadata.items():
                        if key not in ["file_size", "modified_time"]:
                            collected_metadata[key] = value

                except Exception as e:
                    raise DocumentationLoadError(file_path, f"Failed to process file: {str(e)}") from e

            # Create documentation stats
            load_time = (time.time() - start_time) * 1000
            stats = DocumentationStats(
                total_files=len(markdown_files),
                total_endpoints=len(endpoints),
                total_code_samples=total_code_samples,
                languages_found=list(languages_found),
                validation_errors=validation_errors,
                load_time_ms=load_time,
            )

            # Create documentation data
            documentation = DocumentationData(
                endpoints=endpoints,
                global_examples=global_examples,
                metadata={
                    "stats": stats,
                    "docs_directory": docs_path,
                    **collected_metadata,  # Include collected frontmatter metadata
                },
                section_descriptions=collected_section_descriptions,
            )

            # Cache the documentation result if caching is enabled (thread-safe)
            if self.cache_enabled:
                with self._cache_lock:
                    self._documentation_cache = documentation
                    self._documentation_cache_timestamp = time.time()

            return documentation

        except DocumentationLoadError:
            raise
        except Exception as e:
            raise DocumentationLoadError(
                str(self.docs_directory), f"Unexpected error during documentation loading: {str(e)}"
            ) from e

    def _parse_markdown_file(self, file_path: Path) -> list[EndpointDocumentation]:
        """
        Parse a single markdown file and extract endpoint documentation.

        Args:
            file_path: Path to the markdown file

        Returns:
            List of endpoint documentation objects

        Raises:
            DocumentationLoadError: If parsing fails
        """
        try:
            file_data = self._load_file(str(file_path))

            # Extract multiple endpoints from content
            endpoints = self._extract_endpoints_from_content(file_data["content"])

            return endpoints

        except Exception as e:
            raise DocumentationLoadError(str(file_path), f"Failed to parse markdown file: {str(e)}") from e

    def parse_markdown_file(self, file_path: str) -> dict[str, Any]:
        """
        Parse a single markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            Parsed file data

        Raises:
            DocumentationLoadError: If parsing fails
        """
        return self._load_file(file_path)

    def _load_file(self, file_path: str) -> dict[str, Any]:
        """
        Internal method to load and parse a single file.

        Args:
            file_path: Path to the markdown file

        Returns:
            Dictionary containing parsed file data
        """
        # Check cache if enabled
        if self.cache_enabled and self._is_cached(file_path):
            return self._cache[file_path]

        try:
            # Read file content
            with open(file_path, encoding=self.encoding) as f:
                content = f.read()

            # Extract YAML frontmatter if present
            frontmatter_metadata, content_without_frontmatter = self._extract_frontmatter(content)

            # Parse markdown content
            ast = self._markdown_parser(content_without_frontmatter)

            # Extract various components
            endpoint_info = extract_endpoint_info(content_without_frontmatter, self._general_docs_content)
            code_samples = extract_code_samples(content_without_frontmatter, self.supported_languages)
            validation_errors = validate_markdown_structure(content_without_frontmatter, file_path)

            # Create file data
            file_data = {
                "file_path": file_path,
                "content": content_without_frontmatter,
                "ast": ast,
                "endpoint_info": endpoint_info,
                "code_samples": code_samples,
                "validation_errors": validation_errors,
                "metadata": {
                    "file_size": os.path.getsize(file_path),
                    "modified_time": os.path.getmtime(file_path),
                    **frontmatter_metadata,  # Include YAML frontmatter metadata
                },
            }

            # Cache the result if caching is enabled
            if self.cache_enabled:
                self._cache[file_path] = file_data
                self._cache_timestamps[file_path] = time.time()

            return file_data

        except FileNotFoundError:
            raise DocumentationLoadError(file_path, "File not found") from None
        except UnicodeDecodeError as e:
            raise DocumentationLoadError(file_path, f"Encoding error: {str(e)}") from e
        except Exception as e:
            raise DocumentationLoadError(file_path, f"Unexpected error: {str(e)}") from e

    def _load_general_docs(self, docs_path: str) -> Optional[str]:
        """
        Load general documentation content if available.

        Args:
            docs_path: Path to the documentation directory

        Returns:
            General documentation content or None if not found
        """
        # Determine the general docs file path
        if self.general_docs_file:
            # User specified a custom general docs file
            if os.path.isabs(self.general_docs_file):
                general_docs_path = self.general_docs_file
            else:
                general_docs_path = os.path.join(docs_path, self.general_docs_file)
        else:
            # Default to general_docs.md
            general_docs_path = os.path.join(docs_path, "general_docs.md")

        # Try to load the general docs file
        if os.path.exists(general_docs_path):
            try:
                with open(general_docs_path, encoding=self.encoding) as f:
                    content = f.read()

                # Extract content without frontmatter
                _, content_without_frontmatter = self._extract_frontmatter(content)
                return content_without_frontmatter
            except Exception as e:
                # Log warning but don't fail - general docs are optional
                import warnings

                warnings.warn(f"Failed to load general docs from {general_docs_path}: {str(e)}", stacklevel=2)
                return None

        return None

    def _extract_endpoints_from_content(self, content: str) -> list[EndpointDocumentation]:
        """
        Extract endpoint documentation from markdown content.

        Args:
            content: Markdown content

        Returns:
            List of endpoint documentation
        """
        endpoints = []

        # Split content by endpoint headers to handle multiple endpoints
        sections = self._split_content_by_endpoints(content)

        for i, section in enumerate(sections):
            endpoint_info = extract_endpoint_info(section, self._general_docs_content)

            if endpoint_info["method"] and endpoint_info["path"]:
                # Extract code samples from this section
                code_samples = extract_code_samples(section, self.supported_languages)

                # If no code samples found in this section, check subsequent sections
                # that don't have their own endpoint (to handle split code examples)
                if not code_samples and i + 1 < len(sections):
                    next_section = sections[i + 1]
                    next_endpoint_info = extract_endpoint_info(next_section, self._general_docs_content)

                    # If the next section doesn't have an endpoint, it might contain our code examples
                    if not (next_endpoint_info["method"] and next_endpoint_info["path"]):
                        additional_samples = extract_code_samples(next_section, self.supported_languages)
                        code_samples.extend(additional_samples)

                # Extract response examples from this section
                response_examples: list[ResponseExample] = self._extract_response_examples(section)

                # If no response examples in this section, check subsequent section too
                if not response_examples and i + 1 < len(sections):
                    next_section = sections[i + 1]
                    next_endpoint_info = extract_endpoint_info(next_section, self._general_docs_content)

                    if not (next_endpoint_info["method"] and next_endpoint_info["path"]):
                        additional_examples = self._extract_response_examples(next_section)
                        response_examples.extend(additional_examples)

                # Extract parameters from this section
                parameters = self._extract_parameters(section)

                # Create endpoint documentation
                endpoint = EndpointDocumentation(
                    path=endpoint_info["path"],
                    method=HTTPMethod(endpoint_info["method"]),
                    summary=endpoint_info.get("summary", ""),
                    description=endpoint_info.get("description", ""),
                    code_samples=code_samples,
                    response_examples=response_examples,
                    parameters=parameters,
                    sections=endpoint_info.get("sections", []),
                    deprecated=endpoint_info.get("deprecated", False),
                )

                endpoints.append(endpoint)

        return endpoints

    def _split_content_by_endpoints(self, content: str) -> list[str]:
        """
        Split markdown content into sections by endpoint headers.

        Args:
            content: Markdown content

        Returns:
            List of content sections, each containing one endpoint
        """
        lines = content.split("\n")
        sections: list[str] = []
        current_section: list[str] = []
        current_endpoint_level = 0
        in_code_block = False
        code_block_language = ""  # Track the language of current code block

        for _line_num, line in enumerate(lines, 1):
            # Track code block state with better parsing
            stripped_line = line.strip()

            # Handle code block markers
            if stripped_line.startswith("```"):
                if not in_code_block:
                    # Starting a code block
                    in_code_block = True
                    # Extract language if present
                    code_block_language = stripped_line[3:].strip()
                else:
                    # Ending a code block - only if it's a closing marker
                    if stripped_line == "```" or (code_block_language and stripped_line == f"```{code_block_language}"):
                        in_code_block = False
                        code_block_language = ""
                    # If it's not a proper closing marker, treat as content within the block

            # Check if this line is an endpoint header (only if not in code block)
            if not in_code_block:
                endpoint_match = re.match(r"^(#{2,4})\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/", line)
                if endpoint_match:
                    # If we have a current section, save it
                    if current_section:
                        sections.append("\n".join(current_section))
                        current_section = []

                    # Track the level of this endpoint header
                    current_endpoint_level = len(endpoint_match.group(1))
                    current_section.append(line)
                    continue

                # Check if this line is a header that would end the current endpoint section
                if current_section and current_endpoint_level > 0:
                    header_match = re.match(r"^(#{1,})\s+", line)
                    if header_match:
                        header_level = len(header_match.group(1))
                        # Only end the section if we encounter a header at the same level or higher (fewer #'s)
                        # that is NOT a sub-section of the current endpoint (like #### Code Examples)
                        if header_level <= current_endpoint_level:
                            # Check if this is another endpoint header
                            if not re.match(r"^#{2,4}\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/", line):
                                # This is a non-endpoint header at same/higher level
                                # But we should NOT split on sub-headers like "#### Code Examples"
                                # Only split on major section headers (# or ## level)
                                if header_level <= 2:
                                    sections.append("\n".join(current_section))
                                    current_section = [line]
                                    current_endpoint_level = 0
                                    continue

            current_section.append(line)

        # Add the last section if it exists
        if current_section:
            sections.append("\n".join(current_section))

        # Validate that we don't have unclosed code blocks
        for i, section in enumerate(sections):
            if self._has_unclosed_code_blocks(section):
                # Log warning but don't fail - this helps with debugging
                import logging

                logging.warning(f"Section {i} has unclosed code blocks, this may cause parsing issues")

        return sections

    def _extract_response_examples(self, content: str) -> list[ResponseExample]:
        """
        Extract response examples from markdown content.

        Args:
            content: Markdown content section

        Returns:
            List of response examples
        """
        response_examples: list[ResponseExample] = []
        lines = content.split("\n")

        in_response_section = False
        in_code_block = False
        current_code: list[str] = []
        current_status = 200  # Default status code
        current_description = ""  # Current response description

        for line_num, line in enumerate(lines, 1):
            try:
                # Check for Response Examples section (more flexible matching)
                if re.match(r"^#{3,4}\s*Response\s+Examples?", line, re.IGNORECASE):
                    in_response_section = True
                    continue

                # Check for next section (exit response examples)
                if in_response_section and re.match(r"^#{3,4}\s+", line):
                    # Before exiting, handle any unclosed code block
                    if in_code_block and current_code:
                        self._finalize_response_example(
                            response_examples, current_code, current_status, current_description
                        )
                        current_code = []
                        in_code_block = False
                    in_response_section = False
                    continue

                if in_response_section:
                    # Check for response description lines with status codes
                    # Enhanced pattern to handle more variations
                    status_match = re.search(r".*\((\d+).*\).*:", line)
                    if (
                        status_match
                        and line.strip().startswith("**")
                        and (line.strip().endswith(":") or line.strip().endswith(":**"))
                    ):
                        # Before starting new response, finalize any pending code block
                        if in_code_block and current_code:
                            self._finalize_response_example(
                                response_examples, current_code, current_status, current_description
                            )
                            current_code = []
                            in_code_block = False

                        current_status = int(status_match.group(1))
                        # Extract description from the line with better parsing
                        desc_match = re.search(r"\*\*(.*?)\s*\(\d+.*\):", line)
                        if desc_match:
                            current_description = desc_match.group(1).strip()
                        else:
                            # Fallback: extract everything before the status code
                            fallback_match = re.search(r"\*\*(.*?)\s*\(", line)
                            current_description = (
                                fallback_match.group(1).strip()
                                if fallback_match
                                else f"Response with status {current_status}"
                            )
                        continue

                    # Check for code block start/end
                    if line.strip().startswith("```"):
                        if in_code_block:
                            # End of code block - create response example
                            if current_code:
                                self._finalize_response_example(
                                    response_examples, current_code, current_status, current_description
                                )
                                current_code = []
                            in_code_block = False
                            # Reset description for next example
                            current_description = ""
                        else:
                            # Start of code block
                            in_code_block = True
                            # Check for status code in the line (e.g., "```json 201")
                            parts = line.strip().split()
                            if len(parts) > 1 and parts[1].isdigit():
                                current_status = int(parts[1])
                                current_description = f"Response with status {current_status}"
                            # If no status code in code block line and no previous description, use default
                            elif not current_description:
                                current_status = 200
                                current_description = f"Response example with status {current_status}"
                    elif in_code_block:
                        current_code.append(line)

            except (ValueError, AttributeError, IndexError) as e:
                # Log parsing errors but continue processing
                # This prevents a single malformed line from breaking the entire parsing
                import warnings

                warnings.warn(
                    f"Error parsing response example at line {line_num}: {str(e)}. " f"Line content: {repr(line)}",
                    stacklevel=2,
                )
                continue

        # Handle case where code block is at end of content
        if in_code_block and current_code:
            self._finalize_response_example(response_examples, current_code, current_status, current_description)

        return response_examples

    def _finalize_response_example(
        self,
        response_examples: list[ResponseExample],
        current_code: list[str],
        current_status: int,
        current_description: str,
    ) -> None:
        """
        Enhanced helper method to finalize and add a response example supporting multiple content types.

        Args:
            response_examples: List to append the example to
            current_code: Lines of code content
            current_status: HTTP status code
            current_description: Description of the response
        """
        try:
            content_str = "\n".join(current_code).strip()
            if not content_str:
                # Skip empty code blocks
                return

            # Create enhanced response example with content type detection
            response_example = ResponseExample(
                status_code=current_status,
                description=current_description or f"Response example with status {current_status}",
                raw_content=content_str,
            )

            # Process content based on detected type
            if response_example.content_type == "application/json":
                try:
                    import json

                    response_example.content = json.loads(content_str)
                except (json.JSONDecodeError, ValueError):
                    # If JSON parsing fails, treat as plain text
                    response_example.content = content_str
                    response_example.content_type = "text/plain"

            elif response_example.content_type.startswith("text/plain"):
                # Handle Prometheus metrics and other plain text
                response_example.content = content_str

            elif response_example.content_type == "application/xml":
                # Handle XML content
                response_example.content = content_str

            elif response_example.content_type == "application/yaml":
                # Handle YAML content - try to parse if PyYAML is available
                try:
                    import yaml

                    response_example.content = yaml.safe_load(content_str)
                except ImportError:
                    # If PyYAML not available, store as string
                    response_example.content = content_str
                except yaml.YAMLError:
                    # If YAML parsing fails, store as string
                    response_example.content = content_str

            else:
                # Fallback for unknown types - store as string
                response_example.content = content_str

            response_examples.append(response_example)

        except Exception as e:
            # Log but don't fail on individual example processing errors
            import warnings

            warnings.warn(f"Error finalizing response example with status {current_status}: {str(e)}", stacklevel=2)

    def _extract_parameters(self, content: str) -> list[ParameterDocumentation]:
        """
        Extract parameter documentation from markdown content.

        Args:
            content: Markdown content section

        Returns:
            List of parameter documentation
        """
        parameters = []
        lines = content.split("\n")

        in_parameters_section = False

        for line in lines:
            # Check for parameters section header
            if re.match(r"^#{3,4}\s*(Parameters?|Query Parameters?|Path Parameters?)", line, re.IGNORECASE):
                in_parameters_section = True
                continue

            # Check for next section (exit parameters)
            if in_parameters_section and re.match(r"^#{3,4}\s+", line):
                in_parameters_section = False
                continue

            if in_parameters_section:
                # Parse parameter lines (- `name` (type, required): description)
                param_match = re.match(r"^\s*-\s*`([^`]+)`\s*\(([^,)]+)(?:,\s*(required|optional))?\):\s*(.+)", line)
                if param_match:
                    name = param_match.group(1)
                    param_type = param_match.group(2)
                    required_str = param_match.group(3)
                    description = param_match.group(4)

                    required = required_str == "required" if required_str else None

                    parameters.append(
                        ParameterDocumentation(name=name, description=description, type=param_type, required=required)
                    )

        return parameters

    def _extract_section_descriptions_from_content(self, content: str) -> dict[str, str]:
        """
        Extract section descriptions from markdown content by finding Overview sections
        and associating them with sections used in the same file.

        Args:
            content: Markdown content

        Returns:
            Dictionary mapping section names to their descriptions from Overview sections
        """
        section_descriptions: dict[str, str] = {}

        # First, extract all sections used in this file
        file_sections = set()
        lines = content.split("\n")

        for line in lines:
            # Extract sections from "Section:" lines
            section_match = re.match(r"^Section:\s*(.+)", line, re.IGNORECASE)
            if section_match:
                sections = [section.strip() for section in section_match.group(1).split(",")]
                file_sections.update(sections)

        # If no sections found, return empty dict
        if not file_sections:
            return section_descriptions

        # Extract Overview section content
        overview_content = self._extract_overview_section(content)
        if overview_content:
            # Associate the overview content with all sections in this file
            # This assumes that the Overview section describes the API group
            # that all endpoints in this file belong to
            for section in file_sections:
                section_descriptions[section] = overview_content.strip()

        return section_descriptions

    def _extract_overview_section(self, content: str) -> Optional[str]:
        """
        Extract the Overview section content from markdown.

        Args:
            content: Markdown content

        Returns:
            Overview section content or None if not found
        """
        lines = content.split("\n")
        overview_lines = []
        in_overview = False
        overview_found = False

        for line in lines:
            # Check for Overview section header
            if line.strip() == "## Overview":
                in_overview = True
                overview_found = True
                continue

            # Stop collecting when we hit the next major section
            if in_overview:
                header_match = re.match(r"^(#{1,2})\s+", line)
                if header_match:
                    # This is an h1 or h2 header, stop overview collection
                    break
                else:
                    # Regular content line in overview
                    overview_lines.append(line)

        if overview_found and overview_lines:
            # Remove trailing empty lines
            while overview_lines and not overview_lines[-1].strip():
                overview_lines.pop()

            if overview_lines:
                return "\n".join(overview_lines)

        return None

    def _extract_frontmatter(self, content: str) -> tuple[dict[str, Any], str]:
        """
        Extract YAML frontmatter from markdown content.

        Args:
            content: Raw markdown content

        Returns:
            Tuple of (frontmatter_dict, content_without_frontmatter)
        """
        frontmatter: dict[str, Any] = {}

        # Check if content starts with YAML frontmatter
        if content.startswith("---\n"):
            try:
                # Find the end of frontmatter
                end_marker = content.find("\n---\n", 4)
                if end_marker != -1:
                    # Extract YAML content
                    yaml_content = content[4:end_marker]
                    content_without_frontmatter = content[end_marker + 5 :]

                    # Parse YAML
                    try:
                        frontmatter = yaml.safe_load(yaml_content) or {}
                    except yaml.YAMLError:
                        # If YAML parsing fails, ignore frontmatter
                        frontmatter = {}
                        content_without_frontmatter = content
                else:
                    content_without_frontmatter = content
            except Exception:
                # If any error occurs, return original content
                content_without_frontmatter = content
        else:
            content_without_frontmatter = content

        return frontmatter, content_without_frontmatter

    def _create_endpoint_documentation(self, file_data: dict[str, Any]) -> EndpointDocumentation:
        """
        Create endpoint documentation from parsed file data.

        Args:
            file_data: Parsed file data

        Returns:
            Endpoint documentation object
        """
        endpoint_info = file_data["endpoint_info"]

        # Convert code samples to proper objects
        code_samples = []
        for sample_data in file_data["code_samples"]:
            if isinstance(sample_data, dict):
                code_samples.append(
                    CodeSample(
                        language=sample_data["language"],
                        code=sample_data["code"],
                        description=sample_data.get("description"),
                        title=sample_data.get("title"),
                    )
                )
            else:
                code_samples.append(sample_data)

        # Create endpoint documentation
        endpoint = EndpointDocumentation(
            path=endpoint_info["path"],
            method=HTTPMethod(endpoint_info["method"]),
            summary=endpoint_info.get("summary", ""),
            description=endpoint_info.get("description", ""),
            code_samples=code_samples,
            response_examples=[],
            parameters=[],
            sections=endpoint_info.get("sections", []),
            deprecated=endpoint_info.get("deprecated", False),
        )

        return endpoint

    def _is_cached(self, file_path: str) -> bool:
        """
        Check if a file is cached and still valid.

        Args:
            file_path: Path to the file

        Returns:
            True if cached and valid
        """
        if file_path not in self._cache:
            return False

        # Check if cache has expired
        if file_path in self._cache_timestamps:
            cache_age = time.time() - self._cache_timestamps[file_path]
            if cache_age > self.cache_ttl:
                # Remove expired cache entry
                del self._cache[file_path]
                del self._cache_timestamps[file_path]
                return False

        # Check if file has been modified
        try:
            file_mtime = os.path.getmtime(file_path)
            cached_mtime = self._cache[file_path]["metadata"]["modified_time"]
            if file_mtime > cached_mtime:
                # File has been modified, invalidate cache
                del self._cache[file_path]
                del self._cache_timestamps[file_path]
                return False
        except (OSError, KeyError):
            # Error checking file modification time, invalidate cache
            if file_path in self._cache:
                del self._cache[file_path]
            if file_path in self._cache_timestamps:
                del self._cache_timestamps[file_path]
            return False

        return True

    def clear_cache(self) -> None:
        """Clear the documentation cache (thread-safe)."""
        with self._cache_lock:
            self._cache.clear()
            self._cache_timestamps.clear()
            self._documentation_cache = None
            self._documentation_cache_timestamp = None
            self._is_loading = False
            self._loading_event.set()

    def get_stats(self) -> dict[str, Any]:
        """
        Get loader statistics.

        Returns:
            Dictionary containing loader statistics
        """
        return {
            "cache_size": len(self._cache),
            "cache_enabled": self.cache_enabled,
            "docs_directory": self.docs_directory,
            "supported_languages": [lang.value for lang in self.supported_languages],
            "file_patterns": self.file_patterns,
        }

    def _has_unclosed_code_blocks(self, content: str) -> bool:
        """
        Check if content has unclosed code blocks.

        Args:
            content: Content to check

        Returns:
            True if there are unclosed code blocks
        """
        lines = content.split("\n")
        in_code_block = False
        code_block_count = 0

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                code_block_count += 1
                in_code_block = not in_code_block

        # Should have even number of ``` markers
        return code_block_count % 2 != 0
