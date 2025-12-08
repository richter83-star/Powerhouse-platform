@echo off
title Powerhouse - Installation (FIXED)
color 0F

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ================================================================
echo   POWERHOUSE INSTALLATION
echo ================================================================
echo.
echo Current directory: %CD%
echo.
echo Checking folder structure...
echo.

if not exist "backend" (
    echo [ERROR] Backend folder not found!
    echo.
    echo Expected: %CD%\backend
    echo.
    echo Please make sure you:
    echo 1. Extracted the FULL zip file
    echo 2. Are running this from the POWERHOUSE_DEBUG folder
    echo 3. Did not move or rename folders
    echo.
    echo Current folder contents:
    dir /b
    echo.
    pause
    exit /b 1
)

if not exist "frontend" (
    echo [ERROR] Frontend folder not found!
    echo.
    echo Expected: %CD%\frontend
    echo.
    pause
    exit /b 1
)

echo [OK] Folder structure is correct!
echo   - backend: EXISTS
    echo   - frontend: EXISTS
echo.
pause

REM Create log file
echo Installation Log - %date% %time% > install_log.txt
echo. >> install_log.txt
echo Script directory: %SCRIPT_DIR% >> install_log.txt
echo Current directory: %CD% >> install_log.txt
echo. >> install_log.txt

REM Check Docker
echo.
echo [1/5] Checking Docker Desktop...
echo [1/5] Checking Docker Desktop... >> install_log.txt
docker --version >> install_log.txt 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    echo [ERROR] Docker is not installed or not in PATH >> install_log.txt
    echo.
    echo Check install_log.txt for details
    pause
    exit /b 1
)
docker ps >> install_log.txt 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running
    echo [ERROR] Docker Desktop is not running >> install_log.txt
    echo Please start Docker Desktop and try again
    echo.
    echo Check install_log.txt for details
    pause
    exit /b 1
)
echo [OK] Docker is ready
echo [OK] Docker is ready >> install_log.txt

REM Check Python
echo.
echo [2/5] Checking Python...
echo [2/5] Checking Python... >> install_log.txt
python --version >> install_log.txt 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo [ERROR] Python is not installed or not in PATH >> install_log.txt
    echo.
    echo Check install_log.txt for details
    pause
    exit /b 1
)
echo [OK] Python is ready
echo [OK] Python is ready >> install_log.txt

REM Check Node.js
echo.
echo [3/5] Checking Node.js...
echo [3/5] Checking Node.js... >> install_log.txt
node --version >> install_log.txt 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo [ERROR] Node.js is not installed or not in PATH >> install_log.txt
    echo.
    echo Check install_log.txt for details
    pause
    exit /b 1
)
echo [OK] Node.js is ready
echo [OK] Node.js is ready >> install_log.txt

REM Install Backend
echo.
echo [4/5] Installing Backend dependencies...
echo [4/5] Installing Backend dependencies... >> install_log.txt
echo.
echo Current directory before cd: %CD% >> install_log.txt
echo Attempting to change to backend folder... >> install_log.txt

pushd "%SCRIPT_DIR%backend"
if errorlevel 1 (
    echo [ERROR] Failed to enter backend folder
    echo [ERROR] Failed to enter backend folder >> "%SCRIPT_DIR%install_log.txt"
    echo Backend path: %SCRIPT_DIR%backend >> "%SCRIPT_DIR%install_log.txt"
    pause
    exit /b 1
)

echo Successfully changed to: %CD% >> "%SCRIPT_DIR%install_log.txt"

REM Remove old venv if exists
if exist "venv\" (
    echo Removing old virtual environment...
    echo Removing old virtual environment... >> "%SCRIPT_DIR%install_log.txt"
    rmdir /s /q venv
)

echo Creating Python virtual environment...
echo Creating Python virtual environment... >> "%SCRIPT_DIR%install_log.txt"
python -m venv venv >> "%SCRIPT_DIR%install_log.txt" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    echo [ERROR] Failed to create virtual environment >> "%SCRIPT_DIR%install_log.txt"
    popd
    echo.
    echo Check install_log.txt for details
    pause
    exit /b 1
)

echo Activating virtual environment...
echo Activating virtual environment... >> "%SCRIPT_DIR%install_log.txt"
call venv\Scripts\activate.bat

echo Installing Python packages (this may take a few minutes)...
echo Installing Python packages... >> "%SCRIPT_DIR%install_log.txt"
python -m pip install --upgrade pip >> "%SCRIPT_DIR%install_log.txt" 2>&1
python -m pip install -r requirements.txt >> "%SCRIPT_DIR%install_log.txt" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install Python packages
    echo [ERROR] Failed to install Python packages >> "%SCRIPT_DIR%install_log.txt"
    echo.
    echo Check install_log.txt for the specific error
    echo.
    echo Common causes:
    echo - Internet connection issues
    echo - Firewall blocking pip
    echo - Missing build tools for some packages
    echo.
    popd
    pause
    exit /b 1
)

echo [OK] Backend installed successfully
echo [OK] Backend installed successfully >> "%SCRIPT_DIR%install_log.txt"
popd

REM Install Frontend
echo.
echo [5/5] Installing Frontend dependencies...
echo [5/5] Installing Frontend dependencies... >> install_log.txt

pushd "%SCRIPT_DIR%frontend\app"
if errorlevel 1 (
    echo [ERROR] Failed to enter frontend/app folder
    echo [ERROR] Failed to enter frontend/app folder >> "%SCRIPT_DIR%install_log.txt"
    pause
    exit /b 1
)

echo Installing Node.js packages (this may take several minutes)...
echo Installing Node.js packages... >> "%SCRIPT_DIR%install_log.txt"
npm install >> "%SCRIPT_DIR%install_log.txt" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js packages
    echo [ERROR] Failed to install Node.js packages >> "%SCRIPT_DIR%install_log.txt"
    popd
    echo.
    echo Check install_log.txt for details
    pause
    exit /b 1
)

echo [OK] Frontend installed successfully
echo [OK] Frontend installed successfully >> "%SCRIPT_DIR%install_log.txt"
popd

echo.
echo ================================================================
echo   INSTALLATION COMPLETE!
echo ================================================================
echo.
echo Log file created: install_log.txt
echo.
echo To start Powerhouse:
echo   1. Double-click: 1_START_DATABASE.bat
echo   2. Double-click: 2_START_BACKEND.bat
echo   3. Double-click: 3_START_FRONTEND.bat
echo.
echo Then open: http://localhost:3000
echo.
pause
