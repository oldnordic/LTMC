# API Documentation

**Project:** {project_id}  
**Generated:** {generated_at}  
**Template:** Standard API Documentation Format

---

## Overview

This document provides comprehensive API documentation automatically generated from source code analysis. It includes endpoint definitions, data models, and usage examples.

### Quick Stats
- **Total Endpoints:** {total_endpoints}
- **Total Models:** {total_models}
- **Source Files:** {source_files_count}
- **Lines of Code:** {lines_of_code}

---

## API Endpoints

{endpoints_section}

---

## Data Models

{models_section}

---

## Authentication

### Security Requirements
- All endpoints require valid authentication
- Rate limiting applies to all requests
- HTTPS is required for all API calls

### Headers
```
Authorization: Bearer <your-token>
Content-Type: application/json
Accept: application/json
```

---

## Error Responses

### Standard Error Format
```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable error message",
        "details": "Additional error context"
    }
}
```

### Common Error Codes
- `400` - Bad Request: Invalid request parameters
- `401` - Unauthorized: Invalid or missing authentication
- `403` - Forbidden: Insufficient permissions
- `404` - Not Found: Resource does not exist
- `429` - Too Many Requests: Rate limit exceeded
- `500` - Internal Server Error: Server-side error

---

## Usage Examples

### Basic Request
```bash
curl -X GET "https://api.example.com/users" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json"
```

### Response Format
```json
{
    "data": [],
    "meta": {
        "total": 0,
        "page": 1,
        "limit": 10
    }
}
```

---

## Rate Limits

- **Default Rate Limit:** 1000 requests per hour per API key
- **Burst Limit:** 100 requests per minute
- **Rate Limit Headers:** Included in all responses

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

---

## SDK and Libraries

### Python
```python
from api_client import APIClient

client = APIClient(token='your-token')
users = client.users.list()
```

### JavaScript
```javascript
const client = new APIClient('your-token');
const users = await client.users.list();
```

---

## Support and Documentation

- **API Reference:** Complete endpoint documentation
- **Changelog:** Version history and updates
- **Support:** Contact information for API support
- **Status Page:** Real-time API status monitoring

---

*Documentation generated automatically on {generated_at}*