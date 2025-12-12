@echo off
echo ============================================================================
echo Powerhouse - Simple Clean Reinstall
echo ============================================================================
echo.
echo This script will:
echo 1. Stop all services manually
echo 2. Remove Docker containers
echo 3. Install everything fresh
echo.
echo WARNING: This will delete all database data!
echo.
pause

REM Step 1: Stop everything
echo.
echo [1/3] Stopping services...
docker-compose down 2>nul
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul
echo Done.

REM Step 2: Remove Docker containers and volumes
echo.
echo [2/3] Removing Docker containers and volumes...
docker-compose down -v 2>nul
docker volume rm postgres_data redis_data 2>nul
echo Done.

REM Step 3: Run INSTALL.bat
echo.
echo [3/3] Running fresh installation...
echo This will take 5-10 minutes...
echo.
call INSTALL.bat

echo.
echo ============================================================================
echo Reinstall Complete!
echo ============================================================================
echo.
pause

