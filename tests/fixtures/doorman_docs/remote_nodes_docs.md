# Remote Nodes Management Documentation

## Overview

The **Remote Nodes API** enables distributed SynetoOS management by connecting multiple nodes through a central Doorman instance. This API provides secure API proxying and enterprise certificate authority delegation for distributed infrastructure.

### 🌐 **Core Capabilities**

**Remote Node Registration**
- Manual registration of SynetoOS nodes with API key authentication
- Automatic node discovery through Protection API integration
- Kubernetes-based secure credential storage

**Enterprise Certificate Authority**
- Designate a single remote node as enterprise CA (only one allowed)
- Automatic certificate operation delegation to enterprise CA node
- Centralized certificate management across distributed infrastructure

**Universal API Proxying**
- Transparent forwarding of all HTTP methods (GET, POST, PUT, PATCH, DELETE) to remote nodes
- Automatic API key injection and path security (prevents path traversal)
- 60-second timeout for remote operations

### 🛡️ **Security Features**

**Secure Communication**
- HTTPS-only communication between nodes
- API key-based authentication with automatic header injection
- URL path encoding to prevent path traversal attacks

**Credential Management**
- API key tokens stored encrypted in Kubernetes secrets
- Tokens never returned in API responses for security
- Namespace isolation for remote node configurations

### ⚠️ **Important Limitations**

**Enterprise CA Restrictions**
- Only one remote node can be designated as enterprise CA
- Adding a second enterprise CA will result in a 409 Conflict error
- Enterprise CA designation affects all certificate operations globally

**Network Requirements**
- Remote nodes must be accessible via HTTPS
- Custom ports supported in host specification (e.g., `node.example.com:8443`)
- Network connectivity required for all proxy operations

### 🔄 **Remote Node Operations**

- **Node Discovery**: `GET /v1/remoteNodes` - List all registered remote node IDs
- **Node Registration**: `POST /v1/remoteNodes` - Add new nodes with enterprise CA validation
- **Node Details**: `GET /v1/remoteNodes/{id}` - Retrieve node configuration (tokens excluded)
- **Node Removal**: `DELETE /v1/remoteNodes/{id}` - Permanently remove nodes
- **Universal Proxying**: `{METHOD} /v1/remoteNodes/{node_id}/{path:path}` - Forward any request to remote nodes

## Endpoints

### GET /v1/remoteNodes

**List all remote node IDs**

Retrieves a list of all registered remote node identifiers.

**Note**: This endpoint returns only node IDs, not full node objects.

#### Code Examples

##### cURL
```bash
curl -X GET "{base_url}/v1/remoteNodes" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests

url = "{base_url}/v1/remoteNodes"
headers = {"Authorization": "Bearer your_jwt_token"}

response = requests.get(url, headers=headers)
node_ids = response.json()
print(f"Found {len(node_ids)} remote nodes")

for node_id in node_ids:
    print(f"Node ID: {node_id}")
```

#### Response Example

**Success (200 OK):**
```json
[
  "remote-node-1",
  "enterprise-ca",
  "backup-node"
]
```

---

### POST /v1/remoteNodes

**Add a new remote node**

Registers a new remote node for management and API proxying.

**Enterprise CA Validation**: Only one node can be designated as enterprise CA. Attempting to add a second enterprise CA will result in a 409 Conflict error.

#### Code Examples

##### cURL
```bash
# Add standard remote node
curl -X POST "{base_url}/v1/remoteNodes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "id": "remote-node-1",
    "host": "192.168.1.200",
    "apiKeyToken": "sk_1234567890abcdef",
    "apiKeyId": "remote-key-id",
    "enterpriseCa": false
  }'

# Add enterprise CA node
curl -X POST "{base_url}/v1/remoteNodes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "id": "enterprise-ca",
    "host": "ca.enterprise.com",
    "apiKeyToken": "sk_enterprise_key",
    "apiKeyId": "enterprise-key-id",
    "enterpriseCa": true
  }'
```

##### Python
```python
import requests

url = "{base_url}/v1/remoteNodes"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_jwt_token"
}

# Add standard remote node
data = {
    "id": "remote-node-1",
    "host": "192.168.1.200",
    "apiKeyToken": "sk_1234567890abcdef",
    "apiKeyId": "remote-key-id",
    "enterpriseCa": False
}

response = requests.post(url, headers=headers, json=data)
remote_node = response.json()
print(f"Added remote node: {remote_node['id']}")
```

