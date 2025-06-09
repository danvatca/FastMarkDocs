# API Keys Management Documentation

## Overview

The API Keys Management API provides comprehensive functionality for creating, managing, and using API keys for programmatic access to the Syneto Doorman service. 

API keys enable secure, token-based authentication for automated systems, monitoring tools, CI/CD pipelines, and third-party integrations without requiring interactive user authentication.

**Key Features:**

- **Granular Access Control**: Define precise permissions with resource-based scopes
- **Network Security**: Restrict access to specific IP addresses or network ranges using CIDR notation
- **Flexible Expiration**: Configure validity periods from days to years with automatic cleanup
- **Multiple Key Types**: Support for custom keys and pre-configured remote Syneto access
- **Kubernetes Storage**: Secure persistence using Kubernetes Secrets with base64 encoding

**Network Restrictions:**

API keys support sophisticated network-based access control to enhance security:

- **CIDR Notation Support**: Define allowed networks using standard CIDR notation (e.g., `192.168.1.0/24`)
- **Multiple Networks**: Each API key can specify multiple allowed network ranges
- **IP Validation**: Every request validates the client IP against the allowed networks list
- **Automatic Blocking**: Requests from unauthorized networks are immediately rejected
- **Audit Logging**: All network restriction violations are logged for security monitoring

**Common Network Patterns:**
- **Single Host**: `192.168.1.100/32` (specific IP address)
- **Subnet Access**: `10.0.0.0/8` (entire private network)
- **Office Networks**: `172.16.0.0/12` (corporate network range)
- **Container Networks**: `10.244.0.0/16` (Kubernetes pod network)

**API Key Types:**

- **custom**: Fully configurable API key with custom scopes and network restrictions
- **remoteSyneto**: Pre-configured API key optimized for remote Syneto node communication with predefined network access

**Technical Implementation:**

- **Storage**: API keys are stored as Kubernetes Secrets in the `api-keys` namespace
- **Token Format**: Base64 URL-safe encoded tokens (43 characters, no prefix)
- **Validation**: Real-time scope and network validation on each request
- **Caching**: In-memory caching for performance optimization
- **Security**: Network validation occurs before any authorization checks for maximum security

## Endpoints

### GET /v1/apiKeys

**List all API keys with optional filtering**

Retrieves a comprehensive list of all API keys in the system, including metadata such as scopes, expiration dates, and network restrictions. 

The endpoint supports filtering by key type to help organize and manage different categories of API keys.

**Query Parameters:**

- `type` (optional): Filter API keys by type (`custom` or `remoteSyneto`)

**Returns:**

- Array of API key objects (tokens are never returned for security)
- Complete metadata including scopes, expiration, network restrictions
- Owner information and creation timestamps
- Validity periods and expiration dates

**Security Note:** API key tokens are never included in list responses to prevent accidental exposure.

#### Code Examples

##### cURL
```bash
# List all API keys
curl -X GET "{base_url}/v1/apiKeys" \
  -H "Authorization: Bearer your_jwt_token"

# Filter by custom API keys only
curl -X GET "{base_url}/v1/apiKeys?type=custom" \
  -H "Authorization: Bearer your_jwt_token"

# Filter by remote Syneto keys
curl -X GET "{base_url}/v1/apiKeys?type=remoteSyneto" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests
from datetime import datetime
from typing import Dict

class DoormanAPIClient:
    def __init__(self, base_url, jwt_token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {jwt_token}"}
    
    def list_api_keys(self, key_type=None):
        """List API keys with optional type filtering and expiration analysis."""
        url = f"{self.base_url}/v1/apiKeys"
        params = {"type": key_type} if key_type else {}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        api_keys = response.json()
        print(f"Found {len(api_keys)} API keys")
        
        # Analyze expiration status
        for key in api_keys:
            expires_at = datetime.fromisoformat(key['expiresAt'].replace('Z', '+00:00'))
            days_until_expiry = (expires_at - datetime.now().astimezone()).days
            
            if days_until_expiry <= 0:
                status = "🔴 EXPIRED"
            elif days_until_expiry <= 7:
                status = "🟡 EXPIRING SOON"
            elif days_until_expiry <= 30:
                status = "🟠 EXPIRES SOON"
            else:
                status = "✅ ACTIVE"
                
            print(f"  {key['name']} ({key['type']}) - {status} - {days_until_expiry} days remaining")
        
        return api_keys

# Usage examples
client = DoormanAPIClient("https://doorman.example.com", "your_jwt_token")

# List all keys
all_keys = client.list_api_keys()

# List only custom keys for application integrations
custom_keys = client.list_api_keys("custom")

# List only remote Syneto keys for node communication
remote_keys = client.list_api_keys("remoteSyneto")
```

