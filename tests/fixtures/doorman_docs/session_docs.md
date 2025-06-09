# Session Management API Documentation

## Overview

The **Session Management API** is the primary authentication gateway for SynetoOS, providing secure user authentication and session lifecycle management. This API implements enterprise-grade security features including multi-factor authentication and rate limiting.

### 🔐 **Key Authentication Methods**

**Username/Password Authentication**
- Standard credential-based login for regular users
- Supports both local user authentication
- Automatic password policy enforcement

**PIN Authentication** 
- Quick access method for support personnel and emergency scenarios
- Simplified authentication flow with enhanced security monitoring
- Ideal for maintenance windows and troubleshooting sessions

### 🛡️ **Enterprise Security Features**

**Two-Factor Authentication (OTP)**
- TOTP-based second factor using authenticator apps (Google Authenticator, Authy, etc.)
- Recovery codes for account recovery scenarios
- Configurable per-user with administrative override capabilities

**Advanced Rate Limiting**
- Fail2ban integration with automatic IP blocking
- Progressive delays for repeated authentication failures
- Configurable thresholds for different user types and scenarios

### 🔄 **Authentication Flows**

- **Standard Flow (No OTP)**: `Client → POST /v1/session → Session Cookie → Authenticated Requests`
- **Multi-Factor Flow (OTP Enabled)**: `Client → POST /v1/session → Temporary Cookie → POST /v1/session:verifyOtp → Full Session Cookie`
- **Syneto Support Access Flow**: `Support → POST /v1/session (PIN) → Immediate Session Cookie → Administrative Access`

## Endpoints

### POST /v1/session

**Create a new authentication session**

This endpoint authenticates users and creates a session. It supports multiple authentication methods:

1. **Username/Password Authentication**: Standard login for regular users
2. **PIN Authentication**: Quick access for support personnel

**Authentication Flow:**
- If OTP is disabled: Returns a session cookie immediately
- If OTP is enabled: Returns a temporary session cookie and requires OTP verification

**Response Scenarios:**
- `200 OK`: Session created successfully (OTP disabled)
- `203 Non-Authoritative Information`: OTP setup required (first-time OTP users)
- `204 No Content`: Temporary session created, OTP verification needed
- `401 Unauthorized`: Invalid credentials
- `429 Too Many Requests`: Rate limited by fail2ban

#### Code Examples

##### cURL
```bash
curl -X POST "{base_url}/v1/session" \
  -H "Content-Type: application/json" \
  -H "X-Real-IP: 192.168.1.100" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'
```

##### Python
```python
import requests

url = "{base_url}/v1/session"
headers = {
    "Content-Type": "application/json",
    "X-Real-IP": "192.168.1.100"
}
data = {
    "username": "admin",
    "password": "your_password"
}

response = requests.post(url, headers=headers, json=data)
print(response.status_code)
print(response.cookies.get('session'))
```

#### Request Examples

**Username/Password Authentication:**
```json
{
  "username": "admin",
  "password": "your_password"
}
```

**PIN Authentication (Support Access):**
```json
{
  "pin": "123456"
}
```

#### Response Examples

**Success (200 OK) - Session created:**
```json
{
  "id": "user123",
  "username": "admin",
  "fullName": "Administrator",
  "role": "administrator",
  "isOtpEnabled": false
}
```

**OTP Setup Required (203 Non-Authoritative Information):**
```json
{
  "authenticatorLink": "otpauth://totp/Syneto:admin?secret=JBSWY3DPEHPK3PXP&issuer=Syneto",
  "secret": "JBSWY3DPEHPK3PXP"
}
```

**Authentication Failed (401 Unauthorized):**
```json
{
  "detail": "Invalid credentials"
}
```

---

### GET /v1/session

**Get current session information**

Retrieves details about the currently authenticated user based on the session cookie.

**Requirements:**
- Valid session cookie must be present
- Session must not be expired

**Returns:**
- Complete user profile information
- User permissions and role
- OTP status and configuration

#### Code Examples

##### cURL
```bash
curl -X GET "{base_url}/v1/session" \
  -H "Cookie: session=your_session_token"
```

##### Python
```python
import requests

url = "{base_url}/v1/session"
cookies = {"session": "your_session_token"}

response = requests.get(url, cookies=cookies)
user_info = response.json()
print(f"User: {user_info['username']}")
```

