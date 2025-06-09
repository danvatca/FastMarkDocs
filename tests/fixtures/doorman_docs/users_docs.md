# User Management API Documentation

## Overview

The **User Management API** provides comprehensive user account administration for SynetoOS, enabling centralized user lifecycle management with role-based access control and multi-factor authentication. This API supports enterprise-grade user provisioning, security policies, and audit capabilities.

### 👥 **User Management Features**

**Complete User Lifecycle**
- User account creation with customizable roles and permissions
- Profile management and account status control (enable/disable)
- Secure user deletion with data integrity protection

**Role-Based Access Control**
- **Administrator Role**: Full system access and user management capabilities
- **Regular Role**: Limited access based on specific permissions and use cases
- **Support Role**: Special PIN-based authentication for maintenance and troubleshooting

**Multi-Factor Authentication**
- TOTP-based second factor with authenticator app integration
- Recovery codes for account recovery scenarios
- Per-user OTP configuration with administrative override

### 🛡️ **Security Features**

**Password Security**
- Configurable password complexity requirements and minimum length
- Secure password hashing with industry-standard algorithms
- No plain-text password storage or transmission

**Account Protection**
- Automatic account lockout after failed authentication attempts
- Session management with configurable timeout policies
- Comprehensive audit logging for compliance and security monitoring

### 🔄 **User Operations**

- **User Discovery**: `GET /users` - List all user accounts with roles and status
- **User Details**: `GET /users/{id}` - Retrieve complete user profile information
- **User Creation**: `POST /users` - Create new accounts with role assignment
- **User Updates**: `PATCH /users/{id}` - Modify user profiles and settings
- **User Deletion**: `DELETE /users/{id}` - Permanently remove user accounts

## Endpoints

### GET /users

**List all users**

Retrieves a complete list of all user accounts in the system.

#### Code Examples

##### cURL
```bash
curl -X GET "{base_url}/users" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests

url = "{base_url}/users"
headers = {"Authorization": "Bearer your_jwt_token"}

response = requests.get(url, headers=headers)
users = response.json()
print(f"Found {len(users)} users")
```

#### Response Example

**Success (200 OK):**
```json
[
  {
    "id": "admin",
    "username": "admin",
    "fullName": "System Administrator",
    "role": "administrator",
    "isEnabled": true,
    "isOtpEnabled": true,
    "isOtpSetupCompleted": true,
    "canBeDeleted": false,
    "isSupport": false,
    "isAdministrator": true
  },
  {
    "id": "user1",
    "username": "user1",
    "fullName": "Regular User",
    "role": "regular",
    "isEnabled": true,
    "isOtpEnabled": false,
    "isOtpSetupCompleted": false,
    "canBeDeleted": true,
    "isSupport": false,
    "isAdministrator": false
  }
]
```

---

### POST /users

**Create new user**

Creates a new user account with specified credentials and configuration.

#### Code Examples

##### cURL
```bash
curl -X POST "{base_url}/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "username": "newuser",
    "fullName": "New User",
    "password": "secure_password",
    "isOtpEnabled": false
  }'
```

##### Python
```python
import requests

url = "{base_url}/users"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_jwt_token"
}
data = {
    "username": "newuser",
    "fullName": "New User",
    "password": "secure_password",
    "isOtpEnabled": False
}

response = requests.post(url, headers=headers, json=data)
new_user = response.json()
print(f"Created user: {new_user['username']}")
```

#### Request Examples

**Administrator User with OTP:**
```json
{
  "username": "newadmin",
  "fullName": "New Administrator",
  "password": "secure_password123",
  "isOtpEnabled": true
}
```

**Regular User without OTP:**
```json
{
  "username": "regularuser",
  "fullName": "Regular User",
  "password": "user_password123",
  "isOtpEnabled": false
}
```

#### Response Examples

**Success (200 OK):**
```json
{
  "id": "newuser123",
  "username": "newuser",
  "fullName": "New User",
  "role": "administrator",
  "isEnabled": true,
  "isOtpEnabled": true,
  "isOtpSetupCompleted": false,
  "canBeDeleted": true,
  "isSupport": false,
  "isAdministrator": true
}
```

**User Creation Failed (400 Bad Request):**
```json
{
  "detail": "Could not activate OTP for user 'newuser'."
}
```

---

### GET /users/{id}

**Get user details**

Retrieves detailed information about a specific user account.

#### Code Examples

##### cURL
```bash
curl -X GET "{base_url}/users/user123" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests

user_id = "user123"
url = f"{base_url}/users/{user_id}"
headers = {"Authorization": "Bearer your_jwt_token"}

response = requests.get(url, headers=headers)
user = response.json()
print(f"User: {user['username']} - {user['fullName']}")
```

