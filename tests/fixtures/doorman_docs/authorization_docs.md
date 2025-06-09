# Authorization API Documentation

## Overview

The **Authorization API** serves two primary operational purposes in SynetoOS, though they are functionally distinct and will likely be refactored into separate services in the future.

### 🔑 **Primary Purpose 1: SSH Public Key Management**

**Per-User SSH Authorization Configuration**
- Individual user SSH public key storage and retrieval
- Authorized keys file management for secure shell access
- SSH key validation and lifecycle operations for system access

**Key Management Operations:**
- `GET /public-key?username=X` - Retrieve a user's SSH public key
- `GET /authorized-keys?username=X` - List all authorized SSH keys for a user
- `POST /authorized-keys` - Add new SSH public key to user's authorized_keys
- `DELETE /authorized-keys` - Remove SSH public key from user's authorized_keys

### 🌐 **Primary Purpose 2: Nginx Proxy Authorization**

**Remote Node Access Authorization Gateway**
- Nginx auth_request module integration for proxied requests
- Multi-method authentication validation (API keys, JWT tokens, session cookies)
- Authorization decisions for remote node access through the proxy
- Request validation and user context extraction

**Proxy Authorization Operations:**
- `GET /authorization` - Primary authorization endpoint for nginx auth_request
- Validates incoming requests before they're proxied to remote nodes
- Supports API key, JWT Bearer token, and session cookie authentication
- Returns 200 (authorized) or 401/403 (denied) for nginx routing decisions

### 🔧 **Secondary Purpose: Session Utilities**

**JWT Session Information Extraction**
- `GET /session-start-time` - Extract session timestamp from JWT tokens
- Used primarily for audit logging and session tracking by external services

---

## SSH Public Key Management

The SSH key management functionality provides per-user SSH authorization configuration, allowing users to manage their SSH public keys for secure shell access to SynetoOS systems.

### SSH Key Management Architecture

**File System Integration:**
- SSH keys are stored in standard Unix `~/.ssh/authorized_keys` format
- Keys are managed per-user in their respective home directories
- File permissions and ownership are automatically maintained
- Supports all standard SSH key types (RSA, ECDSA, Ed25519)

**Key Validation Process:**
1. **Format Validation**: SSH key format is validated using the `sshpubkeys` library
2. **Duplicate Detection**: Prevents adding duplicate keys to the same user
3. **Key Type Support**: Supports RSA, ECDSA, Ed25519, and other standard SSH key types
4. **Comment Preservation**: SSH key comments are preserved during storage

### SSH Key Use Cases

**System Administration:**
- Administrators can retrieve any user's SSH public key for system configuration
- Bulk SSH key deployment for automated systems and CI/CD pipelines
- SSH key auditing and compliance reporting

**User Self-Service:**
- Users can manage their own authorized SSH keys through the API
- Add new workstation/laptop SSH keys for remote access
- Remove compromised or old SSH keys from their account

**Automation and Integration:**
- Automated SSH key rotation for service accounts
- Integration with configuration management tools (Ansible, Puppet, etc.)
- SSH key synchronization across distributed SynetoOS nodes

### SSH Key Security Considerations

**Access Control:**
- Users can only manage their own SSH keys (enforced by username parameter)
- Administrators have read access to all user SSH keys
- SSH key operations are logged for security auditing

**Key Lifecycle Management:**
- No automatic key expiration (follows standard SSH behavior)
- Manual key removal required when access should be revoked
- Key usage tracking through SSH daemon logs (external to this API)

**Validation and Storage:**
- All SSH keys are validated before storage to prevent malformed entries
- Keys are stored in standard OpenSSH format for maximum compatibility
- File system permissions are automatically set for security (600 for authorized_keys)

### SSH Key Management Workflow

1. **Key Retrieval**: System administrators can retrieve any user's SSH public key
2. **Authorized Keys Management**: Users can manage their own authorized_keys file
3. **Key Validation**: All SSH keys are validated before storage
4. **File System Integration**: Keys are stored in standard SSH authorized_keys format