#### Response Examples

**Success (200 OK):**
```json
[
  {
    "id": "key-cert-automation-001",
    "type": "custom",
    "name": "cert-automation-prod",
    "owner": "platform-team",
    "scopes": [
      {
        "resource": "/ca/*",
        "permissions": ["read", "write"]
      }
    ],
    "allowedNetworks": ["10.100.0.0/16"],
    "validity": "180d",
    "createdAt": "2024-01-15T10:30:00Z",
    "expiresAt": "2024-07-13T10:30:00Z"
  }
]
```

**Authentication Error (401 Unauthorized):**
```json
{
  "detail": "Invalid or expired JWT token",
  "type": "authentication_error",
  "code": "INVALID_TOKEN"
}
```

**Forbidden Access (403 Forbidden):**
```json
{
  "detail": "Insufficient permissions to list API keys",
  "type": "authorization_error",
  "code": "INSUFFICIENT_PERMISSIONS"
}
```

---

### POST /v1/apiKeys

**Create a new API key with specified configuration and permissions**

Creates a new API key with comprehensive configuration options including scoped permissions, network restrictions, and expiration settings. 

The endpoint supports both custom API keys with full configuration flexibility and pre-configured remote Syneto keys for inter-node communication.

**Request Body Requirements:**

- **Custom keys**: Require name, owner, scopes, and network restrictions
- **Remote Syneto keys**: Only require type specification (other settings are pre-configured)
- **Validation**: All parameters are validated for security and consistency

**Security Considerations:**

- API key tokens are only returned once during creation
- Network restrictions should follow the principle of least privilege
- Expiration periods should align with security policies
- Scopes should grant minimal necessary permissions

#### Code Examples

##### cURL
```bash
# Create custom API key for certificate automation
curl -X POST "{base_url}/v1/apiKeys" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "type": "custom",
    "name": "cert-automation-prod",
    "owner": "platform-team",
    "scopes": [
      {
        "resource": "/ca/certs",
        "permissions": ["read", "write"]
      },
      {
        "resource": "/ca/revoke",
        "permissions": ["write"]
      }
    ],
    "allowedNetworks": ["10.100.0.0/16", "172.16.50.0/24"],
    "validity": "180d"
  }'

# Create monitoring API key with read-only access
curl -X POST "{base_url}/v1/apiKeys" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "type": "custom",
    "name": "monitoring-healthcheck",
    "owner": "sre-team",
    "scopes": [
      {
        "resource": "/health",
        "permissions": ["read"]
      },
      {
        "resource": "/metrics",
        "permissions": ["read"]
      }
    ],
    "allowedNetworks": ["192.168.100.0/24"],
    "validity": "365d"
  }'

# Create remote Syneto API key for inter-node communication
curl -X POST "{base_url}/v1/apiKeys" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "type": "remoteSyneto"
  }'
```