#### Request Examples

**Standard Remote Node:**
```json
{
  "id": "remote-node-1",
  "host": "192.168.1.200",
  "apiKeyToken": "sk_1234567890abcdef1234567890abcdef",
  "apiKeyId": "remote-key-id",
  "enterpriseCa": false
}
```

**Enterprise CA Node:**
```json
{
  "id": "enterprise-ca",
  "host": "ca.enterprise.com",
  "apiKeyToken": "sk_enterprise_abcdef1234567890abcdef1234567890",
  "apiKeyId": "enterprise-key-id",
  "enterpriseCa": true
}
```

**Remote Node with Custom Port:**
```json
{
  "id": "remote-node-2",
  "host": "node2.internal:8443",
  "apiKeyToken": "sk_custom_port_key",
  "apiKeyId": "custom-port-key-id",
  "enterpriseCa": false
}
```

#### Response Examples

**Success (200 OK):**
```json
{
  "id": "remote-node-1",
  "host": "192.168.1.200",
  "apiKeyId": "remote-key-id",
  "enterpriseCa": false
}
```

**Enterprise CA Conflict (409 Conflict):**
```json
{
  "message": "An enterprise CA remote node already exists with id 'existing-ca'. Only one remote node can be designated as enterprise CA."
}
```

---

### GET /v1/remoteNodes/{id}

**Get remote node details**

Retrieves detailed information about a specific remote node.

**Security Note**: API key tokens are never returned for security reasons.

#### Code Examples

##### cURL
```bash
curl -X GET "{base_url}/v1/remoteNodes/remote-node-1" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests

node_id = "remote-node-1"
url = f"{base_url}/v1/remoteNodes/{node_id}"
headers = {"Authorization": "Bearer your_jwt_token"}

response = requests.get(url, headers=headers)
node = response.json()
print(f"Node: {node['id']} at {node['host']}")
print(f"Enterprise CA: {node['enterpriseCa']}")
```

#### Response Example

**Success (200 OK):**
```json
{
  "id": "remote-node-1",
  "host": "192.168.1.200",
  "apiKeyId": "remote-key-id",
  "enterpriseCa": false
}
```

---

### DELETE /v1/remoteNodes/{id}

**Remove a remote node**

Permanently removes a remote node from the system. This action is irreversible.

**Warning**: 
- Any ongoing operations with this node will be interrupted
- Certificate operations may fail if this node was the enterprise CA
- API proxying to this node will stop immediately

#### Code Examples

##### cURL
```bash
curl -X DELETE "{base_url}/v1/remoteNodes/remote-node-1" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests

node_id = "remote-node-1"
url = f"{base_url}/v1/remoteNodes/{node_id}"
headers = {"Authorization": "Bearer your_jwt_token"}

response = requests.delete(url, headers=headers)
if response.status_code == 204:
    print(f"Remote node {node_id} deleted successfully")
```

#### Response

**Success (204 No Content):** Remote node removed successfully

## API Proxying

### Universal Proxy Endpoints

All HTTP methods are supported for proxying requests to remote nodes:

- `GET /v1/remoteNodes/{node_id}/{path:path}`
- `POST /v1/remoteNodes/{node_id}/{path:path}`
- `PUT /v1/remoteNodes/{node_id}/{path:path}`
- `PATCH /v1/remoteNodes/{node_id}/{path:path}`
- `DELETE /v1/remoteNodes/{node_id}/{path:path}`

### Proxy Behavior

**Automatic Features**:
- API key injection via `X-API-Key` header
- URL path encoding for security (prevents path traversal)
- Query parameter forwarding
- Request body forwarding for POST/PUT/PATCH methods
- 60-second timeout for remote operations

**Auto-Discovery**:
If a remote node is not found, the system attempts to create it automatically via the Protection API's replication host mechanism.

### Proxy Examples

#### Health Check via Proxy
```bash
# Check health of remote node
curl -X GET "{base_url}/v1/remoteNodes/remote-node-1/health" \
  -H "Authorization: Bearer your_jwt_token"
```

