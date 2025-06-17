#!/usr/bin/env python3
"""
Example demonstrating the fmd-init tool functionality.

This script shows how to use the fmd-init tool both programmatically
and via the command line to generate documentation scaffolding for
existing FastAPI projects.
"""

import tempfile
from pathlib import Path

from fastmarkdocs.scaffolder import DocumentationInitializer


def create_sample_fastapi_project(project_dir: Path) -> None:
    """Create a sample FastAPI project structure for demonstration."""

    # Create main API file
    main_api = project_dir / "main.py"
    main_api.write_text(
        '''
"""Main FastAPI application."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="Sample API",
    description="A sample API for demonstration",
    version="1.0.0"
)


class User(BaseModel):
    """User model."""
    id: int
    name: str
    email: str
    active: bool = True


class UserCreate(BaseModel):
    """User creation model."""
    name: str
    email: str


@app.get("/", tags=["root"])
def read_root():
    """Root endpoint returning API information."""
    return {"message": "Welcome to Sample API", "version": "1.0.0"}


@app.get("/health", tags=["monitoring"])
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


@app.get("/users", response_model=List[User], tags=["users"])
def get_users(skip: int = 0, limit: int = 100):
    """
    Retrieve a list of users.

    This endpoint returns a paginated list of all users in the system.
    You can control pagination using the skip and limit parameters.

    Args:
        skip: Number of users to skip (for pagination)
        limit: Maximum number of users to return

    Returns:
        List of user objects
    """
    # Mock data for demonstration
    users = [
        {"id": 1, "name": "John Doe", "email": "john@example.com", "active": True},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "active": True},
    ]
    return users[skip:skip + limit]


@app.get("/users/{user_id}", response_model=User, tags=["users"])
def get_user(user_id: int):
    """
    Get a specific user by ID.

    Retrieve detailed information about a specific user.

    Args:
        user_id: The unique identifier of the user

    Returns:
        User object with detailed information

    Raises:
        HTTPException: 404 if user not found
    """
    if user_id == 1:
        return {"id": 1, "name": "John Doe", "email": "john@example.com", "active": True}
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/users", response_model=User, tags=["users"])
def create_user(user: UserCreate):
    """
    Create a new user.

    Create a new user account with the provided information.
    The user will be assigned a unique ID automatically.

    Args:
        user: User creation data

    Returns:
        Created user object with assigned ID
    """
    # Mock creation logic
    new_user = {
        "id": 999,
        "name": user.name,
        "email": user.email,
        "active": True
    }
    return new_user


@app.put("/users/{user_id}", response_model=User, tags=["users"])
def update_user(user_id: int, user: UserCreate):
    """Update an existing user."""
    # Mock update logic
    updated_user = {
        "id": user_id,
        "name": user.name,
        "email": user.email,
        "active": True
    }
    return updated_user


@app.delete("/users/{user_id}", tags=["users"])
def delete_user(user_id: int):
    """Delete a user by ID."""
    return {"message": f"User {user_id} deleted successfully"}
'''
    )

    # Create API router file
    api_dir = project_dir / "api"
    api_dir.mkdir()

    orders_router = api_dir / "orders.py"
    orders_router.write_text(
        '''
"""Orders API router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter(prefix="/orders", tags=["orders"])


class Order(BaseModel):
    """Order model."""
    id: int
    user_id: int
    product_name: str
    quantity: int
    total_amount: float
    created_at: datetime


class OrderCreate(BaseModel):
    """Order creation model."""
    user_id: int
    product_name: str
    quantity: int
    unit_price: float


@router.get("/", response_model=List[Order])
def get_orders(user_id: Optional[int] = None):
    """
    Get all orders or orders for a specific user.

    Retrieve a list of orders. Optionally filter by user ID.

    Args:
        user_id: Optional user ID to filter orders

    Returns:
        List of order objects
    """
    # Mock data
    orders = [
        {
            "id": 1,
            "user_id": 1,
            "product_name": "Widget A",
            "quantity": 2,
            "total_amount": 29.98,
            "created_at": "2024-01-01T10:00:00Z"
        }
    ]

    if user_id:
        orders = [o for o in orders if o["user_id"] == user_id]

    return orders


@router.get("/{order_id}", response_model=Order)
def get_order(order_id: int):
    """Get a specific order by ID."""
    if order_id == 1:
        return {
            "id": 1,
            "user_id": 1,
            "product_name": "Widget A",
            "quantity": 2,
            "total_amount": 29.98,
            "created_at": "2024-01-01T10:00:00Z"
        }
    raise HTTPException(status_code=404, detail="Order not found")


@router.post("/", response_model=Order)
def create_order(order: OrderCreate):
    """
    Create a new order.

    Create a new order for a user with the specified products.
    The total amount will be calculated automatically.
    """
    total_amount = order.quantity * order.unit_price
    new_order = {
        "id": 999,
        "user_id": order.user_id,
        "product_name": order.product_name,
        "quantity": order.quantity,
        "total_amount": total_amount,
        "created_at": datetime.now().isoformat()
    }
    return new_order


@router.put("/{order_id}/status")
def update_order_status(order_id: int, status: str):
    """Update the status of an order."""
    return {"message": f"Order {order_id} status updated to {status}"}


@router.delete("/{order_id}")
def cancel_order(order_id: int):
    """Cancel an order."""
    return {"message": f"Order {order_id} cancelled successfully"}
'''
    )

    # Create admin router
    admin_router = api_dir / "admin.py"
    admin_router.write_text(
        '''
"""Admin API router."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin_token(token: str = None):
    """Verify admin authentication token."""
    if not token or token != "admin-secret":
        raise HTTPException(status_code=403, detail="Admin access required")
    return True


@router.get("/stats", dependencies=[Depends(verify_admin_token)])
def get_system_stats():
    """
    Get system statistics.

    Retrieve comprehensive system statistics including user counts,
    order metrics, and system health information.

    Requires admin authentication.
    """
    return {
        "total_users": 150,
        "active_users": 142,
        "total_orders": 1250,
        "revenue": 45678.90,
        "system_health": "excellent"
    }


@router.post("/maintenance", dependencies=[Depends(verify_admin_token)])
def toggle_maintenance_mode(enabled: bool):
    """Toggle system maintenance mode."""
    return {
        "maintenance_mode": enabled,
        "message": f"Maintenance mode {'enabled' if enabled else 'disabled'}"
    }


@router.get("/logs", dependencies=[Depends(verify_admin_token)])
def get_system_logs(level: str = "info", limit: int = 100):
    """Get system logs with optional filtering."""
    return {
        "logs": [
            {"timestamp": "2024-01-01T10:00:00Z", "level": "info", "message": "System started"},
            {"timestamp": "2024-01-01T10:01:00Z", "level": "info", "message": "User logged in"},
        ][:limit],
        "total_count": 1500
    }
'''
    )


