# Users API Documentation

## Overview

The **Users API** provides comprehensive user account management capabilities for the application. This API enables user lifecycle management including account creation, profile retrieval, updates, and deletion operations.

### 👤 **User Management Features**

**Account Operations**
- User account creation with automatic ID assignment
- Profile information retrieval and management
- Account status control (active/inactive users)
- Secure user deletion with proper cleanup

**Data Management**
- Email uniqueness validation across the system
- Flexible user filtering and pagination support
- Complete user profile data access
- Robust error handling for invalid operations

### 🔍 **Query Capabilities**

- **List Users**: Retrieve paginated user lists with filtering options
- **User Details**: Get complete profile information for specific users
- **Status Filtering**: Filter users by active/inactive status
- **Search & Pagination**: Efficient data retrieval for large user bases

## GET /users

Retrieve a list of all users in the system.

This endpoint returns a paginated list of users. By default, only active users are returned, but you can include inactive users by setting the `active_only` parameter to `false`.

### Parameters

- `active_only` (boolean, optional): Filter to only active users. Default: `true`

### Response Examples

```json
[
  {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "active": true
  },
  {
    "id": 2,
    "name": "Jane Smith",
    "email": "jane@example.com",
    "active": true
  }
]
```

### Code Examples

```python
import requests

# Get all active users
response = requests.get("http://localhost:8000/users")
users = response.json()
print(f"Found {len(users)} active users")

# Get all users (including inactive)
response = requests.get("http://localhost:8000/users?active_only=false")
all_users = response.json()
print(f"Found {len(all_users)} total users")
```

```curl
# Get active users only
curl -X GET "http://localhost:8000/users" \
  -H "Accept: application/json"

# Get all users
curl -X GET "http://localhost:8000/users?active_only=false" \
  -H "Accept: application/json"
```

```javascript
// Get all active users
fetch('http://localhost:8000/users')
  .then(response => response.json())
  .then(users => console.log('Active users:', users))
  .catch(error => console.error('Error:', error));

// Get all users
fetch('http://localhost:8000/users?active_only=false')
  .then(response => response.json())
  .then(users => console.log('All users:', users))
  .catch(error => console.error('Error:', error));
```

Section: User Management

## GET /users/{user_id}

Retrieve detailed information about a specific user.

This endpoint returns complete user information including profile data and account status. The user must exist in the system, otherwise a 404 error will be returned.

### Parameters

- `user_id` (integer, required): The unique identifier for the user

### Response Examples

```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "active": true
}
```

### Error Responses

```json
{
  "detail": "User not found"
}
```

### Code Examples

```python
import requests

user_id = 1
response = requests.get(f"http://localhost:8000/users/{user_id}")

if response.status_code == 200:
    user = response.json()
    print(f"User: {user['name']} ({user['email']})")
elif response.status_code == 404:
    print("User not found")
else:
    print(f"Error: {response.status_code}")
```

```curl
curl -X GET "http://localhost:8000/users/1" \
  -H "Accept: application/json"
```

```javascript
const userId = 1;

fetch(`http://localhost:8000/users/${userId}`)
  .then(response => {
    if (response.ok) {
      return response.json();
    }
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  })
  .then(user => console.log('User details:', user))
  .catch(error => console.error('Error:', error));
```

Section: User Management

## POST /users

Create a new user in the system.

This endpoint allows you to create a new user account. The user will be created with an active status by default. Email addresses must be unique across the system.

### Request Body

```json
{
  "name": "John Doe",
  "email": "john@example.com"
}
```

### Response Examples

```json
{
  "id": 4,
  "name": "John Doe",
  "email": "john@example.com",
  "active": true
}
```

### Code Examples

```python
import requests

new_user = {
    "name": "Alice Johnson",
    "email": "alice@example.com"
}

response = requests.post(
    "http://localhost:8000/users",
    json=new_user,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    created_user = response.json()
    print(f"Created user with ID: {created_user['id']}")
else:
    print(f"Error creating user: {response.status_code}")
```

```curl
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "Alice Johnson",
    "email": "alice@example.com"
  }'
```

```javascript
const newUser = {
  name: "Alice Johnson",
  email: "alice@example.com"
};

fetch('http://localhost:8000/users', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  body: JSON.stringify(newUser)
})
  .then(response => response.json())
  .then(user => console.log('Created user:', user))
  .catch(error => console.error('Error:', error));
```

Section: User Management

## PUT /users/{user_id}

Update an existing user's information.

This endpoint allows you to update any field of an existing user. You only need to provide the fields you want to update - other fields will remain unchanged.

### Parameters

- `user_id` (integer, required): The unique identifier for the user to update

### Request Body

```json
{
  "name": "John Smith",
  "email": "john.smith@example.com",
  "active": false
}
```

### Response Examples

```json
{
  "id": 1,
  "name": "John Smith",
  "email": "john.smith@example.com",
  "active": false
}
```

### Code Examples

```python
import requests

user_id = 1
updates = {
    "name": "John Smith",
    "active": False
}

response = requests.put(
    f"http://localhost:8000/users/{user_id}",
    json=updates,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    updated_user = response.json()
    print(f"Updated user: {updated_user['name']}")
elif response.status_code == 404:
    print("User not found")
```

```curl
curl -X PUT "http://localhost:8000/users/1" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "John Smith",
    "active": false
  }'
```

```javascript
const userId = 1;
const updates = {
  name: "John Smith",
  active: false
};

fetch(`http://localhost:8000/users/${userId}`, {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  body: JSON.stringify(updates)
})
  .then(response => response.json())
  .then(user => console.log('Updated user:', user))
  .catch(error => console.error('Error:', error));
```

Section: User Management

## DELETE /users/{user_id}

Delete a user from the system.

This endpoint permanently removes a user from the system. This action cannot be undone, so use with caution.

### Parameters

- `user_id` (integer, required): The unique identifier for the user to delete

### Response Examples

```json
{
  "message": "User John Doe deleted successfully"
}
```

### Code Examples

```python
import requests

user_id = 1
response = requests.delete(f"http://localhost:8000/users/{user_id}")

if response.status_code == 200:
    result = response.json()
    print(result["message"])
elif response.status_code == 404:
    print("User not found")
```

```curl
curl -X DELETE "http://localhost:8000/users/1" \
  -H "Accept: application/json"
```

```javascript
const userId = 1;

fetch(`http://localhost:8000/users/${userId}`, {
  method: 'DELETE',
  headers: {
    'Accept': 'application/json'
  }
})
  .then(response => response.json())
  .then(result => console.log(result.message))
  .catch(error => console.error('Error:', error));
```

Section: User Management 