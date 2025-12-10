# Powerhouse Troubleshooting Guide

This guide helps you diagnose and resolve common issues with Powerhouse.

## Table of Contents

- [Common Issues](#common-issues)
- [Database Issues](#database-issues)
- [Backend Issues](#backend-issues)
- [Frontend Issues](#frontend-issues)
- [Authentication Issues](#authentication-issues)
- [Performance Issues](#performance-issues)
- [Deployment Issues](#deployment-issues)
- [Logs and Debugging](#logs-and-debugging)

## Common Issues

### Port Already in Use

**Symptoms:**
- Error: "Address already in use"
- Services fail to start

**Solutions:**
1. Check if services are already running:
   ```powershell
   netstat -ano | findstr :3000
   netstat -ano | findstr :8001
   netstat -ano | findstr :5434
   ```

2. Stop existing processes:
   ```powershell
   # Find and kill process on port 3000
   taskkill /F /PID <PID>
   ```

3. Or change ports in:
   - Frontend: `frontend/app/.env.local` - `PORT=3001`
   - Backend: `backend/.env` - `API_PORT=8002`
   - Database: `docker-compose.yml` - `5435:5432`

### Environment Variables Not Loaded

**Symptoms:**
- Services start but fail with configuration errors
- Missing API keys or database connection errors

**Solutions:**
1. Verify `.env` files exist:
   - `backend/.env`
   - `frontend/app/.env.local`

2. Check file format (no spaces around `=`):
   ```bash
   KEY=value  # ✅ Correct
   KEY = value  # ❌ Wrong
   ```

3. Restart services after changing environment variables

## Database Issues

### Database Connection Failed

**Symptoms:**
- "Connection refused" errors
- "Cannot connect to database" messages

**Solutions:**
1. Verify Docker is running:
   ```powershell
   docker ps
   ```

2. Check database container:
   ```powershell
   docker ps | findstr postgres
   ```

3. Start database:
   ```powershell
   docker-compose up -d postgres
   ```

4. Check database logs:
   ```powershell
   docker logs powerhouse_db
   ```

5. Verify connection string in `backend/.env`:
   ```env
   DB_HOST=localhost
   DB_PORT=5434
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_NAME=powerhouse
   ```

### Database Migration Errors

**Symptoms:**
- "Table already exists" errors
- Migration failures

**Solutions:**
1. Check current migration status:
   ```bash
   cd backend
   alembic current
   ```

2. Reset migrations (⚠️ **Warning: Drops all data**):
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

3. Create new migration:
   ```bash
   alembic revision --autogenerate -m "description"
   alembic upgrade head
   ```

### Connection Pool Exhausted

**Symptoms:**
- "Too many connections" errors
- Slow queries

**Solutions:**
1. Check connection pool stats:
   ```bash
   curl http://localhost:8001/api/v1/metrics/db/pool
   ```

2. Increase pool size in `backend/.env`:
   ```env
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=40
   ```

3. Review for connection leaks (check logs for warnings)

## Backend Issues

### Backend Won't Start

**Symptoms:**
- Port 8001 not responding
- Import errors in logs

**Solutions:**
1. Check Python version:
   ```bash
   python --version  # Should be 3.11+
   ```

2. Reinstall dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Check for missing environment variables:
   ```bash
   python -m core.validation
   ```

4. Check logs:
   ```bash
   # Windows
   type logs\backend.log
   
   # Linux/Mac
   tail -f logs/backend.log
   ```

### Import Errors

**Symptoms:**
- "ModuleNotFoundError"
- Missing package errors

**Solutions:**
1. Activate virtual environment (if using):
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

2. Reinstall requirements:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

### API Endpoints Returning 500 Errors

**Symptoms:**
- Internal server errors
- Empty error messages

**Solutions:**
1. Check backend logs for detailed errors
2. Verify database connection
3. Check Redis connection (if using)
4. Verify environment variables are set correctly
5. Enable debug mode (development only):
   ```env
   DEBUG=True
   ```

## Frontend Issues

### Frontend Won't Build

**Symptoms:**
- Build failures
- TypeScript errors

**Solutions:**
1. Clear Next.js cache:
   ```bash
   cd frontend/app
   rm -rf .next
   npm run build
   ```

2. Update dependencies:
   ```bash
   npm install
   npm update
   ```

3. Fix TypeScript errors:
   ```bash
   npm run lint
   ```

### Frontend Can't Connect to Backend

**Symptoms:**
- Network errors
- "Cannot connect to backend" messages

**Solutions:**
1. Verify backend is running:
   ```bash
   curl http://localhost:8001/health
   ```

2. Check CORS settings in `backend/.env`:
   ```env
   CORS_ORIGINS=http://localhost:3000,http://localhost:8001
   ```

3. Verify frontend API URL in `frontend/app/.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8001
   ```

## Authentication Issues

### Login Fails

**Symptoms:**
- "Invalid credentials" errors
- Authentication timeout

**Solutions:**
1. Verify user exists in database
2. Check password hashing
3. Verify JWT secret key is set:
   ```env
   SECRET_KEY=<long-random-string>
   JWT_SECRET_KEY=<long-random-string>
   ```

4. Check token expiration:
   ```env
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

### Token Expiration Issues

**Symptoms:**
- "Token expired" errors
- Frequent re-logins required

**Solutions:**
1. Increase token expiration (development only):
   ```env
   ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
   ```

2. Implement refresh token logic on frontend
3. Check Redis token blacklist (if enabled)

## Performance Issues

### Slow API Responses

**Symptoms:**
- High latency
- Timeout errors

**Solutions:**
1. Check database query performance:
   ```bash
   # Enable query logging
   LOG_SQL_QUERIES=True
   ```

2. Review database indexes:
   ```bash
   python -m core.database.optimization
   ```

3. Check connection pool utilization:
   ```bash
   curl http://localhost:8001/api/v1/metrics/db/pool
   ```

4. Enable caching:
   ```env
   REDIS_URL=redis://localhost:6379/0
   ```

### High Memory Usage

**Symptoms:**
- Out of memory errors
- System slowdowns

**Solutions:**
1. Check memory usage:
   ```bash
   curl http://localhost:8001/api/v1/metrics/system
   ```

2. Reduce worker processes:
   ```bash
   # In uvicorn command
   --workers 2  # Instead of 4
   ```

3. Review memory-intensive operations
4. Increase system RAM or add swap space

## Deployment Issues

### Docker Build Fails

**Symptoms:**
- Build errors
- Image creation fails

**Solutions:**
1. Clear Docker cache:
   ```bash
   docker system prune -a
   ```

2. Rebuild without cache:
   ```bash
   docker-compose build --no-cache
   ```

3. Check Dockerfile syntax
4. Verify all required files are present

### Kubernetes Deployment Issues

**Symptoms:**
- Pods not starting
- Health check failures

**Solutions:**
1. Check pod logs:
   ```bash
   kubectl logs <pod-name>
   ```

2. Verify health check endpoints:
   ```bash
   kubectl exec <pod-name> -- curl http://localhost:8001/health
   ```

3. Check resource limits
4. Verify secrets and config maps

## Logs and Debugging

### Viewing Logs

**Backend Logs:**
```bash
# Windows
type logs\backend.log
type logs\powerhouse.log

# Linux/Mac
tail -f logs/backend.log
tail -f logs/powerhouse.log
```

**Frontend Logs:**
- Check browser console (F12)
- Check Next.js build output

**Database Logs:**
```bash
docker logs powerhouse_db
```

**Docker Compose Logs:**
```bash
docker-compose logs -f
```

### Enabling Debug Mode

**Backend:**
```env
DEBUG=True
LOG_LEVEL=DEBUG
```

**Frontend:**
```env
NODE_ENV=development
```

### Correlation IDs

All requests include correlation IDs for tracking. Look for:
- `X-Correlation-ID` header in responses
- Correlation ID in error messages
- Correlation ID in logs

Use correlation IDs to trace requests across services.

## Getting Help

1. **Check Logs**: Most issues are visible in logs
2. **Search Issues**: Check GitHub issues for similar problems
3. **Enable Debug Mode**: Get more detailed error messages
4. **Check Health Endpoints**: Verify service status
5. **Review Configuration**: Ensure all environment variables are set

## Emergency Procedures

### Complete Reset (⚠️ **Deletes All Data**)

1. Stop all services
2. Remove Docker containers and volumes:
   ```bash
   docker-compose down -v
   ```
3. Delete database:
   ```bash
   docker volume rm powerhouse_postgres_data
   ```
4. Restart services

### Restore from Backup

1. Stop services
2. Restore database backup:
   ```bash
   docker exec -i powerhouse_db psql -U postgres powerhouse < backup.sql
   ```
3. Restart services

