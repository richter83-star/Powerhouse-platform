# 🚀 START HERE - Fast First-Time Installation

## ⚡ Choose Your Installation Method

### 🏆 RECOMMENDED: Docker-Only Install (Fastest!)

**File:** `INSTALL_DOCKER_ONLY.bat`  
**Time:** 5-8 minutes first time, 30 seconds after  
**Requirements:** Just Docker Desktop!

```bash
# Just double-click this file:
INSTALL_DOCKER_ONLY.bat
```

**Why this is best:**
- ✅ Only need Docker Desktop (no Python/Node.js installation)
- ✅ Fastest setup process
- ✅ Everything cached for instant future startups
- ✅ One script handles everything

---

### 📋 Alternative Options

#### Option 2: Docker Quick Start (after install)
`docker-quickstart.bat` - Starts services quickly

---

## ✅ What You Need First

**Before running any installer, you only need:**

1. **Docker Desktop** 
   - Download: https://www.docker.com/products/docker-desktop/
   - Install and start it
   - Wait for it to fully start (whale icon in system tray)

**That's it!** No Python, no Node.js, nothing else needed for Docker-only install.

---

## 🎯 After Installation

Once installation completes:

1. **Access Powerhouse:**
   - Open: http://localhost:3000

2. **Start/Stop Services:**
   ```bash
   # Start
   docker-quickstart.bat
   # OR
   docker-compose up -d
   
   # Stop
   STOP_ALL.bat
   # OR
   docker-compose down
   ```

3. **Desktop App:**
   - Use the Electron installer: `electron-app/dist/Powerhouse Setup 1.0.0.exe`
   - Provides one-click launch and system tray integration

---

## 📚 More Information

- **Detailed guide:** `README_QUICK_START.md`
- **Troubleshooting:** See installation script output
- **Service logs:** `docker-compose logs -f`

---

## ⏱️ Time Comparison

| Method | First Time | After First Time |
|--------|-----------|------------------|
| Docker-Only Install | 5-8 min | 30 sec |
| Docker Quick Start | 30 sec | 30 sec |

**Recommendation:** Use `INSTALL_DOCKER_ONLY.bat` for the fastest experience!

