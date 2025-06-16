#!/usr/bin/env python3
"""
Example showing how to use FastMarkDocs with app_title, app_description, and api_links
to create a comprehensive API documentation system.

This example demonstrates how to:
1. Override the application title
2. Add a custom application description
3. Include links to other APIs in your system
4. Create a unified documentation experience across multiple services
"""

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from fastmarkdocs import APILink, CodeLanguage, enhance_openapi_with_docs


def create_enhanced_api_app() -> FastAPI:
    """Create a FastAPI app with enhanced documentation."""

    app = FastAPI(
        title="Original API Title",  # This will be overridden
        description="Original description",  # This will be overridden
        version="1.0.0",
    )

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.get("/auth/login")
    async def login() -> dict[str, str]:
        """Login endpoint."""
        return {"message": "Login endpoint"}

    @app.get("/users")
    async def get_users() -> dict[str, list[Any]]:
        """Get all users."""
        return {"users": []}

    def custom_openapi() -> dict[str, Any]:
        """Generate custom OpenAPI schema with enhanced documentation."""
        if app.openapi_schema:
            return app.openapi_schema

        # Define the APIs available in your system
        apis = [
            {"url": "/docs", "description": "Authentication"},
            {"url": "/api/users/docs", "description": "User Management"},
            {"url": "/api/orders/docs", "description": "Order Processing"},
            {"url": "/api/inventory/docs", "description": "Inventory"},
            {"url": "/api/payments/docs", "description": "Payments"},
            {"url": "/api/notifications/docs", "description": "Notifications"},
            {"url": "/api/analytics/docs", "description": "Analytics"},
        ]

        # Convert to APILink objects
        api_links = [APILink(url=api["url"], description=api["description"]) for api in apis]

        # Generate base OpenAPI schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Enhance with FastMarkDocs and custom title/description/links
        enhanced_schema = enhance_openapi_with_docs(
            openapi_schema=openapi_schema,
            docs_directory="docs/api",  # Your API documentation directory
            base_url="https://api.example.com",
            include_code_samples=True,
            include_response_examples=True,
            code_sample_languages=[CodeLanguage.CURL, CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT],
            custom_headers={"Content-Type": "application/json", "Authorization": "Bearer YOUR_TOKEN"},
            # Enhanced documentation parameters
            app_title="My API Gateway",
            app_description="Comprehensive API management and authentication service",
            api_links=api_links,
        )

        app.openapi_schema = enhanced_schema
        return app.openapi_schema

    def set_custom_openapi() -> None:
        """Set the custom OpenAPI function on the app."""
        app.openapi = custom_openapi  # type: ignore[method-assign]

    set_custom_openapi()
    return app


def demonstrate_different_configurations() -> None:
    """Show different ways to use the new parameters."""

    base_schema = {
        "openapi": "3.0.0",
        "info": {"title": "Original API", "version": "1.0.0", "description": "Original description"},
        "paths": {},
    }

    print("=== Different Configuration Examples ===\n")

    # Example 1: Full configuration with API links
    print("1. Full configuration with API links:")
    api_links = [
        APILink(url="/docs", description="Authentication"),
        APILink(url="/api/users/docs", description="User Management"),
        APILink(url="/api/orders/docs", description="Order Processing"),
    ]

    enhanced = enhance_openapi_with_docs(
        openapi_schema=base_schema,
        docs_directory="docs",  # Empty directory for this example
        app_title="E-Commerce API Gateway",
        app_description="Central API management for e-commerce platform",
        api_links=api_links,
    )

    print(f"Title: {enhanced['info']['title']}")
    print(f"Description:\n{enhanced['info']['description']}\n")

    # Example 2: Only API links
    print("2. Only API links (preserves original title and description):")
    enhanced2 = enhance_openapi_with_docs(
        openapi_schema=base_schema,
        docs_directory="docs",
        api_links=[
            APILink(url="/main/docs", description="Main API"),
            APILink(url="/admin/docs", description="Admin API"),
        ],
    )

    print(f"Title: {enhanced2['info']['title']}")
    print(f"Description:\n{enhanced2['info']['description']}\n")

    # Example 3: Only title and description override
    print("3. Only title and description override:")
    enhanced3 = enhance_openapi_with_docs(
        openapi_schema=base_schema,
        docs_directory="docs",
        app_title="Custom Microservice",
        app_description="A specialized microservice for data processing",
    )

    print(f"Title: {enhanced3['info']['title']}")
    print(f"Description:\n{enhanced3['info']['description']}\n")

    # Example 4: Microservices architecture
    print("4. Microservices architecture example:")
    microservice_links = [
        APILink(url="/auth/docs", description="Authentication Service"),
        APILink(url="/user-service/docs", description="User Service"),
        APILink(url="/order-service/docs", description="Order Service"),
        APILink(url="/payment-service/docs", description="Payment Service"),
        APILink(url="/notification-service/docs", description="Notification Service"),
    ]

    enhanced4 = enhance_openapi_with_docs(
        openapi_schema=base_schema,
        docs_directory="docs",
        app_title="Authentication Service",
        app_description="Handles user authentication and authorization",
        api_links=microservice_links,
    )

    print(f"Title: {enhanced4['info']['title']}")
    print(f"Description:\n{enhanced4['info']['description']}\n")


if __name__ == "__main__":
    # Create the app
    app = create_enhanced_api_app()

    print("=== Enhanced FastAPI App Created ===")
    print("The app now has enhanced OpenAPI documentation with:")
    print("- Custom title: 'My API Gateway'")
    print("- Custom description with API links")
    print("- Enhanced documentation from markdown files")
    print("- Multi-language code samples")
    print("\nTo run the app:")
    print("uvicorn api_links_example:app --reload")
    print("Then visit: http://localhost:8000/docs")
    print()

    # Show different configuration examples
    demonstrate_different_configurations()
