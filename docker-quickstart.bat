@echo off
REM Docker Quick Start Script for Powerhouse Platform (Windows)
REM This script provides a simple way to start the Powerhouse Platform with Docker

setlocal enabledelayedexpansion
title Powerhouse Platform - Docker Quick Start
color 0B

echo.
echo ================================================================
echo                                                           
echo         Powerhouse Platform - Docker Quick Start          
echo                                                           
echo ================================================================
echo.

REM Check for build flag
set BUILD=false
set LOGS=false

:parse_args
if "%~1"=="" goto end_parse
if /i "%~1"=="--build" set BUILD=true
if /i "%~1"=="-b" set BUILD=true
if /i "%~1"=="--logs" set LOGS=true
if /i "%~1"=="-l" set LOGS=true
if /i "%~1"=="--help" goto show_help
if /i "%~1"=="-h" goto show_help
shift
goto parse_args

:show_help
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   -b, --build    Build Docker images before starting
echo   -l, --logs     Show logs after starting
echo   -h, --help     Show this help message
echo.
pause
exit /b 0

:end_parse

REM ================================================================
REM Check Docker
REM ================================================================
echo [1/4] Checking Docker installation...
echo.

docker --version >nul 2>&1
if errorlevel 1 (
    echo [X] Docker is NOT installed
    echo.
    echo Please install Docker Desktop from:
    echo   https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

docker ps >nul 2>&1
if errorlevel 1 (
    echo [X] Docker is NOT running
    echo.
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo [OK] Docker is installed and running
docker --version
echo.

REM ================================================================
REM Check Docker Compose
REM ================================================================
echo [2/4] Checking Docker Compose...
echo.

docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo [X] Docker Compose is not available
        pause
        exit /b 1
    )
    set COMPOSE_CMD=docker compose
) else (
    set COMPOSE_CMD=docker-compose
)

echo [OK] Docker Compose is available
%COMPOSE_CMD% --version
echo.

REM ================================================================
REM Build images if requested
REM ================================================================
if "%BUILD%"=="true" (
    echo [3/4] Building Docker images...
    echo This may take 5-10 minutes on first run...
    echo.
    %COMPOSE_CMD% build
    if errorlevel 1 (
        echo [X] Failed to build images
        pause
        exit /b 1
    )
    echo [OK] Images built successfully
    echo.
)

REM ================================================================
REM Start services
REM ================================================================
echo [4/4] Starting Powerhouse Platform services...
echo.

%COMPOSE_CMD% up -d

if errorlevel 1 (
    echo [X] Failed to start services
    pause
    exit /b 1
)

echo [OK] Services started successfully
echo.

REM ================================================================
REM Wait for services to initialize
REM ================================================================
echo Waiting for services to initialize...
echo This may take 2-3 minutes (services have a lot to load)...
echo.

REM Simple wait loop - check status every 15 seconds
for /L %%i in (1,1,12) do (
    set /a remaining=180-%%i*15
    if !remaining! gtr 0 (
        echo Waiting... !remaining! seconds remaining...
    )
    timeout /t 15 /nobreak >nul 2>nul
)
echo.
echo Checking final service status...
echo.

%COMPOSE_CMD% ps
echo.

REM ================================================================
REM Show status and URLs
REM ================================================================
echo ================================================================
echo                    SERVICES STATUS                         
echo ================================================================
echo.

REM Final health checks
echo Performing final health checks...
echo.

REM Use a simple PowerShell script file to avoid inline command issues
echo try { $null = Invoke-WebRequest -Uri 'http://localhost:8001/health' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Write-Host 'OK' } catch { Write-Host 'FAIL' } > %TEMP%\check_backend.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File %TEMP%\check_backend.ps1 2>nul | findstr /C:"OK" >nul
if errorlevel 1 (
    echo [X] Backend: Not responding yet
    echo     Checking container status...
    %COMPOSE_CMD% ps backend 2>nul
    echo     View logs: %COMPOSE_CMD% logs backend
) else (
    echo [OK] Backend: Responding at http://localhost:8001/health
)
del %TEMP%\check_backend.ps1 2>nul

echo try { $null = Invoke-WebRequest -Uri 'http://localhost:3000' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Write-Host 'OK' } catch { Write-Host 'FAIL' } > %TEMP%\check_frontend.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File %TEMP%\check_frontend.ps1 2>nul | findstr /C:"OK" >nul
if errorlevel 1 (
    echo [X] Frontend: Not responding yet
    echo     Checking container status...
    %COMPOSE_CMD% ps frontend 2>nul
    echo     View logs: %COMPOSE_CMD% logs frontend
) else (
    echo [OK] Frontend: Responding at http://localhost:3000
)
del %TEMP%\check_frontend.ps1 2>nul

echo.
echo Access your application:
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8001
echo   Health:    http://localhost:8001/health
echo.

REM ================================================================
REM Open browser automatically
REM ================================================================
echo Opening application in browser...
timeout /t 2 /nobreak >nul 2>nul
start http://localhost:3000
echo.

REM ================================================================
REM Show logs or exit
REM ================================================================
if "%LOGS%"=="true" (
    echo Showing logs (Ctrl+C to exit)...
    echo.
    %COMPOSE_CMD% logs -f
) else (
    echo Quick Commands:
    echo   View logs:  %COMPOSE_CMD% logs -f
    echo   Stop:       %COMPOSE_CMD% down
    echo   Restart:    %COMPOSE_CMD% restart
    echo   Status:     %COMPOSE_CMD% ps
    echo.
    echo Note: Services may take 2-3 minutes to fully initialize.
    echo       If services don't respond, wait a bit and refresh.
    echo.
    pause
)

endlocal


