"""
Integration tests using real-world API documentation test fixtures.

This test suite validates that the FastMarkDocs library can correctly
parse and process complex, real-world documentation files. The test fixtures
are static copies of documentation from the Syneto Doorman project, providing
a comprehensive regression test base while keeping the library completely
independent and portable.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest
from fastmarkdocs import CodeSampleGenerator, MarkdownDocumentationLoader, enhance_openapi_with_docs
from fastmarkdocs.exceptions import DocumentationLoadError
from fastmarkdocs.types import CodeLanguage, DocumentationData, HTTPMethod


class TestDoormanDocsIntegration:
    """Integration tests using real-world API documentation test fixtures."""

    @pytest.fixture
    def doorman_docs_path(self):
        """Path to the copied Doorman documentation test fixtures."""
        # Use the copied documentation files in test fixtures
        docs_path = Path(__file__).parent.parent / "fixtures" / "doorman_docs"
        if not docs_path.exists():
            pytest.skip(f"Doorman test fixtures not found at {docs_path}")
        return docs_path

    @pytest.fixture
    def temp_docs_dir(self, doorman_docs_path):
        """Create a temporary directory with copies of test fixture docs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Copy all markdown files from test fixtures
            for md_file in doorman_docs_path.glob("*.md"):
                # Skip README files and focus on API docs
                if "README" not in md_file.name and "_docs.md" in md_file.name:
                    dest_path = temp_path / md_file.name
                    shutil.copy2(md_file, dest_path)

            yield temp_path

    def test_load_all_doorman_docs(self, temp_docs_dir: Any) -> None:
        """Test loading all Doorman documentation files."""
        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), recursive=True, cache_enabled=False)

        documentation = loader.load_documentation()

        # Verify documentation was loaded
        assert isinstance(documentation, DocumentationData)
        assert len(documentation.endpoints) > 0

        # Print summary for debugging
        print(f"\n📚 Loaded {len(documentation.endpoints)} endpoints from test fixtures")
        stats = documentation.metadata.get("stats")
        if stats:
            print(f"📁 Found {stats.total_files} files")
        else:
            print("📁 Stats not available")

        # Verify we have endpoints from different API areas
        paths = [ep.path for ep in documentation.endpoints]
        methods = [ep.method for ep in documentation.endpoints]

        # Should have various endpoint paths
        assert any("/v1/session" in path for path in paths), "Should have session endpoints"
        assert any("/v1/apiKeys" in path for path in paths), "Should have API key endpoints"

        # Should have various HTTP methods
        assert HTTPMethod.GET in methods, "Should have GET endpoints"
        assert HTTPMethod.POST in methods, "Should have POST endpoints"
        assert HTTPMethod.DELETE in methods, "Should have DELETE endpoints"

    def test_doorman_endpoint_parsing_quality(self, temp_docs_dir: Any) -> None:
        """Test the quality of endpoint parsing from real-world documentation."""
        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), recursive=True, cache_enabled=False)

        documentation = loader.load_documentation()

        # Analyze endpoint quality
        endpoints_with_summaries = [ep for ep in documentation.endpoints if ep.summary]
        endpoints_with_descriptions = [ep for ep in documentation.endpoints if ep.description]
        endpoints_with_code_samples = [ep for ep in documentation.endpoints if ep.code_samples]

        print("\n📊 Endpoint Quality Analysis:")
        print(f"   Total endpoints: {len(documentation.endpoints)}")
        print(
            f"   With summaries: {len(endpoints_with_summaries)} ({len(endpoints_with_summaries)/len(documentation.endpoints)*100:.1f}%)"
        )
        print(
            f"   With descriptions: {len(endpoints_with_descriptions)} ({len(endpoints_with_descriptions)/len(documentation.endpoints)*100:.1f}%)"
        )
        print(
            f"   With code samples: {len(endpoints_with_code_samples)} ({len(endpoints_with_code_samples)/len(documentation.endpoints)*100:.1f}%)"
        )

        # Quality assertions
        assert len(endpoints_with_summaries) > 0, "Should have endpoints with summaries"
        assert len(endpoints_with_code_samples) > 0, "Should have endpoints with code samples"

        # Check specific known endpoints
        session_post = next(
            (ep for ep in documentation.endpoints if ep.path == "/v1/session" and ep.method == HTTPMethod.POST), None
        )
        if session_post:
            assert session_post.summary, "Session POST should have a summary"
            print(f"   ✓ Session POST endpoint: '{session_post.summary}'")

    def test_doorman_code_samples_extraction(self, temp_docs_dir: Any) -> None:
        """Test extraction of code samples from Doorman docs."""
        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), recursive=True, cache_enabled=False)

        documentation = loader.load_documentation()

        # Analyze code samples
        all_code_samples = []
        for endpoint in documentation.endpoints:
            all_code_samples.extend(endpoint.code_samples)

        # Group by language
        samples_by_language: dict[str, int] = {}
        for sample in all_code_samples:
            lang = sample.language
            if lang not in samples_by_language:
                samples_by_language[lang] = []
            samples_by_language[lang].append(sample)

        print("\n🔧 Code Samples Analysis:")
        print(f"   Total code samples: {len(all_code_samples)}")
        for lang, samples in samples_by_language.items():
            print(f"   {lang.value}: {len(samples)} samples")

        # Verify we extracted code samples
        assert len(all_code_samples) > 0, "Should extract code samples from Doorman docs"

        # Should have multiple languages
        assert len(samples_by_language) > 1, "Should have multiple programming languages"

        # Check for specific languages that should be in Doorman docs
        languages = set(samples_by_language.keys())
        assert CodeLanguage.CURL in languages, "Should have cURL samples"
        assert CodeLanguage.PYTHON in languages, "Should have Python samples"

    def test_doorman_docs_with_code_generator(self, temp_docs_dir: Any) -> None:
        """Test generating additional code samples for Doorman endpoints."""
        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), recursive=True, cache_enabled=False)

        documentation = loader.load_documentation()

        # Create code generator
        generator = CodeSampleGenerator(
            base_url="https://api.example.com",
            code_sample_languages=[CodeLanguage.CURL, CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT, CodeLanguage.GO],
            custom_headers={"Authorization": "Bearer YOUR_TOKEN_HERE", "Content-Type": "application/json"},
        )

        # Generate samples for a few endpoints
        sample_endpoints = documentation.endpoints[:3]  # Test first 3 endpoints

        generated_samples = []
        for endpoint in sample_endpoints:
            try:
                samples = generator.generate_samples_for_endpoint(endpoint)
                generated_samples.extend(samples)
                print(f"   ✓ Generated {len(samples)} samples for {endpoint.method.value} {endpoint.path}")
            except Exception as e:
                print(f"   ⚠️  Failed to generate samples for {endpoint.method.value} {endpoint.path}: {e}")

        print("\n🚀 Code Generation Test:")
        print(f"   Generated {len(generated_samples)} additional code samples")

        # Verify generation worked
        assert len(generated_samples) > 0, "Should generate additional code samples"

        # Verify we have samples in different languages
        generated_languages = {sample.language for sample in generated_samples}
        assert len(generated_languages) > 1, "Should generate samples in multiple languages"

    def test_doorman_docs_openapi_enhancement(self, temp_docs_dir: Any) -> None:
        """Test enhancing OpenAPI schema with Doorman documentation."""
        # Create a sample OpenAPI schema that matches some Doorman endpoints
        openapi_schema = {
            "openapi": "3.0.2",
            "info": {"title": "Example API", "version": "1.0.0", "description": "Example API for testing FastMarkDocs"},
            "paths": {
                "/v1/session": {
                    "post": {"summary": "Create session", "responses": {"200": {"description": "Success"}}},
                    "get": {"summary": "Get session info", "responses": {"200": {"description": "Success"}}},
                    "delete": {"summary": "Delete session", "responses": {"200": {"description": "Success"}}},
                },
                "/v1/apiKeys": {
                    "get": {"summary": "List API keys", "responses": {"200": {"description": "Success"}}},
                    "post": {"summary": "Create API key", "responses": {"201": {"description": "Created"}}},
                },
            },
        }

        # Load documentation
        MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), recursive=True, cache_enabled=False)

        # Enhance the schema
        try:
            enhanced_schema = enhance_openapi_with_docs(
                openapi_schema=openapi_schema,
                docs_directory=str(temp_docs_dir),
                base_url="https://api.example.com",
                code_sample_languages=[CodeLanguage.CURL, CodeLanguage.PYTHON],
                include_code_samples=True,
                include_response_examples=True,
            )

            print("\n🔧 OpenAPI Enhancement Test:")
            print("   ✓ Successfully enhanced OpenAPI schema")

            # Verify enhancement
            assert enhanced_schema is not None
            assert "paths" in enhanced_schema

            # Check if code samples were added
            session_post = enhanced_schema.get("paths", {}).get("/v1/session", {}).get("post", {})
            if "x-codeSamples" in session_post:
                code_samples = session_post["x-codeSamples"]
                print(f"   ✓ Added {len(code_samples)} code samples to POST /v1/session")

                # Verify sample structure
                for sample in code_samples:
                    assert "lang" in sample
                    assert "source" in sample
                    print(f"     - {sample['lang']} sample")

            # Check if documentation stats were added
            if "x-documentation-stats" in enhanced_schema.get("info", {}):
                stats = enhanced_schema["info"]["x-documentation-stats"]
                print(f"   ✓ Added documentation stats: {stats}")

        except Exception as e:
            pytest.fail(f"OpenAPI enhancement failed: {e}")

    def test_doorman_docs_performance(self, temp_docs_dir: Any) -> None:
        """Test performance of loading Doorman documentation."""
        import time

        loader = MarkdownDocumentationLoader(
            docs_directory=str(temp_docs_dir),
            recursive=True,
            cache_enabled=True,  # Test with caching
        )

        # First load (cold)
        start_time = time.time()
        documentation1 = loader.load_documentation()
        cold_load_time = time.time() - start_time

        # Second load (cached)
        start_time = time.time()
        documentation2 = loader.load_documentation()
        cached_load_time = time.time() - start_time

        print("\n⚡ Performance Test:")
        print(f"   Cold load time: {cold_load_time:.3f}s")
        print(f"   Cached load time: {cached_load_time:.3f}s")
        print(f"   Speedup: {cold_load_time/cached_load_time:.1f}x")

        # Verify caching worked
        assert documentation1 is documentation2, "Should return cached object"
        assert cached_load_time < cold_load_time, "Cached load should be faster"

        # Performance assertions
        assert cold_load_time < 5.0, "Cold load should complete within 5 seconds"
        assert cached_load_time < 0.1, "Cached load should complete within 0.1 seconds"

    def test_doorman_docs_error_handling(self, temp_docs_dir: Any) -> None:
        """Test error handling with Doorman documentation."""
        # Test with non-existent directory
        with pytest.raises(DocumentationLoadError):
            loader = MarkdownDocumentationLoader(docs_directory="/nonexistent/directory", cache_enabled=False)
            loader.load_documentation()

        # Test with valid directory but no markdown files
        with tempfile.TemporaryDirectory() as empty_dir:
            loader = MarkdownDocumentationLoader(docs_directory=empty_dir, cache_enabled=False)
            documentation = loader.load_documentation()

            # Should return empty documentation, not error
            assert len(documentation.endpoints) == 0
            assert len(documentation.global_examples) == 0

        print("\n🛡️  Error Handling Test:")
        print("   ✓ Properly handles non-existent directories")
        print("   ✓ Gracefully handles empty directories")

    def test_doorman_docs_comprehensive_summary(self, temp_docs_dir: Any) -> None:
        """Generate a comprehensive summary of Doorman documentation parsing."""
        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), recursive=True, cache_enabled=False)

        documentation = loader.load_documentation()

        # Comprehensive analysis
        endpoints_by_method: dict[str, int] = {}
        endpoints_by_path_prefix: dict[str, int] = {}
        total_code_samples = 0
        total_response_examples = 0
        total_parameters = 0

        for endpoint in documentation.endpoints:
            # Group by method
            method = endpoint.method
            if method not in endpoints_by_method:
                endpoints_by_method[method] = []
            endpoints_by_method[method].append(endpoint)

            # Group by path prefix
            path_prefix = "/" + endpoint.path.split("/")[1] if "/" in endpoint.path else endpoint.path
            if path_prefix not in endpoints_by_path_prefix:
                endpoints_by_path_prefix[path_prefix] = []
            endpoints_by_path_prefix[path_prefix].append(endpoint)

            # Count samples and examples
            total_code_samples += len(endpoint.code_samples)
            total_response_examples += len(endpoint.response_examples)
            total_parameters += len(endpoint.parameters)

        print("\n📋 Comprehensive Doorman Documentation Summary:")
        stats = documentation.metadata.get("stats")
        if stats:
            print(f"   📁 Files processed: {stats.total_files}")
        else:
            print("   📁 Files processed: Unknown")
        print(f"   🔗 Total endpoints: {len(documentation.endpoints)}")
        print(f"   📝 Total code samples: {total_code_samples}")
        print(f"   📋 Total response examples: {total_response_examples}")
        print(f"   ⚙️  Total parameters: {total_parameters}")

        print("\n   📊 Endpoints by HTTP Method:")
        for method, endpoints in sorted(endpoints_by_method.items()):
            print(f"     {method.value}: {len(endpoints)} endpoints")

        print("\n   🗂️  Endpoints by API Area:")
        for prefix, endpoints in sorted(endpoints_by_path_prefix.items()):
            print(f"     {prefix}: {len(endpoints)} endpoints")

        # Verify we have a good distribution
        assert len(endpoints_by_method) >= 3, "Should have at least 3 different HTTP methods"
        assert len(endpoints_by_path_prefix) >= 2, "Should have at least 2 different API areas"
        assert total_code_samples > 0, "Should have extracted code samples"

        print("\n   ✅ All integration tests passed! The library successfully handles real Doorman documentation.")

    def test_doorman_docs_with_general_docs(self, temp_docs_dir: Any) -> None:
        """Test that general docs are properly loaded and available in the loader."""
        # The temp_docs_dir should already include general_docs.md from the fixture
        loader = MarkdownDocumentationLoader(docs_directory=str(temp_docs_dir), recursive=True, cache_enabled=False)

        documentation = loader.load_documentation()

        # Should have endpoints
        assert len(documentation.endpoints) > 0

        print("\n📄 General Docs Integration Test:")
        print("   Testing general docs loading functionality")

        # Check that general docs are loaded into the loader's _general_docs_content
        assert hasattr(loader, "_general_docs_content"), "Loader should have _general_docs_content attribute"
        general_docs_content = loader._general_docs_content
        assert general_docs_content is not None, "General docs content should be loaded"

        print(f"   General docs content length: {len(general_docs_content)} characters")

        # Check that general docs content is loaded correctly
        # Based on the general_docs.md fixture content
        general_docs_indicators = [
            "SynetoOS Authentication Service",
            "centralized authentication and authorization",
            "Quick Start",
            "Supported Authentication Methods",
            "Session Cookie Authentication",
            "Bearer Token Authentication",
            "API Key Authentication",
            "Error Handling",
        ]

        found_indicators = []
        for indicator in general_docs_indicators:
            if indicator in general_docs_content:
                found_indicators.append(indicator)

        print(f"   Found {len(found_indicators)}/{len(general_docs_indicators)} general docs indicators")
        for indicator in found_indicators:
            print(f"     ✓ {indicator}")

        # Should have at least some general docs content
        assert len(found_indicators) > 0, "Should load general documentation content"

        # Find a specific endpoint to test that it does NOT include general docs
        # Sort endpoints by description length to ensure consistent selection across environments
        session_posts = [
            ep for ep in documentation.endpoints if ep.path == "/v1/session" and ep.method == HTTPMethod.POST
        ]
        if session_posts:
            # Select the shortest description to ensure we get the specific endpoint content, not the general overview
            session_post = min(session_posts, key=lambda ep: len(ep.description or ""))

            # Warn about duplicates
            if len(session_posts) > 1:
                print(f"   ⚠️  WARNING: Found {len(session_posts)} duplicate POST /v1/session endpoints!")
                for i, ep in enumerate(session_posts):
                    print(f"      {i+1}. Description length: {len(ep.description or '')} characters")
                print("   💡 Consider using fmd-lint to detect and fix duplicate endpoint documentation.")
        else:
            session_post = None

        if session_post:
            description = session_post.description or ""

            # Should have endpoint-specific content
            # Updated to match content that actually appears in the extracted description
            endpoint_indicators = [
                "Create a new authentication session",
                "Username/Password Authentication",
                "PIN Authentication",
                "support personnel",
                "Authentication Flow",
                "OTP disabled",
            ]

            found_endpoint_indicators = []
            for indicator in endpoint_indicators:
                if indicator in description:
                    found_endpoint_indicators.append(indicator)

            print(f"   Found {len(found_endpoint_indicators)}/{len(endpoint_indicators)} endpoint-specific indicators")
            for indicator in found_endpoint_indicators:
                print(f"     ✓ {indicator}")

            # Should have endpoint-specific content
            assert len(found_endpoint_indicators) > 0, "Should include endpoint-specific content"

            # Should NOT include general docs content in endpoint descriptions
            general_docs_in_endpoint = []
            for indicator in general_docs_indicators:
                if indicator in description:
                    general_docs_in_endpoint.append(indicator)

            assert len(general_docs_in_endpoint) == 0, "Endpoint descriptions should NOT include general docs content"

            print("   ✅ General docs loading working correctly!")

        else:
            print("   ⚠️  POST /v1/session endpoint not found, skipping endpoint test")

    def test_doorman_docs_with_custom_general_docs(self, doorman_docs_path: Any) -> None:
        """Test using a custom general docs file with Doorman documentation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Copy doorman docs
            for md_file in doorman_docs_path.glob("*.md"):
                if "_docs.md" in md_file.name:
                    dest_path = temp_path / md_file.name
                    shutil.copy2(md_file, dest_path)

            # Create a custom general docs file
            custom_general_content = """# Custom API Documentation

