"""
Unit tests for the fmd-init tool functionality.
"""

import tempfile
from pathlib import Path

from fastmarkdocs.scaffolder import (
    DocumentationInitializer,
    EndpointInfo,
    FastAPIEndpointScanner,
    MarkdownScaffoldGenerator,
)


class TestEndpointInfo:
    """Test the EndpointInfo dataclass."""

    def test_endpoint_info_creation(self) -> None:
        """Test creating an EndpointInfo instance."""
        endpoint = EndpointInfo(
            method="GET",
            path="/users",
            function_name="get_users",
            file_path="api/users.py",
            line_number=42,
            summary="Get all users",
            description="Retrieve a list of all users in the system",
            tags=["users"],
        )

        assert endpoint.method == "GET"
        assert endpoint.path == "/users"
        assert endpoint.function_name == "get_users"
        assert endpoint.file_path == "api/users.py"
        assert endpoint.line_number == 42
        assert endpoint.summary == "Get all users"
        assert endpoint.description == "Retrieve a list of all users in the system"
        assert endpoint.tags == ["users"]

    def test_endpoint_info_defaults(self) -> None:
        """Test EndpointInfo with default values."""
        endpoint = EndpointInfo(
            method="POST", path="/users", function_name="create_user", file_path="api/users.py", line_number=10
        )

        assert endpoint.method == "POST"
        assert endpoint.path == "/users"
        assert endpoint.docstring is None
        assert endpoint.summary is None
        assert endpoint.description is None
        assert endpoint.tags == []  # Should be initialized to empty list

    def test_endpoint_info_post_init(self) -> None:
        """Test that __post_init__ initializes tags to empty list when None."""
        endpoint = EndpointInfo(
            method="GET", path="/test", function_name="test_func", file_path="test.py", line_number=1, tags=None
        )

        assert endpoint.tags == []


