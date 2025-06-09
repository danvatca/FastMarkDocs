# Settings API Documentation

## Overview

The **Settings API** provides system-wide security configuration management for SynetoOS. This API enables administrators to configure global authentication policies including multi-factor authentication enforcement and continuous authentication requirements.

### ⚙️ **Global Security Settings**

**Enable/Disable Multi-Factor Authentication (TOTP/MFA) Globally**
- System-wide toggle to enforce TOTP/MFA for all user accounts
- When enabled, all users must complete two-factor authentication
- Overrides individual user OTP preferences when globally enforced

**Enable/Disable Continuous Authentication Globally**
- Requires re-authentication for sensitive operations
- Configurable timeout and scope settings
- Enhanced security for critical system modifications

---

## System Configuration

### GET /settings

**Retrieve current system settings**

Returns the current global security configuration including MFA enforcement and continuous authentication settings.

#### Code Examples

##### cURL
```bash
curl -X GET "{base_url}/settings" \
  -H "Authorization: Bearer your_jwt_token"
```

##### Python
```python
import requests

url = "{base_url}/settings"
headers = {"Authorization": "Bearer your_jwt_token"}

response = requests.get(url, headers=headers)
settings = response.json()
print(f"MFA enabled: {settings['isOtpEnabled']}")
print(f"Continuous auth: {settings['isContinuousAuthEnabled']}")
```

#### Response Example

**Success (200 OK):**
```json
{
  "isOtpEnabled": true,
  "isContinuousAuthEnabled": false
}
```

---

### PATCH /settings

**Update system settings**

Updates global security configuration. Only administrators can modify system settings.

#### Code Examples

##### cURL
```bash
curl -X PATCH "{base_url}/settings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "isOtpEnabled": true,
    "isContinuousAuthEnabled": true
  }'
```

##### Python
```python
import requests

url = "{base_url}/settings"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_jwt_token"
}
data = {
    "isOtpEnabled": True,
    "isContinuousAuthEnabled": True
}

response = requests.patch(url, headers=headers, json=data)
updated_settings = response.json()
print(f"Settings updated: {updated_settings}")
```

#### Request Example

```json
{
  "isOtpEnabled": true,
  "isContinuousAuthEnabled": true
}
```

#### Response Examples

**Success (200 OK):**
```json
{
  "isOtpEnabled": true,
  "isContinuousAuthEnabled": true
}
```

**Validation Error (400 Bad Request):**
```json
{
  "detail": "Invalid configuration values provided"
}
```

**License Restriction (400 Bad Request):**
```json
{
  "detail": "This system's license does not support continuous authentication."
}
```

---

## Health Monitoring

### GET /health

**Service health check**

Returns the current health status of the authentication service. Used for monitoring and load balancer health checks.

#### Code Examples

##### cURL
```bash
curl -X GET "{base_url}/health"
```

##### Python
```python
import requests

url = "{base_url}/health"
response = requests.get(url)
health = response.json()
print(f"Service status: {health['message']}")
```

#### Response Example

**Success (200 OK):**
```json
{
  "message": "OK"
}
```

## Security Considerations

### Settings Management
- **Administrator Access**: Only administrators can modify system settings
- **License Validation**: Feature availability is validated against licensing
- **Audit Logging**: All settings changes are logged for compliance
- **Background Processing**: User updates are processed asynchronously

### Global Security Policies
- **MFA Enforcement**: When enabled globally, overrides individual user preferences
- **Continuous Authentication**: Requires appropriate licensing to enable
- **Configuration Validation**: Settings are validated before application
- **Rollback Capability**: Previous settings can be restored if needed

## Error Responses

**Unauthorized (401 Unauthorized):**
```json
{
  "detail": "Authentication required"
}
```

**Forbidden (403 Forbidden):**
```json
{
  "detail": "User has no rights to do this action"
}
```

**Validation Error (400 Bad Request):**
```json
{
  "detail": "Invalid configuration values provided"
}
```

**License Restriction (400 Bad Request):**
```json
{
  "detail": "This system's license does not support continuous authentication."
}
``` 