##### Python
```python
import requests
import json
from typing import Dict, Optional

class APIKeyManager:
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt_token}"
        }
    
    def create_custom_key(self, 
                         name: str, 
                         owner: str, 
                         scopes: list[Dict], 
                         allowed_networks: list[str], 
                         validity: str = "90d") -> Dict:
        """Create a custom API key with specified permissions and restrictions."""
        
        payload = {
            "type": "custom",
            "name": name,
            "owner": owner,
            "scopes": scopes,
            "allowedNetworks": allowed_networks,
            "validity": validity
        }
        
        response = requests.post(
            f"{self.base_url}/v1/apiKeys",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        
        api_key = response.json()
        
        # Securely handle the token (only shown once)
        print(f"✅ Created API key '{name}' with ID: {api_key['id']}")
        print(f"🔑 Token (save securely): {api_key['token']}")
        print(f"⏰ Expires: {api_key['expiresAt']}")
        print(f"🌐 Networks: {', '.join(api_key['allowedNetworks'])}")
        
        return api_key
    
    def create_cert_automation_key(self, networks: list[str]) -> Dict:
        """Create an API key optimized for certificate automation workflows."""
        return self.create_custom_key(
            name="cert-automation",
            owner="platform-team",
            scopes=[
                {"resource": "/ca/certs", "permissions": ["read", "write"]},
                {"resource": "/ca/revoke", "permissions": ["write"]}
            ],
            allowed_networks=networks,
            validity="180d"
        )
    
    def create_monitoring_key(self, networks: list[str]) -> Dict:
        """Create a read-only monitoring API key for health checks and metrics."""
        return self.create_custom_key(
            name="monitoring-readonly",
            owner="sre-team",
            scopes=[
                {"resource": "/health", "permissions": ["read"]},
                {"resource": "/metrics", "permissions": ["read"]},
                {"resource": "/ca/certs", "permissions": ["read"]}
            ],
            allowed_networks=networks,
            validity="365d"
        )
    
    def create_remote_syneto_key(self) -> Dict:
        """Create a pre-configured API key for remote Syneto node communication."""
        payload = {"type": "remoteSyneto"}
        
        response = requests.post(
            f"{self.base_url}/v1/apiKeys",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        
        api_key = response.json()
        print(f"✅ Created remote Syneto key with ID: {api_key['id']}")
        print(f"🔑 Token (save securely): {api_key['token']}")
        
        return api_key

# Usage examples
manager = APIKeyManager("https://doorman.example.com", "your_jwt_token")

# Create certificate automation key for production environment
cert_key = manager.create_cert_automation_key(["10.100.0.0/16", "172.16.50.0/24"])

# Create monitoring key for SRE team
monitoring_key = manager.create_monitoring_key(["192.168.100.0/24"])

# Create remote Syneto key for cluster communication
remote_key = manager.create_remote_syneto_key()
```

#### Response Examples

**Success (201 Created) - Custom API Key:**
```json
{
  "id": "key-cert-automation-prod-001",
  "type": "custom",
  "name": "cert-automation-prod",
  "owner": "platform-team",
  "token": "a1b2c3d4e5f6789012345678901234567890abcdef123",
  "scopes": [
    {
      "resource": "/ca/certs",
      "permissions": ["read", "write"]
    },
    {
      "resource": "/ca/revoke", 
      "permissions": ["write"]
    }
  ],
  "allowedNetworks": ["10.100.0.0/16", "172.16.50.0/24"],
  "validity": "180d",
  "createdAt": "2024-01-20T15:45:00Z",
  "expiresAt": "2024-07-18T15:45:00Z"
}
```

**Success (201 Created) - Remote Syneto API Key:**
```json
{
  "id": "key-remote-node-001",
  "type": "remoteSyneto",
  "name": "remote-node-cluster-a",
  "owner": "system",
  "token": "x9y8z7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6",
  "allowedNetworks": ["10.200.0.0/16"],
  "validity": "365d",
  "createdAt": "2024-01-05T16:00:00Z",
  "expiresAt": "2025-01-05T16:00:00Z"
}
```

**Validation Error (400 Bad Request):**
```json
{
  "detail": "Validation failed for API key creation",
  "type": "validation_error",
  "code": "VALIDATION_FAILED",
  "errors": [
    {
      "field": "name",
      "message": "API key name must be unique"
    },
    {
      "field": "allowedNetworks",
      "message": "Invalid CIDR notation in network restriction"
    }
  ]
}
```

**Conflict Error (409 Conflict):**
```json
{
  "detail": "API key with this name already exists"
}
```

---

### GET /v1/apiKeys/{id}

**Get detailed information about a specific API key**

Retrieves comprehensive details about a specific API key including its configuration, permissions, and metadata. 

This endpoint is essential for auditing, monitoring, and managing individual API keys.

**Path Parameters:**

- `id` (required): The unique identifier of the API key

**Security Note:** The API key token is never returned in GET requests for security reasons. Tokens are only provided during initial creation.

**Use Cases:**

- Auditing API key permissions and restrictions
- Monitoring API key expiration status
- Verifying API key configuration before updates
- Troubleshooting authentication issues

#### Code Examples

##### cURL
```bash
# Get details for a specific API key
curl -X GET "{base_url}/v1/apiKeys/key-cert-automation-001" \
  -H "Authorization: Bearer your_jwt_token"

# Get details with verbose output for debugging
curl -X GET "{base_url}/v1/apiKeys/key-monitoring-readonly" \
  -H "Authorization: Bearer your_jwt_token" \
  -v
```

