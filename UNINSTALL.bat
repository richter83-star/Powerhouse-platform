@echo off
REM ============================================================================
REM Powerhouse - Complete Uninstall Script
REM ============================================================================
REM This script safely uninstalls Powerhouse, including:
REM - Docker containers and volumes
REM - Python packages
REM - Node.js packages
REM - Build artifacts
REM ============================================================================
REM Usage: UNINSTALL.bat [auto] [preserve_data]
REM   auto - Skip all prompts (use defaults)
REM   preserve_data - Keep database data (only works with auto)
REM ============================================================================

setlocal enabledelayedexpansion

REM Logging setup
set "LOG_FILE=%~dp0.cursor\debug.log"
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='UNINSTALL.bat:ENTRY';message='UNINSTALL script entry';data=@{autoMode='%1';preserveData='%2'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

REM Check if running in auto mode
set "AUTO_MODE=%1"
set "PRESERVE_DATA=%2"

echo.
echo ============================================================================
echo Powerhouse - Complete Uninstall
echo ============================================================================
if /i "%AUTO_MODE%"=="auto" (
    echo Running in AUTO mode (no prompts)
    if /i "%PRESERVE_DATA%"=="preserve_data" (
        echo Data preservation: ENABLED
    ) else (
        echo Data preservation: DISABLED (data will be deleted)
    )
) else (
    echo Running in INTERACTIVE mode
)
echo.

REM Check if running from correct directory
powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='UNINSTALL.bat:42';message='Checking directory';data=@{currentDir='%CD%';checkingFor='backend\requirements.txt'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

if not exist "backend\requirements.txt" (
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='UNINSTALL.bat:44';message='ERROR: Wrong directory';data=@{currentDir='%CD%';action='exit'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    echo [ERROR] Please run this script from the POWERHOUSE_DEBUG directory!
    echo [ERROR] Current directory: %CD%
    echo [ERROR] Looking for: backend\requirements.txt
    if /i not "%AUTO_MODE%"=="auto" (
        pause
    )
    powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='UNINSTALL.bat:52';message='UNINSTALL exiting with error code 1';data=@{exitCode=1};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1
    endlocal
    exit /b 1
)

powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='UNINSTALL.bat:56';message='Directory check passed';data=@{action='continue'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

REM ============================================================================
REM Step 1: Stop All Services
REM ============================================================================

powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='UNINSTALL.bat:64';message='Starting Step 1: Stop Services';data=@{step='1'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

echo [1/5] Stopping all services...
echo.

echo Stopping Docker containers...
docker-compose down 2>nul
if errorlevel 1 (
    echo Warning: Docker compose down failed (containers may not be running)
) else (
    echo Docker containers stopped successfully.
)

echo Stopping backend processes...
taskkill /F /FI "WINDOWTITLE eq Powerhouse - Backend*" 2>nul
taskkill /F /FI "WINDOWTITLE eq *app.py*" 2>nul

echo Stopping frontend processes...
taskkill /F /FI "WINDOWTITLE eq Powerhouse - Frontend*" 2>nul
taskkill /F /FI "WINDOWTITLE eq *next*" 2>nul

echo Stopping Python processes...
taskkill /F /IM python.exe 2>nul
if errorlevel 1 (
    echo No Python processes found running.
) else (
    echo Python processes stopped.
)

echo Stopping Node.js processes...
taskkill /F /IM node.exe 2>nul
if errorlevel 1 (
    echo No Node.js processes found running.
) else (
    echo Node.js processes stopped.
)

echo Waiting 3 seconds for processes to fully stop...
timeout /t 3 /nobreak >nul

powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='UNINSTALL.bat:95';message='Step 1 complete';data=@{step='1_complete'};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

echo [OK] Services stopped.
echo.

REM ============================================================================
REM Step 2: Remove Docker Containers and Volumes
REM ============================================================================

echo [2/5] Removing Docker containers and volumes...
echo.

REM Ask user about data preservation
if /i "%AUTO_MODE%"=="auto" (
    if /i "%PRESERVE_DATA%"=="preserve_data" (
        set "DELETE_DATA=no"
        echo Auto mode: Preserving database data...
    ) else (
        set "DELETE_DATA=yes"
        echo Auto mode: Deleting database data...
    )
    set "REMOVE_IMAGES=no"
) else (
    set /p DELETE_DATA="Do you want to DELETE all database data? (yes/no): "
    if "%DELETE_DATA%"=="" set "DELETE_DATA=no"
    
    set /p REMOVE_IMAGES="Remove Docker images? (yes/no): "
    if "%REMOVE_IMAGES%"=="" set "REMOVE_IMAGES=no"
)

if /i "!DELETE_DATA!"=="yes" (
    echo Removing Docker containers and volumes (this deletes all data!)...
    docker-compose down -v
    if errorlevel 1 (
        echo Warning: docker-compose down -v failed
    ) else (
        echo Docker containers and volumes removed.
    )
    docker volume rm postgres_data redis_data 2>nul
    if errorlevel 1 (
        echo Warning: Some volumes may not exist or are still in use
    ) else (
        echo Database volumes deleted.
    )
    echo [OK] Database data deleted.
) else (
    echo Removing Docker containers (keeping volumes - data preserved)...
    docker-compose down
    if errorlevel 1 (
        echo Warning: docker-compose down failed (containers may not exist)
    ) else (
        echo Docker containers removed.
    )
    echo [OK] Database data preserved in Docker volumes.
)

if /i "!REMOVE_IMAGES!"=="yes" (
    docker rmi powerhouse_backend powerhouse_frontend 2>nul
    echo Docker images removed.
)

echo.

REM ============================================================================
REM Step 3: Uninstall Python Packages
REM ============================================================================

echo [3/5] Uninstalling Python packages...
echo.

cd backend

if exist "requirements.txt" (
    echo Reading requirements.txt...
    echo Attempting to uninstall backend dependencies...
    echo This may take a moment...
    pip uninstall -y -r requirements.txt
    
    if errorlevel 1 (
        echo Warning: Some packages may not have been uninstalled.
        echo This is normal if packages are shared with other projects or not installed.
    ) else (
        echo [OK] Backend packages uninstalled successfully.
    )
) else (
    echo Warning: requirements.txt not found in backend directory
    echo Skipping Python package uninstall.
)

cd ..
echo [OK] Step 3 complete.

echo.

REM ============================================================================
REM Step 4: Remove Node.js Packages
REM ============================================================================

echo [4/5] Removing Node.js packages...
echo.

if exist "frontend\app\node_modules" (
    echo Removing frontend node_modules...
    rmdir /s /q "frontend\app\node_modules" 2>nul
    if exist "frontend\app\node_modules" (
        echo Warning: Failed to remove frontend node_modules completely
    ) else (
        echo [OK] Frontend node_modules removed.
    )
) else (
    echo Frontend node_modules not found (may already be removed).
)

if exist "frontend\app\.next" (
    echo Removing Next.js build cache...
    rmdir /s /q "frontend\app\.next" 2>nul
    echo [OK] Next.js build cache removed.
)

if exist "electron-app\node_modules" (
    echo Removing Electron app node_modules...
    rmdir /s /q "electron-app\node_modules" 2>nul
    if exist "electron-app\node_modules" (
        echo Warning: Failed to remove Electron node_modules completely
    ) else (
        echo [OK] Electron node_modules removed.
    )
) else (
    echo Electron node_modules not found (may already be removed).
)

if exist "electron-app\dist" (
    echo Removing Electron build artifacts...
    rmdir /s /q "electron-app\dist" 2>nul
    echo [OK] Electron build artifacts removed.
)

echo [OK] Step 4 complete.

echo.

REM ============================================================================
REM Step 5: Clean Up Artifacts
REM ============================================================================

echo [5/5] Cleaning up artifacts...
echo.

if /i "%AUTO_MODE%"=="auto" (
    set "CLEAN_CACHE=yes"
    set "REMOVE_ENV=no"
    echo Auto mode: Cleaning cache, preserving .env files...
) else (
    set /p CLEAN_CACHE="Remove Python cache and build artifacts? (yes/no): "
    if "!CLEAN_CACHE!"=="" set "CLEAN_CACHE=yes"
    
    set /p REMOVE_ENV="Remove .env files? (yes/no - recommended: no if you want to keep config): "
    if "!REMOVE_ENV!"=="" set "REMOVE_ENV=no"
)

if /i "!CLEAN_CACHE!"=="yes" (
    echo Removing Python cache files...
    for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
    del /s /q *.pyc 2>nul
    
    echo Removing build artifacts...
    del /s /q *.egg-info 2>nul
    
    echo Cache and artifacts removed.
) else (
    echo Skipping cache cleanup.
)

echo.

REM ============================================================================
REM Optional: Remove Environment Files
REM ============================================================================

if /i "!REMOVE_ENV!"=="yes" (
    echo Removing environment files...
    del backend\.env 2>nul
    del frontend\app\.env.local 2>nul
    del frontend\app\.env 2>nul
    echo Environment files removed.
) else (
    echo Environment files preserved.
)

echo.

REM ============================================================================
REM Summary
REM ============================================================================

echo.
echo ============================================================================
echo Uninstall Complete!
echo ============================================================================
echo.
echo Summary:
echo - Docker containers stopped and removed
if /i "%DELETE_DATA%"=="yes" (
    echo - Database data DELETED
) else (
    echo - Database data PRESERVED in Docker volumes
)
echo - Python packages uninstalled
echo - Node.js packages removed
if /i "%CLEAN_CACHE%"=="yes" (
    echo - Cache and artifacts cleaned
)
if /i "%REMOVE_ENV%"=="yes" (
    echo - Environment files removed
) else (
    echo - Environment files preserved
)
echo.
echo To reinstall Powerhouse:
echo 1. Run: INSTALL.bat
echo 2. Run: START_POWERHOUSE_FULL.bat
echo.
echo ============================================================================

REM Only pause if not in auto mode
if /i not "%AUTO_MODE%"=="auto" (
    pause
)

powershell -Command "$logPath = '%LOG_FILE%'; $log = @{timestamp=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();location='UNINSTALL.bat:326';message='UNINSTALL script about to exit';data=@{exitCode=0};sessionId='debug-session';runId='run1';hypothesisId='D'} | ConvertTo-Json -Compress; Add-Content -Path $logPath -Value $log" >nul 2>&1

endlocal
exit /b 0

