@echo off
REM ============================================================================
REM Powerhouse - Clean Reinstall Script
REM ============================================================================
REM This script performs a complete uninstall followed by a fresh installation.
REM Use this when you want to completely reset Powerhouse.
REM ============================================================================

echo.
echo ============================================================================
echo Powerhouse - Clean Reinstall
echo ============================================================================
echo.
echo This will:
echo 1. Uninstall Powerhouse completely
echo 2. Clean up all artifacts
echo 3. Perform a fresh installation
echo.
echo WARNING: This will delete all database data unless you choose to preserve it!
echo.

set /p CONFIRM="Are you sure you want to proceed? (yes/no): "

if /i not "%CONFIRM%"=="yes" (
    echo Reinstall cancelled.
    pause
    exit /b 0
)

REM ============================================================================
REM Step 1: Uninstall
REM ============================================================================

echo.
echo ============================================================================
echo Step 1: Uninstalling Powerhouse...
echo ============================================================================
echo.

call UNINSTALL.bat

if errorlevel 1 (
    echo.
    echo ERROR: Uninstall failed. Please check the errors above.
    pause
    exit /b 1
)

REM ============================================================================
REM Step 2: Pull Latest Code (if using Git)
REM ============================================================================

echo.
echo ============================================================================
echo Step 2: Updating code...
echo ============================================================================
echo.

if exist ".git" (
    echo Pulling latest code from Git...
    git pull origin main
    
    if errorlevel 1 (
        echo Warning: Git pull failed. Continuing with current code...
    )
) else (
    echo No Git repository found. Using current code...
)

echo.

REM ============================================================================
REM Step 3: Fresh Installation
REM ============================================================================

echo.
echo ============================================================================
echo Step 3: Installing Powerhouse...
echo ============================================================================
echo.

if exist "INSTALL.bat" (
    call INSTALL.bat
) else (
    echo ERROR: INSTALL.bat not found!
    echo Please run installation manually.
    pause
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo ERROR: Installation failed. Please check the errors above.
    pause
    exit /b 1
)

REM ============================================================================
REM Step 4: Start Services
REM ============================================================================

echo.
echo ============================================================================
echo Step 4: Starting services...
echo ============================================================================
echo.

set /p START_SERVICES="Start Powerhouse services now? (yes/no): "

if /i "%START_SERVICES%"=="yes" (
    echo.
    echo Starting Powerhouse...
    call START_POWERHOUSE_FULL.bat
) else (
    echo.
    echo Services not started. Start manually with: START_POWERHOUSE_FULL.bat
)

echo.
echo ============================================================================
echo Clean Reinstall Complete!
echo ============================================================================
echo.
echo Powerhouse has been:
echo - Uninstalled completely
echo - Reinstalled with latest code
echo - All dependencies updated
echo.
echo All 10 advanced AI features are enabled by default!
echo.
echo Access Powerhouse at:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:8001
echo - API Docs: http://localhost:8001/docs
echo.
echo ============================================================================

pause