##### Python
```python
import requests
from datetime import datetime
from typing import Dict

def get_api_key_details(base_url: str, jwt_token: str, key_id: str) -> Dict:
    """Get detailed information about an API key with expiration analysis."""
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    response = requests.get(f"{base_url}/v1/apiKeys/{key_id}", headers=headers)
    response.raise_for_status()
    
    key_info = response.json()
    
    # Analyze key status and expiration
    expires_at = datetime.fromisoformat(key_info['expiresAt'].replace('Z', '+00:00'))
    days_until_expiry = (expires_at - datetime.now().astimezone()).days
    
    # Determine key status
    if days_until_expiry <= 0:
        status = "🔴 EXPIRED"
    elif days_until_expiry <= 7:
        status = "🟡 EXPIRING SOON"
    elif days_until_expiry <= 30:
        status = "🟠 EXPIRES SOON"
    else:
        status = "🟢 ACTIVE"
    
    # Analyze creation and validity
    created_at = datetime.fromisoformat(key_info['createdAt'].replace('Z', '+00:00'))
    days_since_creation = (datetime.now().astimezone() - created_at).days
    
    # Display comprehensive information
    print(f"API Key Details: {key_info['name']}")
    print(f"  ID: {key_info['id']}")
    print(f"  Type: {key_info['type']}")
    print(f"  Owner: {key_info['owner']}")
    print(f"  Status: {status} ({days_until_expiry} days remaining)")
    print(f"  Age: {days_since_creation} days since creation")
    print(f"  Networks: {', '.join(key_info['allowedNetworks'])}")
    
    if 'scopes' in key_info:
        print("  Permissions:")
        for scope in key_info['scopes']:
            permissions = ', '.join(scope['permissions'])
            print(f"    {scope['resource']}: {permissions}")
    
    return key_info

# Usage examples
key_details = get_api_key_details(
    "https://doorman.example.com", 
    "your_jwt_token", 
    "key-cert-automation-001"
)

# Check multiple keys for audit
key_ids = ["key-cert-automation-001", "key-monitoring-readonly", "key-remote-node-001"]
for key_id in key_ids:
    try:
        details = get_api_key_details("https://doorman.example.com", "your_jwt_token", key_id)
        print("---")
    except requests.exceptions.HTTPError as e:
        print(f"Failed to get details for {key_id}: {e}")
```

#### Response Examples

**Success (200 OK) - Custom API Key:**
```json
{
  "id": "key-cert-automation-001",
  "type": "custom",
  "name": "cert-automation-prod",
  "owner": "platform-team",
  "scopes": [
    {
      "resource": "/ca/*",
      "permissions": ["read", "write"]
    }
  ],
  "allowedNetworks": ["10.100.0.0/16"],
  "validity": "180d",
  "createdAt": "2024-01-15T10:30:00Z",
  "expiresAt": "2024-07-13T10:30:00Z"
}
```

**Success (200 OK) - Remote Syneto API Key:**
```json
{
  "id": "key-remote-node-001",
  "type": "remoteSyneto",
  "name": "remote-node-cluster-a",
  "owner": "system",
  "allowedNetworks": ["10.200.0.0/16"],
  "validity": "365d",
  "createdAt": "2024-01-05T16:00:00Z",
  "expiresAt": "2025-01-05T16:00:00Z"
}
```

**Not Found Error (404 Not Found):**
```json
{
  "detail": "API key not found",
  "type": "not_found_error",
  "code": "KEY_NOT_FOUND"
}
```

**Forbidden Access (403 Forbidden):**
```json
{
  "detail": "Insufficient permissions to view this API key",
  "type": "authorization_error",
  "code": "INSUFFICIENT_PERMISSIONS"
}
```

---

### DELETE /v1/apiKeys/{id}

**Permanently delete an API key from the system**

Removes an API key from the system immediately and irreversibly. This action will cause any systems currently using the API key to lose access immediately. 

Use this endpoint carefully and ensure proper coordination with systems that may be using the key.

**Path Parameters:**

- `id` (required): The unique identifier of the API key to delete

**Important Considerations:**

- **Immediate Effect**: The API key becomes invalid immediately upon deletion
- **Irreversible Action**: Deleted API keys cannot be recovered
- **System Impact**: Any automated systems using the key will fail authentication
- **Audit Trail**: Deletion events are logged for security auditing

**Best Practices:**

- Coordinate with teams using the API key before deletion
- Consider disabling the key temporarily before permanent deletion
- Update any automated systems to use alternative authentication
- Document the reason for deletion in change management systems

#### Code Examples

##### cURL
```bash
# Delete a specific API key
curl -X DELETE "{base_url}/v1/apiKeys/key-cert-automation-001" \
  -H "Authorization: Bearer your_jwt_token"

# Delete with verbose output to confirm success
curl -X DELETE "{base_url}/v1/apiKeys/key-monitoring-readonly" \
  -H "Authorization: Bearer your_jwt_token" \
  -v
```