class TestFastAPIEndpointScanner:
    """Test the FastAPIEndpointScanner class."""

    def test_scanner_initialization(self) -> None:
        """Test scanner initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            scanner = FastAPIEndpointScanner(temp_dir)

            assert scanner.source_directory == Path(temp_dir)
            assert scanner.endpoints == []
            assert "get" in scanner.http_method_decorators
            assert scanner.http_method_decorators["get"] == "GET"

    def test_scan_empty_directory(self) -> None:
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            assert endpoints == []

    def test_scan_directory_with_simple_endpoint(self) -> None:
        """Test scanning a directory with a simple FastAPI endpoint."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a Python file with a FastAPI endpoint
            api_file = Path(temp_dir) / "api.py"
            api_file.write_text(
                '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    """Get all users from the system."""
    return {"users": []}
'''
            )

            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            assert len(endpoints) == 1
            endpoint = endpoints[0]
            assert endpoint.method == "GET"
            assert endpoint.path == "/users"
            assert endpoint.function_name == "get_users"
            assert endpoint.file_path == "api.py"
            assert endpoint.summary == "Get all users from the system."

    def test_scan_directory_with_multiple_endpoints(self) -> None:
        """Test scanning with multiple endpoints and HTTP methods."""
        with tempfile.TemporaryDirectory() as temp_dir:
            api_file = Path(temp_dir) / "api.py"
            api_file.write_text(
                '''
from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter()

@app.get("/users")
def get_users():
    """Get all users."""
    return {"users": []}

@app.post("/users")
def create_user():
    """Create a new user."""
    return {"user": {}}

@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Delete a specific user."""
    return {"deleted": True}
'''
            )

            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            assert len(endpoints) == 3

            # Check methods and paths
            methods_paths = [(e.method, e.path) for e in endpoints]
            assert ("GET", "/users") in methods_paths
            assert ("POST", "/users") in methods_paths
            assert ("DELETE", "/users/{user_id}") in methods_paths

    def test_scan_with_tags(self) -> None:
        """Test scanning endpoints with tags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            api_file = Path(temp_dir) / "api.py"
            api_file.write_text(
                '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users", tags=["users", "admin"])
def get_users():
    """Get all users."""
    return {"users": []}

@app.post("/orders", tags=["orders"])
def create_order():
    """Create an order."""
    return {"order": {}}
'''
            )

            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            assert len(endpoints) == 2

            users_endpoint = next(e for e in endpoints if e.path == "/users")
            orders_endpoint = next(e for e in endpoints if e.path == "/orders")

            assert users_endpoint.tags == ["users", "admin"]
            assert orders_endpoint.tags == ["orders"]

    def test_scan_with_complex_docstring(self) -> None:
        """Test scanning with complex docstrings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            api_file = Path(temp_dir) / "api.py"
            api_file.write_text(
                '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    """Get all users from the system.

    This endpoint returns a comprehensive list of all users
    with their profile information and current status.

    Returns:
        List of user objects with detailed information.
    """
    return {"users": []}
'''
            )

            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            assert len(endpoints) == 1
            endpoint = endpoints[0]
            assert endpoint.summary == "Get all users from the system."
            assert "This endpoint returns a comprehensive list" in endpoint.description
            assert "Returns:" in endpoint.description

    def test_scan_ignores_non_fastapi_decorators(self) -> None:
        """Test that scanner ignores non-FastAPI decorators."""
        with tempfile.TemporaryDirectory() as temp_dir:
            api_file = Path(temp_dir) / "api.py"
            api_file.write_text(
                '''
from fastapi import FastAPI

app = FastAPI()

@property
def some_property():
    return "not an endpoint"

@staticmethod
def some_static_method():
    return "not an endpoint"

@app.get("/users")
def get_users():
    """Real endpoint."""
    return {"users": []}
'''
            )

            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            assert len(endpoints) == 1
            assert endpoints[0].path == "/users"

    def test_scan_handles_syntax_errors(self) -> None:
        """Test that scanner handles files with syntax errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file with syntax error
            bad_file = Path(temp_dir) / "bad.py"
            bad_file.write_text(
                """
from fastapi import FastAPI

app = FastAPI()

@app.get("/users"  # Missing closing parenthesis
def get_users():
    return {"users": []}
"""
            )

            # Create a good file
            good_file = Path(temp_dir) / "good.py"
            good_file.write_text(
                """
from fastapi import FastAPI

app = FastAPI()

@app.get("/orders")
def get_orders():
    return {"orders": []}
"""
            )

            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            # Should only find the endpoint from the good file
            assert len(endpoints) == 1
            assert endpoints[0].path == "/orders"

    def test_scan_handles_binary_files(self) -> None:
        """Test that scanner handles binary files gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a binary file
            binary_file = Path(temp_dir) / "binary.py"
            binary_file.write_bytes(b"\x00\x01\x02\x03")

            # Create a good file
            good_file = Path(temp_dir) / "good.py"
            good_file.write_text(
                """
from fastapi import FastAPI

app = FastAPI()

@app.get("/test")
def test_endpoint():
    return {"test": True}
"""
            )

            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            # Should only find the endpoint from the good file
            assert len(endpoints) == 1
            assert endpoints[0].path == "/test"


class TestMarkdownScaffoldGenerator:
    """Test the MarkdownScaffoldGenerator class."""

    def test_generator_initialization(self) -> None:
        """Test generator initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)

            assert generator.output_directory == Path(temp_dir)
            assert generator.output_directory.exists()

    def test_generate_scaffolding_empty_endpoints(self) -> None:
        """Test generating scaffolding with no endpoints."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)
            result = generator.generate_scaffolding([])

            assert result == {}

    def test_generate_scaffolding_single_endpoint(self) -> None:
        """Test generating scaffolding for a single endpoint."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)

            endpoint = EndpointInfo(
                method="GET",
                path="/users",
                function_name="get_users",
                file_path="api/users.py",
                line_number=10,
                summary="Get all users",
                description="Retrieve all users from the database",
                tags=["users"],
            )

            result = generator.generate_scaffolding([endpoint])

            assert len(result) == 1
            file_path = list(result.keys())[0]
            content = result[file_path]

            assert "users.md" in file_path
            assert "# Users API Documentation" in content
            assert "## GET /users" in content
            assert "**Summary:** Get all users" in content
            assert "Retrieve all users from the database" in content
            assert "**Function:** `get_users`" in content
            assert "**File:** `api/users.py:10`" in content

    def test_generate_scaffolding_multiple_endpoints_same_tag(self) -> None:
        """Test generating scaffolding for multiple endpoints with same tag."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)

            endpoints = [
                EndpointInfo(
                    method="GET",
                    path="/users",
                    function_name="get_users",
                    file_path="api/users.py",
                    line_number=10,
                    tags=["users"],
                ),
                EndpointInfo(
                    method="POST",
                    path="/users",
                    function_name="create_user",
                    file_path="api/users.py",
                    line_number=20,
                    tags=["users"],
                ),
            ]

            result = generator.generate_scaffolding(endpoints)

            assert len(result) == 1
            content = list(result.values())[0]

            assert "## GET /users" in content
            assert "## POST /users" in content

    def test_generate_scaffolding_multiple_tags(self) -> None:
        """Test generating scaffolding for endpoints with different tags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)

            endpoints = [
                EndpointInfo(
                    method="GET",
                    path="/users",
                    function_name="get_users",
                    file_path="api/users.py",
                    line_number=10,
                    tags=["users"],
                ),
                EndpointInfo(
                    method="GET",
                    path="/orders",
                    function_name="get_orders",
                    file_path="api/orders.py",
                    line_number=15,
                    tags=["orders"],
                ),
            ]

            result = generator.generate_scaffolding(endpoints)

            assert len(result) == 2

            # Check that both files were created
            file_paths = list(result.keys())
            assert any("users.md" in path for path in file_paths)
            assert any("orders.md" in path for path in file_paths)

    def test_generate_scaffolding_no_tags(self) -> None:
        """Test generating scaffolding for endpoints without tags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)

            endpoint = EndpointInfo(
                method="GET",
                path="/health",
                function_name="health_check",
                file_path="api/health.py",
                line_number=5,
                tags=[],
            )

            result = generator.generate_scaffolding([endpoint])

            assert len(result) == 1
            file_path = list(result.keys())[0]

            assert "api.md" in file_path  # Default group name

    def test_generate_endpoint_section_with_all_fields(self) -> None:
        """Test generating endpoint section with all fields populated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)

            endpoint = EndpointInfo(
                method="POST",
                path="/users/{user_id}/orders",
                function_name="create_user_order",
                file_path="api/orders.py",
                line_number=25,
                summary="Create order for user",
                description="Create a new order for the specified user with validation",
                tags=["orders", "users"],
            )

            section = generator._generate_endpoint_section(endpoint)

            assert "## POST /users/{user_id}/orders" in section
            assert "**Summary:** Create order for user" in section
            assert "Create a new order for the specified user with validation" in section
            assert "**Function:** `create_user_order`" in section
            assert "**File:** `api/orders.py:25`" in section
            assert "**Tags:** orders, users" in section
            assert "### Parameters" in section
            assert "### Response Examples" in section
            assert "### Code Examples" in section

    def test_generate_endpoint_section_minimal_fields(self) -> None:
        """Test generating endpoint section with minimal fields."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = MarkdownScaffoldGenerator(temp_dir)

            endpoint = EndpointInfo(
                method="GET", path="/status", function_name="get_status", file_path="api/status.py", line_number=1
            )

            section = generator._generate_endpoint_section(endpoint)

            assert "## GET /status" in section
            assert "**Summary:** Get /status" in section  # Generated summary
            assert "TODO: Add detailed description" in section
            assert "**Function:** `get_status`" in section
            assert "**File:** `api/status.py:1`" in section
            assert "**Tags:**" not in section  # No tags section if empty


class TestDocumentationInitializer:
    """Test the DocumentationInitializer class."""

    def test_initializer_creation(self) -> None:
        """Test creating a DocumentationInitializer."""
        with tempfile.TemporaryDirectory() as temp_dir:
            initializer = DocumentationInitializer(temp_dir, temp_dir)

            assert initializer.source_directory == temp_dir
            assert initializer.output_directory == temp_dir
            assert isinstance(initializer.scanner, FastAPIEndpointScanner)
            assert isinstance(initializer.generator, MarkdownScaffoldGenerator)

    def test_initialize_no_endpoints(self) -> None:
        """Test initialization when no endpoints are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            initializer = DocumentationInitializer(temp_dir, temp_dir)

            result = initializer.initialize()

            assert result["endpoints_found"] == 0
            assert result["files_generated"] == {}
            assert "No endpoints discovered" in result["summary"]

    def test_initialize_with_endpoints(self) -> None:
        """Test initialization with discovered endpoints."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a Python file with endpoints
            api_file = Path(temp_dir) / "api.py"
            api_file.write_text(
                '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users", tags=["users"])
def get_users():
    """Get all users."""
    return {"users": []}

@app.post("/orders", tags=["orders"])
def create_order():
    """Create an order."""
    return {"order": {}}
'''
            )

            output_dir = Path(temp_dir) / "docs"
            initializer = DocumentationInitializer(temp_dir, str(output_dir))

            result = initializer.initialize()

            assert result["endpoints_found"] == 2
            assert len(result["files_generated"]) == 2
            assert "Documentation Initialization Complete" in result["summary"]
            assert "GET: 1" in result["summary"]
            assert "POST: 1" in result["summary"]

    def test_create_summary(self) -> None:
        """Test summary creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            initializer = DocumentationInitializer(temp_dir, temp_dir)

            endpoints = [
                EndpointInfo("GET", "/users", "get_users", "api.py", 1),
                EndpointInfo("POST", "/users", "create_user", "api.py", 2),
                EndpointInfo("GET", "/orders", "get_orders", "api.py", 3),
            ]

            generated_files = {"docs/users.md": "content1", "docs/orders.md": "content2"}

            summary = initializer._create_summary(endpoints, generated_files)

            assert "**Endpoints discovered:** 3" in summary
            assert "**Files generated:** 2" in summary
            assert "GET: 2" in summary
            assert "POST: 1" in summary
            assert "docs/users.md" in summary
            assert "docs/orders.md" in summary
            assert "Next steps:" in summary
