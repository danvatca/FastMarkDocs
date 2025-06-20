# Certificate Authority API Documentation

## Overview

The **Certificate Authority API** provides enterprise-grade TLS/SSL certificate management for SynetoOS infrastructure. This API enables automated certificate lifecycle management with support for both local CA operations and enterprise CA. A remoteNode can be designated as an enterprise CA, and will be used instead of the local CA.

### 🔐 **Certificate Management Features**

**Automated Certificate Lifecycle**
- Certificate creation with custom parameters (DNS names, IP addresses, validity periods)
- Automatic certificate renewal and rotation capabilities
- Centralized certificate inventory and status monitoring

**Enterprise Features**
- Local CA operations for single node SynetoOS deployments
- Centralised Enterprise CA for multiple SynetoOS nodes

### 🛡️ **Security Features**

**Certificate Security**
- Industry-standard key lengths and encryption algorithms
- Secure private key storage and transmission
- Certificate validation and integrity checking

### 🔄 **Certificate Operations**

- **Certificate Discovery**: `GET /ca/certs` - List all managed certificates
- **Certificate Retrieval**: `GET /ca/certs/{name}` - Get complete certificate data including private keys
- **Certificate Creation**: `POST /ca/certs/{name}` - Generate new certificates with custom parameters
- **Certificate Deletion**: `DELETE /ca/certs/{name}` - Permanently remove certificates and keys

## Endpoints

### GET /ca

**Get Certificate Authority Information**

Retrieves the root CA certificate used by the system.

#### Code Examples

##### cURL
```bash
curl -X GET "{base_url}/ca" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests

url = "{base_url}/ca"
headers = {"Authorization": "Bearer your_jwt_token"}

response = requests.get(url, headers=headers)
ca_cert = response.json()
print("CA Certificate retrieved")
```

#### Response Example

**Success (200 OK):**
```json
{
  "certificate": "-----BEGIN CERTIFICATE-----\nMIIDXTCCAkWgAwIBAgIJAKL0UG+9K8ZxMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV\n...\n-----END CERTIFICATE-----"
}
```

---

### GET /ca/certs

**List All Certificates**

Retrieves a list of all certificates managed by the CA.

#### Code Examples

##### cURL
```bash
curl -X GET "{base_url}/ca/certs" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests

url = "{base_url}/ca/certs"
headers = {"Authorization": "Bearer your_jwt_token"}

response = requests.get(url, headers=headers)
certificates = response.json()
print(f"Found {len(certificates)} certificates")
```

#### Response Example

**Success (200 OK):**
```json
[
  "web-server-cert",
  "client-libvirt",
  "server-libvirt",
  "api-gateway-cert",
  "monitoring-cert"
]
```

---

### GET /ca/certs/{name}

**Get Certificate Details**

Retrieves complete certificate data including certificate, private key, and CA certificate.

**Security Warning:** This endpoint returns the private key. Ensure proper access controls.

#### Code Examples

##### cURL
```bash
curl -X GET "{base_url}/ca/certs/my-certificate" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests

cert_name = "my-certificate"
url = f"{base_url}/ca/certs/{cert_name}"
headers = {"Authorization": "Bearer your_jwt_token"}

response = requests.get(url, headers=headers)
cert_data = response.json()
print(f"Certificate: {cert_name}")
```

#### Response Example

**Success (200 OK):**
```json
{
  "ca": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
  "crt": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
  "key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
}
```

**Certificate Not Found (404 Not Found):**
```json
{
  "detail": "Certificate 'my-certificate' not found"
}
```

**Insufficient Permissions (403 Forbidden):**
```json
{
  "detail": "User has no rights to do this action"
}
```

---

### POST /ca/certs/{name}

**Create New Certificate**

Creates a new certificate with specified parameters.

#### Code Examples

##### cURL
```bash
curl -X POST "{base_url}/ca/certs/my-new-cert" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "commonName": "my-new-cert",
    "dnsNames": ["example.com", "www.example.com"],
    "ipAddresses": ["192.168.1.100"]
  }'
```

##### Python
```python
import requests

cert_name = "my-new-cert"
url = f"{base_url}/ca/certs/{cert_name}"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_jwt_token"
}
data = {
    "commonName": "my-new-cert",
    "dnsNames": ["example.com", "www.example.com"],
    "ipAddresses": ["192.168.1.100"]
}

response = requests.post(url, headers=headers, json=data)
job_response = response.json()
print(f"Certificate creation job: {job_response['jobId']}")
```

#### Request Examples

**Web Server Certificate:**
```json
{
  "commonName": "web-server",
  "dnsNames": ["example.com", "www.example.com"],
  "ipAddresses": ["192.168.1.100"]
}
```

**Client Certificate:**
```json
{
  "commonName": "client-cert",
  "dnsNames": ["client.internal"],
  "ipAddresses": []
}
```