## Project Overview

This is a custom general documentation file for testing.

### Custom Authentication

Custom authentication information.

### Custom Features

- Feature A
- Feature B
- Feature C
"""
            custom_general_file = temp_path / "custom_general.md"
            custom_general_file.write_text(custom_general_content)

            # Test with custom general docs file
            loader = MarkdownDocumentationLoader(
                docs_directory=str(temp_path),
                general_docs_file="custom_general.md",
                recursive=True,
                cache_enabled=False,
            )

            documentation = loader.load_documentation()

            # Should have endpoints
            assert len(documentation.endpoints) > 0

            print("\n📄 Custom General Docs Test:")
            print("   Testing with custom general docs file")

            # Check that custom general docs are loaded into the loader's _general_docs_content
            assert hasattr(loader, "_general_docs_content"), "Loader should have _general_docs_content attribute"
            general_docs_content = loader._general_docs_content
            assert general_docs_content is not None, "Custom general docs content should be loaded"

            print(f"   General docs content length: {len(general_docs_content)} characters")

            # Should include custom general docs content in the loader
            assert "# Custom API Documentation" in general_docs_content
            assert "This is a custom general documentation file" in general_docs_content
            assert "### Custom Authentication" in general_docs_content
            assert "### Custom Features" in general_docs_content
            assert "Feature A" in general_docs_content

            # Check that endpoint descriptions do NOT include custom general docs
            endpoint = documentation.endpoints[0]
            description = endpoint.description or ""

            print(f"   Endpoint description length: {len(description)} characters")

            # Should NOT include custom general docs content in endpoint descriptions
            assert "# Custom API Documentation" not in description
            assert "This is a custom general documentation file" not in description
            assert "### Custom Authentication" not in description
            assert "### Custom Features" not in description

            print("   ✅ Custom general docs file working correctly!")

        print("\n   ✅ All integration tests passed! The library successfully handles real Doorman documentation.")
