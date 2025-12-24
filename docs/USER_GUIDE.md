# Powerhouse Platform - User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [API Usage](#api-usage)
4. [Workflows](#workflows)
5. [Agents](#agents)
6. [Monitoring](#monitoring)
7. [Best Practices](#best-practices)

## Getting Started

### API Endpoints

- **Base URL:** `http://localhost:8001` (development)
- **Production URL:** `https://api.powerhouse.ai`
- **API Version:** `/api/v1`

### Interactive Documentation

- **Swagger UI:** `http://localhost:8001/docs`
- **ReDoc:** `http://localhost:8001/redoc`
- **OpenAPI JSON:** `http://localhost:8001/openapi.json`
- **Postman Collection:** `http://localhost:8001/postman.json`

## Authentication

### Getting an Access Token

**Request:**
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password",
    "tenant_id": "your_tenant_id"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using the Token

Include the token in the Authorization header:

```bash
curl -X GET http://localhost:8001/api/v1/workflows \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Token Refresh

```bash
curl -X POST http://localhost:8001/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

## API Usage

### Request Headers

**Required:**
- `Authorization: Bearer <token>` (for protected endpoints)
- `Content-Type: application/json` (for POST/PUT requests)

**Optional:**
- `X-Correlation-ID: <id>` (for request tracking)
- `X-Tenant-ID: <id>` (if not in token)

### Rate Limiting

- **Standard:** 60 requests/minute
- **Burst:** 120 requests/minute

Rate limit headers in responses:
- `X-RateLimit-Limit`: Maximum requests
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

### Error Handling

All errors follow this format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable message",
  "correlation_id": "abc123-def456",
  "error_code": "ERROR_CODE",
  "details": {},
  "timestamp": "2025-01-01T12:00:00Z"
}
```

## Workflows

### Starting a Compliance Workflow

**Request:**
```bash
curl -X POST http://localhost:8001/api/v1/workflows/compliance \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze our data retention policy for GDPR compliance",
    "jurisdiction": "EU",
    "risk_threshold": 0.8,
    "policy_documents": ["https://example.com/policy.pdf"]
  }'
```

**Response:**
```json
{
  "workflow_id": "wf_abc123",
  "status": "running",
  "message": "Compliance workflow started successfully"
}
```

### Checking Workflow Status

```bash
curl -X GET http://localhost:8001/api/v1/workflows/wf_abc123/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Workflow Status Summary (Canonical UI Contract)

Use the status summary endpoint for UI-friendly progress and agent status data.

```bash
curl -X GET http://localhost:8001/api/v1/workflows/wf_abc123/status-summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example Response:**
```json
{
  "workflow_id": "wf_abc123",
  "status": "running",
  "workflow_type": "compliance",
  "progress_percentage": 50,
  "progress": 0.5,
  "current_step": "Debate perspectives",
  "agent_statuses": [
    {
      "agent_id": "9f5aa831-6202-46d8-8eb1-6fcd3d12f50d",
      "agent_name": "governor",
      "status": "completed",
      "step": "Governor preflight",
      "started_at": "2025-01-15T12:33:10Z",
      "completed_at": "2025-01-15T12:33:12Z",
      "duration_seconds": 2.1,
      "error": null
    },
    {
      "agent_id": "e7b7221b-ff0f-4db6-8bdb-88c4e3dbf26a",
      "agent_name": "react",
      "status": "completed",
      "step": "ReAct analysis",
      "started_at": "2025-01-15T12:33:12Z",
      "completed_at": "2025-01-15T12:33:30Z",
      "duration_seconds": 18.4,
      "error": null
    },
    {
      "agent_id": "4b8334f3-4459-4026-9f3d-8c42f1ad1df8",
      "agent_name": "debate",
      "status": "running",
      "step": "Debate perspectives",
      "started_at": "2025-01-15T12:33:30Z",
      "completed_at": null,
      "duration_seconds": 5.4,
      "error": null
    },
    {
      "agent_id": null,
      "agent_name": "evaluator",
      "status": "pending",
      "step": "Evaluator assessment",
      "started_at": null,
      "completed_at": null,
      "duration_seconds": null,
      "error": null
    }
  ],
  "risk_score": 0.32,
  "risk_level": "medium",
  "updated_at": "2025-01-15T12:33:35Z",
  "error": null
}
```

**Field meanings:**
- `progress_percentage`: 0-100 completion percentage for the workflow.
- `progress`: 0-1 completion fraction (canonical for clients that prefer ratios).
- `current_step`: Human-readable label for the currently running or next step.
- `agent_statuses`: Ordered list of per-agent status summaries.
- `agent_statuses[].error`: Optional error object if an agent run failed.
- `risk_score`: Optional numeric score (0-1) if workflow results include risk assessment.
- `risk_level`: Optional qualitative level paired with `risk_score`.
- `updated_at`: Last update timestamp for the workflow record.
- `error`: Optional error object when the workflow fails.

### Getting Workflow Results

```bash
curl -X GET http://localhost:8001/api/v1/workflows/wf_abc123/results \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Agents

### Listing Available Agents

```bash
curl -X GET http://localhost:8001/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Agent Information

```bash
curl -X GET http://localhost:8001/api/v1/agents/react_agent \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Monitoring

### Health Check

```bash
curl http://localhost:8001/health
```

### Metrics

**Prometheus Metrics:**
```bash
curl http://localhost:8001/metrics/prometheus
```

**System Health:**
```bash
curl http://localhost:8001/metrics/health
```

## Best Practices

### 1. Always Use HTTPS in Production

```bash
# Development
http://localhost:8001

# Production
https://api.powerhouse.ai
```

### 2. Handle Token Expiration

Implement automatic token refresh:

```python
import requests
from datetime import datetime, timedelta

class APIClient:
    def __init__(self, base_url, email, password, tenant_id):
        self.base_url = base_url
        self.email = email
        self.password = password
        self.tenant_id = tenant_id
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
    
    def login(self):
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={
                "email": self.email,
                "password": self.password,
                "tenant_id": self.tenant_id
            }
        )
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"])
    
    def get_headers(self):
        if not self.access_token or datetime.now() >= self.token_expires_at:
            self.refresh_access_token()
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def refresh_access_token(self):
        response = requests.post(
            f"{self.base_url}/api/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"])
```

### 3. Use Correlation IDs

Include correlation IDs for request tracking:

```python
import uuid

correlation_id = str(uuid.uuid4())
headers = {
    "Authorization": f"Bearer {token}",
    "X-Correlation-ID": correlation_id
}
```

### 4. Implement Retry Logic

```python
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
```

### 5. Handle Rate Limits

```python
import time

def make_request_with_rate_limit(session, url, headers):
    response = session.get(url, headers=headers)
    
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        time.sleep(retry_after)
        return make_request_with_rate_limit(session, url, headers)
    
    return response
```

### 6. Monitor Workflow Progress

```python
import time

def wait_for_workflow_completion(workflow_id, max_wait=600):
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = requests.get(
            f"{base_url}/api/v1/workflows/{workflow_id}/status-summary",
            headers=headers
        )
        status = response.json()["status"]
        
        if status == "completed":
            return True
        elif status == "failed":
            return False
        
        time.sleep(5)  # Poll every 5 seconds
    
    return False
```

## OpenAPI Types (Frontend)

Generate frontend API types after changing backend API models or routes:

```bash
cd frontend/app
npm run generate:api
```

**Expected output files:**
- `frontend/app/lib/api-types.ts`

By default the generator reads `http://localhost:8001/openapi.json`. Override with
`OPENAPI_SCHEMA=/path/to/openapi.json` if you want to generate from a file.

## Code Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8001"
TOKEN = "your_access_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Start workflow
response = requests.post(
    f"{BASE_URL}/api/v1/workflows/compliance",
    headers=headers,
    json={
        "query": "Analyze GDPR compliance",
        "jurisdiction": "EU"
    }
)
workflow_id = response.json()["workflow_id"]

# Check status
response = requests.get(
    f"{BASE_URL}/api/v1/workflows/{workflow_id}/status",
    headers=headers
)
print(response.json())
```

### JavaScript/TypeScript

```typescript
const BASE_URL = 'http://localhost:8001';
const TOKEN = 'your_access_token';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// Start workflow
const response = await fetch(`${BASE_URL}/api/v1/workflows/compliance`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    query: 'Analyze GDPR compliance',
    jurisdiction: 'EU'
  })
});

const { workflow_id } = await response.json();

// Check status
const statusResponse = await fetch(
  `${BASE_URL}/api/v1/workflows/${workflow_id}/status`,
  { headers }
);

console.log(await statusResponse.json());
```

### cURL

```bash
# Set variables
TOKEN="your_access_token"
BASE_URL="http://localhost:8001"

# Start workflow
WORKFLOW_ID=$(curl -X POST "${BASE_URL}/api/v1/workflows/compliance" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze GDPR compliance",
    "jurisdiction": "EU"
  }' | jq -r '.workflow_id')

# Check status
curl -X GET "${BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/status" \
  -H "Authorization: Bearer ${TOKEN}"
```

## Support

- **Documentation:** https://docs.powerhouse.ai
- **API Reference:** http://localhost:8001/docs
- **Support Email:** support@powerhouse.ai
- **GitHub Issues:** https://github.com/richter83-star/Powerhouse-platform/issues

