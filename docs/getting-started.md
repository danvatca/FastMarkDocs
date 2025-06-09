---
layout: default
title: Getting Started
description: Learn how to install and set up FastMarkDocs for your FastAPI application
---

# Getting Started

This guide will walk you through installing FastMarkDocs and setting up your first enhanced API documentation.

## Prerequisites

- Python 3.9 or higher
- FastAPI application (existing or new)
- Basic familiarity with markdown

## Installation

### Using pip

```bash
pip install fastmarkdocs
```

### Using Poetry

```bash
poetry add fastmarkdocs
```

### Development Installation

If you want to contribute or use the latest development version:

```bash
git clone https://github.com/danvatca/fastmarkdocs.git
cd fastmarkdocs
pip install -e .
```

## Basic Setup

### 1. Create Your FastAPI Application

If you don't have a FastAPI application yet, create a simple one:

```python
# main.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="My API",
    description="An example API with FastMarkDocs",
    version="1.0.0"
)

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users", response_model=list[User])
async def get_users():
    """Get all users."""
    return [
        User(id=1, name="John Doe", email="john@example.com"),
        User(id=2, name="Jane Smith", email="jane@example.com")
    ]

@app.post("/users", response_model=User)
async def create_user(user: User):
    """Create a new user."""
    return user
```

### 2. Create Documentation Directory

Create a directory structure for your API documentation:

```
your-project/
├── main.py
└── docs/
    └── api/
        └── users.md
```

### 3. Write Markdown Documentation

Create your first documentation file (`docs/api/users.md`):

```markdown
# User Management

## GET /users

Retrieve a list of all users in the system.

### Description
This endpoint returns all users currently registered in the system.

### Response Example

```json
[
  {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  },
  {
    "id": 2,
    "name": "Jane Smith",
    "email": "jane@example.com"
  }
]
```

### Code Examples

```python
import requests

response = requests.get("https://api.example.com/users")
users = response.json()
print(f"Found {len(users)} users")
```

```javascript
const response = await fetch('https://api.example.com/users');
const users = await response.json();
console.log(`Found ${users.length} users`);
```

```curl
curl -X GET "https://api.example.com/users" \
  -H "Accept: application/json"
```

## POST /users

Create a new user in the system.

### Request Body

```json
{
  "id": 3,
  "name": "Bob Wilson",
  "email": "bob@example.com"
}
```

### Code Examples

```python
import requests

user_data = {
    "id": 3,
    "name": "Bob Wilson",
    "email": "bob@example.com"
}

response = requests.post(
    "https://api.example.com/users",
    json=user_data
)
new_user = response.json()
```

```javascript
const userData = {
  id: 3,
  name: "Bob Wilson",
  email: "bob@example.com"
};

const response = await fetch('https://api.example.com/users', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(userData)
});

const newUser = await response.json();
```
```

### 4. Enhance Your FastAPI Application

Update your FastAPI application to use FastMarkDocs:

```python
# main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastmarkdocs import enhance_openapi_with_docs
from pydantic import BaseModel

app = FastAPI(
    title="My API",
    description="An example API with FastMarkDocs",
    version="1.0.0"
)

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users", response_model=list[User])
async def get_users():
    """Get all users."""
    return [
        User(id=1, name="John Doe", email="john@example.com"),
        User(id=2, name="Jane Smith", email="jane@example.com")
    ]

@app.post("/users", response_model=User)
async def create_user(user: User):
    """Create a new user."""
    return user

# Custom OpenAPI function with FastMarkDocs enhancement
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    # Generate base OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Enhance with FastMarkDocs
    enhanced_schema = enhance_openapi_with_docs(
        openapi_schema=openapi_schema,
        docs_directory="docs/api",
        base_url="https://api.example.com"
    )
    
    app.openapi_schema = enhanced_schema
    return enhanced_schema

# Set the custom OpenAPI function
app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 5. Run Your Application

Start your FastAPI application:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload
```

### 6. View Enhanced Documentation

Open your browser and navigate to:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

You should now see your enhanced API documentation with:
- Rich descriptions from your markdown files
- Code samples in multiple languages
- Response examples
- Enhanced parameter documentation

## Configuration Options

FastMarkDocs provides several configuration options for customization:

```python
from fastmarkdocs import enhance_openapi_with_docs

enhanced_schema = enhance_openapi_with_docs(
    openapi_schema=openapi_schema,
    docs_directory="docs/api",
    base_url="https://api.example.com",
    code_sample_languages=["python", "javascript", "curl"],
    custom_headers={"Authorization": "Bearer YOUR_TOKEN"},
    include_response_examples=True,
    include_parameter_examples=True
)
```

## Next Steps

Now that you have FastMarkDocs set up, you can:

1. **[Learn more about markdown documentation structure](user-guide.html#markdown-structure)**
2. **[Explore advanced configuration options](advanced.html)**
3. **[Check out real-world examples](examples.html)**
4. **[Read the complete API reference](api-reference.html)**

## Troubleshooting

### Common Issues

**Documentation not appearing in Swagger UI**
- Ensure your markdown files are in the correct directory
- Check that your endpoint paths in markdown match your FastAPI routes
- Verify that your markdown files follow the correct format

**Code samples not generating**
- Make sure you've specified the correct `base_url`
- Check that your markdown files contain properly formatted code blocks
- Verify that the language identifiers in code blocks are supported

**Performance issues**
- Enable caching for better performance in production
- Consider using recursive=False if you have many nested directories
- Use specific file patterns to limit which files are processed

### Getting Help

If you encounter issues:

1. Check the [API Reference](api-reference.html) for detailed documentation
2. Look at the [Examples](examples.html) for working code samples
3. Search existing [GitHub Issues](https://github.com/danvatca/fastmarkdocs/issues)
4. Create a new issue with a minimal reproduction case

## What's Next?

Continue to the [User Guide](user-guide.html) to learn about advanced features and best practices for organizing your API documentation. 