def demonstrate_programmatic_usage() -> None:
    """Demonstrate using the fmd-init functionality programmatically."""
    print("🚀 Demonstrating fmd-init programmatic usage")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir) / "sample_project"
        project_dir.mkdir()

        # Create sample FastAPI project
        print("📁 Creating sample FastAPI project...")
        create_sample_fastapi_project(project_dir)

        # Initialize documentation
        print("🔍 Scanning for FastAPI endpoints...")
        docs_dir = project_dir / "docs"
        initializer = DocumentationInitializer(str(project_dir), str(docs_dir))

        result = initializer.initialize()

        print("\n✅ Results:")
        print(f"   📊 Endpoints found: {result['endpoints_found']}")
        print(f"   📄 Files generated: {len(result['files_generated'])}")

        print("\n📋 Generated files:")
        for file_path in result["files_generated"].keys():
            print(f"   - {file_path}")

        print("\n📈 Endpoint breakdown:")
        endpoints = result.get("endpoints", [])
        method_counts: dict[str, int] = {}
        for endpoint in endpoints:
            method_counts[endpoint.method] = method_counts.get(endpoint.method, 0) + 1

        for method, count in sorted(method_counts.items()):
            print(f"   {method}: {count}")

        # Show sample of generated content
        if result["files_generated"]:
            first_file = list(result["files_generated"].keys())[0]
            content = result["files_generated"][first_file]

            print(f"\n📝 Sample content from {Path(first_file).name}:")
            print("-" * 40)
            # Show first 10 lines
            lines = content.split("\n")[:10]
            for line in lines:
                print(f"   {line}")
            if len(content.split("\n")) > 10:
                print("   ...")