### GET /public-key

**Retrieve a user's SSH public key**

Retrieves the SSH public key for a specified user. This endpoint is primarily used by system administrators for SSH key management and system configuration tasks.

**Query Parameters:**
- `username` (required): The username whose SSH public key to retrieve

**Access Control:**
- Administrators can retrieve any user's SSH public key
- Regular users can only retrieve their own SSH public key
- Requires valid authentication (API key, JWT token, or session)

#### Code Examples

##### cURL
```bash
# Retrieve SSH public key for a user
curl -X GET "{base_url}/public-key?username=john.doe" \
  -H "X-API-Key: your_api_key"

# Retrieve your own SSH public key (with session)
curl -X GET "{base_url}/public-key?username=current_user" \
  -H "Cookie: session=your_session_token"
```

##### Python
```python
import requests

def get_user_ssh_key(base_url, username, api_key=None, jwt_token=None):
    """
    Retrieve a user's SSH public key.
    
    Args:
        base_url: Doorman base URL
        username: Username whose SSH key to retrieve
        api_key: API key for authentication (optional)
        jwt_token: JWT token for authentication (optional)
    
    Returns:
        str: SSH public key or None if not found
    """
    url = f"{base_url}/public-key"
    params = {"username": username}
    headers = {}
    
    if api_key:
        headers["X-API-Key"] = api_key
    elif jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Retrieved SSH key for {username}")
            return result.get("public_key")
        elif response.status_code == 404:
            print(f"❌ No SSH key found for user: {username}")
            return None
        else:
            print(f"❌ Error: {response.status_code} - {response.json().get('detail', 'Unknown error')}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

# Example usage
ssh_key = get_user_ssh_key(
    "https://doorman.example.com",
    "john.doe",
    api_key="your_api_key"
)

if ssh_key:
    print(f"SSH Key: {ssh_key}")
```

#### Response Examples

**Success (200 OK):**
```json
{
  "username": "john.doe",
  "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7vbqajDhA... john.doe@workstation"
}
```

**Not Found (404 Not Found):**
```json
{
  "detail": "SSH public key not found for user: john.doe"
}
```

### GET /authorized-keys

**List all authorized SSH keys for a user**

Retrieves all SSH public keys from a user's authorized_keys file. This endpoint returns all keys that are authorized for SSH access to the user's account.

**Query Parameters:**
- `username` (required): The username whose authorized keys to retrieve

#### Code Examples

##### cURL
```bash
# List authorized SSH keys for a user
curl -X GET "{base_url}/authorized-keys?username=john.doe" \
  -H "X-API-Key: your_api_key"
```

##### Python
```python
import requests

def get_authorized_keys(base_url, username, api_key):
    """Retrieve all authorized SSH keys for a user."""
    url = f"{base_url}/authorized-keys"
    params = {"username": username}
    headers = {"X-API-Key": api_key}
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        keys = response.json()
        print(f"✅ Found {len(keys)} authorized keys for {username}")
        return keys
    else:
        print(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
        return []

# Example usage
keys = get_authorized_keys("https://doorman.example.com", "john.doe", "your_api_key")
for i, key in enumerate(keys, 1):
    print(f"Key {i}: {key['public_key'][:50]}...")
```

#### Response Examples

**Success (200 OK):**
```json
[
  {
    "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7vbqajDhA... john.doe@workstation"
  },
  {
    "public_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGQw7Q... john.doe@laptop"
  }
]
```

### POST /authorized-keys

**Add a new SSH public key to user's authorized_keys**

Adds a new SSH public key to the specified user's authorized_keys file. The key is validated before being added to ensure it's in proper SSH public key format.

**Request Body:**
- `username` (required): The username to add the key for
- `public_key` (required): The SSH public key to add (full key including type and comment)

#### Code Examples

##### cURL
```bash
# Add SSH public key to authorized_keys
curl -X POST "{base_url}/authorized-keys" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "username": "john.doe",
    "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7vbqajDhA... john.doe@new-workstation"
  }'
```

