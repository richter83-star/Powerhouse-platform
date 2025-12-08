@echo off
echo =============================================
echo   BUILDING POWERHOUSE ELECTRON APP
echo =============================================
echo.
echo This will create a Windows installer (.exe)
echo Size: ~150-200 MB
echo Time: 5-10 minutes
echo.
pause
echo.
echo [1/4] Installing Electron dependencies...
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo.
echo [2/4] Copying project files...
echo (This happens automatically during build)
echo.
echo [3/4] Building Electron app...
echo This will take several minutes...
call npm run dist-win
if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)
echo.
echo [4/4] Build complete!
echo.
echo =============================================
echo   SUCCESS!
echo =============================================
echo.
echo Installer location:
echo %cd%\dist\Powerhouse Setup 1.0.0.exe
echo.
echo You can now:
echo 1. Install the app on this computer
echo 2. Copy the installer to other computers
echo 3. Share the installer with team members
echo.
echo Note: Users still need Docker Desktop installed!
echo.
pause
