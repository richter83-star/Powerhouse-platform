# Powerhouse - Complete Uninstall & Reinstall Guide

Complete guide for safely uninstalling and reinstalling Powerhouse with all advanced AI features enabled.

---

## 📋 Table of Contents

1. [Before You Begin](#before-you-begin)
2. [Step 1: Backup Your Data](#step-1-backup-your-data)
3. [Step 2: Stop All Services](#step-2-stop-all-services)
4. [Step 3: Uninstall Powerhouse](#step-3-uninstall-powerhouse)
5. [Step 4: Clean Up (Optional)](#step-4-clean-up-optional)
6. [Step 5: Fresh Installation](#step-5-fresh-installation)
7. [Step 6: Verify Installation](#step-6-verify-installation)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Before You Begin

### What You'll Need

- ✅ **Python 3.11+** installed
- ✅ **Node.js 18+** installed  
- ✅ **Docker Desktop** installed and running
- ✅ **Git** (optional, for pulling latest code)
- ✅ **Backup location** for your data (if you want to preserve it)

### What Gets Uninstalled

- ❌ All Python packages (backend dependencies)
- ❌ All Node.js packages (frontend dependencies)
- ❌ Docker containers and volumes (database data)
- ❌ Environment configurations
- ❌ Build artifacts and cache files

### What Gets Preserved (if you back it up)

- ✅ Database data (PostgreSQL)
- ✅ Environment variables (.env files)
- ✅ Configuration files
- ✅ User-generated content

---

## 📦 Step 1: Backup Your Data

**⚠️ IMPORTANT: Do this first if you want to keep your data!**

### Option A: Backup Database (if you have important data)

1. **Start services if not running:**
   ```batch
   START_POWERHOUSE_FULL.bat
   ```

2. **Wait for database to be ready (30-60 seconds)**

3. **Backup PostgreSQL database:**
   ```batch
   docker exec powerhouse_db pg_dump -U postgres powerhouse > powerhouse_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.sql
   ```

   Or manually:
   ```powershell
   docker exec powerhouse_db pg_dump -U postgres powerhouse > powerhouse_backup.sql
   ```

4. **Save your backup file** to a safe location (e.g., `C:\Backups\powerhouse_backup.sql`)

### Option B: Backup Configuration Files

1. **Backup environment files:**
   ```batch
   mkdir C:\Backups\PowerhouseConfig
   copy backend\.env C:\Backups\PowerhouseConfig\backend.env
   copy frontend\app\.env* C:\Backups\PowerhouseConfig\
   ```

2. **Backup any custom configurations:**
   - `backend/config/*.py` (if modified)
   - `backend/.env`
   - `frontend/app/.env.local`
   - Any custom scripts or configurations

---

## 🛑 Step 2: Stop All Services

### Quick Method (Windows)

**Double-click:** `STOP_ALL.bat`

This will:
- ✅ Stop all Docker containers
- ✅ Stop backend processes
- ✅ Stop frontend processes

### Manual Method

1. **Stop Docker containers:**
   ```batch
   docker-compose down
   ```

2. **Stop any running Python processes:**
   ```batch
   taskkill /F /IM python.exe
   ```

3. **Stop any running Node.js processes:**
   ```batch
   taskkill /F /IM node.exe
   ```

4. **Verify nothing is running:**
   ```batch
   docker ps
   netstat -ano | findstr ":8001"
   netstat -ano | findstr ":3000"
   ```

---

## 🗑️ Step 3: Uninstall Powerhouse

### Method A: Automated Uninstall Script (Recommended)

**Create and run:** `UNINSTALL.bat` (see script below)

### Method B: Manual Uninstall

#### 3.1 Remove Docker Containers and Volumes

```batch
REM Navigate to project directory
cd /d C:\dev\POWERHOUSE_DEBUG

REM Stop and remove containers
docker-compose down -v

REM Remove all Powerhouse-related Docker volumes (optional - deletes ALL data!)
docker volume rm postgres_data redis_data 2>nul

REM Remove Docker images (optional)
docker rmi powerhouse_backend powerhouse_frontend 2>nul
```

#### 3.2 Uninstall Python Packages

```batch
REM Navigate to backend directory
cd backend

REM Uninstall all backend dependencies
pip uninstall -y -r requirements.txt

REM Or remove entire virtual environment if you used one
REM (skip if using system Python)
```

#### 3.3 Uninstall Node.js Packages

```batch
REM Navigate to frontend directory
cd ..\frontend\app

REM Remove node_modules
rmdir /s /q node_modules

REM Remove build artifacts
rmdir /s /q .next 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul

REM Navigate to electron-app (if exists)
cd ..\..\electron-app
rmdir /s /q node_modules 2>nul
rmdir /s /q dist 2>nul
```

#### 3.4 Remove Environment Files (Optional)

```batch
REM Optional: Remove .env files to force fresh setup
cd C:\dev\POWERHOUSE_DEBUG
del backend\.env 2>nul
del frontend\app\.env.local 2>nul
del frontend\app\.env 2>nul
```

---

## 🧹 Step 4: Clean Up (Optional)

### Deep Clean - Remove All Artifacts

```batch
REM Clean Python cache
cd C:\dev\POWERHOUSE_DEBUG
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul

REM Clean Node.js cache
cd frontend\app
call npm cache clean --force 2>nul

REM Clean pip cache (optional)
pip cache purge

REM Clean Docker system (optional - removes unused images/containers)
docker system prune -a --volumes
```

**⚠️ Warning:** `docker system prune -a --volumes` will remove ALL unused Docker resources, not just Powerhouse!

---

## 🚀 Step 5: Fresh Installation

### Option A: Automated Installation (Recommended)

1. **Pull latest code (if using Git):**
   ```batch
   git pull origin main
   ```

2. **Run installer:**
   ```batch
   INSTALL.bat
   ```

   This will:
   - ✅ Check prerequisites
   - ✅ Install all backend dependencies
   - ✅ Install all frontend dependencies
   - ✅ Set up environment files
   - ✅ Verify installation

### Option B: Manual Installation

#### 5.1 Install Backend Dependencies

```batch
cd C:\dev\POWERHOUSE_DEBUG\backend

REM Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

REM Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

REM Verify installation
python -c "import fastapi; print('Backend OK')"
```

#### 5.2 Install Frontend Dependencies

```batch
cd C:\dev\POWERHOUSE_DEBUG\frontend\app

REM Install dependencies
npm install

REM Verify installation
npm list --depth=0
```

#### 5.3 Set Up Environment Files

```batch
cd C:\dev\POWERHOUSE_DEBUG

REM Copy example env files if they don't exist
if not exist backend\.env (
    copy backend\.env.example backend\.env
)

if not exist frontend\app\.env.local (
    copy frontend\app\.env.example frontend\app\.env.local
)
```

#### 5.4 Restore Your Backups (if applicable)

```batch
REM Restore environment files
copy C:\Backups\PowerhouseConfig\backend.env backend\.env

REM Restore database (after starting services)
REM See Step 6 for database restoration
```

---

## ✅ Step 6: Verify Installation

### 6.1 Start Services

```batch
START_POWERHOUSE_FULL.bat
```

Wait for all services to start (30-60 seconds).

### 6.2 Verify Backend

```batch
REM Check health endpoint
curl http://localhost:8001/health

REM Check API docs
start http://localhost:8001/docs
```

### 6.3 Verify Frontend

```batch
REM Open frontend
start http://localhost:3000
```

### 6.4 Verify Advanced Features

1. **Check API documentation:**
   - Visit: http://localhost:8001/docs
   - Look for `/api/advanced/*` endpoints

2. **Test an advanced feature:**
   ```batch
   curl -X POST http://localhost:8001/api/advanced/causal/discover ^
     -H "Content-Type: application/json" ^
     -d "{\"data\": {\"X\": [1,2,3], \"Y\": [2,4,6]}}"
   ```

3. **Check backend logs:**
   ```batch
   docker-compose logs backend | findstr "advanced"
   ```

   Should see:
   ```
   INFO - Advanced features routes loaded (causal reasoning, program synthesis, swarm, etc.)
   ```

### 6.5 Restore Database (if you backed it up)

```batch
REM Make sure database is running
docker-compose up -d postgres

REM Wait for database to be ready
timeout /t 10

REM Restore database
docker exec -i powerhouse_db psql -U postgres powerhouse < C:\Backups\powerhouse_backup.sql
```

---

## 🔧 Troubleshooting

### Issue: "Module not found" errors

**Solution:**
```batch
cd backend
pip install -r requirements.txt --force-reinstall
```

### Issue: Docker containers won't start

**Solution:**
```batch
docker-compose down -v
docker-compose up -d
```

### Issue: Port already in use (8001 or 3000)

**Solution:**
```batch
REM Find process using port
netstat -ano | findstr ":8001"
netstat -ano | findstr ":3000"

REM Kill process (replace PID with actual process ID)
taskkill /F /PID <PID>
```

### Issue: Database connection errors

**Solution:**
```batch
REM Restart database
docker-compose restart postgres

REM Check database logs
docker-compose logs postgres

REM Recreate database if needed
docker-compose down -v
docker-compose up -d postgres
```

### Issue: Advanced features not showing in API docs

**Solution:**
1. Check `backend/config/advanced_features_config.py` - all flags should be `True`
2. Check backend logs for import errors
3. Verify all dependencies are installed:
   ```batch
   pip install networkx pgmpy pandas scipy transformers Pillow
   ```

---

## 📝 Quick Reference

### Complete Uninstall Command Sequence

```batch
REM 1. Stop services
STOP_ALL.bat

REM 2. Remove Docker containers and volumes
docker-compose down -v

REM 3. Uninstall Python packages
cd backend
pip uninstall -y -r requirements.txt

REM 4. Remove Node.js packages
cd ..\frontend\app
rmdir /s /q node_modules

REM 5. Clean up
cd ..\..
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
```

### Complete Reinstall Command Sequence

```batch
REM 1. Pull latest code
git pull origin main

REM 2. Install everything
INSTALL.bat

REM 3. Start services
START_POWERHOUSE_FULL.bat
```

---

## 🎉 You're Done!

After completing these steps, you'll have a fresh installation of Powerhouse with all advanced AI features enabled by default.

**All 10 advanced features are active:**
- ✅ Causal Reasoning & Discovery
- ✅ Neurosymbolic Integration
- ✅ Hierarchical Task Decomposition
- ✅ Memory-Augmented Neural Networks (MANN)
- ✅ Knowledge Distillation
- ✅ Swarm Intelligence
- ✅ Adversarial Robustness
- ✅ Program Synthesis
- ✅ Scientific Discovery
- ✅ Multi-Modal Learning

Enjoy your fully-updated Powerhouse platform! 🚀

