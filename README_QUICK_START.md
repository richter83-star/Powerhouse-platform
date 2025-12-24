# Powerhouse Platform - Quick Start

## 🚀 Fastest Way to Start

**Windows:**
```batch
docker-quickstart.bat
```

**Linux/macOS:**
```bash
./docker-quickstart.sh
```

This will:
- Check Docker installation
- Start all services (PostgreSQL, Redis, Backend, Frontend)
- Wait for services to initialize
- Open your browser automatically

## 📋 Available Scripts

### Essential Scripts
- `docker-quickstart.bat` - **Main startup script** (use this!)
- `INSTALL_DOCKER_ONLY.bat` - First-time Docker installation
- `STOP_ALL.bat` - Stop all services
- `UNINSTALL.bat` - Complete uninstall

### Utilities
- `DIAGNOSE.bat` - Diagnostic tool
- `VERIFY_DEPLOYMENT.bat` - Verify deployment
- `CLEAN_REINSTALL.bat` - Clean reinstall

### Testing
- `TEST_PHASE1.bat` - Phase 1 tests
- `TEST_COMMERCIAL_GRADE.bat` - Commercial grade tests

## 📚 Documentation

- `README.md` - Main documentation
- `DOCKER_INSTALLATION_GUIDE.md` - Complete Docker guide
- `DOCKER_README.md` - Quick Docker reference
- `QUICK_START.md` - Quick start guide
- `START_HERE.md` - Getting started

## 🔧 Manual Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart a service
docker-compose restart backend
```

## 🌐 Access URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **Health Check:** http://localhost:8001/health