#### Certificate Operations via Proxy
```bash
# List certificates on remote node
curl -X GET "{base_url}/v1/remoteNodes/remote-node-1/ca/certs" \
  -H "Authorization: Bearer your_jwt_token"

# Create certificate on remote node
curl -X POST "{base_url}/v1/remoteNodes/remote-node-1/ca/certs/my-cert" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "commonName": "my-cert",
    "dnsNames": ["example.com"]
  }'
```

#### User Management via Proxy
```bash
# Get users from remote node
curl -X GET "{base_url}/v1/remoteNodes/remote-node-1/users" \
  -H "Authorization: Bearer your_jwt_token"

# Update user on remote node
curl -X PATCH "{base_url}/v1/remoteNodes/remote-node-1/users/admin" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{"isEnabled": true}'
```

## Enterprise CA Configuration

### Single Enterprise CA Limitation

**Important**: Only one remote node can be designated as enterprise CA across the entire system.

**Behavior when Enterprise CA is configured**:
- All certificate operations are automatically delegated to the enterprise CA node
- Local CA functionality is bypassed
- Certificate creation becomes synchronous (no job queuing)
- CA certificate is retrieved from the remote enterprise CA

### Enterprise CA Requirements

**Remote Node Setup**:
- Remote node must have certificate authority functionality enabled
- API key must have CA operation permissions (`ca:*` scope)
- Network latency should be minimal for optimal performance

**Network Considerations**:
- Stable network connection required for certificate operations
- Consider using dedicated network links for enterprise CA communication
- Monitor network latency as it directly affects certificate operation performance

### ⚠️ **Enterprise CA Failure Behavior**

**Critical Design Decision: No Fallback to Local CA**

When an enterprise CA remote node is configured but fails to respond, the system implements a **strict no-fallback policy**. This is a deliberate design choice to maintain certificate authority consistency and prevent security issues.

#### **Certificate Operations During Enterprise CA Failure**

**All Certificate API Operations Fail (502 Bad Gateway)**:
- `GET /ca` - CA certificate retrieval fails completely
- `GET /ca/certs` - Certificate listing fails completely  
- `GET /ca/certs/{name}` - Individual certificate retrieval fails completely
- `POST /ca/certs/{name}` - Certificate creation fails completely

**Example Error Response**:
```json
{
  "detail": "Failed to get CA certificate from enterprise CA: Connection timeout"
}
```

#### **Certificate Renewal Behavior During Enterprise CA Failure**

**Automatic Certificate Renewal Skips Failed Certificates**:
- Certificates managed by the enterprise CA are **not renewed** if the enterprise CA is unreachable
- The system logs a warning and skips renewal rather than falling back to local CA
- Existing certificates remain valid until their natural expiration
- No local secrets are deleted when enterprise CA communication fails

**Renewal Process Logic**:
1. System attempts to contact enterprise CA to list managed certificates
2. If communication fails, renewal is **skipped entirely** for that certificate
3. Warning logged: `"Failed to renew certificate {name} through enterprise CA: {error}. Skipping renewal."`
4. Certificate remains in its current state (no local fallback)

#### **Metrics and Monitoring During Failures**

**Enterprise CA Request Metrics**:
- All failed operations are recorded with `CertificateStatus.FAILURE`
- Metrics include operation type, duration, and error classification
- Certificate validation metrics continue to track enterprise CA certificate health

**Monitoring Implications**:
- Monitor enterprise CA connectivity proactively
- Set up alerts for enterprise CA communication failures
- Track certificate expiration dates more closely when enterprise CA is unreachable

#### **Operational Impact of Enterprise CA Failures**

**Immediate Impact**:
- **Certificate Creation**: Completely blocked - no new certificates can be issued
- **Certificate Retrieval**: Existing certificate data cannot be accessed via API
- **Certificate Listing**: Cannot enumerate available certificates
- **CA Certificate Access**: Cannot retrieve the CA certificate for validation

**Long-term Impact**:
- **Certificate Renewal**: Automatic renewal stops for enterprise CA managed certificates
- **Certificate Expiration**: Certificates will expire without renewal if enterprise CA remains unreachable
- **Service Disruption**: Services depending on certificate operations will fail

