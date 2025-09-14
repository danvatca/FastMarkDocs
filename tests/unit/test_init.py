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
    RouterInfo,
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
            sections=["users"],
        )

        assert endpoint.method == "GET"
        assert endpoint.path == "/users"
        assert endpoint.function_name == "get_users"
        assert endpoint.file_path == "api/users.py"
        assert endpoint.line_number == 42
        assert endpoint.summary == "Get all users"
        assert endpoint.description == "Retrieve a list of all users in the system"
        assert endpoint.sections == ["users"]

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
        assert endpoint.sections == []  # Should be initialized to empty list

    def test_endpoint_info_post_init(self) -> None:
        """Test that __post_init__ initializes sections to empty list when None."""
        endpoint = EndpointInfo(
            method="GET", path="/test", function_name="test_func", file_path="test.py", line_number=1, sections=None
        )

        assert endpoint.sections == []


class TestRouterInfo:
    """Test the RouterInfo dataclass."""

    def test_router_info_creation(self) -> None:
        """Test creating a RouterInfo instance."""
        router = RouterInfo(name="user_router", tags=["users", "admin"], prefix="/users", line_number=10)

        assert router.name == "user_router"
        assert router.tags == ["users", "admin"]
        assert router.prefix == "/users"
        assert router.line_number == 10

    def test_router_info_minimal(self) -> None:
        """Test RouterInfo with minimal required fields."""
        router = RouterInfo(name="api_router", tags=["api"])

        assert router.name == "api_router"
        assert router.tags == ["api"]
        assert router.prefix is None
        assert router.line_number is None


