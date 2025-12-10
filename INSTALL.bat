@echo off
title Powerhouse - One-Click Installer
color 0B
setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo ================================================================
echo   POWERHOUSE - ONE-CLICK INSTALLER
echo ================================================================
echo.
echo This will install everything you need to run Powerhouse.
echo Estimated time: 5-10 minutes
echo.
pause

REM Create log file
set "LOG_FILE=%SCRIPT_DIR%install_log.txt"
echo Installation Log - %date% %time% > "%LOG_FILE%"
echo ================================================================ >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM ================================================================
REM STEP 1: Check Prerequisites
REM ================================================================
echo.
echo [STEP 1/6] Checking Prerequisites...
echo [STEP 1/6] Checking Prerequisites... >> "%LOG_FILE%"
echo.

set "ERRORS=0"

REM Check folder structure
if not exist "backend" (
    echo [ERROR] Backend folder not found!
    echo [ERROR] Backend folder not found! >> "%LOG_FILE%"
    set /a ERRORS+=1
)
if not exist "frontend" (
    echo [ERROR] Frontend folder not found!
    echo [ERROR] Frontend folder not found! >> "%LOG_FILE%"
    set /a ERRORS+=1
)

if !ERRORS! GTR 0 (
    echo.
    echo Please make sure you extracted the full project to: %CD%
    echo.
    pause
    exit /b 1
)

REM Check Python
echo Checking Python...
python --version >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.11+ is required but not found
    echo [ERROR] Python 3.11+ is required but not found >> "%LOG_FILE%"
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    set /a ERRORS+=1
) else (
    python --version
    echo [OK] Python found
)

REM Check Node.js
echo Checking Node.js...
node --version >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js 18+ is required but not found
    echo [ERROR] Node.js 18+ is required but not found >> "%LOG_FILE%"
    echo Please install Node.js from https://nodejs.org/
    set /a ERRORS+=1
) else (
    node --version
    echo [OK] Node.js found
)

REM Check npm
echo Checking npm...
npm --version >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] npm is required but not found
    echo [ERROR] npm is required but not found >> "%LOG_FILE%"
    set /a ERRORS+=1
) else (
    npm --version
    echo [OK] npm found
)

REM Check Docker (optional but recommended)
echo Checking Docker...
docker --version >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARN] Docker not found - database will need manual setup
    echo [WARN] Docker not found >> "%LOG_FILE%"
) else (
    docker ps >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [WARN] Docker installed but not running
        echo [WARN] Docker installed but not running >> "%LOG_FILE%"
        echo Please start Docker Desktop before starting the database
    ) else (
        docker --version
        echo [OK] Docker is running
    )
)

if !ERRORS! GTR 0 (
    echo.
    echo Please fix the errors above and run this installer again.
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] All prerequisites met!
echo.

REM ================================================================
REM STEP 2: Install Backend Dependencies
REM ================================================================
echo.
echo [STEP 2/6] Installing Backend Dependencies...
echo [STEP 2/6] Installing Backend Dependencies... >> "%LOG_FILE%"
echo This may take 3-5 minutes...
echo.

pushd "%SCRIPT_DIR%backend"
if errorlevel 1 (
    echo [ERROR] Cannot access backend folder
    echo [ERROR] Cannot access backend folder >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Remove old venv if exists
if exist "venv\" (
    echo Removing old virtual environment...
    rmdir /s /q venv 2>nul
)

REM Create virtual environment
echo Creating Python virtual environment...
python -m venv venv >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    echo [ERROR] Failed to create virtual environment >> "%LOG_FILE%"
    popd
    pause
    exit /b 1
)

REM Activate and upgrade pip
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Upgrading pip...
python -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1

REM Install requirements
echo Installing Python packages (this may take a few minutes)...
python -m pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install Python packages
    echo [ERROR] Failed to install Python packages >> "%LOG_FILE%"
    echo Check install_log.txt for details
    popd
    pause
    exit /b 1
)

echo [OK] Backend dependencies installed
popd

REM ================================================================
REM STEP 3: Install Frontend Dependencies
REM ================================================================
echo.
echo [STEP 3/6] Installing Frontend Dependencies...
echo [STEP 3/6] Installing Frontend Dependencies... >> "%LOG_FILE%"
echo This may take 3-5 minutes...
echo.

