"""Tests for parameter analysis functionality in the scaffolder."""

import ast

from fastmarkdocs.scaffolder import FastAPIEndpointScanner, ParameterInfo


class TestParameterAnalysis:
    """Test parameter analysis functionality."""

    def test_extract_path_parameters(self):
        """Test extraction of path parameters from URL patterns."""
        scanner = FastAPIEndpointScanner(".")

        # Test simple path parameter
        params = scanner._extract_path_parameters("/users/{user_id}")
        assert params == {"user_id"}

        # Test multiple path parameters
        params = scanner._extract_path_parameters("/users/{user_id}/posts/{post_id}")
        assert params == {"user_id", "post_id"}

        # Test path parameter with type annotation
        params = scanner._extract_path_parameters("/files/{file_path:path}")
        assert params == {"file_path"}

        # Test mixed parameters
        params = scanner._extract_path_parameters("/api/{version}/users/{user_id:int}/files/{file_path:path}")
        assert params == {"version", "user_id", "file_path"}

        # Test no parameters
        params = scanner._extract_path_parameters("/users")
        assert params == set()

    def test_is_dependency_parameter(self):
        """Test detection of FastAPI dependency injection parameters."""
        # Create AST for function with Depends()
        code = """
async def test_endpoint(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pass
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        scanner = FastAPIEndpointScanner(".")

        # user_id should not be a dependency
        assert not scanner._is_dependency_parameter(func_node, "user_id")

        # db should be a dependency
        assert scanner._is_dependency_parameter(func_node, "db")

        # current_user should be a dependency
        assert scanner._is_dependency_parameter(func_node, "current_user")

    def test_get_type_hint(self):
        """Test extraction of type hints from function arguments."""
        code = """
def test_endpoint(
    user_id: str,
    count: int,
    data: UserModel,
    optional_param: Optional[str]
):
    pass
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        scanner = FastAPIEndpointScanner(".")

        # Test different type hints
        assert scanner._get_type_hint(func_node.args.args[0]) == "str"
        assert scanner._get_type_hint(func_node.args.args[1]) == "int"
        assert scanner._get_type_hint(func_node.args.args[2]) == "UserModel"
        assert scanner._get_type_hint(func_node.args.args[3]) == "Optional[str]"

    def test_get_default_value(self):
        """Test extraction of default values from function parameters."""
        code = """
def test_endpoint(
    required_param: str,
    optional_param: str = "default",
    count: int = 10,
    flag: bool = True,
    db: Session = Depends(get_db)
):
    pass
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        scanner = FastAPIEndpointScanner(".")

        # Test required parameter (no default)
        assert scanner._get_default_value(func_node, "required_param") is None

        # Test optional parameters with defaults
        assert scanner._get_default_value(func_node, "optional_param") == "'default'"
        assert scanner._get_default_value(func_node, "count") == "10"
        assert scanner._get_default_value(func_node, "flag") == "True"

        # Test dependency parameter (should return None even though it has default)
        assert scanner._get_default_value(func_node, "db") is None

    def test_is_body_parameter(self):
        """Test detection of request body parameters."""
        scanner = FastAPIEndpointScanner(".")

        # Create mock arguments with different type hints
        arg_with_model = ast.arg(arg="data", annotation=ast.Name(id="UserModel"))
        arg_with_request = ast.arg(arg="request", annotation=ast.Name(id="CreateUserRequest"))
        arg_with_str = ast.arg(arg="name", annotation=ast.Name(id="str"))
        arg_with_schema = ast.arg(arg="schema", annotation=ast.Name(id="UserSchema"))

        # Test body parameter detection
        assert scanner._is_body_parameter(arg_with_model, "UserModel")
        assert scanner._is_body_parameter(arg_with_request, "CreateUserRequest")
        assert scanner._is_body_parameter(arg_with_schema, "UserSchema")

        # Test non-body parameters
        assert not scanner._is_body_parameter(arg_with_str, "str")
        assert not scanner._is_body_parameter(arg_with_str, "int")

    def test_extract_parameters_integration(self):
        """Test complete parameter extraction for a realistic endpoint."""
        code = """
