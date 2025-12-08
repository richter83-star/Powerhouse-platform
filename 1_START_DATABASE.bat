@echo off
title Powerhouse - Database
color 0A
echo ========================================
echo   POWERHOUSE DATABASE
echo ========================================
echo.
echo Starting PostgreSQL database...
echo.
docker-compose up -d
timeout /t 5 /nobreak >nul
echo.
echo [OK] Database is running on port 5433
echo.
pause