##### Python
```python
import requests
from datetime import datetime
from typing import Optional

class APIKeyManager:
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {jwt_token}"}
    
    def delete_api_key(self, key_id: str, confirm: bool = False) -> bool:
        """Delete an API key with optional confirmation and safety checks."""
        
        if not confirm:
            # Get key details first for confirmation
            try:
                key_info = self.get_api_key_details(key_id)
                
                print(f"⚠️  You are about to delete API key:")
                print(f"   ID: {key_info['id']}")
                print(f"   Name: {key_info['name']}")
                print(f"   Owner: {key_info['owner']}")
                print(f"   Type: {key_info['type']}")
                print(f"   Created: {key_info.get('createdAt', 'Unknown')}")
                
                # Check if key is recently created (might be in active use)
                if 'createdAt' in key_info:
                    created_at = datetime.fromisoformat(key_info['createdAt'].replace('Z', '+00:00'))
                    days_since_creation = (datetime.now().astimezone() - created_at).days
                    if days_since_creation <= 30:
                        print(f"   ⚠️  This key was created recently ({days_since_creation} days ago) - ensure no systems depend on it")
                
                confirmation = input("\nType 'DELETE' to confirm permanent removal: ")
                if confirmation != 'DELETE':
                    print("❌ Deletion cancelled")
                    return False
                    
            except requests.exceptions.HTTPError:
                print(f"⚠️  Could not retrieve details for key {key_id}, proceeding with deletion...")
        
        try:
            response = requests.delete(f"{self.base_url}/v1/apiKeys/{key_id}", headers=self.headers)
            
            if response.status_code == 204:
                print(f"✅ API key {key_id} deleted successfully")
                print("   All systems using this key will lose access immediately")
                return True
            elif response.status_code == 404:
                print(f"❌ API key {key_id} not found (may already be deleted)")
                return False
            else:
                print(f"❌ Failed to delete API key: HTTP {response.status_code}")
                if response.content:
                    error = response.json()
                    print(f"   Error: {error.get('detail', 'Unknown error')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error during deletion: {e}")
            return False
    
    def get_api_key_details(self, key_id: str) -> dict:
        """Helper method to get API key details."""
        response = requests.get(f"{self.base_url}/v1/apiKeys/{key_id}", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def bulk_delete_expired_keys(self, dry_run: bool = True) -> list[str]:
        """Delete all expired API keys with safety checks."""
        
        # Get all keys
        response = requests.get(f"{self.base_url}/v1/apiKeys", headers=self.headers)
        response.raise_for_status()
        all_keys = response.json()
        
        expired_keys = []
        for key in all_keys:
            expires_at = datetime.fromisoformat(key['expiresAt'].replace('Z', '+00:00'))
            if expires_at < datetime.now().astimezone():
                expired_keys.append(key)
        
        if not expired_keys:
            print("✅ No expired keys found")
            return []
        
        print(f"Found {len(expired_keys)} expired keys:")
        for key in expired_keys:
            print(f"  - {key['name']} (expired: {key['expiresAt']})")
        
        if dry_run:
            print("\n🔍 DRY RUN - No keys will be deleted")
            return [key['id'] for key in expired_keys]
        
        # Delete expired keys
        deleted_keys = []
        for key in expired_keys:
            if self.delete_api_key(key['id'], confirm=True):
                deleted_keys.append(key['id'])
        
        return deleted_keys

# Usage examples
manager = APIKeyManager("https://doorman.example.com", "your_jwt_token")

# Delete a specific key with confirmation
success = manager.delete_api_key("key-cert-automation-001")

# Delete without confirmation (use carefully)
success = manager.delete_api_key("key-old-unused", confirm=True)

# Clean up expired keys (dry run first)
expired_key_ids = manager.bulk_delete_expired_keys(dry_run=True)
print(f"Would delete {len(expired_key_ids)} expired keys")

# Actually delete expired keys
# deleted_keys = manager.bulk_delete_expired_keys(dry_run=False)
```

#### Response Examples

**Success (204 No Content):**
```
HTTP/1.1 204 No Content
Date: Mon, 20 Jan 2024 15:45:00 GMT
Server: uvicorn
```

**Not Found Error (404 Not Found):**
```json
{
  "detail": "API key not found",
  "type": "not_found_error",
  "code": "KEY_NOT_FOUND"
}
```

