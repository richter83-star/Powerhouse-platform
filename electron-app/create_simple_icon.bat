@echo off
title Create Icon for Electron App
echo =============================================
echo   CREATING PLACEHOLDER ICON
echo =============================================
echo.

cd /d "%~dp0"

REM Create build directory if it doesn't exist
if not exist "build" mkdir build

REM Check if we can use Python to create a proper icon
python --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Python not found. Creating minimal placeholder...
    echo [WARNING] This is a placeholder. Replace with real icon.ico for production.
    REM Create a minimal ICO file (just header)
    (
        echo 00 00 01 00 01 00 20 20 00 00 01 00 20 00 28 10
        echo 00 00 16 00 00 00 28 00 00 00 20 00 00 00 40 00
        echo 00 00 01 00 20 00 00 00 00 00 00 10 00 00 00 00
        echo 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    ) > build\icon.ico
    echo [OK] Placeholder icon created at: build\icon.ico
    echo.
    echo IMPORTANT: Replace build\icon.ico with your actual application icon!
    echo.
    pause
    exit /b 0
)

REM Try to create icon using Python
echo [INFO] Attempting to create icon using Python...
python create_icon.py 2>nul
if errorlevel 1 (
    echo [WARNING] Failed to create icon with Python. Creating placeholder...
    REM Create minimal placeholder
    (
        echo 00 00 01 00
    ) > build\icon.ico
    echo [OK] Placeholder created at: build\icon.ico
    echo.
    echo IMPORTANT: Replace build\icon.ico with your actual application icon!
) else (
    echo [OK] Icon created successfully!
)

echo.
pause