**Recovery Actions**:
1. **Restore Enterprise CA Connectivity**: Fix network issues, restart remote node, verify API key validity
2. **Monitor Certificate Expiration**: Check certificate validity periods during outage
3. **Manual Intervention**: May require manual certificate management if outage is prolonged
4. **Consider Enterprise CA Removal**: In extreme cases, remove enterprise CA designation to restore local operations

#### **Why No Fallback to Local CA?**

**Security Consistency**:
- Prevents certificate authority fragmentation
- Maintains single source of truth for certificate issuance
- Avoids potential certificate conflicts between local and enterprise CA

**Operational Clarity**:
- Clear failure mode - operations either work via enterprise CA or fail completely
- No ambiguity about which CA issued which certificates
- Prevents mixed certificate environments that are difficult to manage

**Design Philosophy**:
- Fail-fast approach ensures problems are immediately visible
- Forces proper enterprise CA infrastructure planning and monitoring
- Encourages high availability setup for enterprise CA nodes

## Security Considerations

### API Key Management
- **Secure Storage**: API key tokens are encrypted and stored in Kubernetes secrets
- **Limited Scope**: Use minimal required permissions for remote API keys
- **Regular Rotation**: Rotate API keys periodically for security
- **Network Restrictions**: Configure API key network restrictions when possible

### Network Security
- **HTTPS Only**: All communication uses TLS encryption
- **Path Security**: URL encoding prevents path traversal attacks
- **Firewall Rules**: Implement appropriate network restrictions
- **VPN/Private Networks**: Use secure network connections when possible

### Access Control
- **Authentication Required**: All remote node operations require valid JWT authentication
- **Permission Validation**: Operations are validated against user permissions
- **Audit Logging**: All remote operations are logged for audit purposes

## Error Responses

**Remote Node Not Found (404 Not Found):**
```json
{
  "detail": "Could not find remote node with id remote-node-1"
}
```

**Enterprise CA Conflict (409 Conflict):**
```json
{
  "message": "An enterprise CA remote node already exists with id 'existing-ca'. Only one remote node can be designated as enterprise CA."
}
```

**Communication Error (502 Bad Gateway):**
```json
{
  "detail": "Error communicating with remote node: Connection timeout"
}
```

**Auto-Discovery Failure (404 Not Found):**
```json
{
  "detail": "Remote node with id 'node-id' not found!"
}
```

### GET /v1/remoteNodes/{node_id}/{path:path}

**Proxy GET request to remote node**

Forwards a GET request to the specified remote node. This endpoint enables transparent access to any GET endpoint on the remote node through the Doorman proxy.

**Proxy Features:**
- Automatic API key injection via `X-API-Key` header
- URL path encoding for security (prevents path traversal)
- Query parameter forwarding
- 60-second timeout for remote operations

#### Code Examples

##### cURL
```bash
# Get health status from remote node
curl -X GET "{base_url}/v1/remoteNodes/remote-node-1/health" \
  -H "Authorization: Bearer your_jwt_token"

# List certificates on remote node
curl -X GET "{base_url}/v1/remoteNodes/remote-node-1/ca/certs" \
  -H "Authorization: Bearer your_jwt_token"

# Get users from remote node with query parameters
curl -X GET "{base_url}/v1/remoteNodes/remote-node-1/users?limit=10&offset=0" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests

def proxy_get_request(base_url, jwt_token, node_id, path, params=None):
    """Proxy a GET request to a remote node."""
    url = f"{base_url}/v1/remoteNodes/{node_id}/{path}"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# Examples
health = proxy_get_request(
    "{base_url}", "your_jwt_token", "remote-node-1", "health"
)

certificates = proxy_get_request(
    "{base_url}", "your_jwt_token", "remote-node-1", "ca/certs"
)

users = proxy_get_request(
    "{base_url}", "your_jwt_token", "remote-node-1", "users",
    params={"limit": 10, "offset": 0}
)
```

#### Response Examples

**Success (200 OK) - Health Check:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Success (200 OK) - Certificate List:**
```json
[
  {
    "name": "server-cert",
    "commonName": "server.example.com",
    "expiresAt": "2025-01-15T10:30:00Z"
  }
]
```

### POST /v1/remoteNodes/{node_id}/{path:path}

**Proxy POST request to remote node**