##### Python
```python
import requests

def add_ssh_key(base_url, username, public_key, api_key):
    """Add SSH public key to user's authorized_keys."""
    url = f"{base_url}/authorized-keys"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    data = {
        "username": username,
        "public_key": public_key
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ SSH key added successfully for {username}")
        return True
    else:
        print(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
        return False

# Example usage
new_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7vbqajDhA... john.doe@new-workstation"
success = add_ssh_key("https://doorman.example.com", "john.doe", new_key, "your_api_key")
```

#### Response Examples

**Success (200 OK):**
```json
{
  "username": "john.doe",
  "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7vbqajDhA... john.doe@new-workstation"
}
```

**Validation Error (400 Bad Request):**
```json
{
  "detail": "Invalid SSH public key format"
}
```

### DELETE /authorized-keys

**Remove SSH public key from user's authorized_keys**

Removes a specific SSH public key from the user's authorized_keys file. The key must match exactly (including comments) to be removed.

**Request Body:**
- `username` (required): The username to remove the key from
- `public_key` (required): The exact SSH public key to remove

#### Code Examples

##### cURL
```bash
# Remove SSH public key from authorized_keys
curl -X DELETE "{base_url}/authorized-keys" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "username": "john.doe",
    "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7vbqajDhA... john.doe@old-workstation"
  }'
```

##### Python
```python
import requests

def remove_ssh_key(base_url, username, public_key, api_key):
    """Remove SSH public key from user's authorized_keys."""
    url = f"{base_url}/authorized-keys"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    data = {
        "username": username,
        "public_key": public_key
    }
    
    response = requests.delete(url, json=data, headers=headers)
    
    if response.status_code == 200:
        print(f"✅ SSH key removed successfully for {username}")
        return True
    elif response.status_code == 404:
        print(f"❌ SSH key not found in authorized_keys for {username}")
        return False
    else:
        print(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
        return False

# Example usage
old_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7vbqajDhA... john.doe@old-workstation"
success = remove_ssh_key("https://doorman.example.com", "john.doe", old_key, "your_api_key")
```

#### Response Examples

**Success (200 OK):**
```json
{
  "message": "SSH public key removed successfully from authorized_keys for user: john.doe"
}
```

**Not Found (404 Not Found):**
```json
{
  "detail": "SSH public key not found in authorized_keys for user: john.doe"
}
```

## Authorization Gateway

### GET /authorization

**Nginx proxy authorization validation for remote node access**

This is the primary authorization endpoint used by nginx's auth_request module to validate incoming requests before they are proxied to remote SynetoOS nodes. This endpoint performs comprehensive authentication and authorization checks based on the request context and determines whether the request should be allowed to proceed to the target remote node.

**Primary Use Case: Multi-Appliance Automation**
This endpoint enables centralized access control for distributed SynetoOS infrastructure, allowing customers to automate operations across multiple appliances through a single central doorman instance. When a client makes a request like `GET /api/remote-node-1/ca/certs`, nginx:
1. Extracts the original request details (URI, method, client IP)
2. Calls this authorization endpoint with the extracted context
3. Based on the response (200 = allow, 401/403 = deny), either forwards the request to the remote node or returns an error

**Headers Required for Nginx Integration:**
- `x-original-uri`: The original request URI being validated (e.g., `/api/remote-node-1/ca/certs`)
- `x-original-method`: The HTTP method of the original request (GET, POST, DELETE, etc.)
- `x-real-ip`: Client IP address for network-based API key restrictions

**Authentication Methods Supported (in order of precedence):**
1. **API Key**: `X-API-Key` header with network IP validation and scope checking
2. **JWT Bearer Token**: `Authorization: Bearer <token>` header with user context extraction
3. **Session Cookie**: `session` cookie for browser-based requests with user role validation

