# Powerhouse Commercial-Grade Installer Guide

## 🎯 Overview

Powerhouse now includes a **commercial-grade installation system** that rivals professional software products. This guide explains what's included and how to use it.

## ✨ Key Features

### 1. Professional Installer Experience
- Modern, branded installer UI
- License agreement (EULA) acceptance
- Component selection
- Custom installation directory
- Progress indicators
- Launch option on completion

### 2. System Requirements Validation
- **Automatic checking** before installation
- **Windows 10+** requirement
- **RAM validation** (4GB minimum, 8GB recommended)
- **Disk space** checking (2GB minimum, 5GB recommended)
- **Port availability** verification
- **Clear error messages** if requirements not met
- **Warnings** for sub-optimal configurations

### 3. Auto-Updater
- **Automatic update checking** (every 24 hours)
- **Background operation** (non-intrusive)
- **Update notifications** with release notes
- **One-click update** download and install
- **Skip version** option
- **Ready for update server** integration

### 4. Code Signing Ready
- **Full configuration** for code signing certificates
- **Multiple CA support** (DigiCert, Sectigo, GlobalSign)
- **Environment variable** configuration
- **Manual signing** option available
- **Removes Windows security warnings** when signed

### 5. Professional Uninstaller
- **Complete removal** of all files
- **Registry cleanup**
- **Shortcut removal**
- **Data retention** option (user choice)
- **Clean, professional UI**

### 6. Windows Integration
- **Proper registry entries**
- **Add/Remove Programs** integration
- **Desktop shortcuts**
- **Start Menu** integration
- **System tray** support
- **Version tracking**

## 🚀 Quick Start

### Building the Installer

```batch
BUILD_PRODUCTION.bat
```

This creates: `electron-app/dist/Powerhouse Setup 1.0.0.exe`

### What Happens During Build

1. ✅ System prerequisites checked
2. ✅ Backend dependencies installed
3. ✅ Frontend production build created
4. ✅ Electron app packaged
5. ✅ NSIS installer generated
6. ✅ Code signing (if configured)
7. ✅ Final verification

### Installation Experience

**User runs installer:**
1. Welcome screen with app info
2. License agreement (must accept)
3. Component selection
4. Installation directory choice
5. Installation progress
6. Finish screen with launch option

**User launches Powerhouse.exe:**
1. System requirements checked automatically
2. Services start automatically
3. Desktop window opens
4. App minimizes to system tray when closed

## 🔧 Configuration

### Version Number

Update in two places:

1. `electron-app/package.json`:
   ```json
   "version": "1.0.0"
   ```

2. `backend/config/settings.py`:
   ```python
   app_version: str = "1.0.0"
   ```

### Code Signing (Optional but Recommended)

See `electron-app/code-signing.md` for complete instructions.

**Quick setup:**
1. Obtain code signing certificate (~$200-600/year)
2. Export as `.pfx` file
3. Set environment variables:
   ```batch
   set CERTIFICATE_FILE=C:\path\to\certificate.pfx
   set CERTIFICATE_PASSWORD=your-password
   ```
4. Build installer (will auto-sign)

### Update Server

Configure in `electron-app/auto-updater.js`:
```javascript
const UPDATE_CHECK_URL = 'https://powerhouse.ai/api/updates/check';
```

Your server should return:
```json
{
  "version": "1.0.1",
  "releaseNotes": "Bug fixes and improvements",
  "downloadUrl": "https://powerhouse.ai/downloads/Powerhouse-Setup-1.0.1.exe"
}
```

Or return HTTP 204 if no updates available.

## 📋 Pre-Release Checklist

Before distributing:

- [ ] Update version numbers
- [ ] Review LICENSE.txt (EULA)
- [ ] Configure code signing (recommended)
- [ ] Set up update server endpoint
- [ ] Test on clean Windows 10 machine
- [ ] Test on clean Windows 11 machine
- [ ] Verify uninstaller works
- [ ] Test system requirements checking
- [ ] Verify all shortcuts work
- [ ] Check registry entries
- [ ] Review error messages
- [ ] Test auto-updater (if server ready)

## 🎨 Customization

### Installer Branding

Edit `electron-app/installer.nsh`:
- Change `APP_NAME`, `APP_PUBLISHER`, `APP_WEB_SITE`
- Customize welcome page text
- Modify component descriptions

### License Agreement

Edit `electron-app/LICENSE.txt` with your EULA.

### System Requirements

Adjust in `electron-app/system-check.js`:
```javascript
const MIN_RAM_GB = 4;
const MIN_DISK_SPACE_GB = 2;
```

## 📊 What Users See

### Installation
- Professional branded installer
- Clear progress indicators
- Helpful error messages
- Clean finish screen

### First Launch
- System requirements check (if issues, clear error)
- Automatic service startup
- Professional loading screen
- Native desktop window

### Updates
- Automatic background checking
- Non-intrusive notifications
- One-click update installation
- Option to skip versions

### Uninstallation
- Clean removal process
- Option to keep user data
- Complete registry cleanup

## 🔐 Security

### Code Signing Benefits
- ✅ No "Unknown Publisher" warnings
- ✅ Windows SmartScreen approval
- ✅ User trust and confidence
- ✅ Professional appearance

### Best Practices
- Never commit certificates to version control
- Use environment variables for passwords
- Store certificates securely
- Renew before expiration

## 📞 Support

### For Build Issues
- Check `BUILD_PRODUCTION.bat` output
- Review error messages
- Verify prerequisites installed
- See `electron-app/COMMERCIAL_FEATURES.md`

### For User Issues
- Check logs: `%APPDATA%\Powerhouse\data\powerhouse.log`
- Review system requirements output
- Check Windows Event Viewer
- Contact: support@powerhouse.ai

## 📈 Comparison

| Feature | Before | Now (Commercial) |
|---------|--------|------------------|
| Installer UI | Basic | Professional branded |
| System Checks | None | Automatic validation |
| Updates | Manual | Automatic |
| Code Signing | None | Ready/configured |
| Uninstaller | Basic | Complete cleanup |
| Registry | Minimal | Full integration |
| Error Handling | Basic | Comprehensive |
| User Experience | Good | Excellent |

## 🎯 Next Steps

1. **Test the build**: Run `BUILD_PRODUCTION.bat`
2. **Configure code signing**: See `code-signing.md`
3. **Set up update server**: Configure endpoint
4. **Test on clean machine**: Verify everything works
5. **Distribute**: Share with users

## 📚 Additional Documentation

- **Commercial Features**: `electron-app/COMMERCIAL_FEATURES.md`
- **Code Signing**: `electron-app/code-signing.md`
- **Quick Reference**: `BUILD_QUICK_REFERENCE.md`
- **Production Build**: `electron-app/README_PRODUCTION.md`

---

**Your Powerhouse installer is now commercial-grade and ready for professional distribution!** 🚀

