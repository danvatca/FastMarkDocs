"""
Copyright (c) 2025 Dan Vatca

Code sample generation for FastMarkDocs.

This module provides the CodeSampleGenerator class for generating
code samples in multiple programming languages from API endpoint definitions.
"""

import json
from typing import Any, Optional
from urllib.parse import urlencode, urljoin

from .exceptions import CodeSampleGenerationError
from .types import CodeLanguage, CodeSample, CodeSampleTemplate, EndpointDocumentation


class CodeSampleGenerator:
    """
    Generates code samples in multiple programming languages for API endpoints.

    This class provides templates and generation logic for creating code samples
    that demonstrate how to call API endpoints using various programming languages
    and tools.
    """

    def __init__(
        self,
        base_url: str = "https://api.example.com",
        custom_headers: Optional[dict[str, str]] = None,
        code_sample_languages: Optional[list[CodeLanguage]] = None,
        server_urls: Optional[list[str]] = None,
        authentication_schemes: Optional[list[str]] = None,
        custom_templates: Optional[dict[CodeLanguage, str]] = None,
        cache_enabled: bool = False,
    ):
        """
        Initialize the code sample generator.

        Args:
            base_url: Base URL for API requests
            custom_headers: Custom headers to include in requests
            code_sample_languages: Languages to generate samples for
            server_urls: List of server URLs
            authentication_schemes: Authentication schemes to support
            custom_templates: Custom templates for code generation
            cache_enabled: Whether to enable caching
        """
        self.base_url = base_url
        self.custom_headers = custom_headers or {}
        self.code_sample_languages = code_sample_languages or [
            CodeLanguage.CURL,
            CodeLanguage.PYTHON,
            CodeLanguage.JAVASCRIPT,
        ]
        self.server_urls = server_urls or [base_url]
        self.authentication_schemes = authentication_schemes or []
        self.custom_templates = custom_templates or {}
        self.cache_enabled = cache_enabled
        self._cache: Optional[dict[str, Any]] = {} if cache_enabled else None

        # Initialize templates
        self._templates = self._initialize_templates()

    def generate_samples_for_endpoint(self, endpoint: EndpointDocumentation) -> list[CodeSample]:
        """
        Generate code samples for an endpoint in all configured languages.

        Args:
            endpoint: Endpoint documentation

        Returns:
            List of generated code samples

        Raises:
            CodeSampleGenerationError: If generation fails
        """
        samples = []

        for language in self.code_sample_languages:
            try:
                if language == CodeLanguage.CURL:
                    sample = self.generate_curl_sample(endpoint)
                elif language == CodeLanguage.PYTHON:
                    sample = self.generate_python_sample(endpoint)
                elif language == CodeLanguage.JAVASCRIPT:
                    sample = self.generate_javascript_sample(endpoint)
                elif language == CodeLanguage.TYPESCRIPT:
                    sample = self.generate_typescript_sample(endpoint)
                elif language == CodeLanguage.GO:
                    sample = self.generate_go_sample(endpoint)
                elif language == CodeLanguage.JAVA:
                    sample = self.generate_java_sample(endpoint)
                elif language == CodeLanguage.PHP:
                    sample = self.generate_php_sample(endpoint)
                elif language == CodeLanguage.RUBY:
                    sample = self.generate_ruby_sample(endpoint)
                elif language == CodeLanguage.CSHARP:
                    sample = self.generate_csharp_sample(endpoint)
                else:
                    sample = self._generate_sample_for_language(endpoint, language.value)

                if sample:
                    samples.append(sample)

            except Exception as e:
                # Handle case where endpoint is None
                endpoint_info = "unknown"
                if endpoint:
                    try:
                        endpoint_info = f"{endpoint.method}:{endpoint.path}"
                    except AttributeError:
                        endpoint_info = "invalid_endpoint"

                raise CodeSampleGenerationError(
                    language.value, endpoint_info, f"Failed to generate sample: {str(e)}"
                ) from e

        return samples

    def generate_curl_sample(
        self,
        endpoint: EndpointDocumentation,
        path_params: Optional[dict[str, Any]] = None,
        query_params: Optional[dict[str, Any]] = None,
        request_body: Any = None,
    ) -> CodeSample:
        """Generate a cURL code sample."""
        if not endpoint or not endpoint.path:
            raise CodeSampleGenerationError("curl", "unknown", "Endpoint path cannot be empty")

        url = self._build_url(endpoint.path, path_params, query_params)

        curl_parts = [f"curl -X {endpoint.method.value}"]
        curl_parts.append(f'"{url}"')

        # Add headers
        headers = dict(self.custom_headers)
        if request_body:
            headers.setdefault("Content-Type", "application/json")

        # Add authentication headers if schemes are configured
        if "bearer" in self.authentication_schemes:
            headers["Authorization"] = "Bearer YOUR_TOKEN_HERE"
        elif "api_key" in self.authentication_schemes:
            headers["X-API-Key"] = "YOUR_API_KEY_HERE"
        elif "basic" in self.authentication_schemes:
            headers["Authorization"] = "Basic YOUR_CREDENTIALS_HERE"

        for key, value in headers.items():
            curl_parts.append(f'-H "{key}: {value}"')

        # Add body
        if request_body:
            if isinstance(request_body, (dict, list)):
                body_str = json.dumps(request_body, indent=2)
            else:
                body_str = str(request_body)
            curl_parts.append(f"-d '{body_str}'")

        code = " \\\n  ".join(curl_parts)

        return CodeSample(language=CodeLanguage.CURL, code=code, title="cURL Request")

    def generate_python_sample(
        self,
        endpoint: EndpointDocumentation,
        path_params: Optional[dict[str, Any]] = None,
        query_params: Optional[dict[str, Any]] = None,
        request_body: Any = None,
    ) -> CodeSample:
        """Generate a Python code sample."""
        # Check if there's a custom template for Python
        if CodeLanguage.PYTHON in self.custom_templates:
            return self._generate_from_template(endpoint, CodeLanguage.PYTHON, path_params, query_params, request_body)

        url = self._build_url(endpoint.path, path_params, query_params)

        code_lines = ["import requests"]
        code_lines.append("")

        # Prepare request parameters
        if request_body:
            if isinstance(request_body, (dict, list)):
                code_lines.append(f"response = requests.{endpoint.method.value.lower()}(")
                code_lines.append(f'    "{url}",')
                code_lines.append(f"    json={json.dumps(request_body, indent=4)}")
            else:
                code_lines.append(f"response = requests.{endpoint.method.value.lower()}(")
                code_lines.append(f'    "{url}",')
                code_lines.append(f'    data="{request_body}"')
        else:
            code_lines.append(f'response = requests.{endpoint.method.value.lower()}("{url}"')

        # Add headers
        headers = dict(self.custom_headers)

        # Add authentication headers if schemes are configured
        if "bearer" in self.authentication_schemes:
            headers["Authorization"] = "Bearer YOUR_TOKEN_HERE"
        elif "api_key" in self.authentication_schemes:
            headers["X-API-Key"] = "YOUR_API_KEY_HERE"
        elif "basic" in self.authentication_schemes:
            headers["Authorization"] = "Basic YOUR_CREDENTIALS_HERE"

        if headers:
            code_lines.append(f"    headers={json.dumps(headers, indent=4)}")

        code_lines.append(")")
        code_lines.append("")
        code_lines.append("print(f'Status: {response.status_code}')")
        code_lines.append("print(f'Response: {response.json()}')")

        return CodeSample(language=CodeLanguage.PYTHON, code="\n".join(code_lines), title="Python Request")

    def generate_javascript_sample(
        self,
        endpoint: EndpointDocumentation,
        path_params: Optional[dict[str, Any]] = None,
        query_params: Optional[dict[str, Any]] = None,
        request_body: Any = None,
    ) -> CodeSample:
        """Generate a JavaScript code sample."""
        url = self._build_url(endpoint.path, path_params, query_params)

        code_lines = []

        # Prepare fetch options
        headers = dict(self.custom_headers)
        options: dict[str, Any] = {"method": endpoint.method.value, "headers": headers}

        if request_body:
            headers["Content-Type"] = "application/json"
            if isinstance(request_body, (dict, list)):
                options["body"] = "JSON.stringify(" + json.dumps(request_body) + ")"
            else:
                options["body"] = f'"{request_body}"'

        code_lines.append(f'fetch("{url}", {{')
        code_lines.append(f"  method: '{endpoint.method.value}',")

        if headers:
            code_lines.append("  headers: {")
            for key, value in headers.items():
                code_lines.append(f'    "{key}": "{value}",')
            code_lines.append("  },")

        if request_body:
            if isinstance(request_body, (dict, list)):
                code_lines.append(f"  body: JSON.stringify({json.dumps(request_body)})")
            else:
                code_lines.append(f'  body: "{request_body}"')

        code_lines.append("})")
        code_lines.append(".then(response => response.json())")
        code_lines.append(".then(data => console.log(data))")
        code_lines.append('.catch(error => console.error("Error:", error));')

        return CodeSample(language=CodeLanguage.JAVASCRIPT, code="\n".join(code_lines), title="JavaScript Request")

    def generate_typescript_sample(self, endpoint: EndpointDocumentation) -> CodeSample:
        """Generate a TypeScript code sample."""
        url = self._build_url(endpoint.path)

        # Generate TypeScript with proper type annotations and async/await
        code = f"""// TypeScript example
interface ApiResponse {{
  [key: string]: any;
}}

const fetchData = async (): Promise<ApiResponse> => {{
  try {{
    const response = await fetch("{url}", {{
      method: "{endpoint.method.value}",
      headers: {{
        "Content-Type": "application/json",
      }},
    }});

    if (!response.ok) {{
      throw new Error(`HTTP error! status: ${{response.status}}`);
    }}

    const data: ApiResponse = await response.json();
    return data;
  }} catch (error) {{
    console.error("Error:", error);
    throw error;
  }}
}};

// Usage
fetchData().then(data => console.log(data));"""

        return CodeSample(language=CodeLanguage.TYPESCRIPT, code=code, title="TypeScript Request")

    def generate_go_sample(self, endpoint: EndpointDocumentation) -> CodeSample:
        """Generate a Go code sample."""
        url = self._build_url(endpoint.path)

        # Prepare headers
        headers = dict(self.custom_headers)

        # Add authentication headers if schemes are configured
        if "bearer" in self.authentication_schemes:
            headers["Authorization"] = "Bearer YOUR_TOKEN_HERE"
        elif "api_key" in self.authentication_schemes:
            headers["X-API-Key"] = "YOUR_API_KEY_HERE"
        elif "basic" in self.authentication_schemes:
            headers["Authorization"] = "Basic YOUR_CREDENTIALS_HERE"

        # Build header setting code
        header_code = ""
        if headers:
            for key, value in headers.items():
                header_code += f'    req.Header.Set("{key}", "{value}")\n'

        code = f"""package main

import (
    "fmt"
    "net/http"
    "io/ioutil"
)

func main() {{
    req, err := http.NewRequest("{endpoint.method.value}", "{url}", nil)
    if err != nil {{
        panic(err)
    }}

{header_code}    client := &http.Client{{}}
    resp, err := client.Do(req)
    if err != nil {{
        panic(err)
    }}
    defer resp.Body.Close()

    body, err := ioutil.ReadAll(resp.Body)
    if err != nil {{
        panic(err)
    }}

    fmt.Printf("Status: %s\\n", resp.Status)
    fmt.Printf("Response: %s\\n", string(body))
}}"""

        return CodeSample(language=CodeLanguage.GO, code=code, title="Go Request")

    def generate_java_sample(self, endpoint: EndpointDocumentation) -> CodeSample:
        """Generate a Java code sample."""
        url = self._build_url(endpoint.path)

        code = f"""import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;

public class ApiExample {{
    public static void main(String[] args) throws Exception {{
        HttpClient client = HttpClient.newHttpClient();

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("{url}"))
            .{endpoint.method.value.lower()}()
            .build();

        HttpResponse<String> response = client.send(request,
            HttpResponse.BodyHandlers.ofString());

        System.out.println("Status: " + response.statusCode());
        System.out.println("Response: " + response.body());
    }}
}}"""

        return CodeSample(language=CodeLanguage.JAVA, code=code, title="Java Request")

    def generate_php_sample(self, endpoint: EndpointDocumentation) -> CodeSample:
        """Generate a PHP code sample."""
        url = self._build_url(endpoint.path)

        code = f"""<?php
$curl = curl_init();

curl_setopt_array($curl, array(
    CURLOPT_URL => "{url}",
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_CUSTOMREQUEST => "{endpoint.method.value}",
));

$response = curl_exec($curl);
$httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);

curl_close($curl);

echo "Status: " . $httpCode . "\\n";
echo "Response: " . $response . "\\n";
?>"""

        return CodeSample(language=CodeLanguage.PHP, code=code, title="PHP Request")

    def generate_ruby_sample(self, endpoint: EndpointDocumentation) -> CodeSample:
        """Generate a Ruby code sample."""
        url = self._build_url(endpoint.path)

        code = f'''require 'net/http'
require 'uri'
require 'json'

uri = URI.parse("{url}")
http = Net::HTTP.new(uri.host, uri.port)
http.use_ssl = true if uri.scheme == 'https'

request = Net::HTTP::{endpoint.method.value.title()}.new(uri)

response = http.request(request)

puts "Status: #{{response.code}}"
puts "Response: #{{response.body}}"'''

        return CodeSample(language=CodeLanguage.RUBY, code=code, title="Ruby Request")

    def generate_csharp_sample(self, endpoint: EndpointDocumentation) -> CodeSample:
        """Generate a C# code sample."""
        url = self._build_url(endpoint.path)

        code = f"""using System;
using System.Net.Http;
using System.Threading.Tasks;

class Program
{{
    static async Task Main(string[] args)
    {{
        using var client = new HttpClient();

        var response = await client.{endpoint.method.value.title()}Async("{url}");
        var content = await response.Content.ReadAsStringAsync();

        Console.WriteLine($"Status: {{response.StatusCode}}");
        Console.WriteLine($"Response: {{content}}");
    }}
}}"""

        return CodeSample(language=CodeLanguage.CSHARP, code=code, title="C# Request")

    def _generate_sample_for_language(self, endpoint: EndpointDocumentation, language: str) -> CodeSample:
        """Generate a sample for an unsupported language (raises error)."""
        raise CodeSampleGenerationError(
            language, f"{endpoint.method}:{endpoint.path}", f"Unsupported language: {language}"
        )

    def _generate_from_template(
        self,
        endpoint: EndpointDocumentation,
        language: CodeLanguage,
        path_params: Optional[dict[str, Any]] = None,
        query_params: Optional[dict[str, Any]] = None,
        request_body: Any = None,
    ) -> CodeSample:
        """Generate a code sample from a custom template."""
        template = self.custom_templates.get(language)
        if not template:
            raise CodeSampleGenerationError(
                language.value, f"{endpoint.method}:{endpoint.path}", f"No custom template found for {language.value}"
            )

        # Build URL and prepare template variables
        url = self._build_url(endpoint.path, path_params, query_params)

        # Template variables
        template_vars = {
            "method": endpoint.method.value,
            "method_lower": endpoint.method.value.lower(),
            "path": endpoint.path,
            "url": url,
            "base_url": self.base_url,
            "summary": endpoint.summary or "",
            "description": endpoint.description or "",
        }

        # Format the template
        try:
            code = template.format(**template_vars)
            # Clean up any extra whitespace
            code = code.strip()

            return CodeSample(language=language, code=code, title=f"{language.value.title()} Request")
        except KeyError as e:
            raise CodeSampleGenerationError(
                language.value, f"{endpoint.method}:{endpoint.path}", f"Template variable not found: {e}"
            ) from e

    def _build_url(
        self, path: str, path_params: Optional[dict[str, Any]] = None, query_params: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Build a complete URL from path and parameters.

        Args:
            path: API path
            path_params: Path parameters to substitute
            query_params: Query parameters to append

        Returns:
            Complete URL
        """
        # Use the first server URL or base URL
        base = self.server_urls[0] if self.server_urls else self.base_url

        # Substitute path parameters
        if path_params:
            for key, value in path_params.items():
                path = path.replace(f"{{{key}}}", str(value))

        # Build full URL
        url = urljoin(base.rstrip("/") + "/", path.lstrip("/"))

        # Add query parameters
        if query_params:
            # Convert boolean values to lowercase strings
            formatted_params = {}
            for key, value in query_params.items():
                if isinstance(value, bool):
                    formatted_params[key] = str(value).lower()
                else:
                    formatted_params[key] = str(value)

            query_string = urlencode(formatted_params)
            url = f"{url}?{query_string}"

        return url

    def _initialize_templates(self) -> dict[CodeLanguage, CodeSampleTemplate]:
        """Initialize code templates for all supported languages."""
        templates = {}

        # Use custom templates if provided
        for language, template_str in self.custom_templates.items():
            templates[language] = CodeSampleTemplate(language=language, template=template_str)

        return templates
