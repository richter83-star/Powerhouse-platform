@echo off
title Powerhouse - Quick Launch
color 0A

cd /d "%~dp0"

echo ================================================================
echo   POWERHOUSE - QUICK LAUNCH
echo ================================================================
echo.

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo.
    echo Please start Docker Desktop first, then run this script again.
    echo.
    pause
    exit /b 1
)

echo Checking services...
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo Services are not running. Starting...
    echo.
    docker-compose up -d
    if errorlevel 1 (
        echo [ERROR] Failed to start services
        pause
        exit /b 1
    )
    echo.
    echo Waiting for services to initialize...
    timeout /t 10 /nobreak >nul
) else (
    echo [OK] Services are already running
)

echo.
echo ================================================================
echo   POWERHOUSE IS READY!
echo ================================================================
echo.
echo Opening browser...
echo.
start http://localhost:3000
echo.
echo Access your application at:
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8001
echo.
echo To stop services: docker-compose down
echo.
pause

