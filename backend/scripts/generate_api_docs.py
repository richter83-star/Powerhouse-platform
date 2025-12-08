#!/usr/bin/env python3
"""
Script to generate API documentation files.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app
from api.docs_config import custom_openapi, generate_postman_collection


def main():
    """Generate API documentation files"""
    output_dir = Path(__file__).parent.parent / "docs" / "api"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate OpenAPI schema
    print("Generating OpenAPI schema...")
    openapi_schema = custom_openapi(app)
    openapi_file = output_dir / "openapi.json"
    with open(openapi_file, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"✓ OpenAPI schema saved to {openapi_file}")
    
    # Generate Postman collection
    print("Generating Postman collection...")
    postman_collection = generate_postman_collection(app)
    postman_file = output_dir / "postman.json"
    with open(postman_file, "w") as f:
        json.dump(postman_collection, f, indent=2)
    print(f"✓ Postman collection saved to {postman_file}")
    
    # Generate README
    readme_content = f"""# Powerhouse API Documentation

## OpenAPI Specification

- **OpenAPI 3.0 Schema**: [openapi.json](./openapi.json)
- **Interactive Docs**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Postman Collection

- **Collection**: [postman.json](./postman.json)
- **Import**: Import this file into Postman for easy API testing

## Quick Start

1. **View Interactive Documentation**: Navigate to http://localhost:8001/docs
2. **Import Postman Collection**: Import `postman.json` into Postman
3. **Get Access Token**: Use `/api/auth/login` endpoint
4. **Set Token in Postman**: Add token to collection variables

## API Version

Current API version: {app.version}

## Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/signup` - User registration
- `POST /api/auth/verify-email` - Verify email address
- `POST /api/auth/reset-password` - Request password reset

### Workflows
- `POST /api/v1/workflows/compliance` - Start compliance workflow
- `GET /api/v1/workflows/{{workflow_id}}/status` - Get workflow status
- `GET /api/v1/workflows/{{workflow_id}}/results` - Get workflow results

### Health
- `GET /health` - Health check

## Rate Limiting

- Standard: 60 requests/minute
- Burst: 120 requests/minute

Rate limit headers:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

## Request Tracking

All requests include correlation IDs:
- Request header: `X-Correlation-ID` (optional)
- Response header: `X-Correlation-ID` (always included)

## Error Format

All errors follow this format:
```json
{{
  "error": "ErrorType",
  "message": "Human-readable message",
  "correlation_id": "abc123",
  "error_code": "ERROR_CODE",
  "details": {{}},
  "timestamp": "2025-01-01T12:00:00Z"
}}
```
"""
    
    readme_file = output_dir / "README.md"
    with open(readme_file, "w") as f:
        f.write(readme_content)
    print(f"✓ README saved to {readme_file}")
    
    print("\n✓ All documentation files generated successfully!")


if __name__ == "__main__":
    main()

