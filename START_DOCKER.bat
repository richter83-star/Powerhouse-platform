@echo off
title Powerhouse - Start Services (Docker)
color 0A

cd /d "%~dp0"

echo ================================================================
echo   STARTING POWERHOUSE (DOCKER)
echo ================================================================
echo.

docker-compose ps | findstr "Up" >nul
if errorlevel 0 (
    echo Services are already running!
    echo.
    docker-compose ps
    echo.
    pause
    exit /b 0
)

echo Starting all services...
docker-compose up -d

if errorlevel 1 (
    echo [ERROR] Failed to start services
    echo.
    echo Make sure Docker Desktop is running!
    pause
    exit /b 1
)

echo.
echo [OK] Services starting...
echo.
echo Waiting for services to initialize...
timeout /t 10 /nobreak >nul

echo.
echo ================================================================
echo   SERVICES STARTED!
echo ================================================================
echo.
echo Access your application:
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8001
echo.
echo Services may take 20-30 seconds to fully start.
echo.
echo To check status:  docker-compose ps
echo To view logs:     docker-compose logs -f
echo To stop:          docker-compose down
echo.
pause