**Authorization Logic:**
1. **Whitelist Check**: If the URI matches whitelisted patterns (docs, health), immediately return 200 (authorized)
2. **API Key Validation**: If API key provided, validate token, check IP restrictions, and verify scopes
3. **JWT Token Validation**: If Bearer token provided, validate JWT signature and extract user context
4. **Session Cookie Validation**: If session cookie provided, validate session and check user status
5. **Role-Based Access**: Check if user has sufficient permissions for the requested operation
6. **Continuous Authentication**: For sensitive operations, verify recent re-authentication

**Multi-Appliance Automation Benefits:**
- **Centralized Authentication**: Single point of authentication for multiple SynetoOS appliances
- **Network Security**: API keys can be restricted to specific IP networks (CIDR notation)
- **Role-Based Access**: Fine-grained permissions based on user roles and operation types
- **Audit Trail**: All authorization decisions are logged for compliance and troubleshooting

#### Code Examples

##### cURL
```bash
# Validate API access with API key for remote node request
curl -X GET "{base_url}/authorization" \
  -H "X-API-Key: sk_1234567890abcdef" \
  -H "x-original-uri: /api/remote-node-1/ca/certs" \
  -H "x-original-method: GET" \
  -H "x-real-ip: 192.168.1.100"

# Validate with JWT token for user-based access
curl -X GET "{base_url}/authorization" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "x-original-uri: /api/remote-node-1/users" \
  -H "x-original-method: POST" \
  -H "x-real-ip: 192.168.1.100"

# Validate sensitive operation requiring continuous auth
curl -X GET "{base_url}/authorization" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "continuous-auth: user_password_or_otp" \
  -H "x-original-uri: /api/remote-node-1/users/123" \
  -H "x-original-method: DELETE" \
  -H "x-real-ip: 192.168.1.100"
```