#### Response Examples

**Success (200 OK) - Local CA (Async Job):**
```json
{
  "jobId": "cert-job-12345",
  "status": "pending",
  "message": "Certificate creation job queued"
}
```

**Success (201 Created) - Enterprise CA (Direct):**
```json
{
  "ca": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
  "crt": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
  "key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
}
```

---

### DELETE /ca/certs/{name}

**Delete Certificate**

Permanently removes a certificate and its private key.

**Warning:** This operation is irreversible.

#### Code Examples

##### cURL
```bash
curl -X DELETE "{base_url}/ca/certs/my-certificate" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests

cert_name = "my-certificate"
url = f"{base_url}/ca/certs/{cert_name}"
headers = {"Authorization": "Bearer your_jwt_token"}

response = requests.delete(url, headers=headers)
if response.status_code == 204:
    print(f"Certificate {cert_name} deleted successfully")
```

#### Response

**Success (200 OK):** Certificate deleted successfully

## Unsupported HTTP Methods

### 🚫 **Certificate Modification Not Supported**

The Certificate Authority API **does not support certificate modification** after creation. Certificates are **immutable** once generated to maintain security and integrity.

#### **Unsupported Methods on `/ca/certs/{name}`:**

- **PUT /ca/certs/{name}** - ❌ Not Supported
- **PATCH /ca/certs/{name}** - ❌ Not Supported

#### **405 Method Not Allowed Response**

When PUT or PATCH methods are attempted on any certificate endpoint, the server returns a **405 Method Not Allowed** response:

```json
{
  "error": "Method not allowed",
  "message": "Certificate 'certificate-name' cannot be modified. Certificates are immutable once created.",
  "certificate_name": "certificate-name",
  "allowed_methods": ["GET", "DELETE"],
  "alternatives": [
    "GET /ca/certs/certificate-name - Get certificate details",
    "DELETE /ca/certs/certificate-name - Delete certificate", 
    "POST /ca/certs/{new_name} - Create new certificate with different name"
  ],
  "hint": "To update a certificate, delete the old one and create a new one with the desired parameters"
}
```

#### **Certificate Update Workflow**

To update certificate parameters, follow this workflow:

1. **Create New Certificate**: Generate a new certificate with updated parameters using a different name
2. **Update Applications**: Configure applications to use the new certificate
3. **Delete Old Certificate**: Remove the old certificate once it's no longer needed

**Example:**
```bash
# Step 1: Create new certificate with updated parameters
curl -X POST "{base_url}/ca/certs/web-server-v2" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "commonName": "web-server-v2",
    "dnsNames": ["example.com", "www.example.com", "api.example.com"],
    "ipAddresses": ["192.168.1.100", "192.168.1.101"]
  }'

# Step 2: Update application configuration to use new certificate
# (Application-specific configuration changes)

# Step 3: Delete old certificate
curl -X DELETE "{base_url}/ca/certs/web-server-v1" \
  -H "Authorization: Bearer your_jwt_token"
```

## Certificate Types and Use Cases

### Server Certificates
- **Purpose**: TLS/SSL for web servers and services
- **Common Names**: Service hostnames or domain names
- **DNS Names**: All domains the certificate should cover
- **IP Addresses**: Server IP addresses for direct IP access

### Client Certificates
- **Purpose**: Mutual TLS authentication
- **Common Names**: Client or service identifiers
- **DNS Names**: Client hostnames (optional)
- **IP Addresses**: Usually empty for client certificates

### Service Certificates
- **Purpose**: Inter-service communication
- **Common Names**: Service names or identifiers
- **DNS Names**: Internal service discovery names
- **IP Addresses**: Service cluster IPs

## Security Best Practices

### Certificate Management
- **Regular Rotation**: Implement certificate rotation policies
- **Minimal Validity**: Use shortest practical certificate lifetimes
- **Secure Storage**: Protect private keys with appropriate permissions
- **Access Control**: Limit certificate access to necessary services

### Network Security
- **HTTPS Only**: Always use HTTPS for certificate operations
- **API Authentication**: Require proper authentication for all operations
- **Network Restrictions**: Use firewall rules to limit CA access
- **Audit Logging**: Log all certificate operations for compliance

## Error Responses

**Certificate Not Found (404 Not Found):**
```json
{
  "detail": "Certificate not found"
}
```

**Enterprise CA Communication Error (502 Bad Gateway):**
```json
{
  "detail": "Failed to get CA certificate from enterprise CA: Connection timeout"
}
```

**Certificate Already Exists (409 Conflict):**
```json
{
  "detail": "Certificate already exists"
}
```

**Invalid Certificate Request (400 Bad Request):**
```json
{
  "detail": "Invalid certificate specification: Common name is required"
}
``` 