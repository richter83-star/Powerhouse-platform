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

REM Check if running in auto mode
set "AUTO_MODE=%1"
set "PRESERVE_DATA=%2"

echo.
echo ============================================================================
echo Powerhouse - Complete Uninstall
echo ============================================================================
echo.

REM Check if running from correct directory
if not exist "backend\requirements.txt" (
    echo ERROR: Please run this script from the POWERHOUSE_DEBUG directory!
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM ============================================================================
REM Step 1: Stop All Services
REM ============================================================================

echo [1/5] Stopping all services...
echo.

if exist "STOP_ALL.bat" (
    call STOP_ALL.bat
) else (
    echo Stopping Docker containers...
    docker-compose down 2>nul
    
    echo Stopping Python processes...
    taskkill /F /IM python.exe 2>nul
    
    echo Stopping Node.js processes...
    taskkill /F /IM node.exe 2>nul
)

timeout /t 3 /nobreak >nul
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
    docker-compose down -v 2>nul
    docker volume rm postgres_data redis_data 2>nul
    echo Database data deleted.
) else (
    echo Removing Docker containers (keeping volumes - data preserved)...
    docker-compose down 2>nul
    echo Database data preserved in Docker volumes.
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
    
    REM Try to uninstall packages
    echo Attempting to uninstall backend dependencies...
    pip uninstall -y -r requirements.txt 2>nul
    
    if errorlevel 1 (
        echo Warning: Some packages may not have been uninstalled.
        echo This is normal if packages are shared with other projects.
    ) else (
        echo Backend packages uninstalled successfully.
    )
) else (
    echo Warning: requirements.txt not found, skipping Python package uninstall.
)

cd ..

echo.

REM ============================================================================
REM Step 4: Remove Node.js Packages
REM ============================================================================

echo [4/5] Removing Node.js packages...
echo.

if exist "frontend\app\node_modules" (
    echo Removing frontend node_modules...
    rmdir /s /q "frontend\app\node_modules" 2>nul
    echo Frontend node_modules removed.
)

if exist "frontend\app\.next" (
    echo Removing Next.js build cache...
    rmdir /s /q "frontend\app\.next" 2>nul
)

if exist "electron-app\node_modules" (
    echo Removing Electron app node_modules...
    rmdir /s /q "electron-app\node_modules" 2>nul
    echo Electron node_modules removed.
)

if exist "electron-app\dist" (
    echo Removing Electron build artifacts...
    rmdir /s /q "electron-app\dist" 2>nul
)

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

exit /b 0

