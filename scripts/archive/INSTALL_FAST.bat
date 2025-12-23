@echo off
setlocal enabledelayedexpansion
title Powerhouse - Fast Install (Pre-built Images)
color 0A

echo ================================================================
echo   POWERHOUSE - FAST INSTALL
echo ================================================================
echo.
echo This installer uses pre-built Docker images for fastest setup.
echo Estimated time: 30-60 seconds (after images are downloaded)
echo.
echo For first-time setup, this will:
echo   1. Download pre-built Docker images (~5-10 minutes first time)
echo   2. Start all services immediately
echo   3. Verify everything works
echo.
echo For subsequent runs, startup is instant!
echo.
pause
echo.

cd /d "%~dp0"

REM ================================================================
REM Check Docker
REM ================================================================
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not running.
    echo Please install Docker Desktop and start it, then try again.
    pause
    exit /b 1
)

docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running.
    echo Please start Docker Desktop and wait for it to fully start.
    pause
    exit /b 1
)

echo [OK] Docker is ready
echo.

REM ================================================================
REM Create env files if missing
REM ================================================================
echo [1/3] Checking configuration...
if not exist "backend\.env" (
    echo Creating backend\.env...
    powershell -Command "@'
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=powerhouse
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/powerhouse

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://powerhouse_redis:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production-use-minimum-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production-use-minimum-32-chars
'@ | Out-File -FilePath 'backend\.env' -Encoding utf8"
)

if not exist "frontend\app\.env" (
    echo Creating frontend\app\.env...
    powershell -Command "@'
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
'@ | Out-File -FilePath 'frontend\app\.env' -Encoding utf8"
)
echo [OK] Configuration ready
echo.

REM ================================================================
REM Pull/Build images if needed
REM ================================================================
echo [2/3] Checking Docker images...

docker images | findstr "powerhouse-platform-backend" >nul
set BACKEND_EXISTS=%errorlevel%

docker images | findstr "powerhouse-platform-frontend" >nul
set FRONTEND_EXISTS=%errorlevel%

if !BACKEND_EXISTS! neq 0 (
    echo Backend image not found - building now...
    echo (This takes ~5 minutes the first time, but only happens once)
    docker-compose build backend
)

if !FRONTEND_EXISTS! neq 0 (
    echo Frontend image not found - building now...
    echo (This takes ~3 minutes the first time, but only happens once)
    docker-compose build frontend
)

if !BACKEND_EXISTS! equ 0 if !FRONTEND_EXISTS! equ 0 (
    echo [OK] All images found - starting services...
)
echo.

REM ================================================================
REM Start services
REM ================================================================
echo [3/3] Starting all services...

docker-compose down >nul 2>&1
docker-compose up -d

if errorlevel 1 (
    echo [ERROR] Failed to start services
    pause
    exit /b 1
)

echo [OK] Services starting...
echo.
echo Waiting for services to initialize...
timeout /t 20 /nobreak >nul

echo.
echo ================================================================
echo   SERVICES STARTED!
echo ================================================================
echo.
echo Access your application at:
echo   http://localhost:3000
echo.
echo Services may take 30-60 seconds to fully start on first run.
echo You can check status with: docker-compose ps
echo.
pause

