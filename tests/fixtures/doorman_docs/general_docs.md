# SynetoOS Authentication Service API

## Overview

The SynetoOS Authentication Service provides centralized authentication and authorization for the entire Syneto platform. This service manages user sessions, API keys, certificates, and access control across all Syneto components.

**Main Functions:**
- **User Authentication**: Session management with multi-factor authentication support
- **API Key Management**: Programmatic access tokens with granular permissions and network restrictions
- **Certificate Authority**: TLS certificate generation and management for secure communications
- **User Administration**: Account creation, management, and role-based access control
- **Authorization**: Fine-grained permission control and continuous authentication for sensitive operations

## Quick Start

Congratulations! After logging in to the SynetoOS and reaching this page, your browser already has an authentication cookie.

And this documentation is alive!

This means that you can use the API immediately using the "Try it out" buttons you can find on every documented API endpoint.

However, you may want to get to programming. Here's a simple shell script to authenticate and list users:

```bash
#!/bin/bash

# Login and save session cookie
curl -c /tmp/syneto_session.txt -X POST "https://your-syneto-host/v1/session" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# List all users using the session cookie
curl -b /tmp/syneto_session.txt "https://your-syneto-host/users"

# Clean up
rm /tmp/syneto_session.txt
```

## Supported Authentication Methods

* **Session Cookie Authentication** - Browser-based authentication with automatic cookie management (`Cookie: session=<session_token>`)
  - Secure HttpOnly cookies with SameSite protection
  - Automatic expiration and renewal
  - Ideal for web applications and interactive use
  - Supports both regular users and support personnel

* **Bearer Token Authentication** - JWT tokens for API clients and web applications (`Authorization: Bearer <jwt_token>`)
  - Stateless authentication with cryptographic signatures
  - Configurable expiration times (12 hours standard, 12 minutes temporary)
  - Contains user context and permissions
  - Perfect for mobile apps and single-page applications

* **API Key Authentication** - Long-lived tokens for automation and service-to-service communication (`X-API-Key: <api_key>`)
  - Network-restricted access with IP/CIDR validation
  - Granular scope control for specific operations
  - Audit trail with usage tracking
  - Designed for automation scripts and multi-appliance management

## Error Handling

All endpoints return structured JSON error responses with consistent formatting:

```json
{
  "detail": "Human-readable error description",
  "type": "error_category",
  "code": "SPECIFIC_ERROR_CODE"
}
```

**Common Error Categories:**
- **Authentication Errors (401)**: Missing or invalid credentials, expired tokens
- **Authorization Errors (403)**: Insufficient permissions, role restrictions
- **Validation Errors (400)**: Invalid input data, malformed requests
- **Rate Limiting (429)**: Too many requests, temporary throttling
- **Server Errors (500)**: Internal processing errors, service unavailable

**Rate Limiting:**
Authentication endpoints implement progressive rate limiting to prevent abuse:
- Failed login attempts trigger temporary IP-based restrictions
- API key usage is monitored for unusual patterns
- Continuous authentication failures result in account lockouts

**Continuous Authentication:**
Sensitive operations require re-authentication regardless of session status:
- User management operations always require password or OTP verification
- Configurable continuous auth for additional endpoints
- Re-authentication expires after 1 minute of inactivity

## Request Examples

### POST /v1/session

**Login with username and password:**
```json
{
  "username": "admin",
  "password": "your_password"
}
```

**Login with PIN (support access):**
```json
{
  "pin": "123456"
}
```

### POST /v1/session:verifyOtp

**Verify OTP code:**
```json
{
  "otp_code": "123456"
}
```
