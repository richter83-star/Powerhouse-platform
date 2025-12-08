# Powerhouse Electron Desktop App

This folder contains everything needed to build Powerhouse as a standalone desktop application (.exe installer).

## What You Get

**Powerhouse.exe** - A professional Windows desktop application that:
- ✅ Looks like a native Windows app (no browser chrome)
- ✅ Has its own taskbar icon
- ✅ Minimizes to system tray
- ✅ Auto-starts all services (database, backend, frontend)
- ✅ Provides one-click installation
- ✅ ~150-200 MB installer size

## Requirements

### For Building the Installer:
- Node.js (already installed)
- Internet connection (to download Electron)
- ~500 MB free disk space

### For Running the App (End Users):
- Windows 10/11
- Docker Desktop (must be installed and running)
- ~2 GB free disk space

## How to Build

### Step 1: Make Sure Everything Works First!

Before building the Electron app, test that everything works:

```batch
# From the main powerhouse_b2b_platform folder:
1_START_DATABASE.bat
2_START_BACKEND.bat
3_START_FRONTEND.bat
```

If any of these fail, fix them FIRST before building Electron app.

### Step 2: Build the Electron App

```batch
cd electron-app
BUILD_ELECTRON.bat
```

This will:
1. Install Electron and dependencies (~5 minutes)
2. Copy all project files
3. Build the Windows installer (~5-10 minutes)
4. Create: `dist\Powerhouse Setup 1.0.0.exe`

### Step 3: Install or Distribute

**Option A: Install on This Computer**
```batch
cd dist
"Powerhouse Setup 1.0.0.exe"
```

**Option B: Share with Others**
Copy `Powerhouse Setup 1.0.0.exe` to:
- USB drive
- Network share
- Email (if under size limit)
- Cloud storage (Dropbox, Google Drive)

## File Structure

```
electron-app/
├── main.js                  # Electron main process (app logic)
├── package.json             # Electron configuration
├── BUILD_ELECTRON.bat       # Build script
├── README_ELECTRON.md       # This file
└── dist/                    # Build output (created after build)
    └── Powerhouse Setup 1.0.0.exe  # Final installer
```

## How It Works

The Electron app:

1. **Starts Database**
   - Runs `docker-compose up -d`
   - Waits 5 seconds for initialization

2. **Starts Backend**
   - Activates Python venv
   - Runs `python app.py`
   - Waits for port 8001 to respond

3. **Starts Frontend**
   - Runs `npm run dev` in frontend/app
   - Waits for port 3000 to respond

4. **Opens Application Window**
   - Loads `http://localhost:3000` in Electron window
   - No browser chrome visible
   - Looks like native app

## Features

### System Tray Integration
- Minimize to tray instead of closing
- Right-click tray icon for menu:
  - Show Powerhouse
  - Hide Powerhouse
  - Quit

### Auto-Start Services
- No need to run batch files manually
- Everything starts automatically
- Loading screen while services start

### Clean Shutdown
- Stops all services on quit:
  - Frontend (npm)
  - Backend (Python)
  - Database (Docker)

## Troubleshooting

### Build Fails
**Error**: "npm not found"
- Solution: Install Node.js and restart terminal

**Error**: "electron-builder failed"
- Solution: Delete `node_modules` folder and run `npm install` again

### App Won't Start
**Error**: "Failed to Start" screen
- Cause: Docker Desktop not running
- Solution: Start Docker Desktop first, then launch Powerhouse

**Error**: Services timeout
- Cause: Ports 3000, 8001, or 5433 already in use
- Solution: Close other apps using these ports

### Installation Issues
**Error**: "Windows protected your PC"
- Solution: Click "More info" → "Run anyway"
- Note: This happens because the app isn't code-signed

## Customization

### Change App Name
Edit `electron-app/package.json`:
```json
{
  "build": {
    "productName": "Your Name Here"
  }
}
```

### Change App Icon
1. Get a 256x256 PNG image
2. Convert to .ico format
3. Replace `icon.ico` in electron-app folder

### Change Window Size
Edit `electron-app/main.js`:
```javascript
mainWindow = new BrowserWindow({
  width: 1600,  // Change this
  height: 1000, // Change this
  ...
});
```

## Advanced: Custom Build Options

### Build for Different Platforms
```batch
# Windows 64-bit (default)
npm run dist-win

# Windows 32-bit
npm run dist -- --win --ia32

# Windows portable (no installer)
npm run pack
```

### Reduce Installer Size
Edit `package.json` and add to `extraResources`:
```json
"filter": [
  "**/*",
  "!node_modules",
  "!*.log",
  "!*.md"
]
```

## Distribution

### For Internal Team
- Share the `.exe` file directly
- Minimum requirements:
  - Windows 10/11
  - Docker Desktop

### For External Clients
- Consider code-signing certificate ($200-400/year)
- Prevents "Windows protected" warning
- Makes app look more professional

### For Public Release
- Upload to GitHub Releases
- Host on your website
- Submit to software directories

## Comparison: Batch Files vs Electron App

| Feature | Batch Files | Electron App |
|---------|-------------|--------------|
| **Setup** | 3 files to click | 1 app to launch |
| **UI** | Browser with address bar | Native window |
| **Tray** | No | Yes |
| **Distribution** | Copy folder | Single installer |
| **Size** | ~50 MB | ~150 MB |
| **Speed** | Instant start | 5-10 sec start |
| **Best For** | Development | End users |

## FAQ

**Q: Do users need Python/Node.js installed?**
A: No! Everything is bundled in the installer.

**Q: Do users need Docker Desktop?**
A: Yes. Docker Desktop must be installed and running.

**Q: Can I auto-start Powerhouse with Windows?**
A: Yes. Put a shortcut in:
`C:\Users\YourName\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`

**Q: Can I run multiple instances?**
A: No. Ports 3000/8001/5433 can only be used once.

**Q: How do I update the app?**
A: Build a new installer and reinstall. User data is preserved.

**Q: Can I deploy this to Mac/Linux?**
A: Not with this Windows build. You'd need separate Mac/Linux builds.

## Next Steps

1. ✅ Build the Electron app
2. ✅ Test the installer
3. ✅ Share with team
4. 🎉 Everyone uses professional desktop app!

## Support

If you encounter issues:
1. Check Docker Desktop is running
2. Check ports 3000, 8001, 5433 are free
3. Try the batch files first to debug
4. Check logs in terminal window

---

**Built with ❤️ using Electron**