#### Response Example

**Success (200 OK):**
```json
{
  "id": "user123",
  "username": "user1",
  "fullName": "Regular User",
  "role": "regular",
  "isEnabled": true,
  "isOtpEnabled": false,
  "isOtpSetupCompleted": false,
  "canBeDeleted": true,
  "isSupport": false,
  "isAdministrator": false
}
```

---

### PATCH /users/{id}

**Edit user**

Updates user account information and settings.

#### Code Examples

##### cURL
```bash
curl -X PATCH "{base_url}/users/user123" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "fullName": "Updated Full Name",
    "isEnabled": true
  }'
```

##### Python
```python
import requests

user_id = "user123"
url = f"{base_url}/users/{user_id}"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_jwt_token"
}
data = {
    "fullName": "Updated Full Name",
    "isEnabled": True
}

response = requests.patch(url, headers=headers, json=data)
updated_user = response.json()
print(f"Updated user: {updated_user['username']}")
```

#### Request Examples

**Administrator User with OTP:**
```json
{
  "username": "john.doe",
  "fullName": "John Doe Updated",
  "isEnabled": true
}
```

**Regular User without OTP:**
```json
{
  "username": "john.doe",
  "fullName": "John Doe Updated",
  "isEnabled": true
}
```

#### Response Example

**Success (200 OK):**
```json
{
  "id": "john.doe",
  "username": "john.doe",
  "fullName": "John Doe Updated",
  "role": "regular",
  "isEnabled": true,
  "isOtpEnabled": false,
  "isOtpSetupCompleted": false,
  "canBeDeleted": true,
  "isSupport": false,
  "isAdministrator": false
}
```

---

### DELETE /users/{id}

**Delete user**

Permanently removes a user account from the system.

**Warning:** This operation is irreversible.

#### Code Examples

##### cURL
```bash
curl -X DELETE "{base_url}/users/user123" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests

user_id = "user123"
url = f"{base_url}/users/{user_id}"
headers = {"Authorization": "Bearer your_jwt_token"}

response = requests.delete(url, headers=headers)
if response.status_code == 204:
    print(f"User {user_id} deleted successfully")
```

## User Roles and Permissions

### Administrator Role
- **Full System Access**: Complete access to all system functions
- **User Management**: Can create, modify, and delete user accounts
- **System Configuration**: Can modify global system settings
- **Certificate Management**: Full access to CA operations
- **API Key Management**: Can create and manage API keys

### Regular Role
- **Limited Access**: Access based on specific permissions
- **Profile Management**: Can modify own profile information
- **Certificate Access**: Limited certificate operations
- **Read-Only Settings**: Can view but not modify system settings

### Support Role
- **Special Access**: PIN-based authentication for support operations
- **Diagnostic Access**: Access to system diagnostics and logs
- **Limited User Management**: Can assist with user account issues
- **Certificate Viewing**: Can view certificate information

## Multi-Factor Authentication (MFA)

### OTP Configuration
- **TOTP Support**: Time-based One-Time Password using authenticator apps
- **Recovery Codes**: Single-use backup codes for account recovery
- **QR Code Setup**: Easy setup via QR code scanning
- **Flexible Enforcement**: Can be enabled per-user or globally

### OTP Setup Process
1. User account created with `isOtpEnabled: true`
2. First login provides authenticator setup link and secret
3. User configures authenticator app with provided secret
4. User completes setup by verifying first OTP code
5. System provides recovery codes for backup access

## Security Features

### Password Requirements
- **Minimum Length**: Configurable minimum password length
- **Complexity Rules**: Optional complexity requirements
- **Secure Hashing**: Passwords are securely hashed before storage
- **No Plain Text**: Passwords are never stored in plain text

### Account Security
- **Account Lockout**: Automatic lockout after failed login attempts
- **Session Management**: Secure session handling with expiration
- **Audit Logging**: All user operations are logged for audit purposes
- **Role-Based Access**: Granular permissions based on user roles

## Error Responses

**User Not Found (404 Not Found):**
```json
{
  "detail": "User not found"
}
```

**Username Already Exists (409 Conflict):**
```json
{
  "detail": "Username already exists"
}
```

**Cannot Delete User (409 Conflict):**
```json
{
  "detail": "Cannot delete this user account"
}
```

**Insufficient Permissions (403 Forbidden):**
```json
{
  "detail": "User has no rights to do this action"
}
```

**Invalid User Data (400 Bad Request):**
```json
{
  "detail": "Invalid user data: Username is required"
}
``` 