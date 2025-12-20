@echo off
setlocal enabledelayedexpansion
title Powerhouse - Quick Install (First Time Setup)
color 0B

echo ================================================================
echo   POWERHOUSE - QUICK INSTALL (FIRST TIME SETUP)
echo ================================================================
echo.
echo This installer is optimized for first-time users.
echo Estimated time: 2-3 minutes (vs 10+ minutes normally)
echo.
echo What this does:
echo   1. Checks prerequisites
echo   2. Sets up environment files (if missing)
echo   3. Starts services with Docker (fast startup)
echo   4. Verifies everything is working
echo.
pause
echo.

REM Change to script directory
cd /d "%~dp0"

REM ================================================================
REM STEP 1: Check Prerequisites
REM ================================================================
echo [1/4] Checking Prerequisites...
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH.
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    echo After installing Docker Desktop, restart this script.
    pause
    exit /b 1
)
echo [OK] Docker found
docker --version

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running.
    echo.
    echo Please start Docker Desktop and wait for it to fully start,
    echo then run this script again.
    pause
    exit /b 1
)
echo [OK] Docker is running
echo.

REM ================================================================
REM STEP 2: Create Environment Files (if missing)
REM ================================================================
echo [2/4] Setting up configuration files...
echo.

REM Backend .env
if not exist "backend\.env" (
    echo Creating backend\.env...
    (
        echo # Database Configuration
        echo DB_HOST=postgres
        echo DB_PORT=5432
        echo DB_USER=postgres
        echo DB_PASSWORD=postgres
        echo DB_NAME=powerhouse
        echo DATABASE_URL=postgresql://postgres:postgres@postgres:5432/powerhouse
        echo.
        echo # Redis Configuration
        echo REDIS_HOST=redis
        echo REDIS_PORT=6379
        echo REDIS_URL=redis://powerhouse_redis:6379/0
        echo.
        echo # Security
        echo SECRET_KEY=your-secret-key-change-in-production-use-minimum-32-chars
        echo JWT_SECRET_KEY=your-jwt-secret-key-change-in-production-use-minimum-32-chars
    ) > "backend\.env"
    echo [OK] Created backend\.env
) else (
    echo [OK] backend\.env already exists
)

REM Frontend .env
if not exist "frontend\app\.env" (
    echo Creating frontend\app\.env...
    (
        echo # Next.js Environment Variables
        echo NEXT_PUBLIC_API_URL=http://localhost:8001
        echo NEXT_PUBLIC_APP_URL=http://localhost:3000
        echo NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
    ) > "frontend\app\.env"
    echo [OK] Created frontend\app\.env
) else (
    echo [OK] frontend\app\.env already exists
)
echo.

REM ================================================================
REM STEP 3: Quick Start Services (Docker only, no build)
REM ================================================================
echo [3/4] Starting services (fast mode - using existing images)...
echo.

REM Stop any existing containers
echo Stopping any existing containers...
docker-compose down >nul 2>&1

REM Start database and Redis (fast - just containers)
echo Starting database and Redis...
docker-compose up -d postgres redis
if errorlevel 1 (
    echo [ERROR] Failed to start database/Redis
    echo This might be your first time - pulling images...
    echo This will take 2-3 minutes...
    docker-compose pull postgres redis
    docker-compose up -d postgres redis
    if errorlevel 1 (
        echo [ERROR] Failed to start services
        pause
        exit /b 1
    )
)

REM Wait for database to be ready
echo Waiting for database to be ready...
timeout /t 8 /nobreak >nul

REM Check if backend/frontend images exist, if not, build them
echo Checking if services need to be built...
docker images | findstr "powerhouse-platform-backend" >nul
if errorlevel 1 (
    echo Backend image not found - building (this takes ~5 minutes first time)...
    docker-compose build backend
)

docker images | findstr "powerhouse-platform-frontend" >nul
if errorlevel 1 (
    echo Frontend image not found - building (this takes ~3 minutes first time)...
    docker-compose build frontend
)

REM Start all services
echo Starting all services...
docker-compose up -d

if errorlevel 1 (
    echo [ERROR] Failed to start services
    pause
    exit /b 1
)

echo [OK] Services started
echo.

REM ================================================================
REM STEP 4: Verify Installation
REM ================================================================
echo [4/4] Verifying installation...
echo.

REM Wait a bit for services to initialize
echo Waiting for services to initialize...
timeout /t 15 /nobreak >nul

REM Check database
echo Checking database...
docker-compose ps postgres | findstr "healthy" >nul
if errorlevel 1 (
    echo [WARN] Database may still be initializing...
) else (
    echo [OK] Database is healthy
)

REM Check Redis
echo Checking Redis...
docker-compose ps redis | findstr "healthy" >nul
if errorlevel 1 (
    echo [WARN] Redis may still be initializing...
) else (
    echo [OK] Redis is healthy
)

REM Check backend (if available)
echo Checking backend...
timeout /t 10 /nobreak >nul
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo [INFO] Backend is still starting (may take 30-60 seconds more)...
) else (
    echo [OK] Backend is responding
)

REM Check frontend
echo Checking frontend...
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo [INFO] Frontend is still starting (may take 30-60 seconds more)...
) else (
    echo [OK] Frontend is responding
)

echo.
echo ================================================================
echo   INSTALLATION COMPLETE!
echo ================================================================
echo.
echo Services are starting up. You can access:
echo.
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8001
echo   Health:    http://localhost:8001/health
echo.
echo Note: Services may take 30-60 seconds to fully initialize
echo       on first startup. Refresh the browser if you see errors.
echo.
echo To check service status:
echo   docker-compose ps
echo.
echo To view logs:
echo   docker-compose logs -f
echo.
echo To stop all services:
echo   docker-compose down
echo.
pause

