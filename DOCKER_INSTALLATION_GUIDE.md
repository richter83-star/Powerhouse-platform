# Docker Installation Guide for Powerhouse Platform

This guide will help you set up and run the Powerhouse Platform using Docker. Docker allows you to run the entire application stack without installing Python, Node.js, or PostgreSQL directly on your machine.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Manual Installation](#manual-installation)
4. [Docker Architecture](#docker-architecture)
5. [Configuration](#configuration)
6. [Common Commands](#common-commands)
7. [Troubleshooting](#troubleshooting)
8. [Production Deployment](#production-deployment)

## Prerequisites

### 1. Install Docker Desktop

**Windows:**
- Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
- Run the installer and follow the setup wizard
- Restart your computer if prompted
- Launch Docker Desktop and wait for it to fully start (whale icon in system tray)

**macOS:**
- Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
- Drag Docker.app to Applications folder
- Launch Docker Desktop from Applications

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and log back in

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. Verify Docker Installation

Open a terminal/command prompt and run:

```bash
docker --version
docker-compose --version
```

Both commands should return version numbers. If not, Docker is not properly installed.

### 3. Ensure Docker is Running

**Windows/macOS:**
- Check system tray for Docker Desktop icon
- Icon should be steady (not animated)
- If not running, launch Docker Desktop

**Linux:**
```bash
sudo systemctl status docker
```

## Quick Start

### Option 1: Automated Installation (Recommended)

**Windows:**
```batch
INSTALL_DOCKER_ONLY.bat
```

**Linux/macOS:**
```bash
chmod +x scripts/install-docker.sh
./scripts/install-docker.sh
```

### Option 2: Manual Quick Start

1. **Clone/Navigate to the project:**
   ```bash
   cd Powerhouse-platform
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Wait for services to start (30-60 seconds):**
   ```bash
   docker-compose ps
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - Health Check: http://localhost:8001/health

## Manual Installation

### Step 1: Build Docker Images

Build all images (first time only, takes 5-10 minutes):

```bash
docker-compose build
```

Or build specific services:

```bash
docker-compose build backend
docker-compose build frontend
```

### Step 2: Start Services

Start all services in detached mode:

```bash
docker-compose up -d
```

### Step 3: Check Service Status

```bash
docker-compose ps
```

You should see all services with status "Up" or "Up (healthy)".

### Step 4: View Logs

View logs from all services:

```bash
docker-compose logs -f
```

View logs from a specific service:

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Step 5: Verify Services

**Check Backend:**
```bash
curl http://localhost:8001/health
```

**Check Frontend:**
Open browser: http://localhost:3000

**Check Database:**
```bash
docker-compose exec postgres psql -U powerhouse_user -d powerhouse -c "SELECT version();"
```

## Docker Architecture

The Powerhouse Platform consists of the following Docker services:

### Services Overview

1. **PostgreSQL** (`postgres`)
   - Database for application data
   - Port: 5434 (host) → 5432 (container)
   - Volume: `postgres_data` (persistent storage)

2. **Redis** (`redis`)
   - Caching and session storage
   - Port: 6379
   - Volume: `redis_data` (persistent storage)

3. **Backend** (`backend`)
   - FastAPI application
   - Port: 8001 (host) → 8000 (container)
   - Depends on: postgres, redis

4. **Frontend** (`frontend`)
   - Next.js application
   - Port: 3000
   - Depends on: postgres, backend

### Network

All services run on the same Docker network (`powerhouse-platform_default`) and can communicate using service names as hostnames.

## Configuration

### Environment Variables

Environment variables are set in `docker-compose.yml`. For production, use environment files:

**Create `.env` file in project root:**

```env
# Database
POSTGRES_USER=powerhouse_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=powerhouse

# Backend
SECRET_KEY=your_secret_key_minimum_32_characters
JWT_SECRET_KEY=your_jwt_secret_key_minimum_32_characters
NEXT_PUBLIC_API_URL=http://localhost:8001

# Frontend
NEXTAUTH_SECRET=your_nextauth_secret_minimum_32_characters
NEXTAUTH_URL=http://localhost:3000
```

Then update `docker-compose.yml` to use variables:

```yaml
environment:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  SECRET_KEY: ${SECRET_KEY}
  # ... etc
```

### Port Configuration

Default ports (can be changed in `docker-compose.yml`):

- **Frontend:** 3000
- **Backend:** 8001
- **PostgreSQL:** 5434
- **Redis:** 6379

To change ports, modify the `ports` section:

```yaml
ports:
  - "NEW_PORT:CONTAINER_PORT"
```

## Common Commands

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d backend

# Start with logs visible
docker-compose up
```

### Stopping Services

```bash
# Stop all services (keeps containers)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (⚠️ deletes data)
docker-compose down -v
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Restarting Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Rebuilding Images

```bash
# Rebuild all
docker-compose build --no-cache

# Rebuild specific service
docker-compose build --no-cache backend
```

### Accessing Containers

```bash
# Execute command in container
docker-compose exec backend bash
docker-compose exec postgres psql -U powerhouse_user -d powerhouse

# Run one-off command
docker-compose run backend python manage.py migrate
```

### Database Operations

```bash
# Access PostgreSQL shell
docker-compose exec postgres psql -U powerhouse_user -d powerhouse

# Backup database
docker-compose exec postgres pg_dump -U powerhouse_user powerhouse > backup.sql

# Restore database
docker-compose exec -T postgres psql -U powerhouse_user powerhouse < backup.sql
```

### Cleanup

```bash
# Remove stopped containers
docker-compose rm

# Remove unused images
docker image prune

# Remove all unused Docker resources
docker system prune -a
```

## Troubleshooting

### Services Won't Start

1. **Check Docker is running:**
   ```bash
   docker ps
   ```

2. **Check logs for errors:**
   ```bash
   docker-compose logs
   ```

3. **Check port conflicts:**
   - Ensure ports 3000, 8001, 5434, 6379 are not in use
   - Windows: `netstat -ano | findstr :3000`
   - Linux/macOS: `lsof -i :3000`

### Database Connection Issues

1. **Wait for database to be healthy:**
   ```bash
   docker-compose ps postgres
   ```
   Wait until status shows "healthy"

2. **Check database logs:**
   ```bash
   docker-compose logs postgres
   ```

3. **Verify connection:**
   ```bash
   docker-compose exec postgres psql -U powerhouse_user -d powerhouse -c "SELECT 1;"
   ```

### Backend Won't Start

1. **Check backend logs:**
   ```bash
   docker-compose logs backend
   ```

2. **Rebuild backend image:**
   ```bash
   docker-compose build --no-cache backend
   docker-compose up -d backend
   ```

3. **Check dependencies:**
   ```bash
   docker-compose exec backend pip list
   ```

### Frontend Build Fails

1. **Check frontend logs:**
   ```bash
   docker-compose logs frontend
   ```

2. **Rebuild frontend image:**
   ```bash
   docker-compose build --no-cache frontend
   docker-compose up -d frontend
   ```

3. **Check Node modules:**
   ```bash
   docker-compose exec frontend npm list
   ```

### Out of Disk Space

```bash
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a --volumes
```

### Permission Issues (Linux)

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and log back in, then:
newgrp docker
```

## Production Deployment

### Security Considerations

1. **Change default passwords:**
   - Update `POSTGRES_PASSWORD` in `docker-compose.yml`
   - Update `SECRET_KEY` and `JWT_SECRET_KEY`
   - Use strong, randomly generated passwords

2. **Use environment files:**
   - Never commit `.env` files to version control
   - Use Docker secrets or environment variable injection

3. **Network security:**
   - Don't expose database ports publicly
   - Use reverse proxy (nginx/traefik) for frontend/backend
   - Enable SSL/TLS

4. **Resource limits:**
   Add to `docker-compose.yml`:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
           reservations:
             cpus: '1'
             memory: 1G
   ```

### Production docker-compose.yml

Use `docker-compose.prod.yml` for production:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Monitoring

1. **Health checks:**
   ```bash
   curl http://localhost:8001/health
   ```

2. **Container stats:**
   ```bash
   docker stats
   ```

3. **Log aggregation:**
   Consider using Docker logging drivers or external log aggregation tools.

### Backup Strategy

1. **Database backups:**
   ```bash
   # Automated backup script
   docker-compose exec postgres pg_dump -U powerhouse_user powerhouse | gzip > backup_$(date +%Y%m%d).sql.gz
   ```

2. **Volume backups:**
   ```bash
   docker run --rm -v powerhouse-platform_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
   ```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

## Support

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Review this guide's troubleshooting section
3. Check GitHub issues
4. Contact support

---

**Last Updated:** 2025-01-27