Forwards a POST request with request body to the specified remote node. This endpoint enables creation operations on remote nodes through the Doorman proxy.

**Proxy Features:**
- Request body forwarding
- Automatic API key injection via `X-API-Key` header
- URL path encoding for security
- Content-Type header preservation
- 60-second timeout for remote operations

#### Code Examples

##### cURL
```bash
# Create certificate on remote node
curl -X POST "{base_url}/v1/remoteNodes/remote-node-1/ca/certs/my-cert" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "commonName": "my-cert.example.com",
    "dnsNames": ["my-cert.example.com", "alt.example.com"]
  }'

# Create user on remote node
curl -X POST "{base_url}/v1/remoteNodes/remote-node-1/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "username": "newuser",
    "fullName": "New User",
    "role": "user"
  }'
```

##### Python
```python
import requests

def proxy_post_request(base_url, jwt_token, node_id, path, data):
    """Proxy a POST request to a remote node."""
    url = f"{base_url}/v1/remoteNodes/{node_id}/{path}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}"
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# Create certificate
cert_data = {
    "commonName": "my-cert.example.com",
    "dnsNames": ["my-cert.example.com", "alt.example.com"]
}

certificate = proxy_post_request(
    "{base_url}", "your_jwt_token", "remote-node-1", 
    "ca/certs/my-cert", cert_data
)

# Create user
user_data = {
    "username": "newuser",
    "fullName": "New User",
    "role": "user"
}

user = proxy_post_request(
    "{base_url}", "your_jwt_token", "remote-node-1", 
    "users", user_data
)
```

#### Response Examples

**Success (200 OK) - Certificate Created:**
```json
{
  "name": "my-cert",
  "commonName": "my-cert.example.com",
  "dnsNames": ["my-cert.example.com", "alt.example.com"],
  "expiresAt": "2025-01-15T10:30:00Z",
  "certificate": "-----BEGIN CERTIFICATE-----\n..."
}
```

**Success (201 Created) - User Created:**
```json
{
  "id": "user123",
  "username": "newuser",
  "fullName": "New User",
  "role": "user",
  "isEnabled": true
}
```

### PUT /v1/remoteNodes/{node_id}/{path:path}

**Proxy PUT request to remote node**

Forwards a PUT request with request body to the specified remote node. This endpoint enables full resource replacement operations on remote nodes through the Doorman proxy.

**Proxy Features:**
- Complete request body forwarding
- Automatic API key injection via `X-API-Key` header
- URL path encoding for security
- Content-Type header preservation
- 60-second timeout for remote operations

#### Code Examples

##### cURL
```bash
# Replace user configuration on remote node
curl -X PUT "{base_url}/v1/remoteNodes/remote-node-1/users/admin" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "username": "admin",
    "fullName": "System Administrator",
    "role": "administrator",
    "isEnabled": true
  }'

# Replace system settings on remote node
curl -X PUT "{base_url}/v1/remoteNodes/remote-node-1/settings/security" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "sessionTimeout": 3600,
    "maxLoginAttempts": 5,
    "requireMfa": true
  }'
```

##### Python
```python
import requests

def proxy_put_request(base_url, jwt_token, node_id, path, data):
    """Proxy a PUT request to a remote node."""
    url = f"{base_url}/v1/remoteNodes/{node_id}/{path}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}"
    }
    
    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# Replace user configuration
user_config = {
    "username": "admin",
    "fullName": "System Administrator", 
    "role": "administrator",
    "isEnabled": True
}

updated_user = proxy_put_request(
    "{base_url}", "your_jwt_token", "remote-node-1",
    "users/admin", user_config
)

# Replace security settings
security_config = {
    "sessionTimeout": 3600,
    "maxLoginAttempts": 5,
    "requireMfa": True
}

updated_settings = proxy_put_request(
    "{base_url}", "your_jwt_token", "remote-node-1",
    "settings/security", security_config
)
```

#### Response Examples

**Success (200 OK) - User Updated:**
```json
{
  "id": "admin",
  "username": "admin",
  "fullName": "System Administrator",
  "role": "administrator",
  "isEnabled": true,
  "lastModified": "2024-01-15T10:30:00Z"
}
```