##### Python
```python
import requests

def validate_remote_node_access(base_url, auth_method, original_uri, method="GET", client_ip="192.168.1.100", continuous_auth=None):
    """
    Validate authorization for remote node access through nginx proxy.
    
    Args:
        base_url: Doorman base URL
        auth_method: Dict with authentication (api_key, jwt_token, or session_cookie)
        original_uri: The original URI being requested (e.g., /api/remote-node-1/ca/certs)
        method: HTTP method of the original request
        client_ip: Client IP address for network restrictions
        continuous_auth: Password or OTP for sensitive operations
    
    Returns:
        bool: True if authorized, False if denied
    """
    url = f"{base_url}/authorization"
    headers = {
        "x-original-uri": original_uri,
        "x-original-method": method,
        "x-real-ip": client_ip
    }
    
    # Add authentication based on method
    if "api_key" in auth_method:
        headers["X-API-Key"] = auth_method["api_key"]
    elif "jwt_token" in auth_method:
        headers["Authorization"] = f"Bearer {auth_method['jwt_token']}"
    elif "session_cookie" in auth_method:
        # Session cookie would be handled by requests session
        pass
    
    # Add continuous authentication if required
    if continuous_auth:
        headers["continuous-auth"] = continuous_auth
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Authorized: {result.get('message', 'Access granted')}")
            return True
        elif response.status_code == 401:
            error = response.json()
            print(f"❌ Unauthorized: {error.get('detail', 'Authentication required')}")
            return False
        elif response.status_code == 403:
            error = response.json()
            print(f"🚫 Forbidden: {error.get('detail', 'Insufficient permissions')}")
            return False
        elif response.status_code == 428:
            error = response.json()
            print(f"🔐 Continuous Auth Required: {error.get('detail', 'Re-authentication needed')}")
            return False
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

# Example usage for multi-appliance automation
def automate_across_appliances():
    """Example of automating operations across multiple SynetoOS appliances."""
    base_url = "https://central-doorman.example.com"
    api_key = {"api_key": "sk_1234567890abcdef"}
    jwt_token = {"jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    
    # Define operations across multiple remote nodes
    operations = [
        {"node": "remote-node-1", "uri": "/ca/certs", "method": "GET", "auth": api_key},
        {"node": "remote-node-2", "uri": "/ca/certs", "method": "GET", "auth": api_key},
        {"node": "remote-node-1", "uri": "/users", "method": "POST", "auth": jwt_token},
        {"node": "remote-node-2", "uri": "/settings", "method": "PATCH", "auth": jwt_token, "continuous_auth": "user_password"}
    ]
    
    results = []
    for op in operations:
        original_uri = f"/api/{op['node']}{op['uri']}"
        is_authorized = validate_remote_node_access(
            base_url,
            op["auth"],
            original_uri,
            op["method"],
            continuous_auth=op.get("continuous_auth")
        )
        results.append({
            "operation": f"{op['method']} {original_uri}",
            "authorized": is_authorized
        })
    
    # Summary
    authorized_count = sum(1 for r in results if r["authorized"])
    print(f"\n📊 Authorization Summary: {authorized_count}/{len(results)} operations authorized")
    
    return results

# Run multi-appliance automation example
automation_results = automate_across_appliances()

#### Response Examples

**Success - Whitelisted URL (200 OK):**
```json
{
  "message": "Authorized a whitelisted URI."
}
```

**Success - Valid API Key (200 OK):**
```json
{
  "message": "Authorized request using valid API key."
}
```

**Success - Valid JWT Token (200 OK):**
```json
{
  "message": "Authorized request using valid JWT token."
}
```

**Unauthorized - Missing Authentication (401 Unauthorized):**
```json
{
  "detail": "Authentication required"
}
```

**Forbidden - Insufficient Permissions (403 Forbidden):**
```json
{
  "detail": "User has no rights to do this action."
}
```

**Continuous Auth Required (428 Precondition Required):**
```json
{
  "detail": "This action requires re-introducing the user's password",
  "type": "continuous_auth_required"
}
```

**API Key Network Restriction (403 Forbidden):**
```json
{
  "detail": "API key access denied: client IP not in allowed networks"
}
```

---

## Session Utilities

### GET /session-start-time

**Extract session start timestamp from JWT token**

Utility endpoint that extracts the session start timestamp from a JWT token. This is primarily used by external services for audit logging and session tracking purposes.

**Authentication:**
- Requires valid JWT token in Authorization header
- Token must contain session start time claim

#### Code Examples

##### cURL
```bash
# Get session start time from JWT token
curl -X GET "{base_url}/session-start-time" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

##### Python
```python
import requests

def get_session_start_time(base_url, jwt_token):
    """Extract session start time from JWT token."""
    url = f"{base_url}/session-start-time"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Session started at: {result['session_start_time']}")
        return result["session_start_time"]
    else:
        print(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
        return None

# Example usage
start_time = get_session_start_time(
    "https://doorman.example.com",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
)
```

#### Response Examples

**Success (200 OK):**
```json
{
  "session_start_time": "2024-01-15T10:30:45Z"
}
```

**Invalid Token (401 Unauthorized):**
```json
{
  "detail": "Invalid or expired JWT token"
}
```

## Authorization Behavior

### Whitelisted URLs

The following URLs bypass authorization checks:
- `/cake/system.json` (GET) - System information endpoint
- `/api/*/docs` (GET) - API documentation endpoints
- `/api/*/openapi.json` (GET) - OpenAPI specification endpoints

### Administrator-Only Endpoints

These endpoints require administrator role:
- `/api/auth/apiKeys` (POST, GET, DELETE) - API key management

### Continuous Authentication

**Always Protected Routes:**
- `/api/auth/users` (PATCH) - User modifications always require re-authentication

**Configurable Protected Routes:**
- When continuous authentication is globally enabled, additional routes require re-authentication
- Users must provide password or OTP in `continuous-auth` header
- Re-authentication expires after 1 minute of inactivity

### Authentication Priority

1. **Whitelisted URLs**: Immediate authorization without authentication
2. **API Key + IP**: Validates API key and client IP address
3. **JWT Bearer Token**: Validates JWT token and extracts user context
4. **Session Cookie**: Validates session and checks user status