#### Response Example

**Success (200 OK):**
```json
{
  "id": "user123",
  "username": "admin",
  "fullName": "System Administrator",
  "role": "administrator",
  "isEnabled": true,
  "isOtpEnabled": true,
  "isOtpSetupCompleted": true,
  "canBeDeleted": false,
  "isSupport": false,
  "isAdministrator": true
}
```

---

### DELETE /v1/session

**Terminate current session and logout user**

Logs out the current user by invalidating their session cookie and clearing it from the browser. This endpoint provides a secure way to terminate user sessions and is essential for proper logout functionality in web applications.

**Session Termination Process:**
1. **Cookie Validation**: Validates the current session cookie
2. **Session Invalidation**: Marks the session as invalid on the server
3. **Cookie Clearing**: Instructs the browser to delete the session cookie
4. **Security Cleanup**: Ensures no session data remains accessible

**Security Features:**
- **Immediate Effect**: Session is invalidated immediately upon request
- **Cookie Clearing**: Browser is instructed to delete the session cookie
- **No Authentication Required**: Works even with expired sessions for cleanup
- **Idempotent**: Safe to call multiple times without side effects

**Use Cases:**
- **User Logout**: Standard logout functionality in web applications
- **Security Cleanup**: Clear sessions when switching users or devices
- **Session Management**: Programmatic session termination in automation scripts
- **Security Response**: Force logout in response to security events

#### Code Examples

##### cURL
```bash
# Standard logout with session cookie
curl -X DELETE "{base_url}/v1/session" \
  -H "Cookie: session=your_session_token" \
  -v  # Verbose to see cookie clearing headers

# Logout without session cookie (cleanup)
curl -X DELETE "{base_url}/v1/session"

# Logout with additional security headers
curl -X DELETE "{base_url}/v1/session" \
  -H "Cookie: session=your_session_token" \
  -H "X-Real-IP: 192.168.1.100" \
  -H "User-Agent: MyApp/1.0"
```

##### Python
```python
import requests

def logout_user(base_url, session_token=None):
    """
    Logout user and clear session cookie.
    
    Args:
        base_url: Doorman base URL
        session_token: Current session token (optional for cleanup)
    
    Returns:
        bool: True if logout successful, False otherwise
    """
    url = f"{base_url}/v1/session"
    cookies = {}
    
    if session_token:
        cookies["session"] = session_token
    
    try:
        response = requests.delete(url, cookies=cookies)
        
        if response.status_code == 204:
            print("✅ Successfully logged out")
            
            # Check if session cookie was cleared
            if 'Set-Cookie' in response.headers:
                print("🍪 Session cookie cleared by server")
            
            return True
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Logout request failed: {e}")
        return False

def logout_with_session_management(base_url, session_token):
    """
    Enhanced logout with session management and cleanup.
    """
    # Create a session object to handle cookies
    session = requests.Session()
    session.cookies.set('session', session_token)
    
    try:
        # Perform logout
        response = session.delete(f"{base_url}/v1/session")
        
        if response.status_code == 204:
            print("✅ User logged out successfully")
            
            # Verify session cookie was cleared
            session_cookie = session.cookies.get('session')
            if not session_cookie:
                print("🍪 Session cookie cleared from client")
            
            # Clear any remaining cookies
            session.cookies.clear()
            
            return True
        else:
            print(f"❌ Logout failed: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Network error during logout: {e}")
        return False
    finally:
        # Always close the session
        session.close()

# Example usage
success = logout_user("https://doorman.example.com", "your_session_token")

# Enhanced logout with session management
success = logout_with_session_management(
    "https://doorman.example.com", 
    "your_session_token"
)

# Cleanup logout (no session token)
cleanup_success = logout_user("https://doorman.example.com")
```

#### Response Examples

**Success (204 No Content):**
```
HTTP/1.1 204 No Content
Set-Cookie: session=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0
Content-Length: 0
```

**Response Headers Explanation:**
- `204 No Content`: Indicates successful logout with no response body
- `Set-Cookie: session=; Max-Age=0`: Instructs browser to delete the session cookie
- `HttpOnly; Secure; SameSite=Strict`: Security attributes for cookie handling

