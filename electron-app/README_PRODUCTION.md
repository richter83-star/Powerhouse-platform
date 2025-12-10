# Powerhouse Production Build Guide

This guide explains how to build a production-ready installer for Powerhouse that creates:
- **Setup.exe** - Professional Windows installer
- **Powerhouse.exe** - Desktop launcher application

## Quick Build

From the project root, run:

```batch
BUILD_PRODUCTION.bat
```

This will:
1. Clean previous builds
2. Check prerequisites (Python, Node.js)
3. Install backend dependencies
4. Build frontend production bundle
5. Create Electron installer
6. Output: `electron-app/dist/Powerhouse Setup 1.0.0.exe`

## Requirements for Building

- **Python 3.11+** - For backend
- **Node.js 18+** - For frontend and Electron
- **npm** - Comes with Node.js
- **Windows 10/11** - For building Windows installer
- **~2 GB free disk space** - For build artifacts

## What Gets Bundled

The installer includes:
- ✅ Backend (Python FastAPI) - All dependencies bundled
- ✅ Frontend (Next.js) - Production build
- ✅ Electron runtime - Desktop app wrapper
- ✅ Database configuration - Docker Compose file
- ✅ All project files - Excluding dev-only files

## Installation Size

- **Installer**: ~500-800 MB
- **Installed size**: ~1-1.5 GB
- **Runtime requirements**: 
  - Docker Desktop (for database) OR
  - Portable PostgreSQL (bundled)

## Distribution

### For Internal Use
1. Build the installer using `BUILD_PRODUCTION.bat`
2. Copy `Powerhouse Setup 1.0.0.exe` to shared location
3. Users run the installer
4. Users launch `Powerhouse.exe` from Start Menu or Desktop

### For External Clients
1. Build the installer
2. Test on clean Windows machine
3. Consider code signing (optional, ~$200-400/year)
4. Distribute via:
   - USB drive
   - Network share
   - Cloud storage (Dropbox, Google Drive)
   - Email (if under size limit)

## User Experience

### Installation
1. User runs `Powerhouse Setup 1.0.0.exe`
2. Chooses installation directory (default: `C:\Program Files\Powerhouse`)
3. Installer copies all files
4. Creates desktop and Start Menu shortcuts

### Running
1. User launches `Powerhouse.exe`
2. App shows loading screen
3. Automatically starts:
   - Database (Docker or portable PostgreSQL)
   - Backend API (port 8001)
   - Frontend (port 3000)
4. Opens desktop window with Powerhouse UI
5. Minimizes to system tray when closed

### System Tray
- Right-click tray icon for options:
  - Show/Hide Powerhouse
  - Open in Browser
  - Quit

## Troubleshooting

### Build Fails
- Check Python and Node.js versions
- Ensure all prerequisites are installed
- Check disk space (need ~2 GB free)
- Review error messages in console

### Installer Won't Run
- Check Windows version (needs Windows 10+)
- Try running as administrator
- Check antivirus (may block unsigned installers)

### App Won't Start
- Check if ports 3000, 8001, 5434 are available
- Ensure Docker Desktop is running (if using Docker)
- Check log file: `%APPDATA%\Powerhouse\data\powerhouse.log`
- Try running services manually with batch files

## Advanced Options

### Custom Icon
Replace `electron-app/icon.ico` with your icon file (256x256 recommended)

### Custom Branding
Edit `electron-app/main.js`:
- Change `APP_NAME` constant
- Modify loading screen HTML
- Update window title

### Reduce Size
Edit `electron-app/package.json`:
- Add more filters to `extraResources`
- Exclude unnecessary files
- Use `compression: "maximum"` (already set)

### Code Signing
Add to `electron-app/package.json`:
```json
"win": {
  "certificateFile": "path/to/certificate.pfx",
  "certificatePassword": "password"
}
```

## Manual Build Steps

If you prefer manual control:

```batch
REM 1. Prepare backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd ..

REM 2. Prepare frontend
cd frontend\app
npm install
npm run build
cd ..\..

REM 3. Build Electron
cd electron-app
npm install
npm run dist-win
cd ..
```

## Support

For issues or questions:
1. Check log file: `%APPDATA%\Powerhouse\data\powerhouse.log`
2. Review build console output
3. Test services manually with batch files
4. Check Windows Event Viewer for errors