## Security Considerations

### SSH Key Management
- **Key Validation**: All SSH keys are validated before storage
- **File System Security**: Authorized keys are stored in user home directories
- **Access Control**: Users can only manage their own SSH keys

### Authorization Gateway
- **Network Security**: API keys are validated against allowed IP networks
- **Session Security**: JWT tokens are validated for signature and expiration
- **User Status**: Disabled users are automatically denied access

### Continuous Authentication
- **Sensitive Operations**: Critical operations require re-authentication
- **Time-based Expiry**: Re-authentication expires after 1 minute
- **Flexible Methods**: Supports both password and OTP re-authentication

## Error Responses

**Authentication Required (401 Unauthorized):**
```json
{
  "detail": "Authentication required"
}
```

**Insufficient Permissions (403 Forbidden):**
```json
{
  "detail": "User has no rights to do this action."
}
```

**Invalid SSH Key (400 Bad Request):**
```json
{
  "detail": "Invalid SSH public key format"
}
```

**Continuous Auth Required (428 Precondition Required):**
```json
{
  "detail": "This action requires re-introducing the user's password",
  "type": "continuous_auth_required"
}
```

## Nginx Proxy Authorization Gateway

The authorization gateway serves as the primary authentication and authorization layer for nginx-proxied requests to remote nodes. This system enables centralized access control for distributed SynetoOS infrastructure.

### Proxy Authorization Architecture

**Nginx Integration Flow:**
1. **Incoming Request**: Client makes request to nginx proxy (e.g., `/api/remote-node-1/ca/certs`)
2. **Auth Request**: Nginx calls `GET /authorization` with original request headers
3. **Authorization Decision**: Doorman validates authentication and returns 200 (allow) or 401/403 (deny)
4. **Request Routing**: If authorized, nginx forwards request to the target remote node
5. **Response Proxying**: Remote node response is returned to the client through nginx

**Authentication Method Priority:**
1. **Whitelisted URLs**: Immediate authorization for public endpoints (docs, health)
2. **API Key Authentication**: `X-API-Key` header with network IP validation
3. **JWT Bearer Token**: `Authorization: Bearer <token>` with user context
4. **Session Cookie**: Browser session with user role and permission validation

### Remote Node Access Control

**Network-Based Restrictions:**
- API keys can be restricted to specific IP networks (CIDR notation)
- Client IP validation prevents unauthorized key usage
- Supports both single IPs and network ranges

**Role-Based Access:**
- Administrator users have full access to all remote node operations
- Regular users have limited access based on their permissions
- Support users have special access patterns for diagnostic operations

**Continuous Authentication:**
- Sensitive operations require re-authentication (password or OTP)
- Always-protected routes (user modifications) require continuous auth regardless of global settings
- Configurable continuous auth for additional endpoints when globally enabled

### Authorization Headers and Context

**Required Headers for Nginx Integration:**
- `x-original-uri`: The original request URI being validated (e.g., `/api/remote-node-1/ca/certs`)
- `x-original-method`: The HTTP method of the original request (GET, POST, etc.)
- `x-real-ip`: Client IP address for network-based API key restrictions

**Authentication Headers (one required):**
- `X-API-Key`: API key for programmatic access with network validation
- `Authorization: Bearer <token>`: JWT token for user-based access
- `Cookie: session=<token>`: Session cookie for browser-based access

### Whitelisted Endpoints

The following URLs bypass authorization checks entirely:
- `/cake/system.json` (GET) - System information endpoint
- `/api/*/docs` (GET) - API documentation endpoints  
- `/api/*/openapi.json` (GET) - OpenAPI specification endpoints

### Administrator-Only Endpoints

These endpoints require administrator role regardless of authentication method:
- `/api/auth/apiKeys` (POST, GET, DELETE) - API key management operations

## Deprecated Endpoints

**POST /login** - This endpoint is deprecated. Use `POST /v1/session` instead for authentication. The `/login` endpoint will be removed in a future version. 