**Success (200 OK) - Settings Updated:**
```json
{
  "sessionTimeout": 3600,
  "maxLoginAttempts": 5,
  "requireMfa": true,
  "lastModified": "2024-01-15T10:30:00Z"
}
```

### PATCH /v1/remoteNodes/{node_id}/{path:path}

**Proxy PATCH request to remote node**

Forwards a PATCH request with request body to the specified remote node. This endpoint enables partial resource updates on remote nodes through the Doorman proxy.

**Proxy Features:**
- Partial request body forwarding
- Automatic API key injection via `X-API-Key` header
- URL path encoding for security
- Content-Type header preservation
- 60-second timeout for remote operations

#### Code Examples

##### cURL
```bash
# Partially update user on remote node
curl -X PATCH "{base_url}/v1/remoteNodes/remote-node-1/users/admin" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "isEnabled": false
  }'

# Update specific system setting on remote node
curl -X PATCH "{base_url}/v1/remoteNodes/remote-node-1/settings/security" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "sessionTimeout": 7200
  }'
```

##### Python
```python
import requests

def proxy_patch_request(base_url, jwt_token, node_id, path, data):
    """Proxy a PATCH request to a remote node."""
    url = f"{base_url}/v1/remoteNodes/{node_id}/{path}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}"
    }
    
    response = requests.patch(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# Disable user account
user_update = {"isEnabled": False}

updated_user = proxy_patch_request(
    "{base_url}", "your_jwt_token", "remote-node-1",
    "users/admin", user_update
)

# Update session timeout
setting_update = {"sessionTimeout": 7200}

updated_setting = proxy_patch_request(
    "{base_url}", "your_jwt_token", "remote-node-1",
    "settings/security", setting_update
)
```

#### Response Examples

**Success (200 OK) - User Partially Updated:**
```json
{
  "id": "admin",
  "username": "admin",
  "fullName": "System Administrator",
  "role": "administrator",
  "isEnabled": false,
  "lastModified": "2024-01-15T10:30:00Z"
}
```

**Success (200 OK) - Setting Updated:**
```json
{
  "sessionTimeout": 7200,
  "maxLoginAttempts": 5,
  "requireMfa": true,
  "lastModified": "2024-01-15T10:30:00Z"
}
```

### DELETE /v1/remoteNodes/{node_id}/{path:path}

**Proxy DELETE request to remote node**

Forwards a DELETE request to the specified remote node. This endpoint enables resource deletion operations on remote nodes through the Doorman proxy.

**Proxy Features:**
- Automatic API key injection via `X-API-Key` header
- URL path encoding for security
- Query parameter forwarding
- 60-second timeout for remote operations

#### Code Examples

##### cURL
```bash
# Delete certificate on remote node
curl -X DELETE "{base_url}/v1/remoteNodes/remote-node-1/ca/certs/old-cert" \
  -H "Authorization: Bearer your_jwt_token"

# Delete user on remote node
curl -X DELETE "{base_url}/v1/remoteNodes/remote-node-1/users/olduser" \
  -H "Authorization: Bearer your_jwt_token"

# Delete with query parameters
curl -X DELETE "{base_url}/v1/remoteNodes/remote-node-1/cache?type=all" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests

def proxy_delete_request(base_url, jwt_token, node_id, path, params=None):
    """Proxy a DELETE request to a remote node."""
    url = f"{base_url}/v1/remoteNodes/{node_id}/{path}"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    response = requests.delete(url, headers=headers, params=params)
    response.raise_for_status()
    
    # DELETE requests may return 204 No Content
    if response.status_code == 204:
        return None
    return response.json()

# Delete certificate
proxy_delete_request(
    "{base_url}", "your_jwt_token", "remote-node-1", "ca/certs/old-cert"
)

# Delete user
proxy_delete_request(
    "{base_url}", "your_jwt_token", "remote-node-1", "users/olduser"
)

# Delete with parameters
proxy_delete_request(
    "{base_url}", "your_jwt_token", "remote-node-1", "cache",
    params={"type": "all"}
)
```

#### Response Examples

**Success (204 No Content):** Resource deleted successfully

**Success (200 OK) - Deletion Confirmation:**
```json
{
  "message": "Certificate 'old-cert' deleted successfully",
  "deletedAt": "2024-01-15T10:30:00Z"
}
``` 