@echo off
setlocal enabledelayedexpansion
title Powerhouse - First Time Setup Wizard
color 0E

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║        POWERHOUSE - FIRST TIME SETUP WIZARD                ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo Welcome! This wizard will help you get Powerhouse running
echo in the fastest way possible.
echo.
echo Estimated time: 3-5 minutes (first time)
echo                  ~30 seconds (subsequent runs)
echo.
pause
echo.

cd /d "%~dp0"

REM ================================================================
REM Step 1: Prerequisites Check
REM ================================================================
echo [STEP 1/5] Checking Prerequisites...
echo.

set MISSING_PREREQ=0

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [✗] Docker Desktop is NOT installed
    set MISSING_PREREQ=1
) else (
    echo [✓] Docker Desktop is installed
    docker --version
    
    REM Check if running
    docker ps >nul 2>&1
    if errorlevel 1 (
        echo [✗] Docker Desktop is NOT running
        echo.
        echo Please:
        echo   1. Open Docker Desktop
        echo   2. Wait for it to fully start (whale icon in system tray)
        echo   3. Run this script again
        pause
        exit /b 1
    ) else (
        echo [✓] Docker Desktop is running
    )
)
echo.

if !MISSING_PREREQ! equ 1 (
    echo ─────────────────────────────────────────────────────────
    echo MISSING PREREQUISITES DETECTED
    echo ─────────────────────────────────────────────────────────
    echo.
    echo Docker Desktop is required. Please install it from:
    echo.
    echo   https://www.docker.com/products/docker-desktop/
    echo.
    echo After installation:
    echo   1. Start Docker Desktop
    echo   2. Wait for it to fully initialize
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)

REM ================================================================
REM Step 2: Configuration Setup
REM ================================================================
echo [STEP 2/5] Setting up configuration files...
echo.

if not exist "backend\.env" (
    echo Creating backend configuration...
    powershell -Command "@'
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=powerhouse
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/powerhouse
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://powerhouse_redis:6379/0
SECRET_KEY=your-secret-key-change-in-production-use-minimum-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production-use-minimum-32-chars
'@ | Out-File -FilePath 'backend\.env' -Encoding utf8"
    echo [✓] Created backend\.env
) else (
    echo [✓] backend\.env already exists
)

if not exist "frontend\app\.env" (
    echo Creating frontend configuration...
    powershell -Command "@'
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
'@ | Out-File -FilePath 'frontend\app\.env' -Encoding utf8"
    echo [✓] Created frontend\app\.env
) else (
    echo [✓] frontend\app\.env already exists
)
echo.

REM ================================================================
REM Step 3: Check for Existing Images
REM ================================================================
echo [STEP 3/5] Checking Docker images...
echo.

docker images | findstr "powerhouse-platform-backend" >nul
set HAS_BACKEND=%errorlevel%

docker images | findstr "powerhouse-platform-frontend" >nul
set HAS_FRONTEND=%errorlevel%

if !HAS_BACKEND! equ 0 (
    echo [✓] Backend image found
) else (
    echo [⚠] Backend image not found (will build on first start)
)

if !HAS_FRONTEND! equ 0 (
    echo [✓] Frontend image found
) else (
    echo [⚠] Frontend image not found (will build on first start)
)
echo.

REM ================================================================
REM Step 4: Pre-pull base images (faster startup)
REM ================================================================
echo [STEP 4/5] Preparing base images...
echo.
echo This ensures faster startup by downloading base images now.
echo (This only happens once)
echo.

docker pull postgres:15-alpine >nul 2>&1
if errorlevel 1 (
    echo [⚠] Could not pre-pull postgres image (will pull when starting)
) else (
    echo [✓] PostgreSQL image ready
)

docker pull redis:7-alpine >nul 2>&1
if errorlevel 1 (
    echo [⚠] Could not pre-pull redis image (will pull when starting)
) else (
    echo [✓] Redis image ready
)
echo.

REM ================================================================
REM Step 5: Start Services
REM ================================================================
echo [STEP 5/5] Starting Powerhouse services...
echo.

REM Stop any existing
docker-compose down >nul 2>&1

REM Build if needed (only if images don't exist)
if !HAS_BACKEND! neq 0 (
    echo Building backend image (this takes ~5 minutes first time)...
    echo Please be patient...
    docker-compose build backend
    if errorlevel 1 (
        echo [✗] Backend build failed
        pause
        exit /b 1
    )
)

if !HAS_FRONTEND! neq 0 (
    echo Building frontend image (this takes ~3 minutes first time)...
    echo Please be patient...
    docker-compose build frontend
    if errorlevel 1 (
        echo [✗] Frontend build failed
        pause
        exit /b 1
    )
)

echo Starting all services...
docker-compose up -d

if errorlevel 1 (
    echo [✗] Failed to start services
    echo.
    echo Try running: docker-compose logs
    pause
    exit /b 1
)

echo [✓] Services started!
echo.

REM ================================================================
REM Wait and Verify
REM ================================================================
echo Waiting for services to initialize...
echo (This takes 20-30 seconds on first startup)
echo.

for /L %%i in (1,1,30) do (
    timeout /t 1 /nobreak >nul
    set /a remaining=30-%%i
    if !remaining! gtr 0 (
        echo [!remaining! seconds remaining...]
    )
)

echo.
echo Checking service status...
echo.

REM Check database
docker-compose ps postgres | findstr "healthy" >nul
if errorlevel 1 (
    echo [⚠] Database: Starting...
) else (
    echo [✓] Database: Healthy
)

REM Check Redis
docker-compose ps redis | findstr "healthy" >nul
if errorlevel 1 (
    echo [⚠] Redis: Starting...
) else (
    echo [✓] Redis: Healthy
)

REM Check backend
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo [⚠] Backend: Still starting (may take 30-60 more seconds)
) else (
    echo [✓] Backend: Running
)

REM Check frontend
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo [⚠] Frontend: Still starting (may take 30-60 more seconds)
) else (
    echo [✓] Frontend: Running
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║              SETUP COMPLETE!                               ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo Your Powerhouse installation is ready!
echo.
echo Access your application:
echo   🌐 Frontend:  http://localhost:3000
echo   🔧 Backend:   http://localhost:8001
echo   ❤️  Health:    http://localhost:8001/health
echo.
echo Note: If services show as "Starting", they may need another
echo       30-60 seconds to fully initialize. Just refresh your browser!
echo.
echo Quick Commands:
echo   • Check status:  docker-compose ps
echo   • View logs:     docker-compose logs -f
echo   • Stop all:      docker-compose down
echo   • Restart:       docker-compose restart
echo.
echo Next time you want to start Powerhouse, just run:
echo   docker-compose up -d
echo.
echo Or use the desktop app installer you built!
echo.
pause

