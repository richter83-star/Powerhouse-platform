@echo off
title Powerhouse - Stop All Services
color 0E
echo ========================================
echo   STOPPING POWERHOUSE
echo ========================================
echo.

echo Stopping Docker containers...
docker-compose down
echo.

echo Stopping backend processes...
taskkill /F /FI "WINDOWTITLE eq Powerhouse - Backend*" 2>nul
taskkill /F /FI "WINDOWTITLE eq *app.py*" 2>nul
echo.

echo Stopping frontend processes...
taskkill /F /FI "WINDOWTITLE eq Powerhouse - Frontend*" 2>nul
taskkill /F /FI "WINDOWTITLE eq *next*" 2>nul
echo.

echo [OK] All services stopped
echo.

REM Only pause if AUTO_MODE is not set to "auto" (interactive mode)
if /i not "%AUTO_MODE%"=="auto" (
    pause
)