class TestFastAPIEndpointScanner:
    """Test the FastAPIEndpointScanner class."""

    def test_scanner_initialization(self) -> None:
        """Test scanner initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            scanner = FastAPIEndpointScanner(temp_dir)

            assert scanner.source_directory == Path(temp_dir)
            assert scanner.endpoints == []

    def test_scan_empty_directory(self) -> None:
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            assert endpoints == []

    def test_scan_directory_with_simple_endpoint(self) -> None:
        """Test scanning directory with a simple endpoint."""
        with tempfile.TemporaryDirectory() as temp_dir:
            api_file = Path(temp_dir) / "api.py"
            api_file.write_text(
                '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    """Get all users."""
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
            assert endpoint.summary == "Get all users."
            assert endpoint.sections == ["User Management"]  # Inferred from path

    def test_scan_directory_with_multiple_endpoints(self) -> None:
        """Test scanning directory with multiple endpoints."""
        with tempfile.TemporaryDirectory() as temp_dir:
            api_file = Path(temp_dir) / "api.py"
            api_file.write_text(
                '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    """Get all users."""
    return {"users": []}

@app.post("/users")
def create_user():
    """Create a user."""
    return {"user": {}}

@app.get("/orders")
def get_orders():
    return {"orders": []}
'''
            )

            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            assert len(endpoints) == 3

            methods = [ep.method for ep in endpoints]
            paths = [ep.path for ep in endpoints]

            assert "GET" in methods
            assert "POST" in methods
            assert "/users" in paths
            assert "/orders" in paths

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

            users_endpoint = next(ep for ep in endpoints if ep.path == "/users")
            orders_endpoint = next(ep for ep in endpoints if ep.path == "/orders")

            assert users_endpoint.sections == ["users"]  # First tag used as section
            assert orders_endpoint.sections == ["orders"]  # Tag used as section

    def test_scan_with_router_level_tags(self) -> None:
        """Test scanning endpoints with router-level tags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            api_file = Path(temp_dir) / "users.py"
            api_file.write_text(
                    '''
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("")
def get_users():
    """Get all users."""
    return {"users": []}

@router.post("")
def create_user():
    """Create a user."""
    return {"user": {}}

@router.get("/{user_id}")
def get_user(user_id: int):
    """Get a specific user."""
    return {"user": {}}
'''
            )

            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            assert len(endpoints) == 3

            # All endpoints should have router-level tags as section
            for endpoint in endpoints:
                assert endpoint.sections == ["users"]

            # Check path prefixes are applied
            paths = [ep.path for ep in endpoints]
            assert "/users" in paths  # From @router.get("")
            assert "/users/{user_id}" in paths  # From @router.get("/{user_id}")

    def test_scan_with_mixed_router_and_endpoint_tags(self) -> None:
        """Test scanning with both router-level and endpoint-level tags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            api_file = Path(temp_dir) / "mixed.py"
            api_file.write_text(
                '''
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/users", tags=["users"])
def get_users():
    """Get all users."""
    return {"users": []}

@router.post("/orders", tags=["orders", "admin"])
def create_order():
    """Create an order."""
    return {"order": {}}

@router.get("/health")
def health_check():
    """Health check."""
    return {"status": "ok"}
'''
            )

            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            assert len(endpoints) == 3

            users_endpoint = next(ep for ep in endpoints if "users" in ep.path)
            orders_endpoint = next(ep for ep in endpoints if "orders" in ep.path)
            health_endpoint = next(ep for ep in endpoints if "health" in ep.path)

            # Router tags are used as scaffolding hints, endpoint tags take precedence
            assert users_endpoint.sections == ["users"]  # endpoint tag takes precedence
            assert orders_endpoint.sections == ["orders"]  # first endpoint tag used
            assert health_endpoint.sections == ["api"]  # router tag used as fallback

    def test_scan_with_multiple_routers(self) -> None:
        """Test scanning file with multiple routers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            api_file = Path(temp_dir) / "multi_router.py"
            api_file.write_text(
                    """
from fastapi import APIRouter

users_router = APIRouter(prefix="/users", tags=["users"])
orders_router = APIRouter(prefix="/orders", tags=["orders"])

@users_router.get("")
def get_users():
    return {"users": []}

@users_router.post("")
def create_user():
    return {"user": {}}

@orders_router.get("")
def get_orders():
    return {"orders": []}

@orders_router.post("")
def create_order():
    return {"order": {}}
"""
            )

            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            assert len(endpoints) == 4

            user_endpoints = [ep for ep in endpoints if "users" in ep.sections]
            order_endpoints = [ep for ep in endpoints if "orders" in ep.sections]

            assert len(user_endpoints) == 2
            assert len(order_endpoints) == 2

            for ep in user_endpoints:
                assert ep.sections == ["users"]

            for ep in order_endpoints:
                assert ep.sections == ["orders"]

    def test_scan_with_complex_docstring(self) -> None:
        """Test scanning endpoint with complex docstring."""
        with tempfile.TemporaryDirectory() as temp_dir:
            api_file = Path(temp_dir) / "api.py"
            api_file.write_text(
                '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    """
    Get all users from the system.

    This endpoint returns a comprehensive list of all users
    registered in the system with their basic information.

    Returns:
        List of user objects with id, name, and email.
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

    def test_scan_recursive_directories(self) -> None:
        """Test that scanner works recursively across multiple subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create nested directory structure
            api_dir = temp_path / "api"
            v1_dir = api_dir / "v1"
            v2_dir = api_dir / "v2"
            services_dir = temp_path / "services"

            api_dir.mkdir()
            v1_dir.mkdir()
            v2_dir.mkdir()
            services_dir.mkdir()

            # Create endpoints in different directories
            # Root level
            (temp_path / "main.py").write_text(
                """
from fastapi import FastAPI
app = FastAPI()

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
"""
            )

            # api/ level
            (api_dir / "users.py").write_text(
                """
from fastapi import APIRouter
router = APIRouter(prefix="/users", tags=["users"])

@router.get("")
def get_users():
    return {"users": []}
"""
            )

            # api/v1/ level
            (v1_dir / "orders.py").write_text(
                """
from fastapi import APIRouter
router = APIRouter(prefix="/v1/orders", tags=["orders", "v1"])

@router.get("")
def get_orders():
    return {"orders": []}

@router.post("")
def create_order():
    return {"order": {}}
"""
            )

            # api/v2/ level
            (v2_dir / "products.py").write_text(
                """
from fastapi import APIRouter
router = APIRouter(prefix="/v2/products", tags=["products", "v2"])

@router.get("")
def get_products():
    return {"products": []}
"""
            )

            # services/ level
            (services_dir / "auth.py").write_text(
                """
from fastapi import APIRouter
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login():
    return {"token": "..."}
"""
            )

            # Scan recursively
            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            # Should find all endpoints across all directories
            assert len(endpoints) == 6

            # Check that endpoints from different directories are found
            paths = [ep.path for ep in endpoints]
            assert "/health" in paths  # from main.py
            assert "/users" in paths  # from api/users.py
            assert "/v1/orders" in paths  # from api/v1/orders.py
            assert "/v2/products" in paths  # from api/v2/products.py
            assert "/auth/login" in paths  # from services/auth.py

            # Check file paths are relative to source directory
            file_paths = [ep.file_path for ep in endpoints]
            assert "main.py" in file_paths
            assert "api/users.py" in file_paths
            assert "api/v1/orders.py" in file_paths
            assert "api/v2/products.py" in file_paths
            assert "services/auth.py" in file_paths

            # Check tags are properly inherited
            health_ep = next(ep for ep in endpoints if ep.path == "/health")
            users_ep = next(ep for ep in endpoints if ep.path == "/users")
            orders_ep = next(ep for ep in endpoints if ep.path == "/v1/orders")

            assert health_ep.sections == ["health"]  # From endpoint tag
            assert users_ep.sections == ["users"]
            assert orders_ep.sections == ["orders"]  # First tag from ["orders", "v1"]

    def test_scan_excludes_common_directories(self) -> None:
        """Test that scanner excludes common non-source directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directories that should be excluded
            excluded_dirs = ["__pycache__", ".git", ".pytest_cache", "htmlcov", ".venv", "node_modules"]

            for excluded_dir in excluded_dirs:
                dir_path = temp_path / excluded_dir
                dir_path.mkdir()

                # Add a Python file with an endpoint in the excluded directory
                (dir_path / "fake_api.py").write_text(
                    """
from fastapi import FastAPI
app = FastAPI()

@app.get("/should-not-be-found")
def fake_endpoint():
    return {"fake": True}
"""
                )

            # Add a legitimate endpoint in the root
            (temp_path / "real_api.py").write_text(
                """
from fastapi import FastAPI
app = FastAPI()

@app.get("/real-endpoint", tags=["real"])
def real_endpoint():
    return {"real": True}
"""
            )

            # Scan
            scanner = FastAPIEndpointScanner(temp_dir)
            endpoints = scanner.scan_directory()

            # Should only find the real endpoint, not the ones in excluded directories
            assert len(endpoints) == 1
            assert endpoints[0].path == "/real-endpoint"
            assert endpoints[0].file_path == "real_api.py"


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

            # Should create general_docs.md even with no endpoints
            assert len(result) == 1
            file_path = list(result.keys())[0]
            assert "general_docs.md" in file_path

            content = result[file_path]
            assert "# General API Documentation" in content
            assert "TODO:" in content  # Should contain TODO items

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
                sections=["users"],
            )

            result = generator.generate_scaffolding([endpoint])

            # Should create both general_docs.md and users.md
            assert len(result) == 2

            # Find the users.md file
            users_file = [path for path in result.keys() if "users.md" in path][0]
            content = result[users_file]

            assert "users.md" in users_file
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
                    sections=["users"],
                ),
                EndpointInfo(
                    method="POST",
                    path="/users",
                    function_name="create_user",
                    file_path="api/users.py",
                    line_number=20,
                    sections=["users"],
                ),
            ]

            result = generator.generate_scaffolding(endpoints)

            # Should create both general_docs.md and users.md
            assert len(result) == 2

            # Find the users.md file content
            users_content = [content for path, content in result.items() if "users.md" in path][0]

            assert "## GET /users" in users_content
            assert "## POST /users" in users_content

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
                    sections=["users"],
                ),
                EndpointInfo(
                    method="GET",
                    path="/orders",
                    function_name="get_orders",
                    file_path="api/orders.py",
                    line_number=15,
                    sections=["orders"],
                ),
            ]

            result = generator.generate_scaffolding(endpoints)

            # Should create general_docs.md, users.md, and orders.md
            assert len(result) == 3

            # Check that all files were created
            file_paths = list(result.keys())
            assert any("general_docs.md" in path for path in file_paths)
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
                sections=[],
            )

            result = generator.generate_scaffolding([endpoint])

            # Should create both general_docs.md and api.md
            assert len(result) == 2

            # Check that api.md was created (default group name)
            file_paths = list(result.keys())
            assert any("general_docs.md" in path for path in file_paths)
            assert any("api.md" in path for path in file_paths)

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
                sections=["orders", "users"],
            )

            section = generator._generate_endpoint_section(endpoint)

            assert "## POST /users/{user_id}/orders" in section
            assert "**Summary:** Create order for user" in section
            assert "Create a new order for the specified user with validation" in section
            assert "**Function:** `create_user_order`" in section
            assert "**File:** `api/orders.py:25`" in section
            assert "**Sections:** orders, users" in section
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

    def test_initialize_no_endpoints(self) -> None:
        """Test initialization when no endpoints are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            initializer = DocumentationInitializer(temp_dir, temp_dir)

            result = initializer.initialize()

            assert result["endpoints"] == []
            # Should still create general_docs.md
            assert len(result["files"]) == 1
            assert any("general_docs.md" in f for f in result["files"])
            assert "general API documentation" in result["summary"]

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

            assert len(result["endpoints"]) == 2
            # Should create general_docs.md, users.md, and orders.md
            assert len(result["files"]) == 3
            assert "Documentation Initialization Complete" in result["summary"]
            assert "GET: 1" in result["summary"]
            assert "POST: 1" in result["summary"]

            # Check that files were actually created
            assert (output_dir / "general_docs.md").exists()
            assert (output_dir / "users.md").exists()
            assert (output_dir / "orders.md").exists()

    def test_create_summary(self) -> None:
        """Test summary creation with endpoint statistics."""
        endpoints = [
            EndpointInfo("GET", "/users", "get_users", "api.py", 10, sections=["users"]),
            EndpointInfo("POST", "/users", "create_user", "api.py", 20, sections=["users"]),
            EndpointInfo("GET", "/orders", "get_orders", "orders.py", 15, sections=["orders"]),
        ]
        generated_files = {
            "docs/general_docs.md": "general content",
            "docs/users.md": "content",
            "docs/orders.md": "content",
        }

        initializer = DocumentationInitializer("src", "docs")
        summary = initializer._create_summary(endpoints, generated_files)

        assert "3" in summary  # endpoint count
        assert "3" in summary  # file count (including general_docs.md)
        assert "GET: 2" in summary
        assert "POST: 1" in summary
        assert "docs/users.md" in summary
        assert "docs/orders.md" in summary

    def test_create_summary_with_unsectioned_endpoints(self) -> None:
        """Test summary creation includes warning about unsectioned endpoints."""
        endpoints = [
            EndpointInfo("GET", "/users", "get_users", "api.py", 10, sections=["users"]),
            EndpointInfo("POST", "/health", "health_check", "main.py", 5, sections=[]),  # No tags
            EndpointInfo("GET", "/status", "get_status", "main.py", 15, sections=[]),  # No tags
        ]
        generated_files = {
            "docs/general_docs.md": "general content",
            "docs/users.md": "content",
            "docs/api.md": "content",
        }

        initializer = DocumentationInitializer("src", "docs")
        summary = initializer._create_summary(endpoints, generated_files)

        # Should include warning section
        assert "⚠️  **Endpoints without sections" in summary
        assert "POST /health → `main.py:5`" in summary
        assert "GET /status → `main.py:15`" in summary

        # Should include helpful tips
        assert "💡 **Tip:**" in summary
        assert "@app.get('/path', tags=['tag_name'])" in summary
        assert "router = APIRouter(prefix='/prefix', tags=['tag_name'])" in summary

        # Should include additional next step
        assert "5. Consider adding sections to unsectioned endpoints" in summary

    def test_create_summary_no_unsectioned_endpoints(self) -> None:
        """Test summary creation when all endpoints have sections."""
        endpoints = [
            EndpointInfo("GET", "/users", "get_users", "api.py", 10, sections=["users"]),
            EndpointInfo("POST", "/orders", "create_order", "orders.py", 20, sections=["orders"]),
        ]
        generated_files = {
            "docs/general_docs.md": "general content",
            "docs/users.md": "content",
            "docs/orders.md": "content",
        }

        initializer = DocumentationInitializer("src", "docs")
        summary = initializer._create_summary(endpoints, generated_files)

        # Should NOT include warning section
        assert "⚠️  **Endpoints without tags" not in summary
        assert "💡 **Tip:**" not in summary

        # Should not include the additional next step
        assert "5. Consider adding tags" not in summary
        assert "5. Run `fmd-lint`" in summary  # Should go straight to step 5
