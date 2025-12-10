# Powerhouse - Quick Start Guide

## 🎯 Fastest Way to Get Started

### Step 1: Install Everything (One Click)

**Double-click:** `INSTALL.bat`

This will:
- ✅ Check if Python, Node.js, and Docker are installed
- ✅ Install all backend dependencies (Python packages)
- ✅ Install all frontend dependencies (Node.js packages)
- ✅ Set up environment files
- ✅ Verify everything is working

**Time:** 5-10 minutes (depending on your internet speed)

### Step 2: Start Powerhouse (One Click)

**Double-click:** `START_POWERHOUSE_FULL.bat`

This will:
- ✅ Start PostgreSQL database
- ✅ Start FastAPI backend server
- ✅ Start Next.js frontend server
- ✅ Open your browser automatically

**Time:** 30-60 seconds

### Step 3: Use Powerhouse

Open your browser to: **http://localhost:3000**

That's it! You're ready to use Powerhouse.

---

## 📋 What You Need First

Before running `INSTALL.bat`, make sure you have:

1. **Python 3.11 or higher**
   - Download: https://www.python.org/downloads/
   - ⚠️ **Important:** Check "Add Python to PATH" during installation
   - Verify: Open Command Prompt and type `python --version`

2. **Node.js 18 or higher**
   - Download: https://nodejs.org/ (get the LTS version)
   - Verify: Open Command Prompt and type `node --version`

3. **Docker Desktop** (for the database)
   - Download: https://www.docker.com/products/docker-desktop/
   - ⚠️ **Important:** Start Docker Desktop before running `START_POWERHOUSE_FULL.bat`
   - Verify: Docker Desktop should show "Running" status

---

## 🛠️ Troubleshooting

### "Python not found"
- Reinstall Python and make sure to check "Add Python to PATH"
- Restart your computer after installing
- Try running `python --version` in Command Prompt

### "Node.js not found"
- Reinstall Node.js (LTS version)
- Restart your computer after installing
- Try running `node --version` in Command Prompt

### "Docker not running"
- Open Docker Desktop
- Wait for it to fully start (whale icon in system tray)
- Try again

### Installation fails
1. Run `DIAGNOSE.bat` to check your system
2. Check `install_log.txt` for error details
3. Make sure you have internet connection
4. Try running as Administrator (right-click > Run as Administrator)

### Services won't start
- Make sure Docker Desktop is running
- Check if ports 3000, 8001, or 5432 are already in use
- Close any other applications using those ports
- Try restarting your computer

---

## 📁 Project Structure

```
POWERHOUSE_DEBUG/
├── INSTALL.bat                    ← Start here! (Install everything)
├── START_POWERHOUSE_FULL.bat      ← Then this! (Start everything)
├── DIAGNOSE.bat                   ← Troubleshooting tool
├── backend/                       ← Python FastAPI backend
├── frontend/                      ← Next.js React frontend
└── docker-compose.yml             ← Docker configuration
```

---

## 🎮 Manual Start (Alternative)

If you prefer to start services individually:

1. **Start Database:**
   - Double-click: `1_START_DATABASE.bat`
   - Wait for it to finish, then close the window

2. **Start Backend:**
   - Double-click: `2_START_BACKEND.bat`
   - **Keep this window open**

3. **Start Frontend:**
   - Double-click: `3_START_FRONTEND.bat`
   - **Keep this window open**

4. **Open Browser:**
   - Go to: http://localhost:3000

---

## 🛑 Stopping Powerhouse

To stop all services:

- **Double-click:** `STOP_ALL.bat`

Or manually close the windows for:
- `2_START_BACKEND.bat` (backend)
- `3_START_FRONTEND.bat` (frontend)

The database will stop automatically when you close Docker Desktop.

---

## 📚 More Help

- **Full Documentation:** See `README.md`
- **Architecture Details:** See `docs/ARCHITECTURE.md`
- **Deployment Guide:** See `docs/DEPLOYMENT_GUIDE.md`
- **Installation Issues:** See `README_FIRST.txt`

---

## ✅ Success Checklist

After installation, you should have:

- ✅ `backend/venv/` folder exists (Python virtual environment)
- ✅ `frontend/app/node_modules/` folder exists (Node.js packages)
- ✅ `install_log.txt` shows no errors
- ✅ Docker Desktop is running
- ✅ Can access http://localhost:3000
- ✅ Can access http://localhost:8001/docs

If all checkboxes are checked, you're good to go! 🎉

