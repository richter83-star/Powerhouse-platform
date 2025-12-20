@echo off
setlocal enabledelayedexpansion
title Powerhouse - Docker-Only Install (Fastest!)
color 0E

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║     POWERHOUSE - DOCKER-ONLY INSTALL (FASTEST WAY!)       ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo This installer runs EVERYTHING in Docker - no need to install
echo Python or Node.js on your computer!
echo.
echo ✅ Fastest setup (only Docker required)
echo ✅ No local dependencies (Python/Node.js not needed)
echo ✅ Easy to uninstall (just delete containers)
echo ✅ Works the same on any computer
echo.
echo Estimated time:
echo   • First time: 5-8 minutes (downloading images)
echo   • Next time:  30 seconds (everything cached)
echo.
pause
echo.

cd /d "%~dp0"

REM ================================================================
REM Check Docker
REM ================================================================
echo [1/3] Checking Docker...
echo.

docker --version >nul 2>&1
if errorlevel 1 (
    echo [✗] Docker Desktop is NOT installed
    echo.
    echo Please install Docker Desktop:
    echo   1. Download from: https://www.docker.com/products/docker-desktop/
    echo   2. Install and start Docker Desktop
    echo   3. Wait for Docker to fully start (whale icon in system tray)
    echo   4. Run this script again
    echo.
    pause
    exit /b 1
)

docker ps >nul 2>&1
if errorlevel 1 (
    echo [✗] Docker is installed but NOT running
    echo.
    echo Please:
    echo   1. Open Docker Desktop
    echo   2. Wait for it to fully start
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)

echo [✓] Docker is ready!
docker --version
echo.

REM ================================================================
REM Create environment files
REM ================================================================
echo [2/3] Setting up configuration...
echo.

if not exist "backend\.env" (
    echo Creating backend\.env...
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
    echo [✓] Created
)

if not exist "frontend\app\.env" (
    echo Creating frontend\app\.env...
    powershell -Command "@'
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
'@ | Out-File -FilePath 'frontend\app\.env' -Encoding utf8"
    echo [✓] Created
)

echo [✓] Configuration ready
echo.

REM ================================================================
REM Pre-download images for faster startup
REM ================================================================
echo [3/3] Preparing Docker images...
echo.

echo This may take a few minutes the first time...
echo (Images are cached, so future startups are instant!)
echo.

REM Pre-pull base images
echo Downloading base images...
docker pull postgres:15-alpine >nul 2>&1
docker pull redis:7-alpine >nul 2>&1
echo [✓] Base images ready

REM Check if application images exist
docker images | findstr "powerhouse-platform-backend" >nul
if errorlevel 1 (
    echo.
    echo Building backend image...
    echo (This takes ~5 minutes first time - please be patient)
    echo.
    docker-compose build backend
    if errorlevel 1 (
        echo [✗] Backend build failed
        pause
        exit /b 1
    )
    echo [✓] Backend image built
) else (
    echo [✓] Backend image found (using cached version)
)

docker images | findstr "powerhouse-platform-frontend" >nul
if errorlevel 1 (
    echo.
    echo Building frontend image...
    echo (This takes ~3 minutes first time - please be patient)
    echo.
    docker-compose build frontend
    if errorlevel 1 (
        echo [✗] Frontend build failed
        pause
        exit /b 1
    )
    echo [✓] Frontend image built
) else (
    echo [✓] Frontend image found (using cached version)
)

echo.
echo [✓] All images ready!
echo.

REM ================================================================
REM Start services
REM ================================================================
echo Starting Powerhouse services...
echo.

docker-compose down >nul 2>&1
docker-compose up -d

if errorlevel 1 (
    echo [✗] Failed to start services
    pause
    exit /b 1
)

echo [✓] Services starting...
echo.

REM ================================================================
REM Wait and verify
REM ================================================================
echo Waiting for services to initialize...
echo (This takes 20-30 seconds)
echo.

for /L %%i in (1,1,20) do (
    timeout /t 1 /nobreak >nul
    set /a remaining=20-%%i
    if !remaining! gtr 0 (
        echo [!remaining! seconds...]
    )
)

echo.
echo Checking service status...
echo.

docker-compose ps postgres | findstr "healthy" >nul
if errorlevel 0 (
    echo [✓] Database: Healthy
) else (
    echo [⚠] Database: Starting...
)

docker-compose ps redis | findstr "healthy" >nul
if errorlevel 0 (
    echo [✓] Redis: Healthy
) else (
    echo [⚠] Redis: Starting...
)

timeout /t 10 /nobreak >nul
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo [⚠] Backend: Still starting (30-60 more seconds)
) else (
    echo [✓] Backend: Running
)

curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo [⚠] Frontend: Still starting (30-60 more seconds)
) else (
    echo [✓] Frontend: Running
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║              INSTALLATION COMPLETE!                        ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 🎉 Powerhouse is now running!
echo.
echo Access your application:
echo   🌐 Frontend:  http://localhost:3000
echo   🔧 Backend:   http://localhost:8001
echo   ❤️  Health:    http://localhost:8001/health
echo.
echo Note: If services show as "Starting", wait 30-60 seconds
echo       and refresh your browser. They're still initializing!
echo.
echo ─────────────────────────────────────────────────────────────
echo Quick Commands:
echo ─────────────────────────────────────────────────────────────
echo.
echo Start services:     docker-compose up -d
echo Stop services:      docker-compose down
echo View logs:          docker-compose logs -f
echo Check status:       docker-compose ps
echo Restart:            docker-compose restart
echo.
echo ─────────────────────────────────────────────────────────────
echo Next Time:
echo ─────────────────────────────────────────────────────────────
echo.
echo Just run: docker-compose up -d
echo Or use:   START_POWERHOUSE_FULL.bat
echo.
echo Future startups will be instant (~30 seconds)!
echo.
pause