pushd "%SCRIPT_DIR%frontend\app"
if errorlevel 1 (
    echo [ERROR] Cannot access frontend/app folder
    echo [ERROR] Cannot access frontend/app folder >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo Installing Node.js packages...
call npm install >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js packages
    echo [ERROR] Failed to install Node.js packages >> "%LOG_FILE%"
    echo Check install_log.txt for details
    popd
    pause
    exit /b 1
)

echo [OK] Frontend dependencies installed
popd

REM ================================================================
REM STEP 4: Create .env files if they don't exist
REM ================================================================
echo.
echo [STEP 4/6] Setting up environment files...
echo [STEP 4/6] Setting up environment files... >> "%LOG_FILE%"

REM Check for backend .env
if not exist "%SCRIPT_DIR%backend\.env" (
    echo Creating backend .env file...
    if exist "%SCRIPT_DIR%backend\.env.example" (
        copy "%SCRIPT_DIR%backend\.env.example" "%SCRIPT_DIR%backend\.env" >nul
        echo [OK] Created backend/.env from .env.example
    ) else (
        echo [INFO] No .env.example found - you may need to create .env manually
    )
) else (
    echo [OK] Backend .env already exists
)

REM Check for frontend .env
if not exist "%SCRIPT_DIR%frontend\app\.env.local" (
    echo Creating frontend .env.local file...
    if exist "%SCRIPT_DIR%frontend\app\.env.example" (
        copy "%SCRIPT_DIR%frontend\app\.env.example" "%SCRIPT_DIR%frontend\app\.env.local" >nul
        echo [OK] Created frontend/app/.env.local from .env.example
    ) else (
        echo [INFO] No .env.example found - you may need to create .env.local manually
    )
) else (
    echo [OK] Frontend .env.local already exists
)

REM ================================================================
REM STEP 5: Verify Installation
REM ================================================================
echo.
echo [STEP 5/6] Verifying Installation...
echo [STEP 5/6] Verifying Installation... >> "%LOG_FILE%"

set "VERIFY_ERRORS=0"

REM Check backend venv
if not exist "%SCRIPT_DIR%backend\venv\Scripts\python.exe" (
    echo [ERROR] Backend virtual environment not properly created
    set /a VERIFY_ERRORS+=1
) else (
    echo [OK] Backend virtual environment verified
)

REM Check frontend node_modules
if not exist "%SCRIPT_DIR%frontend\app\node_modules" (
    echo [ERROR] Frontend node_modules not found
    set /a VERIFY_ERRORS+=1
) else (
    echo [OK] Frontend node_modules verified
)

if !VERIFY_ERRORS! GTR 0 (
    echo.
    echo [WARN] Some verification checks failed. Installation may be incomplete.
    echo Check install_log.txt for details.
    echo.
) else (
    echo [OK] Installation verified successfully!
)

REM ================================================================
REM STEP 6: Setup Complete
REM ================================================================
echo.
echo [STEP 6/6] Installation Complete!
echo.
echo ================================================================
echo   INSTALLATION COMPLETE!
echo ================================================================
echo.
echo Log file: install_log.txt
echo.
echo NEXT STEPS:
echo.
echo 1. Start the database:
echo    Double-click: 1_START_DATABASE.bat
echo    (Wait for it to finish, then close the window)
echo.
echo 2. Start the backend:
echo    Double-click: 2_START_BACKEND.bat
echo    (Keep this window open)
echo.
echo 3. Start the frontend:
echo    Double-click: 3_START_FRONTEND.bat
echo    (Keep this window open)
echo.
echo OR use the all-in-one launcher:
echo    Double-click: START_POWERHOUSE_FULL.bat
echo.
echo 4. Open your browser:
echo    http://localhost:3000
echo.
echo ================================================================
echo.
echo Would you like to start Powerhouse now? (Y/N)
set /p START_NOW="> "

if /i "!START_NOW!"=="Y" (
    echo.
    echo Starting Powerhouse...
    if exist "%SCRIPT_DIR%START_POWERHOUSE_FULL.bat" (
        call "%SCRIPT_DIR%START_POWERHOUSE_FULL.bat"
    ) else (
        echo Launcher not found. Please start services manually.
    )
) else (
    echo.
    echo You can start Powerhouse anytime by running:
    echo   START_POWERHOUSE_FULL.bat
    echo.
)

echo.
echo Installation complete! Check install_log.txt if you encounter any issues.
echo.
pause

