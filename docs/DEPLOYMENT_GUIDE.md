# Powerhouse Platform - Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [Monitoring & Health Checks](#monitoring--health-checks)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- Docker 20.10+ and Docker Compose 2.0+
- Kubernetes 1.24+ (for K8s deployment)
- kubectl (for K8s deployment)
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB

**Recommended (Production):**
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 50GB+ SSD

## Docker Deployment

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/richter83-star/Powerhouse-platform.git
   cd POWERHOUSE_DEBUG
   ```

2. **Configure environment:**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your configuration
   ```

3. **Start services:**
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment:**
   ```bash
   curl http://localhost:8001/health
   ```

### Production Deployment

1. **Build optimized images:**
   ```bash
   docker-compose build --no-cache
   ```

2. **Start with resource limits:**
   ```bash
   docker-compose up -d
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f backend
   ```

### Environment Variables

Key environment variables for `backend/.env`:

```env
# Database
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_NAME=powerhouse

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Security
SECRET_KEY=your_jwt_secret_key_here
ALGORITHM=HS256

# Application
DEBUG=False
LOG_LEVEL=INFO
LOG_FORMAT=json

# Sentry (optional)
SENTRY_DSN=your_sentry_dsn
SENTRY_ENVIRONMENT=production
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Storage class for persistent volumes
- Ingress controller (nginx recommended)

### Step-by-Step Deployment

1. **Create namespace:**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

2. **Create secrets:**
   ```bash
   cp k8s/secret.yaml.example k8s/secret.yaml
   # Edit k8s/secret.yaml with your values
   kubectl apply -f k8s/secret.yaml
   ```

3. **Apply configuration:**
   ```bash
   kubectl apply -f k8s/configmap.yaml
   ```

4. **Deploy dependencies:**
   ```bash
   kubectl apply -f k8s/postgres-deployment.yaml
   kubectl apply -f k8s/redis-deployment.yaml
   ```

5. **Wait for dependencies:**
   ```bash
   kubectl wait --for=condition=ready pod -l app=postgres -n powerhouse --timeout=300s
   kubectl wait --for=condition=ready pod -l app=redis -n powerhouse --timeout=300s
   ```

6. **Deploy backend:**
   ```bash
   kubectl apply -f k8s/backend-deployment.yaml
   ```

7. **Deploy ingress (production):**
   ```bash
   kubectl apply -f k8s/ingress.yaml
   ```

### Using Deployment Scripts

**Linux/Mac:**
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh production
```

**Windows (PowerShell):**
```powershell
.\scripts\deploy.ps1 -Environment production
```

### Scaling

The backend deployment includes Horizontal Pod Autoscaler (HPA):

- **Min replicas:** 3
- **Max replicas:** 10
- **CPU threshold:** 70%
- **Memory threshold:** 80%

Manually scale:
```bash
kubectl scale deployment powerhouse-backend --replicas=5 -n powerhouse
```

## Environment Configuration

### Development

```env
DEBUG=True
LOG_LEVEL=DEBUG
LOG_FORMAT=text
ENVIRONMENT=development
```

### Staging

```env
DEBUG=False
LOG_LEVEL=INFO
LOG_FORMAT=json
ENVIRONMENT=staging
SENTRY_DSN=your_staging_sentry_dsn
```

### Production

```env
DEBUG=False
LOG_LEVEL=WARNING
LOG_FORMAT=json
ENVIRONMENT=production
SENTRY_DSN=your_production_sentry_dsn
```

## Database Setup

### Initial Migration

1. **Run Alembic migrations:**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

   Or in Kubernetes:
   ```bash
   kubectl exec -it deployment/powerhouse-backend -n powerhouse -- alembic upgrade head
   ```

### Database Backup

**Docker:**
```bash
docker-compose exec postgres pg_dump -U postgres powerhouse > backup.sql
```

**Kubernetes:**
```bash
kubectl exec -it postgres-0 -n powerhouse -- pg_dump -U postgres powerhouse > backup.sql
```

### Database Restore

```bash
docker-compose exec -T postgres psql -U postgres powerhouse < backup.sql
```

## Monitoring & Health Checks

### Health Endpoint

```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-01T12:00:00Z",
  "database_connected": true,
  "redis_connected": true,
  "services": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"}
  },
  "uptime_seconds": 86400.5
}
```

### Prometheus Metrics

```bash
curl http://localhost:8001/metrics/prometheus
```

### System Metrics

```bash
curl http://localhost:8001/metrics/health
```

## Troubleshooting

### Backend Not Starting

1. **Check logs:**
   ```bash
   docker-compose logs backend
   ```

2. **Verify database connection:**
   ```bash
   docker-compose exec backend python -c "from database.session import get_engine; get_engine()"
   ```

3. **Check environment variables:**
   ```bash
   docker-compose exec backend env | grep DB_
   ```

### Database Connection Issues

1. **Verify PostgreSQL is running:**
   ```bash
   docker-compose ps postgres
   ```

2. **Test connection:**
   ```bash
   docker-compose exec postgres psql -U postgres -d powerhouse -c "SELECT 1;"
   ```

### Redis Connection Issues

1. **Verify Redis is running:**
   ```bash
   docker-compose ps redis
   ```

2. **Test connection:**
   ```bash
   docker-compose exec redis redis-cli ping
   ```

### High Memory Usage

1. **Check resource usage:**
   ```bash
   docker stats
   ```

2. **Adjust resource limits in docker-compose.yml**

3. **Review application logs for memory leaks**

### Performance Issues

1. **Enable query logging:**
   ```env
   DEBUG=True
   ```

2. **Check database indexes:**
   ```bash
   docker-compose exec postgres psql -U postgres -d powerhouse -c "\di"
   ```

3. **Review Prometheus metrics:**
   ```bash
   curl http://localhost:8001/metrics/prometheus | grep http_request_duration
   ```

## Production Checklist

- [ ] Environment variables configured
- [ ] Secrets properly secured
- [ ] Database migrations applied
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Backups configured
- [ ] SSL/TLS certificates installed
- [ ] Rate limiting configured
- [ ] Logging configured
- [ ] Error tracking (Sentry) configured
- [ ] Resource limits set
- [ ] Auto-scaling configured (K8s)
- [ ] Ingress configured with TLS
- [ ] CORS properly configured
- [ ] Security headers enabled

## Support

For issues or questions:
- GitHub Issues: https://github.com/richter83-star/Powerhouse-platform/issues
- Documentation: https://docs.powerhouse.ai
- Support: support@powerhouse.ai

