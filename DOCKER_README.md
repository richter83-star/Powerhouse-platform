# Docker Setup for Powerhouse Platform

Quick reference for Docker installation and usage.

## Quick Start

### Windows
```batch
docker-quickstart.bat
```

### Linux/macOS
```bash
./docker-quickstart.sh
```

### Manual Start
```bash
docker-compose up -d
```

## Access URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **Health Check:** http://localhost:8001/health

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart backend

# Rebuild images
docker-compose build --no-cache

# Check status
docker-compose ps
```

## Files Created

- `backend/.dockerignore` - Optimizes backend Docker builds
- `frontend/app/.dockerignore` - Optimizes frontend Docker builds
- `DOCKER_INSTALLATION_GUIDE.md` - Comprehensive installation guide
- `docker-quickstart.sh` - Quick start script (Linux/macOS)
- `docker-quickstart.bat` - Quick start script (Windows)

## Documentation

For detailed information, see [DOCKER_INSTALLATION_GUIDE.md](./DOCKER_INSTALLATION_GUIDE.md)


