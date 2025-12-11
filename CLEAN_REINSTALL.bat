@echo off
setlocal enabledelayedexpansion
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

:preserve_data_loop
set /p PRESERVE_DATA_OPTION="Do you want to preserve database data? (yes/no - default: no): "

if "%PRESERVE_DATA_OPTION%"=="" (
    echo Using default: no (database data will be deleted)
    set "PRESERVE_DATA_OPTION=no"
)

if /i "%PRESERVE_DATA_OPTION%"=="yes" goto preserve_yes
if /i "%PRESERVE_DATA_OPTION%"=="no" goto preserve_no

echo Invalid input. Please enter 'yes' or 'no' (or press Enter for default: no)
goto preserve_data_loop

:preserve_yes
echo.
echo [INFO] Calling uninstall with data preservation...
echo [INFO] Command: UNINSTALL.bat auto preserve_data
echo.
call UNINSTALL.bat auto preserve_data
set "UNINSTALL_RESULT=%ERRORLEVEL%"
goto uninstall_done

:preserve_no
echo.
echo [INFO] Calling uninstall (data will be deleted)...
echo [INFO] Command: UNINSTALL.bat auto
echo.
call UNINSTALL.bat auto
set "UNINSTALL_RESULT=%ERRORLEVEL%"

:uninstall_done
echo.
echo ============================================================================
echo [INFO] Uninstall script finished. Return code: %UNINSTALL_RESULT%
echo ============================================================================
echo.

if !UNINSTALL_RESULT! NEQ 0 (
    echo [ERROR] Uninstall returned error code !UNINSTALL_RESULT!
    echo The uninstall may have had issues, but continuing anyway...
    echo.
    pause
)

REM Error checking moved to after the call, using UNINSTALL_RESULT variable

REM ============================================================================
REM Step 2: Pull Latest Code (if using Git)
REM ============================================================================

echo.
echo ============================================================================
echo Step 2: Updating code...
echo ============================================================================
echo.

if exist ".git" (
    echo [INFO] Pulling latest code from Git...
    git pull origin main
    
    if errorlevel 1 (
        echo [WARN] Git pull failed. Continuing with current code...
        echo [WARN] This is OK if you're already up to date or not connected to remote.
    ) else (
        echo [OK] Git pull successful.
    )
) else (
    echo [INFO] No Git repository found. Using current code...
)

echo [OK] Step 2 complete.
echo.

REM ============================================================================
REM Step 3: Fresh Installation
REM ============================================================================

echo.
echo ============================================================================
echo Step 3: Installing Powerhouse...
echo ============================================================================
echo.

if not exist "INSTALL.bat" (
    echo [ERROR] INSTALL.bat not found!
    echo [ERROR] Please make sure you're in the POWERHOUSE_DEBUG directory.
    echo [ERROR] Current directory: %CD%
    pause
    exit /b 1
)

echo [INFO] Starting installation...
echo [INFO] This may take 5-10 minutes...
echo.
call INSTALL.bat
set "INSTALL_RESULT=%ERRORLEVEL%"

echo.
echo [INFO] Installation script finished. Return code: %INSTALL_RESULT%
echo.

if !INSTALL_RESULT! NEQ 0 (
    echo [ERROR] Installation returned error code !INSTALL_RESULT!
    echo [ERROR] Please check the errors above.
    echo.
    echo Do you want to continue anyway? (yes/no)
    set /p CONTINUE_ANYWAY="> "
    if /i not "!CONTINUE_ANYWAY!"=="yes" (
        pause
        exit /b 1
    )
    echo [WARN] Continuing despite installation errors...
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