**No Session Cookie (204 No Content):**
```
HTTP/1.1 204 No Content
Content-Length: 0
```

**Network Error Handling:**
```json
{
  "detail": "Network connection failed",
  "type": "connection_error"
}
```

#### Integration Examples

**JavaScript/Browser Integration:**
```javascript
// Logout function for web applications
async function logoutUser() {
    try {
        const response = await fetch('/v1/session', {
            method: 'DELETE',
            credentials: 'include'  // Include cookies
        });
        
        if (response.status === 204) {
            console.log('✅ Logged out successfully');
            // Redirect to login page
            window.location.href = '/login';
        } else {
            console.error('❌ Logout failed');
        }
    } catch (error) {
        console.error('❌ Network error:', error);
    }
}
```

**Automation Script Integration:**
```bash
#!/bin/bash
# Logout script for automation

DOORMAN_URL="https://doorman.example.com"
SESSION_TOKEN="your_session_token"

echo "Logging out from Doorman..."
response=$(curl -s -w "%{http_code}" -X DELETE "$DOORMAN_URL/v1/session" \
  -H "Cookie: session=$SESSION_TOKEN")

if [ "$response" = "204" ]; then
    echo "✅ Successfully logged out"
    exit 0
else
    echo "❌ Logout failed with status: $response"
    exit 1
fi
```

### POST /v1/session:verifyOtp

**Verify One-Time Password (OTP)**

Completes the two-factor authentication process by verifying the OTP code.

**Supported Code Types:**
- **6-digit TOTP codes**: Time-based codes from authenticator apps
- **8-digit recovery codes**: Backup codes for account recovery

**Process:**
1. User provides temporary session token (from initial login)
2. User submits OTP code
3. System validates the code
4. If valid, issues a full session token
5. If first-time setup, provides recovery codes

**Security Features:**
- Rate limiting to prevent brute force attacks
- Automatic account lockout after multiple failures
- Recovery codes are single-use only

#### Code Examples

##### cURL
```bash
curl -X POST "{base_url}/v1/session:verifyOtp" \
  -H "Content-Type: application/json" \
  -H "Cookie: temporary_session=your_temp_token" \
  -H "X-Real-IP: 192.168.1.100" \
  -d '{
    "code": "123456"
  }'
```

##### Python
```python
import requests

url = "{base_url}/v1/session:verifyOtp"
headers = {
    "Content-Type": "application/json",
    "X-Real-IP": "192.168.1.100"
}
cookies = {"temporary_session": "your_temp_token"}
data = {"code": "123456"}

response = requests.post(url, headers=headers, cookies=cookies, json=data)
session_cookie = response.cookies.get('session')
print(f"Session established: {session_cookie}")
```

#### Request Examples

**OTP Code Verification:**
```json
{
  "code": "123456"
}
```

**Recovery Code Usage:**
```json
{
  "code": "12345678"
}
```

#### Response Examples

**OTP Verified with Recovery Codes (200 OK) - First-time setup:**
```json
{
  "recoveryCodes": [
    "12345678",
    "87654321",
    "11223344",
    "44332211",
    "55667788"
  ]
}
```

**OTP Verified (204 No Content):** Successfully verified

**Invalid OTP Code (401 Unauthorized):**
```json
{
  "detail": "Invalid OTP code"
}
```

## Authentication Flow Examples

### Standard Login Flow (No OTP)
1. POST `/v1/session` with username/password
2. Receive session cookie in response
3. Use session cookie for subsequent requests

### OTP-Enabled Login Flow
1. POST `/v1/session` with username/password
2. Receive temporary session cookie (204 or 203 response)
3. POST `/v1/session:verifyOtp` with OTP code
4. Receive full session cookie
5. Use session cookie for subsequent requests

### PIN Login Flow (Support Access)
1. POST `/v1/session` with PIN
2. Receive session cookie immediately
3. Use session cookie for subsequent requests

## Security Considerations

- **Rate Limiting**: Authentication endpoints are protected against brute force attacks
- **IP Tracking**: X-Real-IP header is used for fail2ban integration
- **Session Security**: Cookies are HttpOnly, Secure, and SameSite protected
- **OTP Security**: Time-based codes expire quickly, recovery codes are single-use
- **Token Expiration**: Standard tokens expire after 12 hours, temporary tokens after 12 minutes 