# Powerhouse Installer Build Guide

## 📦 What Gets Built

When you run the build process, it creates:

### 1. **Powerhouse Setup 1.0.0.exe** (Installer)
- **Location**: `electron-app/dist/Powerhouse Setup 1.0.0.exe`
- **Purpose**: Windows installer that installs the entire application
- **Features**:
  - Professional installer UI
  - License agreement page
  - System requirements checking
  - Custom installation directory
  - Desktop and Start Menu shortcuts
  - Registry entries for uninstaller
  - Clean uninstall support

### 2. **Powerhouse.exe** (Application Launcher)
- **Location**: `electron-app/dist/win-unpacked/Powerhouse.exe`
- **Purpose**: Standalone launcher that runs the application
- **Features**:
  - Starts database (Docker Compose)
  - Starts backend server
  - Starts frontend server
  - System tray integration
  - Auto-updater support
  - Single-click launch

---

## 🚀 How to Build

### Option 1: Quick Build
```bash
BUILD_INSTALLER.bat
```

### Option 2: Full Production Build
```bash
BUILD_PRODUCTION.bat
```

### Option 3: Manual Build
```bash
cd electron-app
npm install
npm run dist-win
```

---

## 📍 Output Locations

After building, you'll find:

### Installer
```
electron-app/dist/Powerhouse Setup 1.0.0.exe
```

### Launcher (Unpacked)
```
electron-app/dist/win-unpacked/Powerhouse.exe
```

### Portable Version (Optional)
```
electron-app/dist/Powerhouse-1.0.0-portable.exe
```

---

## 🔧 Build Configuration

The build is configured in `electron-app/package.json`:

```json
{
  "build": {
    "appId": "com.powerhouse.desktop",
    "productName": "Powerhouse",
    "win": {
      "target": "nsis",
      "icon": "icon.ico"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true,
      "artifactName": "${productName} Setup ${version}.${ext}"
    }
  }
}
```

---

## ✅ Verification

After building, verify the files exist:

```bash
# Check installer
dir electron-app\dist\Powerhouse Setup*.exe

# Check launcher
dir electron-app\dist\win-unpacked\Powerhouse.exe
```

---

## 🎯 Usage

### For End Users (Installer)
1. Run `Powerhouse Setup 1.0.0.exe`
2. Follow installation wizard
3. Launch from Start Menu or Desktop shortcut

### For Development (Direct Launcher)
1. Run `electron-app/dist/win-unpacked/Powerhouse.exe` directly
2. No installation required
3. Good for testing

---

## 🔍 Troubleshooting

### Build Fails
- Check Node.js version (18+ required)
- Check npm is installed
- Check electron-builder is installed: `npm list electron-builder`
- Review build logs in `electron-app/dist/`

### Installer Not Created
- Check `electron-app/dist/` directory
- Look for error messages in build output
- Verify `electron-app/package.json` is correct

### Launcher Not Working
- Check backend and frontend are built
- Verify Docker is installed (for database)
- Check logs in `%APPDATA%/Powerhouse/logs/`

---

## 📝 Notes

- **First build** takes 10-15 minutes (downloads Electron)
- **Subsequent builds** are faster (2-5 minutes)
- **Installer size**: ~500-800 MB (includes all dependencies)
- **Launcher size**: ~150-200 MB (unpacked)

---

**Status: ✅ Build System Ready**

