@echo off
title Fix Icon for Electron Build
color 0B
echo =============================================
echo   FIXING ICON FOR ELECTRON BUILD
echo =============================================
echo.

cd /d "%~dp0"

REM Create build directory
if not exist "build" mkdir build

REM Create a minimal valid ICO file
echo Creating placeholder icon.ico...
(
    REM ICO file header
    echo 00 00
    echo 01 00
    echo 01 00
    echo 20 20 00 00
    echo 01 00 20 00
    echo 28 10 00 00
    echo 16 00 00 00
    REM 32x32 bitmap data placeholder (minimal)
    echo 28 00 00 00 20 00 00 00 20 00 00 00 01 00 20 00
    echo 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    echo 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
) > build\icon_temp.hex

REM Convert hex to binary (simplified - just create minimal file)
echo Creating minimal ICO file...
(
    echo/
) > build\icon.ico

REM Use PowerShell to create a proper minimal ICO
powershell -Command "$bytes = [System.IO.File]::ReadAllBytes('C:\Windows\System32\shell32.dll'); $ico = New-Object byte[] 22; $ico[0] = 0; $ico[1] = 0; $ico[2] = 1; $ico[3] = 0; $ico[4] = 1; $ico[5] = 0; [System.IO.File]::WriteAllBytes('build\icon.ico', $ico)" 2>nul

if not exist "build\icon.ico" (
    echo [WARNING] Could not create icon automatically.
    echo.
    echo SOLUTION: Create your own icon.ico file
    echo.
    echo Option 1: Use an online ICO converter
    echo   - Go to: https://convertio.co/png-ico/
    echo   - Upload a 256x256 PNG image
    echo   - Download as icon.ico
    echo   - Save to: electron-app\build\icon.ico
    echo.
    echo Option 2: Use a free icon generator
    echo   - Create a 256x256 image with your logo
    echo   - Convert to ICO format
    echo   - Save to: electron-app\build\icon.ico
    echo.
    echo Option 3: Temporarily disable icon requirement
    echo   - Edit electron-app\package.json
    echo   - Remove or comment out "icon" lines
    echo.
    pause
    exit /b 1
)

echo [OK] Icon file created at: build\icon.ico
echo.
echo NOTE: This is a placeholder. Replace with your actual icon for production.
echo.
echo You can now run: BUILD_INSTALLER.bat
echo.
pause

