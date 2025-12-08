# Powerhouse Platform - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                           │
│  Web App (Next.js)  │  Desktop (Electron)  │  API Clients  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                        │
│  FastAPI Backend (Uvicorn)                                  │
│  - Authentication (JWT)                                     │
│  - Rate Limiting (Redis)                                    │
│  - Security Headers                                         │
│  - Correlation IDs                                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  PostgreSQL  │ │  Redis   │ │   Agents     │
│  Database    │ │  Cache   │ │  Orchestrator│
└──────────────┘ └──────────┘ └──────────────┘
```

## Component Overview

### Backend (FastAPI)

- **Framework:** FastAPI 0.115+
- **ASGI Server:** Uvicorn with 4 workers
- **Port:** 8001
- **Features:**
  - JWT Authentication
  - Multi-tenancy
  - Rate limiting
  - Caching
  - Metrics collection

### Database (PostgreSQL)

- **Version:** 15+
- **Features:**
  - Row-Level Security (RLS)
  - Connection pooling
  - Automated backups
  - Multi-tenant isolation

### Cache (Redis)

- **Version:** 7+
- **Uses:**
  - Rate limiting
  - Query result caching
  - Session storage

### Agents

- **Types:** 19+ specialized agents
- **Orchestration:** Dynamic agent selection
- **Execution:** Async with monitoring

## Data Flow

1. **Request** → API Gateway
2. **Authentication** → JWT validation
3. **Rate Limiting** → Redis check
4. **Routing** → Endpoint handler
5. **Database** → Query with tenant filter
6. **Cache** → Check Redis cache
7. **Agent Execution** → Orchestrator
8. **Response** → JSON with correlation ID

## Security Layers

1. **Network:** TLS/SSL encryption
2. **Application:** Security headers (CSP, HSTS, etc.)
3. **Authentication:** JWT tokens
4. **Authorization:** RBAC with tenant isolation
5. **Input:** Validation and sanitization
6. **Rate Limiting:** Redis-backed distributed limiting

## Monitoring

- **Metrics:** Prometheus
- **Logging:** Structured JSON logs
- **Tracing:** Correlation IDs
- **Alerting:** Configurable thresholds
- **Health Checks:** /health endpoint

## Deployment

- **Development:** Docker Compose
- **Production:** Kubernetes with HPA
- **Scaling:** 3-10 replicas (auto-scaling)
- **Storage:** Persistent volumes for DB/Redis