def demonstrate_cli_usage() -> None:
    """Demonstrate CLI usage examples."""
    print("\n🖥️  CLI Usage Examples")
    print("=" * 50)

    examples = [
        {"description": "Basic usage - scan src/ directory", "command": "fmd-init src/"},
        {"description": "Custom output directory", "command": "fmd-init src/ --output-dir api-docs/"},
        {"description": "JSON output format", "command": "fmd-init src/ --format json"},
        {"description": "Dry run (preview without creating files)", "command": "fmd-init src/ --dry-run"},
        {"description": "Verbose output with endpoint details", "command": "fmd-init src/ --verbose"},
        {"description": "Overwrite existing documentation", "command": "fmd-init src/ --overwrite"},
        {"description": "Scan current directory", "command": "fmd-init ."},
    ]

    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['description']}")
        print(f"   $ {example['command']}")
        print()


def demonstrate_workflow_integration() -> None:
    """Demonstrate integration with development workflow."""
    print("🔄 Development Workflow Integration")
    print("=" * 50)

    workflow_steps = [
        "1. 🏗️  Develop FastAPI endpoints in your project",
        "2. 🔍 Run fmd-init to generate documentation scaffolding:",
        "   $ fmd-init src/ --output-dir docs/",
        "",
        "3. ✏️  Review and enhance the generated documentation:",
        "   - Fill in TODO sections",
        "   - Add detailed descriptions",
        "   - Include parameter documentation",
        "   - Add response examples",
        "",
        "4. 🔧 Use fastmarkdocs to enhance your OpenAPI schema:",
        "   from fastmarkdocs import add_markdown_docs",
        "   add_markdown_docs(app, docs_directory='docs')",
        "",
        "5. 🧪 Run fmd-lint to check documentation quality:",
        "   $ fmd-lint openapi.json docs/",
        "",
        "6. 🚀 Deploy with enhanced documentation!",
    ]

    for step in workflow_steps:
        print(step)


def show_generated_structure_example() -> None:
    """Show an example of the generated documentation structure."""
    print("\n📁 Generated Documentation Structure")
    print("=" * 50)

    structure = """
docs/
├── users.md          # User management endpoints
├── orders.md         # Order management endpoints
├── admin.md          # Admin endpoints
└── root.md           # Root/general endpoints

Each file contains:
├── Endpoint headers (## GET /users)
├── Summary and description
├── Implementation details (function name, file location)
├── TODO sections for:
│   ├── Parameters documentation
│   ├── Response examples
│   └── Additional details
└── Placeholder code examples
"""

    print(structure)


def main() -> None:
    """Main demonstration function."""
    print("🎯 FastMarkDocs fmd-init Tool Demonstration")
    print("=" * 60)
    print()
    print("The fmd-init tool helps you bootstrap documentation for existing")
    print("FastAPI projects by scanning your code and generating markdown")
    print("scaffolding that you can then enhance and customize.")
    print()

    # Run demonstrations
    demonstrate_programmatic_usage()
    demonstrate_cli_usage()
    demonstrate_workflow_integration()
    show_generated_structure_example()

    print("\n🎉 That's it! The fmd-init tool makes it easy to get started")
    print("with comprehensive API documentation for your FastAPI projects.")
    print("\nNext steps:")
    print("1. Try it on your own project: fmd-init your-src-directory/")
    print("2. Review and enhance the generated documentation")
    print("3. Use fmd-lint to check documentation completeness")
    print("4. Integrate with fastmarkdocs for enhanced OpenAPI schemas")


if __name__ == "__main__":
    main()
