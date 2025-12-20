# First Time Setup Guide - Quick Start

## ⚡ Fast Installation Options

We've created **3 installation methods** for different needs:

### Option 1: Automated Wizard (Recommended for First Time)
**File:** `SETUP_FIRST_TIME.bat`  
**Time:** 3-5 minutes (first time), ~30 seconds (after)  
**Best for:** First-time users who want step-by-step guidance

**Features:**
- ✅ Checks all prerequisites automatically
- ✅ Creates all configuration files
- ✅ Pre-downloads Docker images for faster startup
- ✅ Builds services only if needed
- ✅ Verifies everything works
- ✅ Helpful error messages

**Usage:**
```bash
SETUP_FIRST_TIME.bat
```

---

### Option 2: Quick Install (Balanced)
**File:** `QUICK_INSTALL.bat`  
**Time:** 2-3 minutes (first time), ~30 seconds (after)  
**Best for:** Users who want fast setup with good defaults

**Features:**
- ✅ Fast startup using existing images
- ✅ Only builds if images don't exist
- ✅ Quick verification
- ✅ Less verbose output

**Usage:**
```bash
QUICK_INSTALL.bat
```

---

### Option 3: Fast Install (Minimal)
**File:** `INSTALL_FAST.bat`  
**Time:** 30-60 seconds (after images exist)  
**Best for:** Users who already have Docker images built

**Features:**
- ✅ Minimal checks
- ✅ Assumes prerequisites are met
- ✅ Fastest startup possible
- ⚠️ Will fail if Docker isn't running or images don't exist

**Usage:**
```bash
INSTALL_FAST.bat
```

---

## 🚀 What Happens During Installation

### First Time (3-5 minutes):
1. **Prerequisites Check** (~10 seconds)
   - Verifies Docker Desktop is installed and running
   
2. **Configuration Setup** (~5 seconds)
   - Creates `backend/.env` if missing
   - Creates `frontend/app/.env` if missing
   
3. **Image Preparation** (~2-3 minutes)
   - Downloads base images (postgres, redis) - ~30 seconds
   - Builds backend image - ~5 minutes (one-time)
   - Builds frontend image - ~3 minutes (one-time)
   
4. **Service Startup** (~30-60 seconds)
   - Starts database and Redis
   - Starts backend
   - Starts frontend
   
5. **Verification** (~10 seconds)
   - Checks all services are responding

### Subsequent Runs (~30 seconds):
- Uses existing Docker images (no build needed)
- Starts containers immediately
- Services ready in 20-30 seconds

---

## 📋 Prerequisites

Before running any installer:

1. **Docker Desktop** (Required)
   - Download from: https://www.docker.com/products/docker-desktop/
   - Must be installed AND running
   - Wait for Docker to fully start (whale icon in system tray)

2. **Windows 10/11** (Required)
   - All installers are batch files for Windows

3. **Internet Connection** (Required for first time)
   - Needed to download Docker images
   - ~500MB download total

---

## 🔍 Troubleshooting

### Docker Not Running
**Error:** "Docker is not running"

**Solution:**
1. Open Docker Desktop
2. Wait for it to fully start (may take 1-2 minutes)
3. Check system tray for Docker whale icon
4. Run installer again

---

### Ports Already in Use
**Error:** "Port 3000/8001/5434 already in use"

**Solution:**
```bash
# Check what's using the ports
netstat -ano | findstr :3000
netstat -ano | findstr :8001
netstat -ano | findstr :5434

# Stop existing Powerhouse containers
docker-compose down

# Or stop the specific process using Task Manager
```

---

### Build Takes Too Long
**Problem:** First build takes 10+ minutes

**Explanation:** This is normal for first-time setup. Docker needs to:
- Download base images (~500MB)
- Install all dependencies
- Build application code

**Tip:** Use `SETUP_FIRST_TIME.bat` which pre-downloads images to save time.

---

### Services Won't Start
**Error:** Containers start but immediately stop

**Solution:**
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild if needed
docker-compose build --no-cache
docker-compose up -d
```

---

## 🎯 After Installation

Once installation completes:

1. **Access the Application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - Health Check: http://localhost:8001/health

2. **Start/Stop Services:**
   ```bash
   # Start
   docker-compose up -d
   
   # Stop
   docker-compose down
   
   # Restart
   docker-compose restart
   
   # View logs
   docker-compose logs -f
   ```

3. **Check Status:**
   ```bash
   docker-compose ps
   ```

---

## 💡 Tips for Faster Startup

1. **Don't stop Docker Desktop** - Keeping it running saves startup time

2. **Use existing images** - After first build, subsequent starts are instant

3. **Use Fast Install** - Once everything is set up, use `INSTALL_FAST.bat`

4. **Desktop App** - Use the built Electron app for one-click startup

---

## 📞 Need Help?

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Verify Docker is running: `docker ps`
3. Check service status: `docker-compose ps`
4. Try the automated wizard: `SETUP_FIRST_TIME.bat`

---

## 🎉 Success!

Once you see:
```
[✓] Database: Healthy
[✓] Redis: Healthy  
[✓] Backend: Running
[✓] Frontend: Running
```

You're ready to use Powerhouse! Open http://localhost:3000 in your browser.

