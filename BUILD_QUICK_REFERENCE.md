# Powerhouse Production Build - Quick Reference

## Build the Installer

```batch
BUILD_PRODUCTION.bat
```

**Output**: `electron-app/dist/Powerhouse Setup 1.0.0.exe`

## What You Get

- **Setup.exe** (~500-800 MB) - Professional Windows installer
- **Powerhouse.exe** - Desktop launcher (created after installation)

## User Installation

1. Run `Powerhouse Setup 1.0.0.exe`
2. Choose installation directory
3. Wait for installation to complete
4. Launch **Powerhouse.exe** from Desktop or Start Menu

## User Experience

- **One-click launch** - Powerhouse.exe starts everything
- **Auto-starts services** - Database, backend, frontend
- **System tray** - Minimizes to tray when closed
- **Native window** - No browser chrome

## Requirements

### For Building
- Python 3.11+
- Node.js 18+
- Windows 10/11
- ~2 GB free disk space

### For End Users
- Windows 10/11
- Docker Desktop (recommended) OR portable PostgreSQL
- ~1.5 GB free disk space

## Troubleshooting

**Build fails?**
- Check Python/Node.js versions
- Ensure prerequisites installed
- Check disk space

**App won't start?**
- Check ports 3000, 8001, 5434 are free
- Check log: `%APPDATA%\Powerhouse\data\powerhouse.log`
- Ensure Docker Desktop is running (if using Docker)

## File Locations

- **Installer**: `electron-app/dist/Powerhouse Setup 1.0.0.exe`
- **User data**: `%APPDATA%\Powerhouse\data\`
- **Logs**: `%APPDATA%\Powerhouse\data\powerhouse.log`

