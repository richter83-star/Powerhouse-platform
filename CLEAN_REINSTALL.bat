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

:confirm_loop
set /p CONFIRM="Are you sure you want to proceed? (yes/no): "

if "%CONFIRM%"=="" (
    echo Please enter 'yes' or 'no'
    goto confirm_loop
)

if /i "%CONFIRM%"=="yes" goto proceed
if /i "%CONFIRM%"=="no" (
    echo Reinstall cancelled.
    pause
    exit /b 0
)

echo Invalid input. Please enter 'yes' or 'no'
goto confirm_loop

:proceed

REM ============================================================================
REM Step 1: Uninstall
REM ============================================================================

echo.
echo ============================================================================
echo Step 1: Uninstalling Powerhouse...
echo ============================================================================
echo.
echo This will:
echo - Stop all services
echo - Remove Docker containers
echo - Uninstall Python packages
echo - Remove Node.js packages
echo - Clean up artifacts
echo.

set /p PRESERVE_DATA_OPTION="Do you want to preserve database data? (yes/no - default: no): "

echo.
if /i "%PRESERVE_DATA_OPTION%"=="yes" (
    echo [INFO] Calling uninstall with data preservation...
    echo [INFO] Command: UNINSTALL.bat auto preserve_data
    call UNINSTALL.bat auto preserve_data
) else (
    echo [INFO] Calling uninstall (data will be deleted)...
    echo [INFO] Command: UNINSTALL.bat auto
    call UNINSTALL.bat auto
)

echo.
echo [INFO] Uninstall script finished. Return code: %ERRORLEVEL%

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

:start_services_loop
set /p START_SERVICES="Start Powerhouse services now? (yes/no): "

if "%START_SERVICES%"=="" (
    echo Please enter 'yes' or 'no'
    goto start_services_loop
)

if /i "%START_SERVICES%"=="yes" (
    echo.
    echo Starting Powerhouse...
    call START_POWERHOUSE_FULL.bat
    goto services_done
)

if /i "%START_SERVICES%"=="no" (
    echo.
    echo Services not started. Start manually with: START_POWERHOUSE_FULL.bat
    goto services_done
)

echo Invalid input. Please enter 'yes' or 'no'
goto start_services_loop

:services_done

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