@router.post("/users/{user_id}/posts", response_model=PostModel)
async def create_post(
    user_id: str,
    post_data: CreatePostRequest,
    published: bool = True,
    tags: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pass
"""
        tree = ast.parse(code)
        func_node = tree.body[0]

        scanner = FastAPIEndpointScanner(".")
        parameters = scanner._extract_parameters(func_node, "/users/{user_id}/posts", "POST")

        # Should extract 4 parameters (excluding dependencies)
        assert len(parameters) == 4

        # Check path parameter
        path_params = [p for p in parameters if p.parameter_type == "path"]
        assert len(path_params) == 1
        assert path_params[0].name == "user_id"
        assert path_params[0].type_hint == "str"
        assert path_params[0].is_required

        # Check body parameter
        body_params = [p for p in parameters if p.parameter_type == "body"]
        assert len(body_params) == 1
        assert body_params[0].name == "post_data"
        assert body_params[0].type_hint == "CreatePostRequest"
        assert body_params[0].is_required

        # Check query parameters
        query_params = [p for p in parameters if p.parameter_type == "query"]
        assert len(query_params) == 2

        # Check published parameter
        published_param = next(p for p in query_params if p.name == "published")
        assert published_param.type_hint == "bool"
        assert not published_param.is_required  # Has default value

        # Check tags parameter
        tags_param = next(p for p in query_params if p.name == "tags")
        assert tags_param.type_hint == "Optional[List[str]]"
        assert not tags_param.is_required  # Has default value

    def test_format_type_hint(self):
        """Test type hint formatting for documentation."""
        from fastmarkdocs.scaffolder import MarkdownScaffoldGenerator

        generator = MarkdownScaffoldGenerator()

        # Test basic type mappings
        assert generator._format_type_hint("str") == "string"
        assert generator._format_type_hint("int") == "integer"
        assert generator._format_type_hint("float") == "number"
        assert generator._format_type_hint("bool") == "boolean"
        assert generator._format_type_hint("list") == "array"
        assert generator._format_type_hint("dict") == "object"

        # Test complex types
        assert generator._format_type_hint("List[str]") == "array<string>"
        assert generator._format_type_hint("Dict[str, int]") == "object<string, integer>"

        # Test Optional types
        assert generator._format_type_hint("Optional[str]") == "string"
        assert generator._format_type_hint("Optional[UserModel]") == "UserModel"

        # Test custom models
        assert generator._format_type_hint("UserModel") == "UserModel"
        assert generator._format_type_hint("CreateUserRequest") == "CreateUserRequest"

        # Test None type hint
        assert generator._format_type_hint(None) == "string"

    def test_parameter_info_creation(self):
        """Test ParameterInfo dataclass creation and validation."""
        # Test required parameter
        param = ParameterInfo(name="user_id", type_hint="str", is_required=True, parameter_type="path")

        assert param.name == "user_id"
        assert param.type_hint == "str"
        assert param.default_value is None
        assert param.is_required
        assert param.parameter_type == "path"

        # Test optional parameter with default
        param = ParameterInfo(
            name="limit", type_hint="int", default_value="10", is_required=False, parameter_type="query"
        )

        assert param.name == "limit"
        assert param.type_hint == "int"
        assert param.default_value == "10"
        assert not param.is_required
        assert param.parameter_type == "query"

    def test_curl_example_generation(self):
        """Test cURL example generation for different endpoint types."""
        from fastmarkdocs.scaffolder import EndpointInfo, MarkdownScaffoldGenerator

        generator = MarkdownScaffoldGenerator()

        # Test GET endpoint
        get_endpoint = EndpointInfo(
            method="GET",
            path="/users/{user_id}",
            function_name="get_user",
            file_path="users.py",
            line_number=10,
            parameters=[ParameterInfo(name="user_id", parameter_type="path", is_required=True)],
        )

        curl_example = generator._generate_curl_example(get_endpoint)
        assert "curl -X GET" in curl_example
        assert "{base_url}/users/{user_id}" in curl_example
        assert "Authorization: Bearer your_token" in curl_example
        assert "Content-Type: application/json" not in curl_example  # Not needed for GET

        # Test POST endpoint with body
        post_endpoint = EndpointInfo(
            method="POST",
            path="/users",
            function_name="create_user",
            file_path="users.py",
            line_number=20,
            parameters=[ParameterInfo(name="user_data", parameter_type="body", is_required=True)],
        )

        curl_example = generator._generate_curl_example(post_endpoint)
        assert "curl -X POST" in curl_example
        assert "{base_url}/users" in curl_example
        assert "Authorization: Bearer your_token" in curl_example
        assert "Content-Type: application/json" in curl_example
        assert '"TODO": "Add request body"' in curl_example