**Forbidden Access (403 Forbidden):**
```json
{
  "detail": "Insufficient permissions to delete this API key",
  "type": "authorization_error",
  "code": "INSUFFICIENT_PERMISSIONS"
}
```

**Authentication Error (401 Unauthorized):**
```json
{
  "detail": "Invalid or expired JWT token",
  "type": "authentication_error",
  "code": "INVALID_TOKEN"
}
```

## API Key Usage

### Authentication with API Keys

Once created, API keys can be used for authentication by including them in the `X-API-Key` header:

```bash
curl -X GET "{base_url}/ca/certs" \
  -H "X-API-Key: a1b2c3d4e5f6789012345678901234567890abcdef123"
```

**Important Notes:**
- API keys are base64 URL-safe encoded tokens (43 characters)
- No prefix is used (unlike some documentation examples showing `sk_`)
- Always use HTTPS when transmitting API keys
- Include the full token exactly as provided during creation

### Scope Configuration

API key scopes define what resources and operations the key can access:

**Resource Patterns:**

- `/ca/*` - All certificate authority operations
- `/health` - Health check endpoint only
- `/settings` - System settings access
- `/users/*` - User management operations

**Permission Types:**

- `read` - GET operations
- `write` - POST, PUT, PATCH operations
- `delete` - DELETE operations

### Network Restrictions

API keys can be restricted to specific IP addresses or networks:

**Examples:**

- `192.168.1.100/32` - Single IP address
- `192.168.1.0/24` - Subnet range
- `10.0.0.0/8` - Large network range
- `0.0.0.0/0` - No restrictions (not recommended)

## Technical Details

### Scope Pattern Matching

API key scopes use Python regex patterns for flexible resource matching:

- **Pattern Engine**: Uses `re.match()` for validation
- **Anchoring**: Patterns are automatically anchored to the start of URIs
- **Case Sensitivity**: Resource patterns are case-sensitive
- **Regex Support**: Full regex syntax supported for complex patterns

**Example Patterns:**

```python
# Exact path matching
{"resource": "/api/ca/certs", "permissions": ["get"]}

# Wildcard matching
{"resource": "/api/ca/.*", "permissions": ["get", "post"]}

# Complex regex patterns
{"resource": "/api/storage/volumes/.+/snapshots", "permissions": ["delete"]}
```

### Network Validation

Network restrictions are validated on every API request:

- **IPv4 Support**: Full IPv4 address and CIDR notation support
- **Real-time Validation**: Client IP checked against allowed networks on each request
- **Default Behavior**: Defaults to `0.0.0.0/0` (all networks) if not specified
- **Performance**: Efficient IP-in-network checking using Python's `ipaddress` module

### Permission System

HTTP method permissions are normalized and validated:

- **Case Normalization**: All methods converted to lowercase internally
- **Supported Methods**: `get`, `post`, `put`, `delete`, `patch`, `head`, `options`, `trace`
- **Validation**: Invalid methods rejected during API key creation
- **Flexible Mapping**: Methods map to standard HTTP operations

## Security Best Practices

### API Key Management

- **Rotate keys regularly**: Set appropriate expiration times
- **Use network restrictions**: Limit access to known IP ranges
- **Principle of least privilege**: Grant minimal required permissions
- **Monitor expiration**: Track API key expiration dates and renew before expiry

### Storage and Transmission

- **Secure storage**: Store API keys securely, never in plain text
- **HTTPS only**: Always use HTTPS when transmitting API keys
- **Environment variables**: Use environment variables for API keys in applications
- **Avoid logging**: Never log API keys in application logs

### Access Control

- **Owner tracking**: Assign clear ownership to API keys
- **Regular audits**: Review API key usage and permissions regularly
- **Immediate revocation**: Delete compromised keys immediately
- **Documentation**: Maintain records of API key purposes and usage

## Error Responses

### Common Errors

**Invalid API Key (401 Unauthorized):**
```json
{
  "detail": "Invalid API key"
}
```

**Expired API Key (401 Unauthorized):**
```json
{
  "detail": "API key has expired"
}
```

**Network Restriction Violation (403 Forbidden):**
```json
{
  "detail": "API key not allowed from this IP address"
}
```

**Insufficient Permissions (403 Forbidden):**
```json
{
  "detail": "API key does not have permission for this operation"
}
```

**API Key Not Found (404 Not Found):**
```json
{
  "detail": "API key not found"
}
```

**API Key Already Exists (409 Conflict):**
```json
{
  "detail": "API key with this name already exists"
}
